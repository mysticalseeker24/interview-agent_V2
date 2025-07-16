#!/usr/bin/env python3
"""
LLM-Based Resume Extractor
Industry-grade implementation with efficient API calling practices.
"""

import os
import json
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry
from app.schema import ResumeJSON, ContactInfo, ExperienceEntry, ProjectEntry, EducationEntry, SkillCategory, CertificationEntry

logger = logging.getLogger(__name__)

class LLMExtractor:
    """
    LLM-based resume extractor with industry-grade practices.
    Handles large files with chunking and extended timeouts.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Using o1-mini for better performance
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        self.max_text_length = 15000  # Maximum text length before chunking
        self.chunk_overlap = 1000  # Overlap between chunks
        
        # Statistics
        self.stats = {
            "total_calls": 0,
            "cache_hits": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_processing_time": 0.0
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError))
    )
    @sleep_and_retry
    @limits(calls=50, period=60)  # 50 calls per minute
    def _call_openai_api(self, messages: List[Dict[str, str]], max_tokens: int = 4000) -> Dict[str, Any]:
        """Call OpenAI API with extended timeout for large files."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.1,  # Low temperature for consistent extraction
                timeout=120  # Extended timeout for large files
            )
            return response.choices[0].message.content
        except openai.APITimeoutError:
            # If timeout occurs, try with smaller max_tokens
            if max_tokens > 2000:
                return self._call_openai_api(messages, max_tokens=max_tokens // 2)
            raise
        except Exception as e:
            self.stats["failed_extractions"] += 1
            raise

    def _create_extraction_prompt(self, text: str) -> str:
        """Create a comprehensive extraction prompt for resume parsing."""
        return f"""
You are an expert resume parser. Extract structured information from the following resume text and return it as a valid JSON object.

RESUME TEXT:
{text}

Please extract and return a JSON object with the following structure:
{{
    "contact": {{
        "name": "Full name",
        "email": "Email address",
        "phone": "Phone number",
        "linkedin": "LinkedIn URL",
        "github": "GitHub URL",
        "website": "Personal website",
        "location": "City, State/Country"
    }},
    "summary": "Professional summary or objective",
    "experience": [
        {{
            "position": "Job title",
            "company": "Company name",
            "start_date": "YYYY-MM or YYYY",
            "end_date": "YYYY-MM, YYYY, or 'Present'",
            "location": "Job location",
            "bullets": ["Achievement 1", "Achievement 2"],
            "metrics": ["Quantified result 1", "Quantified result 2"],
            "technologies": ["Tech 1", "Tech 2"]
        }}
    ],
    "projects": [
        {{
            "name": "Project name",
            "description": "Project description",
            "technologies": ["Tech 1", "Tech 2"],
            "url": "Project URL",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM or 'Present'",
            "bullets": ["Feature 1", "Feature 2"],
            "metrics": ["Quantified result 1"]
        }}
    ],
    "education": [
        {{
            "institution": "University name",
            "degree": "Degree type",
            "field_of_study": "Major/Field",
            "start_date": "YYYY",
            "end_date": "YYYY",
            "gpa": "GPA if available",
            "honors": "Honors or awards"
        }}
    ],
    "skills": [
        {{
            "category": "Programming Languages",
            "skills": ["Python", "JavaScript", "Java"]
        }},
        {{
            "category": "Frameworks & Libraries",
            "skills": ["React", "Django", "TensorFlow"]
        }},
        {{
            "category": "Cloud & DevOps",
            "skills": ["AWS", "Docker", "Kubernetes"]
        }}
    ],
    "certifications": [
        {{
            "name": "Certification name",
            "issuer": "Issuing organization",
            "issue_date": "YYYY-MM",
            "expiry_date": "YYYY-MM or null",
            "credential_id": "Certification ID"
        }}
    ],
    "achievements": ["Achievement 1", "Achievement 2"],
    "domains": ["AI Engineering", "DevOps", "Full Stack Development"]
}}

IMPORTANT:
1. Return ONLY valid JSON - no additional text
2. Use null for missing values, not empty strings
3. Extract all available information accurately
4. For dates, use YYYY-MM format when possible
5. For technologies, extract specific tech names from the text
6. For metrics, look for quantified achievements (%, numbers, etc.)
7. For domains, identify the primary technical domains from the resume
8. Ensure all arrays are properly formatted even if empty
"""

    def _chunk_text(self, text: str) -> List[str]:
        """Split large text into manageable chunks with overlap."""
        if len(text) <= self.max_text_length:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.max_text_length
            
            # Try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + self.max_text_length - 500, start), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
        
        return chunks

    def _merge_chunk_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from multiple chunks into a single comprehensive result."""
        if not chunk_results:
            return {}
        
        if len(chunk_results) == 1:
            return chunk_results[0]
        
        # Start with the first chunk's result
        merged = chunk_results[0].copy()
        
        # Merge contact info (take the most complete)
        for chunk in chunk_results[1:]:
            if chunk.get("contact"):
                for key, value in chunk["contact"].items():
                    if value and (not merged.get("contact", {}).get(key) or 
                                len(str(value)) > len(str(merged["contact"].get(key, "")))):
                        if "contact" not in merged:
                            merged["contact"] = {}
                        merged["contact"][key] = value
        
        # Merge arrays (experience, projects, education, skills, certifications, achievements)
        for array_key in ["experience", "projects", "education", "skills", "certifications", "achievements"]:
            merged[array_key] = merged.get(array_key, [])
            for chunk in chunk_results[1:]:
                if chunk.get(array_key):
                    merged[array_key].extend(chunk[array_key])
        
        # Merge domains (unique list)
        all_domains = set(merged.get("domains", []))
        for chunk in chunk_results[1:]:
            if chunk.get("domains"):
                all_domains.update(chunk["domains"])
        merged["domains"] = list(all_domains)
        
        return merged

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and handle JSON parsing errors."""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            try:
                # Find JSON-like content
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            
            # Return a basic structure if parsing fails
            return {
                "contact": {},
                "summary": None,
                "experience": [],
                "projects": [],
                "education": [],
                "skills": [],
                "certifications": [],
                "achievements": [],
                "domains": []
            }

    def _calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extraction completeness."""
        confidence = 0.0
        total_fields = 0
        
        # Contact information (weight: 30%)
        contact = extracted_data.get("contact", {})
        contact_fields = ["name", "email", "phone", "linkedin", "github", "location"]
        contact_score = sum(1 for field in contact_fields if contact.get(field)) / len(contact_fields)
        confidence += contact_score * 0.3
        total_fields += 1
        
        # Experience (weight: 25%)
        experience = extracted_data.get("experience", [])
        if experience:
            exp_score = min(len(experience) / 3.0, 1.0)  # Normalize to 0-1
            confidence += exp_score * 0.25
        total_fields += 1
        
        # Skills (weight: 20%)
        skills = extracted_data.get("skills", [])
        if skills:
            skills_score = min(len(skills) / 5.0, 1.0)  # Normalize to 0-1
            confidence += skills_score * 0.20
        total_fields += 1
        
        # Education (weight: 15%)
        education = extracted_data.get("education", [])
        if education:
            edu_score = min(len(education) / 2.0, 1.0)  # Normalize to 0-1
            confidence += edu_score * 0.15
        total_fields += 1
        
        # Projects (weight: 10%)
        projects = extracted_data.get("projects", [])
        if projects:
            proj_score = min(len(projects) / 3.0, 1.0)  # Normalize to 0-1
            confidence += proj_score * 0.10
        total_fields += 1
        
        return min(confidence, 1.0)

    def _detect_sections(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Detect which sections were successfully extracted."""
        sections = []
        
        if extracted_data.get("contact", {}).get("name"):
            sections.append("contact")
        if extracted_data.get("experience"):
            sections.append("experience")
        if extracted_data.get("education"):
            sections.append("education")
        if extracted_data.get("skills"):
            sections.append("skills")
        if extracted_data.get("projects"):
            sections.append("projects")
        if extracted_data.get("certifications"):
            sections.append("certifications")
        if extracted_data.get("achievements"):
            sections.append("achievements")
        
        return sections

    def extract_resume(self, text: str) -> ResumeJSON:
        """
        Extract resume information using LLM with support for large files.
        Handles chunking for files > 15KB and includes comprehensive error handling.
        """
        start_time = time.time()
        
        # Generate cache key
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"resume_{text_hash}"
        
        # Check cache
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if datetime.now() - cache_entry["timestamp"] < timedelta(seconds=self.cache_ttl):
                self.stats["cache_hits"] += 1
                return cache_entry["data"]
        
        try:
            # Chunk text if it's too large
            text_chunks = self._chunk_text(text)
            chunk_results = []
            
            for i, chunk in enumerate(text_chunks):
                print(f"Processing chunk {i+1}/{len(text_chunks)} ({len(chunk)} characters)")
                
                # Create prompt for this chunk
                prompt = self._create_extraction_prompt(chunk)
                messages = [{"role": "user", "content": prompt}]
                
                # Call API with retry logic
                response = self._call_openai_api(messages, max_tokens=4000)
                chunk_data = self._parse_llm_response(response)
                chunk_results.append(chunk_data)
                
                # Small delay between chunks to avoid rate limits
                if i < len(text_chunks) - 1:
                    time.sleep(0.5)
            
            # Merge results from all chunks
            merged_data = self._merge_chunk_results(chunk_results)
            
            # Convert to ResumeJSON
            resume_json = ResumeJSON(
                contact=ContactInfo(**merged_data.get("contact", {})),
                summary=merged_data.get("summary"),
                experience=[ExperienceEntry(**exp) for exp in merged_data.get("experience", [])],
                projects=[ProjectEntry(**proj) for proj in merged_data.get("projects", [])],
                education=[EducationEntry(**edu) for edu in merged_data.get("education", [])],
                skills=[SkillCategory(**skill) for skill in merged_data.get("skills", [])],
                certifications=[CertificationEntry(**cert) for cert in merged_data.get("certifications", [])],
                achievements=merged_data.get("achievements", []),
                domains=merged_data.get("domains", []),
                raw_text_length=len(text),
                parsing_confidence=self._calculate_confidence(merged_data),
                sections_detected=self._detect_sections(merged_data),
                text_extraction_method="llm",
                llm_enhanced=True
            )
            
            # Cache the result
            self.cache[cache_key] = {
                "data": resume_json,
                "timestamp": datetime.now()
            }
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats["total_calls"] += 1
            self.stats["successful_extractions"] += 1
            self.stats["average_processing_time"] = (
                (self.stats["average_processing_time"] * (self.stats["successful_extractions"] - 1) + processing_time) /
                self.stats["successful_extractions"]
            )
            
            return resume_json
            
        except Exception as e:
            self.stats["failed_extractions"] += 1
            print(f"Error in LLM extraction: {str(e)}")
            
            # Return a basic ResumeJSON with error information
            return ResumeJSON(
                raw_text_length=len(text),
                parsing_confidence=0.0,
                sections_detected=[],
                text_extraction_method="llm",
                llm_enhanced=True
            )

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics and performance metrics."""
        return {
            "total_calls": self.stats["total_calls"],
            "cache_hits": self.stats["cache_hits"],
            "successful_extractions": self.stats["successful_extractions"],
            "failed_extractions": self.stats["failed_extractions"],
            "average_processing_time": self.stats["average_processing_time"],
            "cache_size": len(self.cache),
            "cache_hit_rate": self.stats["cache_hits"] / max(self.stats["total_calls"], 1)
        }

    def clear_cache(self):
        """Clear the extraction cache."""
        self.cache.clear() 