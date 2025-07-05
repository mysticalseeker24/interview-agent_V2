"""Pydantic schemas for feedback generation and reports."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FeedbackGenerationRequest(BaseModel):
    """Request schema for starting feedback generation."""
    session_id: int = Field(..., description="Session ID to generate feedback for")
    regenerate: bool = Field(False, description="Whether to regenerate if feedback already exists")


class FeedbackGenerationResponse(BaseModel):
    """Response schema for feedback generation start."""
    task_id: str = Field(..., description="Celery task ID for tracking progress")
    session_id: int = Field(..., description="Session ID")
    status: str = Field(..., description="Initial task status")
    message: str = Field(..., description="Status message")


class FeedbackStatusResponse(BaseModel):
    """Response schema for feedback generation status."""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Current task status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    step: Optional[str] = Field(None, description="Current processing step")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data if completed")


class QuestionScore(BaseModel):
    """Schema for individual question score."""
    question_id: int = Field(..., description="Question ID")
    response_id: Optional[int] = Field(None, description="Response ID")
    correctness: float = Field(..., description="Semantic similarity score (0-100)")
    fluency: float = Field(..., description="Fluency score (0-100)")
    depth: float = Field(..., description="Answer depth score (0-100)")
    word_count: Optional[int] = Field(None, description="Number of words in response")
    duration_seconds: Optional[float] = Field(None, description="Response duration in seconds")
    words_per_minute: Optional[float] = Field(None, description="Speaking rate (WPM)")
    computed_at: datetime = Field(..., description="When score was computed")


class FeedbackScoresResponse(BaseModel):
    """Response schema for detailed score breakdown."""
    session_id: int = Field(..., description="Session ID")
    scores: List[QuestionScore] = Field(..., description="Per-question scores")


class FeedbackReportResponse(BaseModel):
    """Response schema for complete feedback report."""
    session_id: int = Field(..., description="Session ID")
    candidate_name: Optional[str] = Field(None, description="Candidate name")
    module_name: str = Field(..., description="Interview module name")
    
    # Aggregated scores
    avg_correctness: float = Field(..., description="Average correctness score (0-100)")
    avg_fluency: float = Field(..., description="Average fluency score (0-100)")
    avg_depth: float = Field(..., description="Average depth score (0-100)")
    overall_score: float = Field(..., description="Weighted overall score (0-100)")
    
    # Percentile rankings
    correctness_percentile: Optional[float] = Field(None, description="Correctness percentile (0-100)")
    fluency_percentile: Optional[float] = Field(None, description="Fluency percentile (0-100)")
    depth_percentile: Optional[float] = Field(None, description="Depth percentile (0-100)")
    overall_percentile: Optional[float] = Field(None, description="Overall percentile (0-100)")
    
    # AI-generated content
    report_text: str = Field(..., description="AI-generated narrative feedback")
    strengths: List[str] = Field(default=[], description="Identified strengths")
    areas_for_improvement: List[str] = Field(default=[], description="Areas needing improvement")
    recommendations: List[str] = Field(default=[], description="Specific recommendations")
    
    # Metadata
    generated_at: datetime = Field(..., description="When report was generated")
    
    class Config:
        from_attributes = True


class FeedbackMetrics(BaseModel):
    """Schema for feedback metrics calculation."""
    semantic_similarity: float = Field(..., description="Semantic similarity score")
    fluency_score: float = Field(..., description="Fluency assessment score")
    depth_score: float = Field(..., description="Answer depth score")
    word_count: int = Field(..., description="Number of words")
    duration_seconds: Optional[float] = Field(None, description="Response duration")


class PercentileData(BaseModel):
    """Schema for percentile calculation data."""
    correctness_percentile: float = Field(..., description="Correctness percentile")
    fluency_percentile: float = Field(..., description="Fluency percentile")
    depth_percentile: float = Field(..., description="Depth percentile")
    overall_percentile: float = Field(..., description="Overall percentile")


class AIFeedbackRequest(BaseModel):
    """Schema for AI feedback generation request."""
    session_id: int = Field(..., description="Session ID")
    candidate_responses: List[str] = Field(..., description="List of candidate responses")
    question_texts: List[str] = Field(..., description="List of question texts")
    scores: List[FeedbackMetrics] = Field(..., description="Calculated scores")
    percentiles: PercentileData = Field(..., description="Percentile rankings")
    module_name: str = Field(..., description="Interview module name")


class AIFeedbackResponse(BaseModel):
    """Schema for AI feedback generation response."""
    narrative: str = Field(..., description="Generated narrative feedback")
    strengths: List[str] = Field(..., description="Identified strengths")
    areas_for_improvement: List[str] = Field(..., description="Areas for improvement")
    recommendations: List[str] = Field(..., description="Specific recommendations")


class FeedbackTaskProgress(BaseModel):
    """Schema for task progress updates."""
    step: str = Field(..., description="Current processing step")
    progress: int = Field(..., description="Progress percentage (0-100)")
    message: str = Field(..., description="Progress message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class FeedbackGenerationConfig(BaseModel):
    """Configuration schema for feedback generation."""
    use_ai_narrative: bool = Field(True, description="Whether to generate AI narrative")
    include_percentiles: bool = Field(True, description="Whether to calculate percentiles")
    min_response_length: int = Field(10, description="Minimum response length to analyze")
    semantic_model: str = Field("all-MiniLM-L6-v2", description="Sentence transformer model")
    openai_model: str = Field("o4-mini", description="OpenAI model for narrative generation")
    max_narrative_tokens: int = Field(1000, description="Maximum tokens for narrative")
    temperature: float = Field(0.1, description="Temperature for AI generation")


class BulkFeedbackRequest(BaseModel):
    """Schema for bulk feedback generation."""
    session_ids: List[int] = Field(..., description="List of session IDs")
    regenerate: bool = Field(False, description="Whether to regenerate existing feedback")
    config: Optional[FeedbackGenerationConfig] = Field(None, description="Generation configuration")


class BulkFeedbackResponse(BaseModel):
    """Schema for bulk feedback generation response."""
    task_ids: List[str] = Field(..., description="List of Celery task IDs")
    total_sessions: int = Field(..., description="Total number of sessions")
    message: str = Field(..., description="Status message")
