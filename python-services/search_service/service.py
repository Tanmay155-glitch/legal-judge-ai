"""
Semantic Search Engine - Legal case law search
Performs natural language search over case law corpus using vector similarity
"""

import os
from typing import List, Dict, Optional, Tuple
import numpy as np
from loguru import logger
import httpx

from shared.models import SearchResult, CaseLawDocument


class SemanticSearchEngine:
    """
    Service for semantic search over legal case law corpus.
    
    Features:
    - Natural language query search
    - Section-specific search (facts, reasoning, etc.)
    - Metadata filtering (year, court, judgment)
    - Result ranking with recency boost
    - Configurable similarity thresholds
    
    Uses:
    - Embedding service for query vectorization
    - Vector index service for similarity search
    """
    
    def __init__(
        self,
        embedding_service_url: str = "http://localhost:8001",
        vector_index_service: any = None,
        default_top_k: int = 10,
        min_similarity: float = 0.6,
        recency_boost_factor: float = 0.05,
        timeout: int = 30
    ):
        """
        Initialize the semantic search engine.
        
        Args:
            embedding_service_url: URL of embedding service
            vector_index_service: VectorIndexService instance
            default_top_k: Default number of results to return
            min_similarity: Minimum similarity threshold (0.0-1.0)
            recency_boost_factor: Boost factor for newer cases (2023 > 2022)
            timeout: HTTP request timeout in seconds
        """
        self.embedding_service_url = embedding_service_url
        self.vector_index_service = vector_index_service
        self.default_top_k = default_top_k
        self.min_similarity = min_similarity
        self.recency_boost_factor = recency_boost_factor
        self.timeout = timeout
        
        logger.info("Initializing SemanticSearchEngine")
        logger.info(f"Embedding Service: {embedding_service_url}")
        logger.info(f"Default top_k: {default_top_k}")
        logger.info(f"Min similarity: {min_similarity}")
    
    async def search(
        self,
        query: str,
        top_k: int = None,
        section_filter: str = None,
        year_range: Tuple[int, int] = None,
        min_similarity: float = None
    ) -> List[SearchResult]:
        """
        Execute semantic search with natural language query.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return (uses default if None)
            section_filter: Filter by section type (facts, issue, reasoning, holding)
            year_range: Tuple of (min_year, max_year) for filtering
            min_similarity: Minimum similarity score (uses default if None)
        
        Returns:
            List of SearchResult objects ranked by relevance
        
        Example:
            results = await engine.search(
                query="landlord breach of warranty habitability",
                top_k=10,
                section_filter="reasoning",
                year_range=(2022, 2023)
            )
        """
        top_k = top_k or self.default_top_k
        min_similarity = min_similarity or self.min_similarity
        
        logger.info(f"Searching for: '{query}'")
        logger.info(f"Parameters: top_k={top_k}, section={section_filter}, "
                   f"year_range={year_range}, min_sim={min_similarity}")
        
        try:
            # Step 1: Generate query embedding
            query_embedding = await self._generate_query_embedding(query)
            
            # Step 2: Build filters
            filters = self._build_filters(section_filter, year_range)
            
            # Step 3: Perform vector search
            # Request more results than needed for ranking
            search_top_k = top_k * 2 if year_range else top_k
            
            raw_results = self.vector_index_service.search_similar(
                query_vector=query_embedding,
                top_k=search_top_k,
                filters=filters,
                score_threshold=min_similarity
            )
            
            # Step 4: Rank results with recency boost
            ranked_results = self._rank_results(raw_results, year_range)
            
            # Step 5: Format and return top_k results
            search_results = self._format_results(ranked_results[:top_k])
            
            logger.success(f"Found {len(search_results)} results")
            return search_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def search_by_facts(
        self,
        facts: str,
        top_k: int = None,
        year_range: Tuple[int, int] = None
    ) -> List[SearchResult]:
        """
        Search specifically in facts sections.
        
        Args:
            facts: Facts text to search for
            top_k: Number of results
            year_range: Year range filter
        
        Returns:
            List of SearchResult objects from facts sections
        """
        logger.info("Searching in facts sections")
        return await self.search(
            query=facts,
            top_k=top_k,
            section_filter="facts",
            year_range=year_range
        )
    
    async def search_by_reasoning(
        self,
        legal_issue: str,
        top_k: int = None,
        year_range: Tuple[int, int] = None
    ) -> List[SearchResult]:
        """
        Search specifically in reasoning sections.
        
        Args:
            legal_issue: Legal issue or reasoning to search for
            top_k: Number of results
            year_range: Year range filter
        
        Returns:
            List of SearchResult objects from reasoning sections
        """
        logger.info("Searching in reasoning sections")
        return await self.search(
            query=legal_issue,
            top_k=top_k,
            section_filter="reasoning",
            year_range=year_range
        )
    
    async def get_similar_cases(
        self,
        case_id: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Find cases similar to a given case.
        
        Args:
            case_id: Document ID of the reference case
            top_k: Number of similar cases to return
        
        Returns:
            List of similar cases
        """
        logger.info(f"Finding cases similar to: {case_id}")
        
        # This would require retrieving the case's vectors and searching
        # For now, this is a placeholder for future implementation
        raise NotImplementedError("get_similar_cases not yet implemented")
    
    async def _generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for search query.
        
        Args:
            query: Search query text
        
        Returns:
            Query embedding vector
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.embedding_service_url}/embed/text",
                    json={"text": query, "normalize": True}
                )
                response.raise_for_status()
                
                data = response.json()
                embedding = np.array(data['embedding'])
                
                logger.debug(f"Generated query embedding: {embedding.shape}")
                return embedding
            
            except httpx.HTTPError as e:
                logger.error(f"Embedding service error: {e}")
                raise
    
    def _build_filters(
        self,
        section_filter: str = None,
        year_range: Tuple[int, int] = None
    ) -> Dict:
        """
        Build metadata filters for vector search.
        
        Args:
            section_filter: Section type to filter by
            year_range: Year range (min, max)
        
        Returns:
            Filter dictionary for Qdrant
        """
        filters = {}
        
        if section_filter:
            filters['section_type'] = section_filter
            logger.debug(f"Filter: section_type={section_filter}")
        
        if year_range:
            min_year, max_year = year_range
            # For Qdrant, we'll need to handle range filters differently
            # For now, we'll search and filter in post-processing
            logger.debug(f"Filter: year_range={year_range}")
        
        return filters
    
    def _rank_results(
        self,
        results: List[Dict],
        year_range: Tuple[int, int] = None
    ) -> List[Dict]:
        """
        Rank search results with recency boost.
        
        Ranking algorithm:
        1. Primary: Cosine similarity score
        2. Secondary: Recency boost (2023 > 2022)
        3. Tertiary: Section relevance (exact match gets boost)
        
        Args:
            results: Raw search results from vector index
            year_range: Year range for filtering
        
        Returns:
            Ranked results
        """
        if not results:
            return []
        
        # Apply year range filter if specified
        if year_range:
            min_year, max_year = year_range
            results = [
                r for r in results
                if min_year <= r['payload'].get('year', 0) <= max_year
            ]
        
        # Calculate adjusted scores with recency boost
        for result in results:
            base_score = result['score']
            year = result['payload'].get('year', 2022)
            
            # Recency boost: 2023 cases get higher boost
            if year == 2023:
                recency_boost = self.recency_boost_factor
            elif year == 2022:
                recency_boost = 0.0
            else:
                recency_boost = -self.recency_boost_factor
            
            # Adjusted score
            result['adjusted_score'] = min(1.0, base_score + recency_boost)
        
        # Sort by adjusted score
        ranked = sorted(results, key=lambda x: x['adjusted_score'], reverse=True)
        
        logger.debug(f"Ranked {len(ranked)} results")
        return ranked
    
    def _format_results(self, results: List[Dict]) -> List[SearchResult]:
        """
        Format raw results into SearchResult objects.
        
        Args:
            results: Ranked search results
        
        Returns:
            List of SearchResult objects
        """
        search_results = []
        
        for result in results:
            payload = result['payload']
            
            # Extract snippet (first 500 chars of text content)
            snippet = payload.get('text_content', '')[:500]
            if not snippet:
                # Fallback: create snippet from available data
                snippet = f"Case: {payload.get('case_name', 'Unknown')}"
            
            # Create SearchResult
            search_result = SearchResult(
                case_name=payload.get('case_name', 'Unknown'),
                year=payload.get('year', 0),
                court=payload.get('court', 'Unknown'),
                section_type=payload.get('section_type', 'unknown'),
                similarity_score=result.get('adjusted_score', result['score']),
                snippet=snippet,
                metadata=payload
            )
            
            search_results.append(search_result)
        
        return search_results
    
    def get_search_stats(self) -> Dict:
        """
        Get search engine statistics.
        
        Returns:
            Dictionary with search statistics
        """
        if not self.vector_index_service:
            return {"error": "Vector index service not configured"}
        
        try:
            collection_info = self.vector_index_service.get_collection_info()
            return {
                "total_vectors": collection_info.get('vectors_count', 0),
                "total_documents": collection_info.get('points_count', 0) // 4,  # Approx
                "collection_status": collection_info.get('status', 'unknown'),
                "default_top_k": self.default_top_k,
                "min_similarity": self.min_similarity
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


# Singleton instance
_search_engine_instance = None


def get_search_engine(
    embedding_service_url: str = None,
    vector_index_service: any = None,
    default_top_k: int = 10,
    min_similarity: float = 0.6
) -> SemanticSearchEngine:
    """
    Get or create the singleton SemanticSearchEngine instance.
    
    Args:
        embedding_service_url: Embedding service URL (only used on first call)
        vector_index_service: VectorIndexService instance (only used on first call)
        default_top_k: Default top_k (only used on first call)
        min_similarity: Min similarity (only used on first call)
    
    Returns:
        SemanticSearchEngine instance
    """
    global _search_engine_instance
    
    if _search_engine_instance is None:
        embedding_service_url = embedding_service_url or os.getenv(
            "EMBEDDING_SERVICE_URL",
            "http://localhost:8001"
        )
        
        default_top_k = int(os.getenv("DEFAULT_TOP_K", default_top_k))
        min_similarity = float(os.getenv("MIN_SIMILARITY_THRESHOLD", min_similarity))
        
        _search_engine_instance = SemanticSearchEngine(
            embedding_service_url=embedding_service_url,
            vector_index_service=vector_index_service,
            default_top_k=default_top_k,
            min_similarity=min_similarity
        )
    
    return _search_engine_instance
