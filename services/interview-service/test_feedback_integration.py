"""Integration tests for feedback generation system."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import numpy as np

from app.tasks.feedback import (
    generate_feedback,
    _generate_feedback_async,
    _compute_response_metrics,
    _calculate_percentiles,
    _calculate_aggregates,
    _generate_ai_feedback,
    _parse_feedback_sections
)
from app.models.session import Session, SessionStatus
from app.models.question import Question
from app.models.response import Response
from app.models.score import Score
from app.models.feedback_report import FeedbackReport


class TestFeedbackGeneration:
    """Test cases for the feedback generation system."""

    @pytest.fixture
    def sample_responses(self):
        """Sample response data for testing."""
        return [
            {
                'id': 1,
                'session_id': 123,
                'question_id': 1,
                'answer_text': 'I implemented a REST API using Flask with SQLAlchemy for the ORM. The architecture followed MVC patterns with proper separation of concerns.',
                'duration_seconds': 120,
                'question_text': 'Describe a web application you built',
                'ideal_answer_summary': 'A web application should use proper architecture patterns, include a database layer, and follow REST principles.',
                'domain': 'software_engineering',
                'difficulty_level': 'intermediate',
                'question_type': 'open_ended'
            },
            {
                'id': 2,
                'session_id': 123,
                'question_id': 2,
                'answer_text': 'For sorting algorithms, I prefer quicksort for most cases due to its O(n log n) average case performance.',
                'duration_seconds': 90,
                'question_text': 'Explain your favorite sorting algorithm',
                'ideal_answer_summary': 'Should discuss time complexity, space complexity, and use cases for different sorting algorithms.',
                'domain': 'data_structures',
                'difficulty_level': 'intermediate',
                'question_type': 'technical'
            }
        ]

    @pytest.fixture
    def sample_session(self):
        """Sample session data for testing."""
        return Session(
            id=123,
            user_id=456,
            module_id=1,
            status=SessionStatus.COMPLETED,
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_compute_response_metrics(self, sample_responses):
        """Test response metrics computation."""
        
        with patch('app.tasks.feedback.get_embedding_model') as mock_embed:
            # Mock the embedding model
            mock_model = Mock()
            mock_model.encode.return_value = [np.array([0.1] * 384)]  # Mock 384-dim embedding
            mock_embed.return_value = mock_model
            
            # Mock database session
            mock_db = AsyncMock()
            
            # Test metrics computation
            scores_data = await _compute_response_metrics(mock_db, sample_responses)
            
            assert len(scores_data) == 2
            assert all('correctness' in score for score in scores_data)
            assert all('fluency' in score for score in scores_data)
            assert all('depth' in score for score in scores_data)
            assert all(0 <= score['correctness'] <= 100 for score in scores_data)
            assert all(0 <= score['fluency'] <= 100 for score in scores_data)
            assert all(0 <= score['depth'] <= 100 for score in scores_data)

    def test_calculate_aggregates(self):
        """Test aggregate calculation."""
        
        scores_data = [
            {'correctness': 85, 'fluency': 70, 'depth': 80},
            {'correctness': 90, 'fluency': 85, 'depth': 75},
            {'correctness': 75, 'fluency': 80, 'depth': 85}
        ]
        
        aggregates = _calculate_aggregates(scores_data)
        
        assert 'correctness_avg' in aggregates
        assert 'fluency_avg' in aggregates
        assert 'depth_avg' in aggregates
        assert 'overall_score' in aggregates
        
        # Check calculations
        expected_correctness = np.mean([85, 90, 75])
        expected_fluency = np.mean([70, 85, 80])
        expected_depth = np.mean([80, 75, 85])
        
        assert abs(aggregates['correctness_avg'] - expected_correctness) < 0.1
        assert abs(aggregates['fluency_avg'] - expected_fluency) < 0.1
        assert abs(aggregates['depth_avg'] - expected_depth) < 0.1

    @pytest.mark.asyncio
    async def test_calculate_percentiles(self):
        """Test percentile calculation with historical data."""
        
        mock_db = AsyncMock()
        
        # Mock historical data query result
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            Mock(avg_correctness=70, avg_fluency=65, avg_depth=75, overall_score=70),
            Mock(avg_correctness=80, avg_fluency=75, avg_depth=80, overall_score=78),
            Mock(avg_correctness=60, avg_fluency=70, avg_depth=65, overall_score=65),
            Mock(avg_correctness=90, avg_fluency=85, avg_depth=88, overall_score=88),
            Mock(avg_correctness=75, avg_fluency=80, avg_depth=70, overall_score=75),
        ]
        
        mock_db.execute.return_value = mock_result
        
        scores_data = [
            {'correctness': 85, 'fluency': 80, 'depth': 82}
        ]
        
        percentiles = await _calculate_percentiles(mock_db, scores_data, module_id=1)
        
        assert 'correctness_percentile' in percentiles
        assert 'fluency_percentile' in percentiles
        assert 'depth_percentile' in percentiles
        assert 'overall_percentile' in percentiles
        assert percentiles['historical_sample_size'] == 5

    @pytest.mark.asyncio
    async def test_generate_ai_feedback(self):
        """Test AI feedback generation using o4-mini."""
        
        aggregates = {
            'correctness_avg': 85.0,
            'fluency_avg': 78.0,
            'depth_avg': 82.0,
            'overall_score': 81.7
        }
        
        percentiles = {
            'correctness_percentile': 75.0,
            'fluency_percentile': 68.0,
            'depth_percentile': 80.0,
            'overall_percentile': 74.0
        }
        
        responses = [
            {
                'answer_text': 'I used React and Node.js to build a full-stack application.',
                'domain': 'software_engineering'
            }
        ]
        
        # Mock settings
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_CHAT_MODEL = "o4-mini"
        mock_settings.OPENAI_MAX_TOKENS = 300
        
        with patch('openai.OpenAI') as mock_openai:
            # Mock OpenAI response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [
                Mock(message=Mock(content="""
                Strong technical performance with clear communication skills.
                
                **Key Strengths:**
                • Demonstrated solid understanding of full-stack development
                • Used appropriate technology stack for the problem
                • Articulated technical concepts clearly
                
                **Areas for Improvement:**
                • Could provide more specific implementation details
                • Consider discussing scalability considerations
                • Practice explaining edge cases and error handling
                """))
            ]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Test AI feedback generation
            feedback_data = await _generate_ai_feedback(
                123, aggregates, percentiles, responses, mock_settings
            )
            
            assert 'report_text' in feedback_data
            assert 'strengths' in feedback_data
            assert 'improvements' in feedback_data
            assert 'model_used' in feedback_data
            assert feedback_data['model_used'] == 'o4-mini'
            assert len(feedback_data['strengths']) <= 3
            assert len(feedback_data['improvements']) <= 3

    def test_parse_feedback_sections(self):
        """Test parsing of strengths and improvements from AI feedback."""
        
        narrative_text = """
        Great performance overall with strong technical skills.
        
        **Key Strengths:**
        • Excellent problem-solving approach
        • Clear and concise explanations
        • Good use of technical terminology
        
        **Areas for Improvement:**
        • Could provide more detailed examples
        • Practice handling edge cases
        • Work on time management
        """
        
        strengths, improvements = _parse_feedback_sections(narrative_text)
        
        assert len(strengths) == 3
        assert len(improvements) == 3
        assert "Excellent problem-solving approach" in strengths[0]
        assert "Could provide more detailed examples" in improvements[0]

    @pytest.mark.asyncio
    async def test_full_feedback_generation_integration(self, sample_session, sample_responses):
        """Test the full feedback generation pipeline."""
        
        with patch('app.tasks.feedback.create_async_engine') as mock_engine, \
             patch('app.tasks.feedback.async_sessionmaker') as mock_session_maker, \
             patch('app.tasks.feedback.get_embedding_model') as mock_embed, \
             patch('app.tasks.feedback._generate_ai_feedback') as mock_ai_feedback:
            
            # Mock database components
            mock_db = AsyncMock()
            mock_session_maker.return_value = mock_db
            mock_db.__aenter__.return_value = mock_db
            mock_db.__aexit__.return_value = None
            
            # Mock session loading
            mock_session_result = Mock()
            mock_session_result.scalar_one_or_none.return_value = sample_session
            mock_db.execute.return_value = mock_session_result
            
            # Mock embedding model
            mock_model = Mock()
            mock_model.encode.return_value = [np.array([0.5] * 384)]
            mock_embed.return_value = mock_model
            
            # Mock AI feedback
            mock_ai_feedback.return_value = {
                'report_text': 'Good technical interview performance.',
                'strengths': ['Strong problem solving', 'Clear communication'],
                'improvements': ['More practice needed', 'Better examples'],
                'model_used': 'o4-mini',
                'generation_method': 'automated'
            }
            
            # Mock database queries for responses and historical data
            mock_db.execute.side_effect = [
                mock_session_result,  # Session query
                Mock(fetchall=lambda: sample_responses),  # Responses query
                Mock(fetchall=lambda: []),  # Historical data query (empty)
                Mock(scalar_one_or_none=lambda: None),  # Existing score check
                Mock(scalar_one_or_none=lambda: None),  # Existing feedback report check
            ]
            
            # Test the full pipeline
            result = await _generate_feedback_async(123)
            
            assert result['status'] == 'success'
            assert result['session_id'] == 123
            assert 'overall_score' in result
            assert 'questions_analyzed' in result

    @pytest.mark.asyncio
    async def test_error_handling_and_retries(self):
        """Test error handling and retry mechanisms."""
        
        with patch('app.tasks.feedback._generate_feedback_async') as mock_async:
            # First call fails, second succeeds
            mock_async.side_effect = [
                Exception("Database connection error"),
                {'status': 'success', 'session_id': 123}
            ]
            
            # Mock the celery task
            mock_task = Mock()
            mock_task.request.retries = 0
            mock_task.update_state = Mock()
            mock_task.retry = Mock(side_effect=Exception("Retry"))
            
            with pytest.raises(Exception):
                # This should trigger a retry
                generate_feedback(mock_task, 123)

    @pytest.mark.asyncio
    async def test_insufficient_historical_data(self):
        """Test handling of insufficient historical data for percentiles."""
        
        mock_db = AsyncMock()
        
        # Mock insufficient historical data (less than 10 records)
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            Mock(avg_correctness=70, avg_fluency=65, avg_depth=75, overall_score=70),
            Mock(avg_correctness=80, avg_fluency=75, avg_depth=80, overall_score=78),
        ]  # Only 2 records
        
        mock_db.execute.return_value = mock_result
        
        scores_data = [{'correctness': 85, 'fluency': 80, 'depth': 82}]
        
        percentiles = await _calculate_percentiles(mock_db, scores_data, module_id=1)
        
        # Should return None for percentiles when insufficient data
        assert percentiles['correctness_percentile'] is None
        assert percentiles['fluency_percentile'] is None
        assert percentiles['depth_percentile'] is None
        assert percentiles['overall_percentile'] is None
        assert percentiles['historical_sample_size'] == 2

    def test_technical_term_counting(self):
        """Test technical term counting for different domains."""
        from app.tasks.feedback import _count_technical_terms
        
        # Software engineering text
        se_text = "I built a REST API using Flask framework with SQLAlchemy ORM and implemented microservices architecture."
        se_count = _count_technical_terms(se_text, "software_engineering")
        assert se_count >= 4  # Should find REST, API, framework, microservices, etc.
        
        # Machine learning text
        ml_text = "I trained a neural network using supervised learning with cross-validation and regularization."
        ml_count = _count_technical_terms(ml_text, "machine_learning")
        assert ml_count >= 4  # Should find neural network, supervised, cross-validation, etc.
        
        # Non-technical text
        basic_text = "I think this is a good question and I would like to answer it."
        basic_count = _count_technical_terms(basic_text, "software_engineering")
        assert basic_count == 0  # Should find no technical terms

    @pytest.mark.asyncio
    async def test_concurrent_feedback_generation(self):
        """Test that concurrent feedback generation is handled properly."""
        
        with patch('app.tasks.feedback._generate_feedback_async') as mock_async:
            mock_async.return_value = {'status': 'success', 'session_id': 123}
            
            # Test concurrent execution
            tasks = [
                asyncio.create_task(_generate_feedback_async(123)),
                asyncio.create_task(_generate_feedback_async(124)),
                asyncio.create_task(_generate_feedback_async(125))
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(result['status'] == 'success' for result in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
