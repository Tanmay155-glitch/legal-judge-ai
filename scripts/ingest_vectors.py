import requests
import json
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "legal_cases"
# Using a local embedding model (sentence-transformers) for bootstrapping
# In production, we should match the Rust-side Burn embedding
from sentence_transformers import SentenceTransformer

def main():
    print("Initializing Qdrant client...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Check if collection exists, if not create it
    collections = client.get_collections()
    if not any(c.name == COLLECTION_NAME for c in collections.collections):
        print(f"Creating collection '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=384,  # Matching mini-lm dimension
                distance=models.Distance.COSINE
            )
        )
    
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Download sample cases (using a specialized subset for demo if available, or CAP API)
    # For this script, I'll generate some dummy 'real-looking' data or fetch from a public source
    # Since we need 1000+, we would usually hit an API. 
    # For Phase 2A demo, I will simulate ingestion of the improved dataset (50 cases) we already made, 
    # plus generate variated synthetic ones to reach scale if needed, or better:
    # prompt the user to let me download from CourtListener if they have valid internet access.
    
    # Re-using the 50 cases from Phase 1 as the seed
    cases_path = r"c:\Users\Tanmay\OneDrive\Desktop\Project\legal-search-rust-mvp\backend-rust\data\cases.json"
    
    if os.path.exists(cases_path):
        with open(cases_path, 'r') as f:
            cases = json.load(f)
            
        print(f"Found {len(cases)} seed cases. Upserting to Vector DB...")
        
        points = []
        for i, case in enumerate(cases):
            # Embed the 'summary' + 'topic'
            text_to_embed = f"{case['topic']}: {case['summary']}"
            embedding = model.encode(text_to_embed).tolist()
            
            points.append(models.PointStruct(
                id=i + 1,
                vector=embedding,
                payload=case
            ))
            
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Successfully indexed {len(points)} cases.")
    else:
        print("Cases file not found. Please ensure Phase 1 data exists.")

if __name__ == "__main__":
    main()
