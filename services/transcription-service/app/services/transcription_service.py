import os
import io
import wave
import base64
import tempfile
import numpy as np
import sounddevice as sd
from openai import OpenAI
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transcription import Transcription
from app.core.config import settings

class TranscriptionService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 5  # seconds per chunk
        self.silence_threshold = 0.03
        self.silence_duration = 2.0  # seconds of silence to stop

    async def record_audio(self) -> bytes:
        """Record audio until silence is detected."""
        print("Recording... (speak now)")
        
        chunk_frames = int(self.sample_rate * self.chunk_duration)
        silence_frames = int(self.sample_rate * self.silence_duration)
        
        recording = []
        silence_count = 0

        def callback(indata, frames, time, status):
            nonlocal silence_count
            if status:
                print(f"Error: {status}")
            recording.append(indata.copy())
            if np.abs(indata).mean() < self.silence_threshold:
                silence_count += frames
            else:
                silence_count = 0

        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels,
                          callback=callback, dtype=np.float32):
            while silence_count < silence_frames:
                sd.sleep(100)  # Sleep for 100ms between checks

        audio_data = np.concatenate(recording, axis=0)
        byte_io = io.BytesIO()
        with wave.open(byte_io, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.sample_rate)
            wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        
        return byte_io.getvalue()

    async def transcribe_audio_chunk(self, audio_data: bytes, use_verbose: bool = True) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper API with detailed segment information."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_filename = temp_file.name

            with open(temp_filename, "rb") as audio_file:
                if use_verbose:
                    # Use verbose_json for detailed segment information
                    transcript_response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        language="en"
                    )
                    
                    # Extract segments and confidence information
                    segments = []
                    total_confidence = 0
                    segment_count = 0
                    
                    if hasattr(transcript_response, 'segments') and transcript_response.segments:
                        for segment in transcript_response.segments:
                            segment_data = {
                                "start": segment.start,
                                "end": segment.end,
                                "text": segment.text.strip(),
                                "tokens": getattr(segment, 'tokens', []),
                                "temperature": getattr(segment, 'temperature', 0.0),
                                "avg_logprob": getattr(segment, 'avg_logprob', 0.0),
                                "compression_ratio": getattr(segment, 'compression_ratio', 0.0),
                                "no_speech_prob": getattr(segment, 'no_speech_prob', 0.0)
                            }
                            segments.append(segment_data)
                            
                            # Calculate confidence from no_speech_prob (inverted)
                            confidence = 1.0 - segment_data["no_speech_prob"]
                            total_confidence += confidence
                            segment_count += 1
                    
                    avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
                    
                    return {
                        "text": transcript_response.text,
                        "segments": segments,
                        "confidence_score": avg_confidence,
                        "language": getattr(transcript_response, 'language', 'en'),
                        "duration": getattr(transcript_response, 'duration', 0.0)
                    }
                else:
                    # Simple text response
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                    return {
                        "text": transcript,
                        "segments": [],
                        "confidence_score": None
                    }
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            raise
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    async def save_transcription_chunk(
        self,
        session: AsyncSession,
        session_id: str,
        media_chunk_id: str,
        sequence_index: int,
        transcript_text: str,
        segments: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[float] = None,
        question_id: Optional[str] = None
    ) -> Transcription:
        """Save a transcription chunk to the database."""
        transcription = Transcription(
            session_id=session_id,
            question_id=question_id,
            media_chunk_id=media_chunk_id,
            sequence_index=sequence_index,
            transcript_text=transcript_text,
            segments=segments,
            confidence_score=confidence_score
        )
        session.add(transcription)
        await session.commit()
        await session.refresh(transcription)
        return transcription

    async def get_session_chunks(
        self,
        session: AsyncSession,
        session_id: str
    ) -> List[Transcription]:
        """Get all transcription chunks for a session, ordered by sequence."""
        result = await session.execute(
            select(Transcription)
            .where(Transcription.session_id == session_id)
            .where(Transcription.media_chunk_id.is_not(None))
            .order_by(Transcription.sequence_index)
        )
        return result.scalars().all()

    async def aggregate_session_transcript(
        self,
        session: AsyncSession,
        session_id: str
    ) -> Dict[str, Any]:
        """Aggregate all chunks for a session into a complete transcript."""
        chunks = await self.get_session_chunks(session, session_id)
        
        if not chunks:
            raise ValueError(f"No transcription chunks found for session {session_id}")
        
        # Combine transcript text
        full_transcript = " ".join(chunk.transcript_text for chunk in chunks if chunk.transcript_text)
        
        # Combine and deduplicate segments
        all_segments = []
        total_confidence = 0
        confidence_count = 0
        
        for chunk in chunks:
            if chunk.segments:
                all_segments.extend(chunk.segments)
            if chunk.confidence_score is not None:
                total_confidence += chunk.confidence_score
                confidence_count += 1
        
        # Calculate average confidence
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else None
        
        # Remove duplicate segments based on timing overlap
        deduplicated_segments = self._deduplicate_segments(all_segments)
        
        return {
            "full_transcript": full_transcript,
            "total_chunks": len(chunks),
            "segments": deduplicated_segments,
            "confidence_score": avg_confidence
        }

    def _deduplicate_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate segments based on timing overlap."""
        if not segments:
            return []
        
        # Sort segments by start time
        sorted_segments = sorted(segments, key=lambda x: x.get("start", 0))
        deduplicated = []
        
        for segment in sorted_segments:
            # Check if this segment overlaps significantly with the last one
            if deduplicated:
                last_segment = deduplicated[-1]
                overlap_threshold = 0.5  # 50% overlap threshold
                
                start_overlap = max(0, min(last_segment.get("end", 0), segment.get("end", 0)) - 
                                  max(last_segment.get("start", 0), segment.get("start", 0)))
                
                segment_duration = segment.get("end", 0) - segment.get("start", 0)
                last_duration = last_segment.get("end", 0) - last_segment.get("start", 0)
                
                if (start_overlap > overlap_threshold * min(segment_duration, last_duration) and 
                    segment.get("text", "").strip() == last_segment.get("text", "").strip()):
                    continue  # Skip duplicate
            
            deduplicated.append(segment)
        
        return deduplicated

    async def save_transcription(
        self,
        session: AsyncSession,
        session_id: str,
        transcript_text: str,
        question_id: Optional[str] = None
    ) -> Transcription:
        """Save a simple transcription (non-chunked)."""
        transcription = Transcription(
            session_id=session_id,
            question_id=question_id,
            transcript_text=transcript_text
        )
        session.add(transcription)
        await session.commit()
        await session.refresh(transcription)
        return transcription

    async def process_audio_chunk(
        self,
        session: AsyncSession,
        session_id: str,
        question_id: Optional[str] = None
    ) -> Transcription:
        """Record and process a single audio chunk."""
        audio_data = await self.record_audio()
        transcript_result = await self.transcribe_audio_chunk(audio_data)
        
        return await self.save_transcription(
            session, 
            session_id, 
            transcript_result["text"], 
            question_id
        )
        return await self.save_transcription(session, session_id, transcript, question_id)
