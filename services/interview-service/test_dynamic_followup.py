"""Unit tests for dynamic follow-up question service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dynamic_followup_service import DynamicFollowUpService
from app.models.session import Session
from app.models.question import Question
from app.models.session_question import SessionQuestion


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def mock_pinecone_service():
    """Mock Pinecone service."""
    with patch('app.services.dynamic_followup_service.PineconeService') as mock:
        service = mock.return_value
        service.search_similar_questions_by_vector = AsyncMock()
        yield service


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = MagicMock()
    
    # Mock embeddings response
    embedding_response = MagicMock()
    embedding_response.data = [MagicMock(embedding=[0.1] * 1536)]
    client.embeddings.create.return_value = embedding_response
    
    # Mock chat completion response
    chat_response = MagicMock()
    chat_response.choices = [MagicMock(message=MagicMock(content="Generated follow-up question?"))]
    client.chat.completions.create.return_value = chat_response
    
    return client


@pytest.fixture
def followup_service(mock_db, mock_pinecone_service):
    """Create DynamicFollowUpService instance with mocked dependencies."""
    with patch('app.services.dynamic_followup_service.OpenAI') as mock_openai:
        service = DynamicFollowUpService(mock_db)
        service.pinecone_service = mock_pinecone_service
        yield service


class TestDynamicFollowUpService:
    """Test cases for DynamicFollowUpService."""

    @pytest.mark.asyncio
    async def test_generate_followup_question_rag_mode(self, followup_service, mock_db):
        """Test follow-up generation using RAG mode (no LLM)."""
        # Setup mocks
        session_id = 123
        answer_text = "I have experience with React and Node.js"
        
        # Mock session context
        mock_session = Session(id=session_id, module_id=1)
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_session
        
        # Mock module info
        mock_db.execute.return_value.fetchone.return_value = MagicMock(
            category="frontend", difficulty_level="intermediate", name="React Development"
        )
        
        # Mock asked questions (empty list)
        mock_db.execute.return_value.fetchall.return_value = []
        
        # Mock Pinecone results
        followup_service.pinecone_service.search_similar_questions_by_vector.return_value = [
            {
                'question_id': 456,
                'text': 'Can you describe a specific React challenge you faced?',
                'domain': 'frontend',
                'type': 'follow-up',
                'score': 0.85
            }
        ]
        
        # Mock database question fetch
        mock_question = Question(
            id=456,
            text='Can you describe a specific React challenge you faced?',
            domain='frontend',
            type='follow-up'
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_question]
        
        # Test
        result = await followup_service.generate_followup_question(
            session_id=session_id,
            answer_text=answer_text,
            use_llm=False
        )
        
        # Assertions
        assert result['follow_up_question'] == 'Can you describe a specific React challenge you faced?'
        assert result['source_ids'] == [456]
        assert result['generation_method'] == 'rag'
        assert 'confidence_score' in result

    @pytest.mark.asyncio
    async def test_generate_followup_question_llm_mode(self, followup_service, mock_db, mock_openai_client):
        """Test follow-up generation using LLM mode."""
        # Setup mocks
        session_id = 123
        answer_text = "I have experience with React and Node.js"
        
        # Patch OpenAI client
        with patch.object(followup_service, 'openai_client', mock_openai_client):
            # Mock session context
            mock_session = Session(id=session_id, module_id=1)
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_session
            
            # Mock module info
            mock_db.execute.return_value.fetchone.return_value = MagicMock(
                category="frontend", difficulty_level="intermediate", name="React Development"
            )
            
            # Mock asked questions (empty list)
            mock_db.execute.return_value.fetchall.return_value = []
            
            # Mock Pinecone results with multiple candidates
            followup_service.pinecone_service.search_similar_questions_by_vector.return_value = [
                {
                    'question_id': 456,
                    'text': 'Can you describe a React challenge?',
                    'domain': 'frontend',
                    'type': 'follow-up',
                    'score': 0.85
                },
                {
                    'question_id': 457,
                    'text': 'How do you handle state management?',
                    'domain': 'frontend', 
                    'type': 'follow-up',
                    'score': 0.82
                }
            ]
            
            # Mock database question fetch
            mock_questions = [
                Question(id=456, text='Can you describe a React challenge?', domain='frontend', type='follow-up'),
                Question(id=457, text='How do you handle state management?', domain='frontend', type='follow-up')
            ]
            mock_db.execute.return_value.scalars.return_value.all.return_value = mock_questions
            
            # Test
            result = await followup_service.generate_followup_question(
                session_id=session_id,
                answer_text=answer_text,
                use_llm=True
            )
            
            # Assertions
            assert result['follow_up_question'] == 'Generated follow-up question?'
            assert len(result['source_ids']) >= 1
            assert result['generation_method'] == 'llm'

    @pytest.mark.asyncio
    async def test_generate_followup_excludes_asked_questions(self, followup_service, mock_db):
        """Test that already asked questions are excluded."""
        # Setup mocks
        session_id = 123
        answer_text = "I have experience with React"
        
        # Mock session context
        mock_session = Session(id=session_id, module_id=1)
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_session
        
        # Mock module info
        mock_db.execute.return_value.fetchone.return_value = MagicMock(
            category="frontend", difficulty_level="intermediate", name="React Development"
        )
        
        # Mock asked questions (question 456 already asked)
        mock_db.execute.return_value.fetchall.return_value = [(456,)]
        
        # Mock Pinecone results including already asked question
        followup_service.pinecone_service.search_similar_questions_by_vector.return_value = [
            {
                'question_id': 456,  # This should be excluded
                'text': 'Already asked question',
                'domain': 'frontend',
                'type': 'follow-up',
                'score': 0.95
            },
            {
                'question_id': 457,  # This should be used
                'text': 'New follow-up question',
                'domain': 'frontend',
                'type': 'follow-up',
                'score': 0.85
            }
        ]
        
        # Mock database question fetch (only returns question 457)
        mock_question = Question(
            id=457,
            text='New follow-up question',
            domain='frontend',
            type='follow-up'
        )
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_question]
        
        # Test
        result = await followup_service.generate_followup_question(
            session_id=session_id,
            answer_text=answer_text,
            use_llm=False
        )
        
        # Assertions - should use question 457, not the already asked 456
        assert result['source_ids'] == [457]
        assert result['follow_up_question'] == 'New follow-up question'

    @pytest.mark.asyncio
    async def test_error_handling_pinecone_failure(self, followup_service, mock_db):
        """Test error handling when Pinecone fails."""
        # Setup mocks
        session_id = 123
        answer_text = "Test answer"
        
        # Mock session context
        mock_session = Session(id=session_id, module_id=1)
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_session
        
        # Mock module info
        mock_db.execute.return_value.fetchone.return_value = MagicMock(
            category="general", difficulty_level="intermediate", name="Test Module"
        )
        
        # Mock asked questions
        mock_db.execute.return_value.fetchall.return_value = []
        
        # Mock Pinecone failure
        followup_service.pinecone_service.search_similar_questions_by_vector.side_effect = Exception("Pinecone error")
        
        # Test
        with pytest.raises(Exception, match="Pinecone error"):
            await followup_service.generate_followup_question(
                session_id=session_id,
                answer_text=answer_text,
                use_llm=False
            )

    @pytest.mark.asyncio
    async def test_get_session_question_history(self, followup_service, mock_db):
        """Test getting session question history."""
        session_id = 123
        
        # Mock database results
        mock_rows = [
            MagicMock(
                id=1,
                question_id=456,
                question_type="follow_up",
                asked_at=MagicMock(isoformat=lambda: "2023-01-01T10:00:00"),
                source="rag",
                question_text="Test follow-up question",
                domain="frontend",
                type="follow-up"
            )
        ]
        mock_db.execute.return_value.fetchall.return_value = mock_rows
        
        # Test
        result = await followup_service.get_session_question_history(session_id)
        
        # Assertions
        assert len(result) == 1
        assert result[0]['question_id'] == 456
        assert result[0]['question_type'] == "follow_up"
        assert result[0]['source'] == "rag"
