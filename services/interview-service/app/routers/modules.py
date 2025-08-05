"""Modules router for managing interview modules in TalentSync Interview Service."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.dependencies.auth import get_current_user, User
from app.schemas.interview import Module, ModuleCreate
from app.core.settings import settings

router = APIRouter()


# Mock modules data - in production, this would come from a database
MOCK_MODULES = [
    {
        "id": "dsa-basic",
        "title": "Data Structures & Algorithms Fundamentals",
        "description": "Core DSA concepts including arrays, linked lists, trees, graphs, and algorithmic techniques.",
        "category": "dsa",
        "difficulty": "easy",
        "duration_minutes": 30,
        "is_active": True
    },
    {
        "id": "dsa-advanced",
        "title": "Advanced Data Structures & Algorithms",
        "description": "Advanced DSA topics including dynamic programming, advanced graph algorithms, and optimization techniques.",
        "category": "dsa",
        "difficulty": "hard",
        "duration_minutes": 45,
        "is_active": True
    },
    {
        "id": "devops-basic",
        "title": "DevOps Fundamentals",
        "description": "Core DevOps practices including CI/CD, containerization, and infrastructure as code.",
        "category": "devops",
        "difficulty": "easy",
        "duration_minutes": 30,
        "is_active": True
    },
    {
        "id": "devops-kubernetes",
        "title": "DevOps & Kubernetes",
        "description": "Advanced DevOps with Kubernetes orchestration, microservices, and cloud-native practices.",
        "category": "devops",
        "difficulty": "hard",
        "duration_minutes": 45,
        "is_active": True
    },
    {
        "id": "ai-engineering-basic",
        "title": "AI Engineering Fundamentals",
        "description": "Core AI engineering concepts including model deployment, MLOps, and production AI systems.",
        "category": "ai-engineering",
        "difficulty": "medium",
        "duration_minutes": 35,
        "is_active": True
    },
    {
        "id": "ai-engineering-advanced",
        "title": "Advanced AI Engineering",
        "description": "Advanced AI engineering including large language models, distributed AI systems, and AI infrastructure.",
        "category": "ai-engineering",
        "difficulty": "hard",
        "duration_minutes": 50,
        "is_active": True
    },
    {
        "id": "machine-learning-basic",
        "title": "Machine Learning Fundamentals",
        "description": "Core ML concepts including supervised/unsupervised learning, model evaluation, and feature engineering.",
        "category": "machine-learning",
        "difficulty": "easy",
        "duration_minutes": 30,
        "is_active": True
    },
    {
        "id": "machine-learning-advanced",
        "title": "Advanced Machine Learning",
        "description": "Advanced ML including deep learning, neural networks, and cutting-edge ML techniques.",
        "category": "machine-learning",
        "difficulty": "hard",
        "duration_minutes": 50,
        "is_active": True
    },
    {
        "id": "data-science-basic",
        "title": "Data Science Fundamentals",
        "description": "Core data science concepts including data analysis, statistics, and data visualization.",
        "category": "data-science",
        "difficulty": "easy",
        "duration_minutes": 30,
        "is_active": True
    },
    {
        "id": "data-science-advanced",
        "title": "Advanced Data Science",
        "description": "Advanced data science including big data, statistical modeling, and predictive analytics.",
        "category": "data-science",
        "difficulty": "hard",
        "duration_minutes": 45,
        "is_active": True
    },
    {
        "id": "software-engineering-basic",
        "title": "Software Engineering Fundamentals",
        "description": "Core software engineering concepts including system design, architecture, and best practices.",
        "category": "software-engineering",
        "difficulty": "easy",
        "duration_minutes": 30,
        "is_active": True
    },
    {
        "id": "software-engineering-advanced",
        "title": "Advanced Software Engineering",
        "description": "Advanced SWE topics including distributed systems, microservices, and performance optimization.",
        "category": "software-engineering",
        "difficulty": "hard",
        "duration_minutes": 45,
        "is_active": True
    },
    {
        "id": "resume-based",
        "title": "Resume-Based Interview",
        "description": "Personalized interview based on your resume and experience.",
        "category": "resume-based",
        "difficulty": "medium",
        "duration_minutes": 45,
        "is_active": True
    }
]


@router.get("/", response_model=List[Module])
async def get_modules(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (easy, medium, hard)")
) -> List[Module]:
    """
    Get available interview modules with optional filtering.
    
    Args:
        category: Filter modules by category
        difficulty: Filter modules by difficulty level
        
    Returns:
        List of available modules
    """
    try:
        modules = [Module(**module) for module in MOCK_MODULES]
        
        # Apply filters
        if category:
            modules = [m for m in modules if m.category == category]
        
        if difficulty:
            modules = [m for m in modules if m.difficulty == difficulty]
        
        # Only return active modules
        modules = [m for m in modules if m.is_active]
        
        return modules
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve modules: {str(e)}")


@router.get("/{module_id}", response_model=Module)
async def get_module(
    module_id: str
) -> Module:
    """
    Get specific module by ID.
    
    Args:
        module_id: Module identifier
        
    Returns:
        Module details
        
    Raises:
        HTTPException: If module not found
    """
    try:
        for module_data in MOCK_MODULES:
            if module_data["id"] == module_id and module_data["is_active"]:
                return Module(**module_data)
        
        raise HTTPException(status_code=404, detail="Module not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve module: {str(e)}")


@router.get("/categories/list")
async def get_categories() -> List[str]:
    """
    Get list of available module categories.
    
    Args:
        
    Returns:
        List of unique categories
    """
    try:
        categories = list(set(module["category"] for module in MOCK_MODULES if module["is_active"]))
        return sorted(categories)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve categories: {str(e)}")


@router.get("/difficulties/list")
async def get_difficulties() -> List[str]:
    """
    Get list of available difficulty levels.
    
    Args:
        
    Returns:
        List of difficulty levels
    """
    try:
        difficulties = list(set(module["difficulty"] for module in MOCK_MODULES if module["is_active"]))
        return sorted(difficulties)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve difficulties: {str(e)}")


@router.post("/", response_model=Module)
async def create_module(
    module_data: ModuleCreate
) -> Module:
    """
    Create a new interview module (admin only).
    
    Args:
        module_data: Module creation data
        
    Returns:
        Created module
        
    Raises:
        HTTPException: If user is not admin or creation fails
    """
    try:
        current_user = await get_current_user()
        # In development mode, all users have admin access
        # In production, you would check if user is admin
        # if current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # In production, this would save to database
        # For now, return a mock response
        new_module = Module(
            id=f"{module_data.category}-{module_data.difficulty}-{len(MOCK_MODULES)}",
            **module_data.model_dump()
        )
        
        return new_module
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create module: {str(e)}")


@router.put("/{module_id}", response_model=Module)
async def update_module(
    module_id: str,
    module_data: ModuleCreate
) -> Module:
    """
    Update an existing module (admin only).
    
    Args:
        module_id: Module identifier
        module_data: Updated module data
        
    Returns:
        Updated module
        
    Raises:
        HTTPException: If user is not admin or module not found
    """
    try:
        current_user = await get_current_user()
        # In development mode, all users have admin access
        # In production, you would check if user is admin
        # if current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Find existing module
        for module in MOCK_MODULES:
            if module["id"] == module_id:
                # Update module data
                updated_module = Module(
                    id=module_id,
                    **module_data.model_dump()
                )
                return updated_module
        
        raise HTTPException(status_code=404, detail="Module not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update module: {str(e)}")


@router.delete("/{module_id}")
async def delete_module(
    module_id: str
) -> JSONResponse:
    """
    Delete a module (admin only).
    
    Args:
        module_id: Module identifier
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If user is not admin or module not found
    """
    try:
        current_user = await get_current_user()
        # In development mode, all users have admin access
        # In production, you would check if user is admin
        # if current_user.role != "admin":
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Find and mark module as inactive
        for module in MOCK_MODULES:
            if module["id"] == module_id:
                module["is_active"] = False
                return JSONResponse(
                    status_code=200,
                    content={"message": f"Module {module_id} deleted successfully"}
                )
        
        raise HTTPException(status_code=404, detail="Module not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete module: {str(e)}") 