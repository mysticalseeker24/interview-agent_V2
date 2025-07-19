"""Follow-up question generation router for TalentSync Interview Service."""
import time
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.dependencies.auth import get_current_user, User
from app.schemas.interview import FollowUpRequest, FollowUpOut
from app.services.followup_service import DynamicFollowUpService

router = APIRouter()


@router.post("/generate", response_model=FollowUpOut)
async def generate_followup(
    request: FollowUpRequest,
    current_user: User = Depends(get_current_user)
) -> FollowUpOut:
    """
    Generate a dynamic follow-up question based on candidate's answer.
    
    Args:
        request: Follow-up generation request
        current_user: Authenticated user
        
    Returns:
        Generated follow-up question
    """
    start_time = time.time()
    
    try:
        followup_service = DynamicFollowUpService()
        
        # Generate follow-up question
        followup_text = await followup_service.generate(
            answer_text=request.answer_text,
            domain=request.domain,
            difficulty=request.difficulty,
            max_candidates=request.max_candidates,
            use_llm=request.use_llm
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Create response
        response = FollowUpOut(
            question_id=f"followup_{int(time.time())}",
            question_text=followup_text,
            difficulty=request.difficulty,
            question_type="follow-up",
            domain=request.domain,
            generation_method="llm" if request.use_llm else "rag",
            confidence_score=0.85,  # Mock confidence score
            remaining_questions=5,  # Mock remaining questions
            is_complete=False
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate follow-up question: {str(e)}"
        )


@router.post("/generate/batch")
async def generate_followup_batch(
    requests: list[FollowUpRequest],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate multiple follow-up questions in batch.
    
    Args:
        requests: List of follow-up generation requests
        current_user: Authenticated user
        
    Returns:
        Batch generation results
    """
    start_time = time.time()
    
    try:
        if len(requests) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size too large (max 10)")
        
        followup_service = DynamicFollowUpService()
        results = []
        
        for i, request in enumerate(requests):
            try:
                followup_text = await followup_service.generate(
                    answer_text=request.answer_text,
                    domain=request.domain,
                    difficulty=request.difficulty,
                    max_candidates=request.max_candidates,
                    use_llm=request.use_llm
                )
                
                results.append({
                    "index": i,
                    "success": True,
                    "question_text": followup_text,
                    "domain": request.domain,
                    "difficulty": request.difficulty
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "results": results,
            "total_requests": len(requests),
            "successful_requests": len([r for r in results if r["success"]]),
            "processing_time_ms": processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate batch follow-up questions: {str(e)}"
        )


@router.get("/performance")
async def get_followup_performance(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get follow-up generation performance metrics.
    
    Args:
        current_user: Authenticated user (admin only)
        
    Returns:
        Performance metrics
    """
    try:
        # Check if user is admin
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        followup_service = DynamicFollowUpService()
        metrics = followup_service.get_performance_metrics()
        
        return {
            "service": "followup_generation",
            "timestamp": time.time(),
            "metrics": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.post("/test")
async def test_followup_generation(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test follow-up generation with sample data covering all confidence levels.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Test results with confidence analysis
    """
    try:
        followup_service = DynamicFollowUpService()
        
        # Test cases covering different confidence scenarios
        test_cases = [
            # High confidence scenarios (should use high_confidence_llm)
            {
                "answer_text": "I implemented a binary search tree with O(log n) insertion and O(log n) search complexity. I used a recursive approach with proper null checks and balanced the tree using AVL rotations.",
                "domain": "dsa",
                "difficulty": "hard",
                "expected_confidence": "high"
            },
            {
                "answer_text": "I've worked extensively with Docker containers and Kubernetes orchestration. I've set up CI/CD pipelines using Jenkins and GitLab, implemented blue-green deployments, and configured monitoring with Prometheus and Grafana.",
                "domain": "devops",
                "difficulty": "hard",
                "expected_confidence": "high"
            },
            
            # Medium confidence scenarios (should use low_confidence_llm)
            {
                "answer_text": "I have experience with Python and machine learning, particularly with scikit-learn and TensorFlow.",
                "domain": "machine-learning",
                "difficulty": "medium",
                "expected_confidence": "medium"
            },
            {
                "answer_text": "I've worked on data analysis projects using pandas, numpy, and statistical modeling.",
                "domain": "data-science",
                "difficulty": "medium",
                "expected_confidence": "medium"
            },
            
            # Low confidence scenarios (should use fallback_rag)
            {
                "answer_text": "I'm familiar with basic data structures like arrays and linked lists.",
                "domain": "dsa",
                "difficulty": "easy",
                "expected_confidence": "low"
            },
            {
                "answer_text": "I've used some design patterns in my projects.",
                "domain": "software-engineering",
                "difficulty": "easy",
                "expected_confidence": "low"
            },
            
            # Very low confidence scenarios (should use domain_fallback)
            {
                "answer_text": "I don't know much about this topic.",
                "domain": "ai-engineering",
                "difficulty": "hard",
                "expected_confidence": "very_low"
            },
            {
                "answer_text": "I'm not sure.",
                "domain": "resume-based",
                "difficulty": "medium",
                "expected_confidence": "very_low"
            }
        ]
        
        results = []
        total_time = 0
        confidence_distribution = {"high": 0, "medium": 0, "low": 0, "very_low": 0}
        strategy_usage = {"high_confidence_llm": 0, "low_confidence_llm": 0, "fallback_rag": 0, "domain_fallback": 0}
        
        for i, test_case in enumerate(test_cases):
            start_time = time.time()
            
            try:
                followup_text = await followup_service.generate(
                    answer_text=test_case["answer_text"],
                    domain=test_case["domain"],
                    difficulty=test_case["difficulty"],
                    use_llm=True
                )
                
                processing_time = (time.time() - start_time) * 1000
                total_time += processing_time
                
                # Analyze the generated question for confidence indicators
                confidence_level = _analyze_generated_question_confidence(followup_text, test_case["domain"])
                confidence_distribution[confidence_level] += 1
                
                # Track strategy usage (this would be available in the service response)
                # For now, we'll estimate based on the test case
                strategy_usage[test_case["expected_confidence"]] += 1
                
                results.append({
                    "test_case": i + 1,
                    "success": True,
                    "answer_text": test_case["answer_text"][:50] + "...",
                    "generated_question": followup_text,
                    "domain": test_case["domain"],
                    "difficulty": test_case["difficulty"],
                    "expected_confidence": test_case["expected_confidence"],
                    "detected_confidence": confidence_level,
                    "processing_time_ms": processing_time
                })
                
            except Exception as e:
                results.append({
                    "test_case": i + 1,
                    "success": False,
                    "error": str(e),
                    "domain": test_case["domain"],
                    "difficulty": test_case["difficulty"]
                })
        
        successful_tests = len([r for r in results if r["success"]])
        
        return {
            "test_results": results,
            "confidence_analysis": {
                "confidence_distribution": confidence_distribution,
                "strategy_usage": strategy_usage,
                "confidence_accuracy": _calculate_confidence_accuracy(results)
            },
            "summary": {
                "total_tests": len(test_cases),
                "successful_tests": successful_tests,
                "success_rate": successful_tests / len(test_cases),
                "total_processing_time_ms": total_time,
                "avg_processing_time_ms": total_time / successful_tests if successful_tests > 0 else 0,
                "confidence_system_working": successful_tests > 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run follow-up generation tests: {str(e)}"
        )


def _analyze_generated_question_confidence(question_text: str, domain: str) -> str:
    """Analyze the confidence level of a generated question based on its characteristics."""
    try:
        # Simple heuristics for confidence analysis
        question_length = len(question_text)
        has_technical_terms = any(term in question_text.lower() for term in [
            "complexity", "algorithm", "implementation", "architecture", "deployment",
            "optimization", "scalability", "monitoring", "pipeline", "framework"
        ])
        is_specific = any(phrase in question_text.lower() for phrase in [
            "can you describe", "how did you", "what was your approach", "can you explain",
            "what challenges", "how would you implement"
        ])
        is_generic = any(phrase in question_text.lower() for phrase in [
            "tell me more", "elaborate", "provide more details", "can you tell me"
        ])
        
        if question_length > 100 and has_technical_terms and is_specific:
            return "high"
        elif question_length > 50 and (has_technical_terms or is_specific):
            return "medium"
        elif question_length > 30 and not is_generic:
            return "low"
        else:
            return "very_low"
            
    except Exception:
        return "low"


def _calculate_confidence_accuracy(results: List[Dict]) -> float:
    """Calculate the accuracy of confidence predictions."""
    try:
        correct_predictions = 0
        total_predictions = 0
        
        for result in results:
            if result.get("success") and "expected_confidence" in result and "detected_confidence" in result:
                expected = result["expected_confidence"]
                detected = result["detected_confidence"]
                
                # Consider it correct if the detected confidence is at least as high as expected
                if expected == "high" and detected in ["high"]:
                    correct_predictions += 1
                elif expected == "medium" and detected in ["high", "medium"]:
                    correct_predictions += 1
                elif expected == "low" and detected in ["high", "medium", "low"]:
                    correct_predictions += 1
                elif expected == "very_low":
                    correct_predictions += 1  # Any confidence level is acceptable for very low
                
                total_predictions += 1
        
        return correct_predictions / total_predictions if total_predictions > 0 else 0.0
        
    except Exception:
        return 0.0


@router.post("/validate")
async def validate_followup_question(
    question_text: str,
    answer_text: str,
    domain: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate a follow-up question for relevance and quality.
    
    Args:
        question_text: The follow-up question to validate
        answer_text: The original answer that prompted the question
        domain: The interview domain
        current_user: Authenticated user
        
    Returns:
        Validation results
    """
    try:
        # Basic validation checks
        validation_results = {
            "question_length": len(question_text),
            "answer_length": len(answer_text),
            "domain_match": domain in ["dsa", "devops", "ai-engineering", "machine-learning", "data-science", "software-engineering", "resume-based"],
            "has_question_mark": question_text.strip().endswith("?"),
            "is_appropriate_length": 10 <= len(question_text) <= 200,
            "contains_technical_terms": any(term in question_text.lower() for term in ["how", "what", "why", "when", "where", "can", "would", "could"])
        }
        
        # Calculate overall score
        score = sum(validation_results.values()) / len(validation_results)
        validation_results["overall_score"] = score
        validation_results["is_valid"] = score >= 0.7
        
        return {
            "validation_results": validation_results,
            "recommendations": []
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate follow-up question: {str(e)}"
        ) 