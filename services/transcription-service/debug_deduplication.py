#!/usr/bin/env python3

"""
Debug script for segment deduplication logic.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.transcription_service import TranscriptionService

def debug_deduplication():
    """Debug the deduplication logic."""
    print("🔧 Debugging Segment Deduplication...")
    
    transcription_service = TranscriptionService()
    
    # Create test segments with overlaps
    test_segments = [
        {"start": 0.0, "end": 2.0, "text": "Hello world"},
        {"start": 1.5, "end": 3.5, "text": "Hello world"},  # Should overlap
        {"start": 3.0, "end": 5.0, "text": "This is a test"},
        {"start": 4.5, "end": 6.5, "text": "This is different"},  # Different text
        {"start": 6.0, "end": 8.0, "text": "Final segment"}
    ]
    
    print("Original segments:")
    for i, segment in enumerate(test_segments):
        print(f"  {i+1}. {segment['start']:.1f}s - {segment['end']:.1f}s: '{segment['text']}'")
    
    # Debug the deduplication process
    sorted_segments = sorted(test_segments, key=lambda x: x.get("start", 0))
    deduplicated = []
    
    for i, segment in enumerate(sorted_segments):
        print(f"\nProcessing segment {i+1}: {segment['start']:.1f}s - {segment['end']:.1f}s: '{segment['text']}'")
        
        if deduplicated:
            last_segment = deduplicated[-1]
            print(f"  Comparing with last segment: {last_segment['start']:.1f}s - {last_segment['end']:.1f}s: '{last_segment['text']}'")
            
            overlap_threshold = 0.2  # 20% overlap threshold
            
            # Calculate overlap duration
            overlap_start = max(last_segment.get("start", 0), segment.get("start", 0))
            overlap_end = min(last_segment.get("end", 0), segment.get("end", 0))
            overlap_duration = max(0, overlap_end - overlap_start)
            
            segment_duration = segment.get("end", 0) - segment.get("start", 0)
            last_duration = last_segment.get("end", 0) - last_segment.get("start", 0)
            
            print(f"  Overlap: {overlap_start:.1f}s - {overlap_end:.1f}s = {overlap_duration:.1f}s")
            print(f"  Segment duration: {segment_duration:.1f}s")
            print(f"  Last segment duration: {last_duration:.1f}s")
            print(f"  Min duration: {min(segment_duration, last_duration):.1f}s")
            print(f"  Overlap threshold: {overlap_threshold * min(segment_duration, last_duration):.1f}s")
            
            text_match = segment.get("text", "").strip().lower() == last_segment.get("text", "").strip().lower()
            overlap_significant = overlap_duration > overlap_threshold * min(segment_duration, last_duration)
            
            print(f"  Text match: {text_match}")
            print(f"  Overlap significant: {overlap_significant}")
            
            if overlap_significant and text_match:
                print(f"  → SKIPPING (duplicate)")
                continue
        
        print(f"  → KEEPING")
        deduplicated.append(segment)
    
    print(f"\nFinal result:")
    print(f"Original: {len(test_segments)} segments")
    print(f"Deduplicated: {len(deduplicated)} segments")
    
    for i, segment in enumerate(deduplicated):
        print(f"  {i+1}. {segment['start']:.1f}s - {segment['end']:.1f}s: '{segment['text']}'")

if __name__ == "__main__":
    debug_deduplication()
