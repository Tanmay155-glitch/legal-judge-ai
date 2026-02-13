"""
Vector Index Service - Qdrant integration
Stores and retrieves case law embeddings using Qdrant vector database
"""

import os
from typing import List, Dict, Optional, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from loguru import logger
import uuid


class VectorIndexService:
    """
    Service for managing vector storage and retrieval using Qdrant.
    
    Features:
    - Create and manage collections
    - Index document vectors with metadata
    - Similarity search with filtering
    - Duplicate prevention
    - Batch operations
    """
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "supreme_court_cases",
        vector_size: int = 768,
        distance: str = "Cosine"
    ):
        """
        Initialize the vector index service with Qdrant client.
        
        Args:
            qdrant_url: URL of Qdrant server
            collection_name: Name of the collection to use
            vector_size: Dimension of vectors (768 for Legal-BERT)
            distance: Distance metric (Cosine, Dot, Euclid)
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        
        logger.info(f"Initializing VectorIndexService")
        logger.info(f"Qdrant URL: {qdrant_url}")
        logger.info(f"Collection: {collection_name}")
        
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(url=qdrant_url)
            logger.success("Successfully connected to Qdrant")
            
            # Verify connection
            collections = self.client.get_collections()
            logger.info(f"Found {len(collections.collections)} existing collections")
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def create_collection(
        self,
        collection_name: str = None,
        vector_size: int = None,
        distance: str = None,
        recreate: bool = False
    ) -> bool:
        """
        Create a vector collection with specified configuration.
        
        Args:
            collection_name: Name of collection (uses default if None)
            vector_size: Vector dimension (uses default if None)
            distance: Distance metric (uses default if None)
            recreate: If True, delete existing collection first
        
        Returns:
            True if collection was created, False if already exists
        """
        collection_name = collection_name or self.collection_name
        vector_size = vector_size or self.vector_size
        distance = distance or self.distance
        
        # Map distance string to Qdrant Distance enum
        distance_map = {
            "Cosine": models.Distance.COSINE,
            "Dot": models.Distance.DOT,
            "Euclid": models.Distance.EUCLID
        }
        distance_metric = distance_map.get(distance, models.Distance.COSINE)
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)
            
            if exists:
                if recreate:
                    logger.warning(f"Deleting existing collection: {collection_name}")
                    self.client.delete_collection(collection_name)
                else:
                    logger.info(f"Collection '{collection_name}' already exists")
                    return False
            
            # Create collection
            logger.info(f"Creating collection '{collection_name}' with vector size {vector_size}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=distance_metric
                )
            )
            
            logger.success(f"Successfully created collection: {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def index_document(
        self,
        doc_id: str,
        vectors: Dict[str, np.ndarray],
        metadata: dict
    ) -> List[str]:
        """
        Index a document with multiple section vectors.
        
        Args:
            doc_id: Unique document identifier
            vectors: Dictionary mapping section types to vectors
                    e.g., {"facts": vector1, "issue": vector2, ...}
            metadata: Document metadata (case_name, year, court, etc.)
        
        Returns:
            List of vector IDs that were indexed
        
        Example:
            vector_ids = service.index_document(
                doc_id="case-123",
                vectors={
                    "facts": facts_vector,
                    "issue": issue_vector,
                    "reasoning": reasoning_vector
                },
                metadata={
                    "case_name": "Doe v. Smith",
                    "year": 2023,
                    "court": "Supreme Court of the United States"
                }
            )
        """
        if not vectors:
            raise ValueError("Vectors dictionary cannot be empty")
        
        points = []
        vector_ids = []
        
        for section_type, vector in vectors.items():
            if vector is None:
                logger.warning(f"Skipping None vector for section '{section_type}'")
                continue
            
            # Convert to numpy array if needed
            if not isinstance(vector, np.ndarray):
                vector = np.array(vector)
            
            # Validate vector dimension
            if len(vector) != self.vector_size:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self.vector_size}, "
                    f"got {len(vector)} for section '{section_type}'"
                )
            
            # Create unique ID for this vector
            vector_id = f"{doc_id}_{section_type}"
            vector_ids.append(vector_id)
            
            # Combine metadata with section-specific info
            payload = {
                **metadata,
                "document_id": doc_id,
                "section_type": section_type,
                "vector_id": vector_id
            }
            
            # Create point
            points.append(
                models.PointStruct(
                    id=vector_id,
                    vector=vector.tolist(),
                    payload=payload
                )
            )
        
        if not points:
            raise ValueError("No valid vectors to index")
        
        try:
            logger.info(f"Indexing {len(points)} vectors for document '{doc_id}'")
            
            # Upsert points (insert or update)
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.success(f"Successfully indexed {len(points)} vectors")
            return vector_ids
        
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            raise
    
    def search_similar(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: dict = None,
        score_threshold: float = None
    ) -> List[Dict]:
        """
        Perform similarity search against indexed vectors.
        
        Args:
            query_vector: Query vector to search for
            top_k: Number of results to return
            filters: Optional metadata filters
                    e.g., {"section_type": "reasoning", "year": 2023}
            score_threshold: Minimum similarity score (0.0 to 1.0)
        
        Returns:
            List of search results with scores and metadata
        
        Example:
            results = service.search_similar(
                query_vector=embedding,
                top_k=10,
                filters={"section_type": "reasoning", "year": 2023},
                score_threshold=0.6
            )
        """
        # Convert to numpy array if needed
        if not isinstance(query_vector, np.ndarray):
            query_vector = np.array(query_vector)
        
        # Validate vector dimension
        if len(query_vector) != self.vector_size:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.vector_size}, "
                f"got {len(query_vector)}"
            )
        
        # Build filter conditions
        filter_conditions = None
        if filters:
            must_conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    # Multiple values (OR condition)
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value)
                        )
                    )
                else:
                    # Single value
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
            
            if must_conditions:
                filter_conditions = models.Filter(must=must_conditions)
        
        try:
            logger.info(f"Searching for top {top_k} similar vectors")
            if filters:
                logger.debug(f"Filters: {filters}")
            
            # Perform search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=top_k,
                query_filter=filter_conditions,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            # Format results
            results = []
            for hit in search_results:
                result = {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                results.append(result)
            
            logger.success(f"Found {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def delete_document(self, doc_id: str) -> int:
        """
        Remove all vectors associated with a document.
        
        Args:
            doc_id: Document identifier
        
        Returns:
            Number of vectors deleted
        """
        try:
            logger.info(f"Deleting document: {doc_id}")
            
            # Delete by filter (all vectors with this document_id)
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=doc_id)
                            )
                        ]
                    )
                )
            )
            
            logger.success(f"Deleted document: {doc_id}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    def get_collection_info(self) -> dict:
        """
        Get information about the collection.
        
        Returns:
            Dictionary with collection metadata
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status,
                "vector_size": self.vector_size,
                "distance": self.distance
            }
        
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise
    
    def check_duplicate(self, case_name: str, year: int) -> Optional[str]:
        """
        Check if a document with the same case_name and year already exists.
        
        Args:
            case_name: Case name to check
            year: Year to check
        
        Returns:
            Document ID if duplicate found, None otherwise
        """
        try:
            # Search for exact match
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="case_name",
                            match=models.MatchValue(value=case_name)
                        ),
                        models.FieldCondition(
                            key="year",
                            match=models.MatchValue(value=year)
                        )
                    ]
                ),
                limit=1,
                with_payload=True
            )
            
            if results[0]:  # results is a tuple (points, next_page_offset)
                doc_id = results[0][0].payload.get("document_id")
                logger.info(f"Found duplicate: {case_name} ({year}) - doc_id: {doc_id}")
                return doc_id
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to check duplicate: {e}")
            return None


# Singleton instance
_vector_index_service_instance = None


def get_vector_index_service(
    qdrant_url: str = None,
    collection_name: str = None,
    vector_size: int = 768
) -> VectorIndexService:
    """
    Get or create the singleton VectorIndexService instance.
    
    Args:
        qdrant_url: Qdrant server URL (only used on first call)
        collection_name: Collection name (only used on first call)
        vector_size: Vector dimension (only used on first call)
    
    Returns:
        VectorIndexService instance
    """
    global _vector_index_service_instance
    
    if _vector_index_service_instance is None:
        qdrant_url = qdrant_url or os.getenv("QDRANT_HOST", "localhost")
        if not qdrant_url.startswith("http"):
            port = os.getenv("QDRANT_PORT", "6333")
            qdrant_url = f"http://{qdrant_url}:{port}"
        
        collection_name = collection_name or os.getenv(
            "QDRANT_COLLECTION_NAME",
            "supreme_court_cases"
        )
        
        _vector_index_service_instance = VectorIndexService(
            qdrant_url=qdrant_url,
            collection_name=collection_name,
            vector_size=vector_size
        )
    
    return _vector_index_service_instance
