"""Vector search router for semantic question search in TalentSync Interview Service."""
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.dependencies.auth import get_current_user, User
from app.schemas.interview import VectorSearchRequest, VectorSearchResponse, VectorSearchResult
from app.services.pinecone_service import PineconeService

router = APIRouter()


@router.post("/vector", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest
) -> VectorSearchResponse:
    """
    Perform semantic vector search for similar questions.
    
    Args:
        request: Vector search request
        current_user: Authenticated user
        
    Returns:
        Search results with similarity scores
    """
    start_time = time.time()
    
    try:
        pinecone_service = PineconeService()
        
        # Perform semantic search
        results = await pinecone_service.search_similar_questions(
            query_text=request.query_text,
            domain=request.domain,
            question_type=request.question_type,
            top_k=request.top_k,
            exclude_ids=request.exclude_ids
        )
        
        # Calculate query time
        query_time = (time.time() - start_time) * 1000
        
        # Convert to response format
        search_results = []
        for result in results:
            search_results.append(VectorSearchResult(
                question_id=result.get('question_id', ''),
                text=result.get('text', ''),
                domain=result.get('domain', ''),
                difficulty=result.get('difficulty', ''),
                question_type=result.get('type', ''),
                similarity_score=result.get('similarity_score', 0.0),
                metadata=result.get('metadata')
            ))
        
        return VectorSearchResponse(
            results=search_results,
            total_found=len(search_results),
            query_time_ms=query_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Vector search failed: {str(e)}"
        )


@router.get("/similar/{question_id}")
async def find_similar_questions(
    question_id: str,
    top_k: int = Query(5, ge=1, le=20, description="Number of similar questions to return"),
    domain: Optional[str] = Query(None, description="Filter by domain")
) -> List[VectorSearchResult]:
    """
    Find questions similar to a specific question.
    
    Args:
        question_id: ID of the reference question
        top_k: Number of similar questions to return
        domain: Optional domain filter
        current_user: Authenticated user
        
    Returns:
        List of similar questions
    """
    try:
        pinecone_service = PineconeService()
        
        # For now, use a mock query - in production, you'd get the question text first
        mock_query = f"Find questions similar to question {question_id}"
        
        results = await pinecone_service.search_similar_questions(
            query_text=mock_query,
            domain=domain,
            top_k=top_k,
            exclude_ids=[question_id]
        )
        
        # Convert to response format
        search_results = []
        for result in results:
            search_results.append(VectorSearchResult(
                question_id=result.get('question_id', ''),
                text=result.get('text', ''),
                domain=result.get('domain', ''),
                difficulty=result.get('difficulty', ''),
                question_type=result.get('type', ''),
                similarity_score=result.get('similarity_score', 0.0),
                metadata=result.get('metadata')
            ))
        
        return search_results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find similar questions: {str(e)}"
        )


@router.post("/embedding")
async def get_embedding(
    text: str
) -> dict:
    """
    Get embedding for a text (admin only).
    
    Args:
        text: Text to embed
        current_user: Authenticated user (admin only)
        
    Returns:
        Embedding vector
    """
    try:
        # Check if user is admin
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        pinecone_service = PineconeService()
        
        # Get embedding
        embedding = await pinecone_service.get_embedding(text)
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "embedding_length": len(embedding),
            "embedding_preview": embedding[:5] + ["..."] if len(embedding) > 5 else embedding
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding: {str(e)}"
        )


@router.get("/stats")
async def get_search_stats() -> dict:
    """
    Get vector search statistics (admin only).
    
    Args:
        current_user: Authenticated user (admin only)
        
    Returns:
        Search statistics
    """
    try:
        # Check if user is admin
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        pinecone_service = PineconeService()
        
        # Get index statistics
        stats = await pinecone_service.get_index_stats()
        
        return {
            "service": "vector_search",
            "timestamp": time.time(),
            "index_stats": stats,
            "health": await pinecone_service.health_check()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve search stats: {str(e)}"
        )


