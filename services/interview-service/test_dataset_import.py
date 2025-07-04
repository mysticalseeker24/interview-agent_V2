"""
Test script to import datasets using the API.
"""
import requests
import json
import os
import sys
from pathlib import Path

# Base URL for the API
BASE_URL = "http://localhost:8002/api/v1"

def test_import_all_datasets():
    """Test importing all datasets."""
    url = f"{BASE_URL}/datasets/import/all"
    response = requests.post(url)
    print(f"Import all datasets response: {response.status_code}")
    print(response.json())

def test_import_specific_dataset(file_path):
    """Test importing a specific dataset."""
    url = f"{BASE_URL}/datasets/import/path"
    params = {"file_path": file_path}
    response = requests.post(url, params=params)
    print(f"Import dataset response: {response.status_code}")
    print(response.json())

def test_sync_all_questions():
    """Test syncing all questions to Pinecone."""
    url = f"{BASE_URL}/vectors/sync/questions/all"
    response = requests.post(url)
    print(f"Sync all questions response: {response.status_code}")
    print(response.json())

def main():
    """Main function to run tests."""
    # Get the absolute path to the data directory
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    
    # Check if path exists
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        sys.exit(1)
        
    print(f"Testing with data directory: {data_dir}")
    
    # Test import all datasets
    test_import_all_datasets()
    
    # Test import specific dataset
    for dataset_file in data_dir.glob("*.json"):
        test_import_specific_dataset(str(dataset_file))
        
    # Test sync all questions
    test_sync_all_questions()

if __name__ == "__main__":
    main()
