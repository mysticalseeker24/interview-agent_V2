"""Test script for feedback system without ML dependencies."""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_basic_imports():
    """Test that all basic imports work."""
    print("Testing basic imports...")
    
    try:
        from app.core.config import get_settings
        print("✅ Config import successful")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from app.models import Score, FeedbackReport, Session, Response
        print("✅ Models import successful")
    except Exception as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from app.schemas.feedback import (
            FeedbackGenerationRequest,
            FeedbackGenerationResponse,
            FeedbackReportResponse
        )
        print("✅ Feedback schemas import successful")
    except Exception as e:
        print(f"❌ Feedback schemas import failed: {e}")
        return False
    
    try:
        from app.tasks import celery_app
        print("✅ Celery configuration import successful")
    except Exception as e:
        print(f"❌ Celery configuration import failed: {e}")
        return False
    
    return True

async def test_schema_validation():
    """Test Pydantic schema validation."""
    print("\nTesting schema validation...")
    
    try:
        from app.schemas.feedback import FeedbackGenerationRequest, FeedbackReportResponse
        
        # Test valid request
        request = FeedbackGenerationRequest(session_id=123, regenerate=False)
        assert request.session_id == 123
        assert request.regenerate == False
        print("✅ FeedbackGenerationRequest validation successful")
        
        # Test response schema
        from datetime import datetime
        response = FeedbackReportResponse(
            session_id=123,
            candidate_name="Test User",
            module_name="Software Engineering",
            avg_correctness=85.5,
            avg_fluency=78.0,
            avg_depth=82.5,
            overall_score=82.0,
            correctness_percentile=75.0,
            fluency_percentile=70.0,
            depth_percentile=80.0,
            overall_percentile=75.0,
            report_text="Test feedback report",
            strengths=["Good technical knowledge"],
            areas_for_improvement=["Improve communication"],
            recommendations=["Practice more"],
            generated_at=datetime.now()
        )
        assert response.session_id == 123
        print("✅ FeedbackReportResponse validation successful")
        
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False
    
    return True

async def test_database_models():
    """Test database model creation."""
    print("\nTesting database models...")
    
    try:
        from app.models import Score, FeedbackReport
        from datetime import datetime
        
        # Test Score model creation
        score = Score(
            session_id=123,
            question_id=456,
            response_id=789,
            correctness=85.5,
            fluency=78.0,
            depth=82.5,
            word_count=150,
            words_per_minute=120.0
        )
        assert score.correctness == 85.5
        print("✅ Score model creation successful")
        
        # Test FeedbackReport model creation
        feedback = FeedbackReport(
            session_id=123,
            avg_correctness=85.5,
            avg_fluency=78.0,
            avg_depth=82.5,
            overall_score=82.0,
            correctness_percentile=75.0,
            fluency_percentile=70.0,
            depth_percentile=80.0,
            overall_percentile=75.0,
            report_text="Test feedback",
            strengths=["Good knowledge"],
            areas_for_improvement=["Communication"],
            model_used="o4-mini",
            generation_version="1.0",
            total_questions=5
        )
        assert feedback.overall_score == 82.0
        print("✅ FeedbackReport model creation successful")
        
    except Exception as e:
        print(f"❌ Database model test failed: {e}")
        return False
    
    return True

async def test_router_structure():
    """Test that the router structure is correct."""
    print("\nTesting router structure...")
    
    try:
        from app.routers.feedback import router
        
        # Check that router has the expected endpoints
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/api/v1/feedback/generate",
            "/api/v1/feedback/status/{task_id}",
            "/api/v1/feedback/report/{session_id}",
            "/api/v1/feedback/scores/{session_id}",
            "/api/v1/feedback/report/{session_id}",  # DELETE endpoint
            "/api/v1/feedback/health"
        ]
        
        print(f"Found routes: {routes}")
        
        # Check that we have the main endpoints
        assert any("generate" in route for route in routes), "Missing generate endpoint"
        assert any("status" in route for route in routes), "Missing status endpoint"
        assert any("report" in route for route in routes), "Missing report endpoint"
        assert any("health" in route for route in routes), "Missing health endpoint"
        
        print("✅ Router structure validation successful")
        
    except Exception as e:
        print(f"❌ Router structure test failed: {e}")
        return False
    
    return True

async def test_followup_service():
    """Test that followup service imports correctly."""
    print("\nTesting followup service...")
    
    try:
        from app.routers.followup import router as followup_router
        from app.schemas.followup import FollowUpRequest, FollowUpResponse
        
        # Check followup schemas
        request = FollowUpRequest(
            session_id=123,
            answer_text="I implemented a REST API using Flask",
            use_llm=True,
            max_candidates=5
        )
        assert request.session_id == 123
        print("✅ FollowUp service structure successful")
        
    except Exception as e:
        print(f"❌ FollowUp service test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests."""
    print("🚀 Starting TalentSync Interview Service Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(await test_basic_imports())
    test_results.append(await test_schema_validation())
    test_results.append(await test_database_models())
    test_results.append(await test_router_structure())
    test_results.append(await test_followup_service())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("🎉 The codebase is ready for deployment!")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("🔧 Please fix the issues before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
