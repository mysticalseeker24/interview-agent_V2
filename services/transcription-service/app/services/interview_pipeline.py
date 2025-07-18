import json
import logging
from typing import Dict, Any, Optional
from ..services.groq_stt import GroqSTTClient
from ..services.playai_tts import GroqTTSClient
from ..core.config import settings

logger = logging.getLogger(__name__)


class InterviewPipeline:
    """
    Interview Pipeline Service
    
    Handles the STT → JSON → TTS flow for interview sessions:
    1. Agent asks question (TTS)
    2. User responds (STT)
    3. Response processed into JSON
    4. Agent replies based on JSON (TTS)
    """
    
    def __init__(self):
        self.stt_client = GroqSTTClient()
        self.tts_client = GroqTTSClient()
    
    async def process_interview_round(
        self,
        agent_question: str,
        user_audio_bytes: bytes,
        session_id: str,
        round_number: int = 1,
        persona: Optional[Any] = None  # Add persona parameter
    ) -> Dict[str, Any]:
        """
        Process one round of the interview pipeline.
        
        Args:
            agent_question: The question the agent is asking
            user_audio_bytes: User's audio response
            session_id: Interview session ID
            round_number: Current round number
            
        Returns:
            Dictionary containing the complete round data
        """
        try:
            logger.info(f"Processing interview round {round_number} for session {session_id}")
            
            # Step 1: Agent asks question (TTS)
            # Generate TTS for agent question
            question_voice = persona.voice if persona else "Briggs-PlayAI"
            question_tts_result = await self.tts_client.synthesize(
                agent_question, 
                voice=question_voice
            )
            
            # Step 2: Transcribe user response (STT)
            transcription_result = await self.stt_client.transcribe(
                audio_bytes=user_audio_bytes,
                response_format="verbose_json"
            )
            
            # Step 3: Process response into structured JSON
            structured_response = self._structure_user_response(
                transcription_result["text"],
                transcription_result.get("segments", []),
                transcription_result.get("confidence", 0.0)
            )
            
            # Step 4: Generate agent reply based on structured response
            agent_reply = await self._generate_agent_reply(
                agent_question,
                structured_response,
                round_number
            )
            
            # Step 5: Synthesize agent reply (TTS)
            # Generate TTS for agent reply
            reply_voice = persona.voice if persona else "Briggs-PlayAI"
            reply_tts_result = await self.tts_client.synthesize(
                agent_reply, 
                voice=reply_voice
            )
            
            # Step 6: Clean up TTS cache after interview round
            await self._cleanup_tts_cache()
            
            return {
                "session_id": session_id,
                "round_number": round_number,
                "agent_question": agent_question,
                "agent_question_audio": question_tts_result,
                "user_response": {
                    "raw_text": transcription_result["text"],
                    "structured_json": structured_response,
                    "confidence": transcription_result.get("confidence", 0.0),
                    "segments": transcription_result.get("segments", []),
                    "language": transcription_result.get("language", "en")
                },
                "agent_reply": agent_reply,
                "agent_reply_audio": reply_tts_result,
                "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
            }
            
        except Exception as e:
            logger.error(f"Interview pipeline failed for round {round_number}: {str(e)}")
            raise
    
    def _structure_user_response(
        self,
        raw_text: str,
        segments: list,
        confidence: float
    ) -> Dict[str, Any]:
        """
        Structure the user's response into JSON format.
        
        This is where you would implement logic to extract key information
        from the user's response for the interview context.
        """
        # Basic structuring - in production, you'd use more sophisticated NLP
        structured_response = {
            "raw_text": raw_text,
            "confidence": confidence,
            "segments": segments,
            "extracted_info": {
                "answer_length": len(raw_text),
                "has_technical_terms": self._detect_technical_terms(raw_text),
                "sentiment": self._analyze_sentiment(raw_text),
                "key_topics": self._extract_key_topics(raw_text)
            },
            "interview_metrics": {
                "response_time": 0.0,  # Would calculate actual time
                "clarity_score": confidence,
                "completeness_score": self._calculate_completeness(raw_text)
            }
        }
        
        return structured_response
    
    def _detect_technical_terms(self, text: str) -> bool:
        """Detect if response contains technical terms."""
        technical_keywords = [
            "algorithm", "database", "api", "framework", "deployment",
            "microservices", "docker", "kubernetes", "aws", "azure",
            "python", "javascript", "react", "node.js", "sql", "nosql"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in technical_keywords)
    
    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis."""
        positive_words = ["good", "great", "excellent", "love", "enjoy", "happy"]
        negative_words = ["bad", "terrible", "hate", "difficult", "problem", "issue"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_key_topics(self, text: str) -> list:
        """Extract key topics from the response."""
        # Simple keyword extraction - in production, use NLP libraries
        topics = []
        text_lower = text.lower()
        
        if "experience" in text_lower or "worked" in text_lower:
            topics.append("work_experience")
        if "project" in text_lower or "built" in text_lower:
            topics.append("projects")
        if "skill" in text_lower or "technology" in text_lower:
            topics.append("skills")
        if "team" in text_lower or "collaboration" in text_lower:
            topics.append("teamwork")
        
        return topics
    
    def _calculate_completeness(self, text: str) -> float:
        """Calculate how complete the response is."""
        # Simple heuristic - in production, use more sophisticated analysis
        if len(text) < 10:
            return 0.2
        elif len(text) < 50:
            return 0.5
        elif len(text) < 200:
            return 0.8
        else:
            return 1.0
    
    async def _generate_agent_reply(
        self,
        original_question: str,
        structured_response: Dict[str, Any],
        round_number: int
    ) -> str:
        """
        Generate agent reply based on structured user response.
        
        In production, this would integrate with your interview logic
        to generate contextual follow-up questions or responses.
        """
        # This is a placeholder - in production, you'd integrate with your
        # interview service to generate contextual responses
        
        user_text = structured_response["raw_text"]
        confidence = structured_response["confidence"]
        
        if confidence < 0.5:
            return "I didn't catch that clearly. Could you please repeat your response?"
        elif len(user_text) < 20:
            return "Could you please elaborate on that? I'd like to hear more details."
        else:
            return f"Thank you for that response. I understand you mentioned {user_text[:50]}... Let me ask you a follow-up question about your experience."
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get the status of the interview pipeline components."""
        try:
            stt_health = await self.stt_client.health_check()
            tts_health = await self.tts_client.health_check()
            
            return {
                "status": "healthy" if stt_health["status"] == "healthy" and tts_health["status"] == "healthy" else "degraded",
                "components": {
                    "stt": stt_health,
                    "tts": tts_health
                },
                "models": {
                    "stt_model": settings.groq_stt_model,
                    "tts_model": settings.groq_tts_model,
                    "default_voice": settings.groq_default_voice
                }
            }
        except Exception as e:
            logger.error(f"Pipeline status check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _cleanup_tts_cache(self) -> None:
        """
        Clean up TTS cache after interview round to free disk space.
        
        This method removes old TTS audio files to prevent disk space issues
        during long interview sessions.
        """
        try:
            # Get cache cleanup endpoint from TTS client
            cleanup_result = await self.tts_client.cleanup_cache()
            logger.info(f"TTS cache cleanup completed: {cleanup_result}")
        except Exception as e:
            logger.warning(f"TTS cache cleanup failed: {str(e)}")
            # Don't raise the exception as cache cleanup failure shouldn't break the interview 