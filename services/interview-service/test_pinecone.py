"""
Test script for Pinecone & RAG Orchestration implementation.
Tests the embedding service and Pinecone integration.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.pinecone_service import PineconeService
from app.services.embedding_service import EmbeddingService


async def test_pinecone_initialization():
    """Test Pinecone service initialization."""
    print("Testing Pinecone initialization...")
    try:
        pinecone_service = PineconeService()
        print("✓ Pinecone service initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Pinecone initialization failed: {str(e)}")
        return False


async def test_embedding_generation():
    """Test embedding generation."""
    print("\nTesting embedding generation...")
    try:
        pinecone_service = PineconeService()
        
        test_text = "What is your experience with Python programming?"
        embedding = pinecone_service.get_embedding(test_text)
        
        print(f"✓ Generated embedding with {len(embedding)} dimensions")
        print(f"✓ First 5 values: {embedding[:5]}")
        return True
    except Exception as e:
        print(f"✗ Embedding generation failed: {str(e)}")
        return False


async def test_question_upsert():
    """Test question upsert functionality."""
    print("\nTesting question upsert...")
    try:
        pinecone_service = PineconeService()
        
        # Test question
        q_id = 999  # Use a test ID
        text = "Describe your experience with microservices architecture."
        metadata = {
            'domain': 'Software Engineering',
            'type': 'technical',
            'difficulty': 'medium'
        }
        
        # Upsert to Pinecone
        pinecone_service.upsert_question_embedding(q_id, text, metadata)
        print(f"✓ Successfully upserted question {q_id}")
        return True
    except Exception as e:
        print(f"✗ Question upsert failed: {str(e)}")
        return False


async def test_semantic_search():
    """Test semantic search functionality."""
    print("\nTesting semantic search...")
    try:
        pinecone_service = PineconeService()
        
        # Search for similar questions
        query = "Tell me about your experience with distributed systems"
        results = await pinecone_service.search_similar_questions(
            query_text=query,
            domain="Software Engineering",
            top_k=3
        )
        
        print(f"✓ Found {len(results)} similar questions")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['similarity_score']:.3f} - {result['text'][:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ Semantic search failed: {str(e)}")
        return False


async def test_embedding_service():
    """Test embedding service functionality."""
    print("\nTesting embedding service...")
    try:
        embedding_service = EmbeddingService()
        
        # Test question sync
        question_data = {
            'id': 1001,
            'text': 'How do you handle technical debt in software projects?',
            'domain': 'Software Engineering',
            'type': 'behavioral',
            'difficulty': 'medium'
        }
        
        success = await embedding_service.sync_question_on_create(question_data)
        if success:
            print("✓ Successfully synced question through embedding service")
        else:
            print("✗ Failed to sync question through embedding service")
        
        return success
    except Exception as e:
        print(f"✗ Embedding service test failed: {str(e)}")
        return False


async def test_health_checks():
    """Test health check functionality."""
    print("\nTesting health checks...")
    try:
        embedding_service = EmbeddingService()
        health = await embedding_service.health_check()
        
        print(f"✓ Embedding Service: {health['embedding_service']}")
        print(f"✓ Pinecone Status: {health['pinecone']['healthy']}")
        print(f"✓ Overall Status: {health['overall_status']}")
        
        return health['overall_status'] == 'healthy'
    except Exception as e:
        print(f"✗ Health check failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Pinecone & RAG Orchestration Test Suite")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv('PINECONE_API_KEY'):
        print("⚠️  PINECONE_API_KEY not set in environment")
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set in environment")
    
    tests = [
        test_pinecone_initialization,
        test_embedding_generation,
        test_question_upsert,
        test_semantic_search,
        test_embedding_service,
        test_health_checks
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if await test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Pinecone & RAG implementation is working correctly.")
    else:
        print("⚠️  Some tests failed. Check your API keys and Pinecone setup.")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
