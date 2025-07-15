#!/usr/bin/env python3
"""
Enhanced API Test Script
Tests the enhanced resume processing API endpoints with various configurations.
"""
import requests
import json
import time
from pathlib import Path
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8004"
TEST_RESUME_PATH = "data/Resume (1).pdf"

def test_health_endpoints():
    """Test health and status endpoints."""
    print("🔍 Testing Health Endpoints...")
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Root endpoint: {data['service']} v{data['version']}")
        print(f"   Enhanced features: {data['enhanced_features']}")
    else:
        print(f"❌ Root endpoint failed: {response.status_code}")
    
    # Test health check
    response = requests.get(f"{BASE_URL}/api/v1/health")
    if response.status_code == 200:
        print(f"✅ Health check: {response.json()}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
    
    # Test enhanced status
    response = requests.get(f"{BASE_URL}/enhanced/status")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Enhanced status: {data['status']}")
        print(f"   Features: {list(data['enhanced_features'].keys())}")
    else:
        print(f"❌ Enhanced status failed: {response.status_code}")

def test_pipeline_info():
    """Test pipeline information endpoint."""
    print("\n🔍 Testing Pipeline Information...")
    
    response = requests.get(f"{BASE_URL}/pipeline/info")
    if response.status_code == 200:
        data = response.json()
        print("✅ Pipeline info retrieved:")
        print(f"   Standard pipeline: {data['standard_pipeline']['pipeline_name']}")
        print(f"   Enhanced pipeline: {data['enhanced_pipeline']['name']}")
        print(f"   Enhanced features: {len(data['enhanced_pipeline']['features'])} features")
    else:
        print(f"❌ Pipeline info failed: {response.status_code}")

def test_standard_upload():
    """Test standard resume upload."""
    print("\n🔍 Testing Standard Resume Upload...")
    
    if not Path(TEST_RESUME_PATH).exists():
        print(f"❌ Test resume not found: {TEST_RESUME_PATH}")
        return
    
    with open(TEST_RESUME_PATH, 'rb') as f:
        files = {'file': ('resume.pdf', f, 'application/pdf')}
        data = {'user_id': 'test_user'}
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Standard upload successful:")
        print(f"   Resume ID: {result['resume_id']}")
        print(f"   File size: {result['file_size']} bytes")
        print(f"   Success: {result['success']}")
        print(f"   Processing time: {result['processing_result']['processing_time']:.2f}s")
        return result['resume_id']
    else:
        print(f"❌ Standard upload failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_enhanced_upload_with_options():
    """Test enhanced resume upload with different processing options."""
    print("\n🔍 Testing Enhanced Resume Upload with Options...")
    
    if not Path(TEST_RESUME_PATH).exists():
        print(f"❌ Test resume not found: {TEST_RESUME_PATH}")
        return
    
    # Test configurations
    configs = [
        {
            'name': 'Full Enhanced Processing',
            'options': {
                'enable_ocr': True,
                'enable_hidden_links': True,
                'enable_metadata': True,
                'enable_tables': True,
                'enable_image_ocr': True
            }
        },
        {
            'name': 'OCR Only',
            'options': {
                'enable_ocr': True,
                'enable_hidden_links': False,
                'enable_metadata': False,
                'enable_tables': False,
                'enable_image_ocr': False
            }
        },
        {
            'name': 'Hidden Links Only',
            'options': {
                'enable_ocr': False,
                'enable_hidden_links': True,
                'enable_metadata': True,
                'enable_tables': False,
                'enable_image_ocr': False
            }
        }
    ]
    
    results = []
    
    for config in configs:
        print(f"\n   Testing: {config['name']}")
        
        with open(TEST_RESUME_PATH, 'rb') as f:
            files = {'file': ('resume.pdf', f, 'application/pdf')}
            data = {
                'user_id': 'test_user_enhanced',
                **config['options']
            }
            
            response = requests.post(f"{BASE_URL}/upload/enhanced", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Enhanced upload successful:")
            print(f"      Resume ID: {result['resume_id']}")
            print(f"      Processing time: {result['processing_result']['processing_time']:.2f}s")
            print(f"      Enhanced features: {result['enhanced_features']}")
            
            # Show extraction summary
            summary = result['extraction_summary']
            print(f"      Text length: {summary.get('text_length', 0)} chars")
            print(f"      Links found: {summary.get('hidden_elements', {}).get('links_found', 0)}")
            print(f"      Tables found: {summary.get('hidden_elements', {}).get('tables_found', 0)}")
            print(f"      Social profiles: {len(summary.get('social_profiles', []))}")
            
            results.append(result['resume_id'])
        else:
            print(f"   ❌ Enhanced upload failed: {response.status_code}")
            print(f"      Error: {response.text}")
    
    return results

def test_enhanced_text_processing():
    """Test enhanced text processing."""
    print("\n🔍 Testing Enhanced Text Processing...")
    
    sample_text = """
    John Doe
    Software Engineer
    john.doe@email.com | (555) 123-4567
    linkedin.com/in/johndoe | github.com/johndoe
    
    EXPERIENCE
    Senior Software Engineer | Tech Corp | 2020-2023
    - Developed microservices using Python and FastAPI
    - Led team of 5 developers
    - Implemented CI/CD pipelines
    
    PROJECTS
    AI Interview Agent | github.com/johndoe/ai-interview
    - Built resume parsing system with OCR
    - Used PyMuPDF for advanced PDF extraction
    - Integrated OpenAI API for LLM enhancement
    
    SKILLS
    Python, FastAPI, PyMuPDF, OpenAI API, Docker, Kubernetes
    """
    
    # Test with LLM enhancement disabled
    data = {
        'text': sample_text,
        'user_id': 'test_user_text',
        'enable_llm_enhancement': False
    }
    
    response = requests.post(f"{BASE_URL}/process-text/enhanced", data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Enhanced text processing successful:")
        print(f"   Success: {result['success']}")
        print(f"   Processing time: {result.get('extraction_summary', {}).get('processing_time', 0):.2f}s")
        
        # Show extraction details
        summary = result['extraction_summary']
        print(f"   Contact: {summary.get('contact_info', {}).get('name', 'N/A')}")
        print(f"   Email: {summary.get('contact_info', {}).get('email', 'N/A')}")
        print(f"   Experience: {summary.get('extracted_data', {}).get('experience_count', 0)} entries")
        print(f"   Projects: {summary.get('extracted_data', {}).get('projects_count', 0)} entries")
        print(f"   Skills: {summary.get('extracted_data', {}).get('skills_count', 0)} categories")
        
        return result.get('resume_id')
    else:
        print(f"❌ Enhanced text processing failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_resume_retrieval(resume_ids):
    """Test resume retrieval endpoints."""
    print("\n🔍 Testing Resume Retrieval...")
    
    for resume_id in resume_ids:
        if not resume_id:
            continue
            
        print(f"\n   Testing retrieval for: {resume_id}")
        
        # Test standard retrieval
        response = requests.get(f"{BASE_URL}/resume/{resume_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Standard retrieval successful:")
            print(f"      Name: {data.get('contact', {}).get('name', 'N/A')}")
            print(f"      Confidence: {data.get('parsing_confidence', 0):.2%}")
        else:
            print(f"   ❌ Standard retrieval failed: {response.status_code}")
        
        # Test enhanced retrieval (if it's an enhanced resume)
        if 'enhanced' in resume_id:
            response = requests.get(f"{BASE_URL}/resume/{resume_id}/enhanced")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Enhanced retrieval successful:")
                print(f"      Enhanced metadata: {data.get('enhanced_metadata', {}).get('extraction_method', 'N/A')}")
                print(f"      File size: {data.get('enhanced_metadata', {}).get('file_size', 0)} bytes")
            else:
                print(f"   ❌ Enhanced retrieval failed: {response.status_code}")

def test_resume_listing():
    """Test resume listing with filters."""
    print("\n🔍 Testing Resume Listing...")
    
    # Test standard listing
    response = requests.get(f"{BASE_URL}/resumes?limit=10")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Standard listing successful:")
        print(f"   Total resumes: {data['total']}")
        for resume in data['resumes'][:3]:  # Show first 3
            print(f"   - {resume['resume_id']}: {resume['filename']} ({resume['processing_type']})")
    else:
        print(f"❌ Standard listing failed: {response.status_code}")
    
    # Test enhanced-only listing
    response = requests.get(f"{BASE_URL}/resumes?enhanced_only=true&limit=10")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Enhanced-only listing successful:")
        print(f"   Enhanced resumes: {data['total']}")
        for resume in data['resumes'][:3]:  # Show first 3
            print(f"   - {resume['resume_id']}: {resume['filename']}")
            if 'enhanced_features' in resume:
                print(f"     Features: {list(resume['enhanced_features'].keys())}")
    else:
        print(f"❌ Enhanced-only listing failed: {response.status_code}")

def main():
    """Run all tests."""
    print("🚀 Enhanced Resume Service API Testing")
    print("=" * 50)
    
    try:
        # Test health and status
        test_health_endpoints()
        
        # Test pipeline information
        test_pipeline_info()
        
        # Test standard upload
        standard_resume_id = test_standard_upload()
        
        # Test enhanced uploads
        enhanced_resume_ids = test_enhanced_upload_with_options()
        
        # Test enhanced text processing
        text_resume_id = test_enhanced_text_processing()
        
        # Test resume retrieval
        all_resume_ids = [standard_resume_id] + enhanced_resume_ids + [text_resume_id]
        test_resume_retrieval([rid for rid in all_resume_ids if rid])
        
        # Test resume listing
        test_resume_listing()
        
        print("\n✅ All tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Failed to connect to the API server.")
        print("   Make sure the server is running on http://localhost:8004")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    main() 