@router.post("/test")
async def test_vector_search() -> dict:
    """
    Test vector search functionality with sample queries.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Test results
    """
    try:
        pinecone_service = PineconeService()
        
        # Test queries
        test_queries = [
            {
                "query": "What is the time complexity of binary search?",
                "domain": "dsa",
                "expected_type": "technical"
            },
            {
                "query": "How do you handle authentication in a microservices architecture?",
                "domain": "software-engineering",
                "expected_type": "technical"
            },
            {
                "query": "Explain the difference between supervised and unsupervised learning",
                "domain": "machine-learning",
                "expected_type": "conceptual"
            },
            {
                "query": "How do you deploy a machine learning model in production?",
                "domain": "ai-engineering",
                "expected_type": "technical"
            },
            {
                "query": "What are the key components of a CI/CD pipeline?",
                "domain": "devops",
                "expected_type": "technical"
            },
            {
                "query": "How do you handle missing data in a dataset?",
                "domain": "data-science",
                "expected_type": "technical"
            }
        ]
        
        results = []
        total_time = 0
        
        for i, test_query in enumerate(test_queries):
            start_time = time.time()
            
            try:
                search_results = await pinecone_service.search_similar_questions(
                    query_text=test_query["query"],
                    domain=test_query["domain"],
                    top_k=3
                )
                
                processing_time = (time.time() - start_time) * 1000
                total_time += processing_time
                
                results.append({
                    "test_case": i + 1,
                    "success": True,
                    "query": test_query["query"],
                    "domain": test_query["domain"],
                    "results_count": len(search_results),
                    "avg_similarity": sum(r.get('similarity_score', 0) for r in search_results) / len(search_results) if search_results else 0,
                    "processing_time_ms": processing_time
                })
                
            except Exception as e:
                results.append({
                    "test_case": i + 1,
                    "success": False,
                    "query": test_query["query"],
                    "error": str(e)
                })
        
        successful_tests = len([r for r in results if r["success"]])
        
        return {
            "test_results": results,
            "summary": {
                "total_tests": len(test_queries),
                "successful_tests": successful_tests,
                "success_rate": successful_tests / len(test_queries),
                "total_processing_time_ms": total_time,
                "avg_processing_time_ms": total_time / successful_tests if successful_tests > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run vector search tests: {str(e)}"
        )


@router.post("/batch")
async def batch_vector_search(
    queries: List[str],
    domain: Optional[str] = None,
    top_k: int = Query(5, ge=1, le=10, description="Number of results per query")
) -> dict:
    """
    Perform batch vector search for multiple queries.
    
    Args:
        queries: List of search queries
        domain: Optional domain filter
        top_k: Number of results per query
        current_user: Authenticated user
        
    Returns:
        Batch search results
    """
    try:
        if len(queries) > 20:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size too large (max 20)")
        
        pinecone_service = PineconeService()
        results = []
        total_time = 0
        
        for i, query in enumerate(queries):
            start_time = time.time()
            
            try:
                search_results = await pinecone_service.search_similar_questions(
                    query_text=query,
                    domain=domain,
                    top_k=top_k
                )
                
                processing_time = (time.time() - start_time) * 1000
                total_time += processing_time
                
                results.append({
                    "index": i,
                    "success": True,
                    "query": query,
                    "results_count": len(search_results),
                    "processing_time_ms": processing_time,
                    "results": search_results[:3]  # Limit results in response
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "query": query,
                    "error": str(e)
                })
        
        successful_queries = len([r for r in results if r["success"]])
        
        return {
            "batch_results": results,
            "summary": {
                "total_queries": len(queries),
                "successful_queries": successful_queries,
                "success_rate": successful_queries / len(queries),
                "total_processing_time_ms": total_time,
                "avg_processing_time_ms": total_time / successful_queries if successful_queries > 0 else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform batch vector search: {str(e)}"
        ) 