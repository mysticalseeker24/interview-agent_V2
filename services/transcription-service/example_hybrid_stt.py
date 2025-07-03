"""
Example implementation of the hybrid STT transcription service.
This matches the task requirements exactly.
"""

import os
import openai
import asyncio
from typing import Dict, Any, List
import httpx


async def transcribe_audio(file_path: str) -> Dict[str, Any]:
    """
    Hybrid STT transcription function as specified in the task.
    
    1. Call OpenAI Whisper first
    2. If any segment confidence < 0.85, fallback to AssemblyAI
    3. Return normalized response
    """
    # Try OpenAI Whisper first
    try:
        with open(file_path, 'rb') as audio_file:
            resp = openai.Audio.transcribe('whisper-1', audio_file)
        
        # Check if any segment has low confidence
        low_conf = any(seg['confidence'] < 0.85 for seg in resp.get('segments', []))
        
        if not low_conf:
            # Good confidence, use OpenAI result
            return normalize_openai_response(resp)
        else:
            # Low confidence, use AssemblyAI fallback
            resp = await assemblyai_transcribe(file_path)
            return normalize_assemblyai_response(resp)
            
    except Exception as e:
        # OpenAI failed, use AssemblyAI
        resp = await assemblyai_transcribe(file_path)
        return normalize_assemblyai_response(resp)


async def assemblyai_transcribe(file_path: str) -> Dict[str, Any]:
    """
    AssemblyAI transcription fallback.
    
    1. Upload file to AssemblyAI
    2. Poll /transcript/{id} until status=completed
    3. Return result
    """
    import assemblyai as aai
    
    # Set API key
    aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    # Create transcriber
    transcriber = aai.Transcriber()
    
    # Transcribe the file
    transcript = transcriber.transcribe(file_path)
    
    # Check for errors
    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"AssemblyAI transcription failed: {transcript.error}")
    
    # Convert to dict format
    result = {
        "text": transcript.text,
        "words": []
    }
    
    # Add word-level timestamps if available
    if hasattr(transcript, 'words') and transcript.words:
        result["words"] = [
            {
                "text": word.text,
                "start": word.start,
                "end": word.end,
                "confidence": word.confidence
            }
            for word in transcript.words
        ]
    
    return result


def normalize_openai_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize OpenAI response to standard format."""
    segments = []
    
    for seg in resp.get('segments', []):
        segments.append({
            "start": seg.get('start', 0),
            "end": seg.get('end', 0),
            "text": seg.get('text', ''),
            "confidence": 1.0 - seg.get('no_speech_prob', 0)
        })
    
    return {
        "transcript": resp.get('text', ''),
        "segments": segments,
        "provider": "openai",
        "fallback_used": False
    }


def normalize_assemblyai_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize AssemblyAI response to standard format."""
    segments = []
    words = resp.get('words', [])
    
    # Group words into segments (every 10 words)
    if words:
        for i in range(0, len(words), 10):
            segment_words = words[i:i+10]
            segments.append({
                "start": segment_words[0].get('start', 0) / 1000.0,
                "end": segment_words[-1].get('end', 0) / 1000.0,
                "text": ' '.join([w.get('text', '') for w in segment_words]),
                "confidence": sum([w.get('confidence', 0) for w in segment_words]) / len(segment_words)
            })
    
    return {
        "transcript": resp.get('text', ''),
        "segments": segments,
        "provider": "assemblyai",
        "fallback_used": True
    }


def normalize(resp: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize response to the required format:
    { transcript: str, segments: [{start,end,text}] }
    """
    return {
        "transcript": resp.get("transcript", ""),
        "segments": resp.get("segments", [])
    }


# Example usage:
if __name__ == "__main__":
    async def main():
        # Example file path
        file_path = "path/to/audio/file.mp3"
        
        # Transcribe
        result = await transcribe_audio(file_path)
        
        # Print normalized result
        normalized = normalize(result)
        print(f"Transcript: {normalized['transcript']}")
        print(f"Segments: {len(normalized['segments'])}")
    
    asyncio.run(main())
