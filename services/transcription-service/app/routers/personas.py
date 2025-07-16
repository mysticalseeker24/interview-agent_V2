"""
Persona Router for TalentSync Transcription Service
Handles persona selection and management for interviews
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.persona_service import persona_service, Persona

router = APIRouter(prefix="/personas", tags=["personas"])

class PersonaResponse(BaseModel):
    """Response model for persona information."""
    name: str
    domain: str
    personality: str
    expertise: List[str]
    interview_approach: List[str]
    evaluation_criteria: List[str]
    success_indicators: List[str]
    technical_domains: List[str]
    voice: str
    voice_description: str

class PersonaSelectionRequest(BaseModel):
    """Request model for persona selection."""
    domain: Optional[str] = None
    persona_name: Optional[str] = None
    resume_data: Optional[Dict[str, Any]] = None

class PersonaSummaryResponse(BaseModel):
    """Response model for persona summary."""
    total_personas: int
    domains: Dict[str, int]
    available_personas: Dict[str, List[str]]

@router.get("/", response_model=PersonaSummaryResponse)
async def get_personas_summary():
    """Get a summary of all available personas."""
    try:
        summary = persona_service.get_persona_summary()
        available_personas = persona_service.get_available_personas()
        summary["available_personas"] = available_personas
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting personas summary: {str(e)}")

@router.get("/domains")
async def get_available_domains():
    """Get all available domains."""
    try:
        domains = list(persona_service.domain_mapping.keys())
        return {"domains": domains, "domain_mapping": persona_service.domain_mapping}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting domains: {str(e)}")

@router.get("/domain/{domain}", response_model=List[PersonaResponse])
async def get_personas_by_domain(domain: str):
    """Get all personas for a specific domain."""
    try:
        domain_personas = persona_service.get_domain_personas(domain)
        if not domain_personas:
            raise HTTPException(status_code=404, detail=f"No personas found for domain: {domain}")
        
        return [
            PersonaResponse(
                name=persona.name,
                domain=persona.domain,
                personality=persona.personality,
                expertise=persona.expertise,
                interview_approach=persona.interview_approach,
                evaluation_criteria=persona.evaluation_criteria,
                success_indicators=persona.success_indicators,
                technical_domains=persona.technical_domains
            )
            for persona in domain_personas
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting personas for domain {domain}: {str(e)}")

@router.get("/{domain}/{persona_name}", response_model=PersonaResponse)
async def get_specific_persona(domain: str, persona_name: str):
    """Get a specific persona by domain and name."""
    try:
        from app.services.persona_service import persona_service
        
        persona = persona_service.get_persona(domain, persona_name)
        if not persona:
            raise HTTPException(
                status_code=404, 
                detail=f"Persona '{persona_name}' not found in domain '{domain}'"
            )
        
        return PersonaResponse(
            name=persona.name,
            domain=persona.domain,
            personality=persona.personality,
            expertise=persona.expertise,
            interview_approach=persona.interview_approach,
            evaluation_criteria=persona.evaluation_criteria,
            success_indicators=persona.success_indicators,
            technical_domains=persona.technical_domains,
            voice=persona.voice,
            voice_description=persona_service.get_voice_description(persona.voice)
        )
        
    except Exception as e:
        logger.error(f"Error getting specific persona: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/voices")
async def get_available_voices():
    """Get all available TTS voices with their descriptions."""
    try:
        from app.services.persona_service import persona_service
        
        voices = persona_service.get_available_voices()
        return {
            "voices": voices,
            "total_voices": len(voices)
        }
        
    except Exception as e:
        logger.error(f"Error getting available voices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/voices/{voice}/personas")
async def get_personas_by_voice(voice: str):
    """Get all personas that use a specific voice."""
    try:
        from app.services.persona_service import persona_service
        
        personas = persona_service.get_personas_by_voice(voice)
        return {
            "voice": voice,
            "voice_description": persona_service.get_voice_description(voice),
            "personas": [
                {
                    "name": persona.name,
                    "domain": persona.domain,
                    "personality": persona.personality[:100] + "..." if len(persona.personality) > 100 else persona.personality
                }
                for persona in personas
            ],
            "count": len(personas)
        }
        
    except Exception as e:
        logger.error(f"Error getting personas by voice: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/voices/summary")
async def get_voice_summary():
    """Get a summary of voice assignments across all personas."""
    try:
        from app.services.persona_service import persona_service
        
        summary = persona_service.get_voice_summary()
        return {
            "voice_summary": summary,
            "total_personas": sum(data["count"] for data in summary.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting voice summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/select", response_model=PersonaResponse)
async def select_persona(request: PersonaSelectionRequest):
    """Select a persona based on domain, name, or resume data."""
    try:
        persona = None
        
        # If resume data is provided, use it to select persona
        if request.resume_data:
            persona = persona_service.get_persona_for_resume(request.resume_data)
        
        # If domain and persona name are provided, get specific persona
        elif request.domain and request.persona_name:
            persona = persona_service.get_persona(request.domain, request.persona_name)
        
        # If only domain is provided, get first persona for that domain
        elif request.domain:
            persona = persona_service.get_persona(request.domain)
        
        if not persona:
            raise HTTPException(
                status_code=404, 
                detail="No suitable persona found for the given criteria"
            )
        
        return PersonaResponse(
            name=persona.name,
            domain=persona.domain,
            personality=persona.personality,
            expertise=persona.expertise,
            interview_approach=persona.interview_approach,
            evaluation_criteria=persona.evaluation_criteria,
            success_indicators=persona.success_indicators,
            technical_domains=persona.technical_domains
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting persona: {str(e)}")

@router.get("/{domain}/{persona_name}/questions")
async def get_persona_questions(domain: str, persona_name: str, category: Optional[str] = None):
    """Get questions for a specific persona and optional category."""
    try:
        persona = persona_service.get_persona(domain, persona_name)
        if not persona:
            raise HTTPException(
                status_code=404, 
                detail=f"Persona {persona_name} not found for domain {domain}"
            )
        
        questions = persona_service.get_persona_questions(persona, category)
        
        return {
            "persona": persona.name,
            "domain": persona.domain,
            "category": category,
            "questions": questions,
            "total_questions": len(questions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting questions for persona {persona_name}: {str(e)}"
        )

@router.get("/health")
async def persona_health_check():
    """Health check for persona service."""
    try:
        summary = persona_service.get_persona_summary()
        return {
            "status": "healthy",
            "total_personas": summary["total_personas"],
            "domains_loaded": len(summary["domains"]),
            "message": "Persona service is operational"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persona service error: {str(e)}") 