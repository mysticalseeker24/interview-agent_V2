#!/usr/bin/env python3
"""
Comprehensive system test for TalentSync Interview Service.
This script will:
1. Upload all datasets to Pinecone
2. Test RAG pipeline functionality
3. Verify service connectivity
4. Test dynamic follow-up question generation
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.pinecone_service import PineconeService
from app.services.dynamic_followup_service import DynamicFollowUpService
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ComprehensiveSystemTester:
    """Comprehensive system tester for TalentSync."""
    
    def __init__(self):
        """Initialize the comprehensive tester."""
        self.settings = get_settings()
        self.pinecone_service = PineconeService()
        self.followup_service = DynamicFollowUpService()
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        
        # Dataset mapping
        self.dataset_mapping = {
            "SWE_dataset.json": "Software Engineering",
            "ML_dataset.json": "Machine Learning", 
            "DSA_dataset.json": "Data Structures & Algorithms",
            "Resume_dataset.json": "Resume Analysis",
            "Resumes_dataset.json": "Resume Analysis"
        }
        
        logger.info("Comprehensive system tester initialized")
    
    async def upload_datasets_to_pinecone(self) -> Dict[str, int]:
        """Upload all datasets to Pinecone."""
        logger.info("=" * 60)
        logger.info("STEP 1: UPLOADING DATASETS TO PINECONE")
        logger.info("=" * 60)
        
        import json
        results = {}
        total_uploaded = 0
        
        # Find all JSON files in data directory
        json_files = list(self.data_dir.glob("*.json"))
        
        if not json_files:
            logger.error(f"No JSON files found in {self.data_dir}")
            return results
        
        logger.info(f"Found {len(json_files)} dataset files")
        
        for file_path in json_files:
            if file_path.name in self.dataset_mapping:
                try:
                    domain = self.dataset_mapping[file_path.name]
                    logger.info(f"Processing dataset: {file_path.name} (Domain: {domain})")
                    
                    # Load dataset
                    with open(file_path, 'r', encoding='utf-8') as f:
                        questions = json.load(f)
                    
                    if not questions:
                        logger.warning(f"No questions found in {file_path.name}")
                        results[file_path.name] = 0
                        continue
                    
                    uploaded_count = 0
                    
                    for i, question in enumerate(questions):
                        try:
                            # Extract question data
                            question_id = question.get('id', f"{file_path.stem}-{i}")
                            question_text = question.get('text', '')
                            question_type = question.get('type', 'conceptual')
                            difficulty = question.get('difficulty', 'medium')
                            
                            # Upload to Pinecone
                            await self.pinecone_service.sync_question_to_pinecone(
                                question_id=question_id,
                                question_text=question_text,
                                domain=domain,
                                question_type=question_type,
                                difficulty=difficulty
                            )
                            
                            uploaded_count += 1
                            
                            # Log progress
                            if (i + 1) % 10 == 0:
                                logger.info(f"Uploaded {i + 1}/{len(questions)} questions from {file_path.name}")
                            
                        except Exception as e:
                            logger.error(f"Error uploading question {question.get('id', 'unknown')}: {e}")
                            continue
                    
                    results[file_path.name] = uploaded_count
                    total_uploaded += uploaded_count
                    logger.info(f"Successfully uploaded {uploaded_count}/{len(questions)} questions from {file_path.name}")
                    
                except Exception as e:
                    logger.error(f"Error uploading {file_path.name}: {e}")
                    results[file_path.name] = 0
        
        logger.info(f"Upload complete! Total questions uploaded: {total_uploaded}")
        return results
    
    async def verify_pinecone_upload(self) -> Dict[str, Any]:
        """Verify the Pinecone upload by checking index stats."""
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: VERIFYING PINECONE UPLOAD")
        logger.info("=" * 60)
        
        try:
            # Get index stats
            index_stats = self.pinecone_service.questions_index.describe_index_stats()
            
            logger.info("Pinecone index statistics:")
            logger.info(f"Total vectors: {index_stats.total_vector_count}")
            logger.info(f"Index dimension: {index_stats.dimension}")
            logger.info(f"Index metric: {index_stats.metric}")
            
            return {
                'status': 'success',
                'total_vectors': index_stats.total_vector_count,
                'dimension': index_stats.dimension,
                'metric': index_stats.metric
            }
            
        except Exception as e:
            logger.error(f"Error verifying upload: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def test_rag_pipeline(self) -> Dict[str, Any]:
        """Test the RAG pipeline with sample queries."""
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: TESTING RAG PIPELINE")
        logger.info("=" * 60)
        
        test_queries = [
            {
                'query': "What is the difference between a process and a thread?",
                'expected_domain': 'Software Engineering'
            },
            {
                'query': "Explain machine learning bias-variance tradeoff",
                'expected_domain': 'Machine Learning'
            },
            {
                'query': "How do you implement a binary search tree?",
                'expected_domain': 'Data Structures & Algorithms'
            },
            {
                'query': "What are the SOLID principles?",
                'expected_domain': 'Software Engineering'
            },
            {
                'query': "How does garbage collection work?",
                'expected_domain': 'Software Engineering'
            }
        ]
        
        results = {}
        
        for test_case in test_queries:
            query = test_case['query']
            expected_domain = test_case['expected_domain']
            
            try:
                logger.info(f"Testing RAG query: {query}")
                
                # Search for similar questions
                similar_questions = await self.pinecone_service.search_similar_questions(
                    query_text=query,
                    top_k=3
                )
                
                if similar_questions:
                    top_match = similar_questions[0]
                    domain_match = top_match.get('domain') == expected_domain
                    
                    results[query] = {
                        'status': 'success',
                        'found_questions': len(similar_questions),
                        'top_match_score': top_match.get('similarity_score'),
                        'top_match_domain': top_match.get('domain'),
                        'domain_match': domain_match,
                        'top_match_text': top_match.get('text')[:100] + "..." if len(top_match.get('text', '')) > 100 else top_match.get('text')
                    }
                    
                    logger.info(f"✅ Found {len(similar_questions)} similar questions")
                    logger.info(f"   Top match: {top_match.get('domain')} (score: {top_match.get('similarity_score'):.3f})")
                    
                else:
                    results[query] = {
                        'status': 'no_results',
                        'found_questions': 0
                    }
                    logger.warning(f"⚠️ No similar questions found for: {query}")
                    
            except Exception as e:
                logger.error(f"❌ RAG test error for '{query}': {str(e)}")
                results[query] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    async def test_dynamic_followup_generation(self) -> Dict[str, Any]:
        """Test dynamic follow-up question generation."""
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: TESTING DYNAMIC FOLLOW-UP GENERATION")
        logger.info("=" * 60)
        
        test_cases = [
            {
                'answer': "A process is an independent program in execution with its own memory space, while a thread is a lightweight unit of execution within a process that shares the process's memory space.",
                'domain': 'Software Engineering',
                'difficulty': 'medium',
                'description': 'Process vs Thread explanation'
            },
            {
                'answer': "The bias-variance tradeoff represents the tension between a model's ability to capture true patterns and its sensitivity to training data variations. High bias means underfitting, high variance means overfitting.",
                'domain': 'Machine Learning',
                'difficulty': 'medium',
                'description': 'Bias-variance tradeoff explanation'
            },
            {
                'answer': "SOLID principles are: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion. They help create maintainable and flexible code.",
                'domain': 'Software Engineering',
                'difficulty': 'hard',
                'description': 'SOLID principles explanation'
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            answer = test_case['answer']
            domain = test_case['domain']
            difficulty = test_case['difficulty']
            description = test_case['description']
            
            try:
                logger.info(f"Testing follow-up generation for: {description}")
                
                # Generate follow-up question
                result = await self.followup_service.generate_followup_question(
                    answer_text=answer,
                    domain=domain,
                    difficulty=difficulty,
                    use_llm=True
                )
                
                results[description] = {
                    'status': 'success',
                    'generated_question': result['follow_up_question'],
                    'method': result['generation_method'],
                    'domain': domain,
                    'difficulty': difficulty,
                    'confidence_score': result.get('confidence_score')
                }
                
                logger.info(f"✅ Generated follow-up: {result['follow_up_question']}")
                logger.info(f"   Method: {result['generation_method']}")
                
            except Exception as e:
                logger.error(f"❌ Follow-up generation error for '{description}': {str(e)}")
                results[description] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    async def test_service_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to other services."""
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: TESTING SERVICE CONNECTIVITY")
        logger.info("=" * 60)
        
        import httpx
        
        # Service configurations with updated ports
        services = {
            'user-service': {
                'url': 'http://localhost:8001',
                'health_endpoint': '/health',
                'description': 'User authentication and profile management'
            },
            'interview-service': {
                'url': 'http://localhost:8006',
                'health_endpoint': '/health',
                'description': 'Core interview orchestration and RAG pipeline'
            },
            'resume-service': {
                'url': 'http://localhost:8004',
                'health_endpoint': '/health',
                'description': 'Resume parsing and skill extraction'
            },
            'transcription-service': {
                'url': 'http://localhost:8005',
                'health_endpoint': '/health',
                'description': 'Speech-to-text and text-to-speech'
            },
            'media-service': {
                'url': 'http://localhost:8002',
                'health_endpoint': '/health',
                'description': 'Media file management and processing'
            },
            'feedback-service': {
                'url': 'http://localhost:8010',
                'health_endpoint': '/health',
                'description': 'Post-interview feedback analysis'
            }
        }
        
        results = {}
        
        for service_name, service_config in services.items():
            try:
                url = f"{service_config['url']}{service_config['health_endpoint']}"
                logger.info(f"Testing {service_name} at {url}")
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ {service_name} is healthy")
                        results[service_name] = {
                            'status': 'healthy',
                            'response_time': response.elapsed.total_seconds(),
                            'status_code': response.status_code
                        }
                    else:
                        logger.warning(f"⚠️ {service_name} returned status {response.status_code}")
                        results[service_name] = {
                            'status': 'unhealthy',
                            'status_code': response.status_code
                        }
                        
            except httpx.ConnectError:
                logger.error(f"❌ {service_name} is not reachable")
                results[service_name] = {
                    'status': 'unreachable'
                }
            except httpx.TimeoutException:
                logger.error(f"⏰ {service_name} request timed out")
                results[service_name] = {
                    'status': 'timeout'
                }
            except Exception as e:
                logger.error(f"❌ {service_name} error: {str(e)}")
                results[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
            
            # Add a small delay between requests
            await asyncio.sleep(0.5)
        
        return results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all comprehensive tests."""
        logger.info("🚀 Starting comprehensive TalentSync system test")
        
        # Step 1: Upload datasets to Pinecone
        upload_results = await self.upload_datasets_to_pinecone()
        
        # Step 2: Verify Pinecone upload
        pinecone_verification = await self.verify_pinecone_upload()
        
        # Step 3: Test RAG pipeline
        rag_results = await self.test_rag_pipeline()
        
        # Step 4: Test dynamic follow-up generation
        followup_results = await self.test_dynamic_followup_generation()
        
        # Step 5: Test service connectivity
        connectivity_results = await self.test_service_connectivity()
        
        # Compile comprehensive results
        comprehensive_results = {
            'dataset_upload': upload_results,
            'pinecone_verification': pinecone_verification,
            'rag_pipeline': rag_results,
            'dynamic_followup': followup_results,
            'service_connectivity': connectivity_results,
            'summary': self._generate_summary(
                upload_results, pinecone_verification, rag_results, 
                followup_results, connectivity_results
            )
        }
        
        # Print summary
        self._print_summary(comprehensive_results)
        
        return comprehensive_results
    
    def _generate_summary(self, upload_results, pinecone_verification, rag_results, 
                         followup_results, connectivity_results):
        """Generate a summary of all test results."""
        # Dataset upload summary
        total_uploaded = sum(upload_results.values())
        
        # Service connectivity summary
        healthy_services = sum(1 for result in connectivity_results.values() 
                             if result.get('status') == 'healthy')
        total_services = len(connectivity_results)
        
        # RAG pipeline summary
        successful_rag_tests = sum(1 for result in rag_results.values() 
                                 if result.get('status') == 'success')
        total_rag_tests = len(rag_results)
        
        # Follow-up generation summary
        successful_followup_tests = sum(1 for result in followup_results.values() 
                                      if result.get('status') == 'success')
        total_followup_tests = len(followup_results)
        
        return {
            'total_questions_uploaded': total_uploaded,
            'pinecone_status': pinecone_verification.get('status', 'unknown'),
            'services_healthy': f"{healthy_services}/{total_services}",
            'rag_success_rate': f"{successful_rag_tests}/{total_rag_tests}",
            'followup_success_rate': f"{successful_followup_tests}/{total_followup_tests}",
            'overall_status': 'healthy' if (
                total_uploaded > 0 and 
                pinecone_verification.get('status') == 'success' and
                successful_rag_tests > 0 and
                successful_followup_tests > 0
            ) else 'issues_detected'
        }
    
    def _print_summary(self, results):
        """Print a formatted summary of test results."""
        summary = results['summary']
        
        logger.info("\n" + "=" * 60)
        logger.info("COMPREHENSIVE SYSTEM TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Questions Uploaded: {summary['total_questions_uploaded']}")
        logger.info(f"Pinecone Status: {summary['pinecone_status']}")
        logger.info(f"Services Health: {summary['services_healthy']} services healthy")
        logger.info(f"RAG Pipeline: {summary['rag_success_rate']} tests successful")
        logger.info(f"Follow-up Generation: {summary['followup_success_rate']} tests successful")
        logger.info(f"Overall Status: {summary['overall_status'].upper()}")
        
        if summary['overall_status'] == 'healthy':
            logger.info("🎉 All systems are operational!")
        else:
            logger.warning("⚠️ Some issues detected. Check individual test results above.")


async def main():
    """Main function to run the comprehensive test."""
    try:
        tester = ComprehensiveSystemTester()
        results = await tester.run_comprehensive_test()
        
        # Return exit code based on overall status
        if results['summary']['overall_status'] == 'healthy':
            logger.info("✅ Comprehensive system test passed successfully!")
            return 0
        else:
            logger.warning("⚠️ Some tests failed. Check the results above.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Comprehensive test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 