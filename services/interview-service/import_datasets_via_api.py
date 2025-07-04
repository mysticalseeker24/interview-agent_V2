"""
Script to import datasets via the FastAPI endpoints.
"""
import os
import requests
import json
from pathlib import Path

# Base URL for the API - update if needed
BASE_URL = "http://localhost:8002/api/v1"

def create_module_if_not_exists(title, category):
    """
    Create a module if it doesn't already exist.
    
    Args:
        title: Module title
        category: Module category from ModuleCategory enum
        
    Returns:
        Module ID if successful, None if failed
    """
    url = f"{BASE_URL}/modules"
    
    payload = {
        "title": title,
        "description": f"Questions for {title}",
        "category": category,
        "difficulty": "medium",
        "duration_minutes": 30
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code in (200, 201):
        return response.json().get("id")
    else:
        print(f"Failed to create module: {response.status_code} - {response.text}")
        return None


def get_modules():
    """
    Get existing modules.
    
    Returns:
        List of modules
    """
    url = f"{BASE_URL}/modules"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json().get("modules", [])
    else:
        print(f"Failed to get modules: {response.status_code} - {response.text}")
        return []


def import_dataset_via_api(file_path, module_id=None):
    """
    Import a dataset via the API.
    
    Args:
        file_path: Path to the dataset file
        module_id: Optional module ID to assign questions to
        
    Returns:
        True if successful, False if failed
    """
    url = f"{BASE_URL}/datasets/import/path"
    params = {"file_path": str(file_path)}
    
    if module_id:
        params["module_id"] = module_id
    
    response = requests.post(url, params=params)
    
    if response.status_code == 202:
        print(f"Successfully started import for {file_path.name}: {response.json().get('message')}")
        return True
    else:
        print(f"Failed to import dataset {file_path.name}: {response.status_code} - {response.text}")
        return False


def sync_questions_to_pinecone():
    """
    Sync all questions to Pinecone.
    
    Returns:
        True if successful, False if failed
    """
    url = f"{BASE_URL}/vectors/sync/questions/all"
    response = requests.post(url)
    
    if response.status_code == 200:
        print(f"Successfully started sync: {response.json().get('message')}")
        return True
    else:
        print(f"Failed to sync questions: {response.status_code} - {response.text}")
        return False


def main():
    """Main entry point for the script."""
    print("Starting dataset import process via API")
    
    # Get the path to the data directory
    data_dir = Path(__file__).resolve().parent.parent / "data"
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    print(f"Data directory: {data_dir}")
    
    # Dataset to category mapping
    dataset_categories = {
        "SWE_dataset.json": "software_engineering",
        "ML_dataset.json": "machine_learning",
        "DSA_dataset.json": "data_structures",
        "Resume_dataset.json": "resume_driven",
        "Resumes_dataset.json": "resume_driven",
    }
    
    # Get existing modules
    existing_modules = get_modules()
    module_map = {m["title"].lower(): m["id"] for m in existing_modules}
    
    # Import each dataset
    for file_path in data_dir.glob("*.json"):
        if file_path.name in dataset_categories:
            # Get module title
            module_title = file_path.stem.replace("_dataset", "").replace("_", " ").title()
            module_category = dataset_categories[file_path.name]
            
            # Check if module exists or create it
            module_id = module_map.get(module_title.lower())
            
            if not module_id:
                module_id = create_module_if_not_exists(module_title, module_category)
                
            if module_id:
                # Import dataset
                import_dataset_via_api(file_path, module_id)
    
    # Sync all questions to Pinecone
    sync_questions_to_pinecone()
    
    print("Dataset import process via API completed")


if __name__ == "__main__":
    main()
