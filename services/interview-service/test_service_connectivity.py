#!/usr/bin/env python3
"""
Script to test service connectivity and dynamic follow-up question functionality.
This script will check all services are reachable and test the RAG pipeline.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Any
import httpx
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.pinecone_service import PineconeService
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ServiceConnectivityTester:
    """Tests connectivity between all services."""
    
    def __init__(self):
        """Initialize the tester with service configurations."""
        self.settings = get_settings()
        
        # Service configurations with updated ports
        self.services = {
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
        
        self.pinecone_service = PineconeService()
        logger.info("Service connectivity tester initialized")
    
    async def test_service_health(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test health endpoint of a specific service."""
        try:
            url = f"{service_config['url']}{service_config['health_endpoint']}"
            logger.info(f"Testing {service_name} at {url}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} is healthy")
                    return {
                        'status': 'healthy',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code,
                        'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    }
                else:
                    logger.warning(f"⚠️ {service_name} returned status {response.status_code}")
                    return {
                        'status': 'unhealthy',
                        'status_code': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    }
                    
        except httpx.ConnectError:
            logger.error(f"❌ {service_name} is not reachable")
            return {
                'status': 'unreachable',
                'error': 'Connection failed'
            }
        except httpx.TimeoutException:
            logger.error(f"⏰ {service_name} request timed out")
            return {
                'status': 'timeout',
                'error': 'Request timeout'
            }
        except Exception as e:
            logger.error(f"❌ {service_name} error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def test_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Test health of all services."""
        logger.info("=" * 60)
        logger.info("TESTING SERVICE CONNECTIVITY")
        logger.info("=" * 60)
        
        results = {}
        
        for service_name, service_config in self.services.items():
            result = await self.test_service_health(service_name, service_config)
            results[service_name] = result
            
            # Add a small delay between requests
            await asyncio.sleep(0.5)
        
        return results
    
    async def test_pinecone_connectivity(self) -> Dict[str, Any]:
        """Test Pinecone connectivity and index status."""
        logger.info("\n" + "=" * 60)
        logger.info("TESTING PINECONE CONNECTIVITY")
        logger.info("=" * 60)
        
        try:
            # Test health check
            health_result = await self.pinecone_service.health_check()
            logger.info("✅ Pinecone service is healthy")
            
            # Get index stats
            index_stats = self.pinecone_service.questions_index.describe_index_stats()
            logger.info(f"📊 Pinecone index stats: {index_stats.total_vector_count} vectors")
            
            return {
                'status': 'healthy',
                'health_check': health_result,
                'index_stats': {
                    'total_vectors': index_stats.total_vector_count,
                    'dimension': index_stats.dimension,
                    'metric': index_stats.metric
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Pinecone error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def test_rag_pipeline(self) -> Dict[str, Any]:
        """Test the RAG pipeline with sample queries."""
        logger.info("\n" + "=" * 60)
        logger.info("TESTING RAG PIPELINE")
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
        logger.info("TESTING DYNAMIC FOLLOW-UP GENERATION")
        logger.info("=" * 60)
        
        test_cases = [
            {
                'answer': "A process is an independent program in execution with its own memory space, while a thread is a lightweight unit of execution within a process that shares the process's memory space.",
                'expected_topic': 'threading',
                'description': 'Process vs Thread explanation'
            },
            {
                'answer': "The bias-variance tradeoff represents the tension between a model's ability to capture true patterns and its sensitivity to training data variations. High bias means underfitting, high variance means overfitting.",
                'expected_topic': 'machine learning',
                'description': 'Bias-variance tradeoff explanation'
            },
            {
                'answer': "SOLID principles are: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion. They help create maintainable and flexible code.",
                'expected_topic': 'software design',
                'description': 'SOLID principles explanation'
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            answer = test_case['answer']
            description = test_case['description']
            
            try:
                logger.info(f"Testing follow-up generation for: {description}")
                
                # Search for follow-up questions based on answer
                follow_up_questions = await self.pinecone_service.get_follow_up_questions(
                    answer_text=answer,
                    session_context={'domain': 'general', 'difficulty': 'medium'},
                    exclude_ids=[]
                )
                
                if follow_up_questions:
                    results[description] = {
                        'status': 'success',
                        'found_followups': len(follow_up_questions),
                        'followup_questions': [
                            {
                                'text': q.get('text', '')[:100] + "..." if len(q.get('text', '')) > 100 else q.get('text', ''),
                                'domain': q.get('domain'),
                                'type': q.get('type'),
                                'score': q.get('similarity_score')
                            }
                            for q in follow_up_questions[:3]  # Show top 3
                        ]
                    }
                    
                    logger.info(f"✅ Generated {len(follow_up_questions)} follow-up questions")
                    for i, q in enumerate(follow_up_questions[:2]):
                        logger.info(f"   {i+1}. {q.get('text', '')[:80]}...")
                        
                else:
                    results[description] = {
                        'status': 'no_followups',
                        'found_followups': 0
                    }
                    logger.warning(f"⚠️ No follow-up questions generated for: {description}")
                    
            except Exception as e:
                logger.error(f"❌ Follow-up generation error for '{description}': {str(e)}")
                results[description] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and provide comprehensive results."""
        logger.info("🚀 Starting comprehensive service connectivity and functionality test")
        
        # Test service connectivity
        service_results = await self.test_all_services()
        
        # Test Pinecone connectivity
        pinecone_results = await self.test_pinecone_connectivity()
        
        # Test RAG pipeline
        rag_results = await self.test_rag_pipeline()
        
        # Test dynamic follow-up generation
        followup_results = await self.test_dynamic_followup_generation()
        
        # Compile comprehensive results
        comprehensive_results = {
            'service_connectivity': service_results,
            'pinecone_connectivity': pinecone_results,
            'rag_pipeline': rag_results,
            'dynamic_followup': followup_results,
            'summary': self._generate_summary(service_results, pinecone_results, rag_results, followup_results)
        }
        
        # Print summary
        self._print_summary(comprehensive_results)
        
        return comprehensive_results
    
    def _generate_summary(self, service_results, pinecone_results, rag_results, followup_results):
        """Generate a summary of all test results."""
        # Service connectivity summary
        healthy_services = sum(1 for result in service_results.values() if result.get('status') == 'healthy')
        total_services = len(service_results)
        
        # RAG pipeline summary
        successful_rag_tests = sum(1 for result in rag_results.values() if result.get('status') == 'success')
        total_rag_tests = len(rag_results)
        
        # Follow-up generation summary
        successful_followup_tests = sum(1 for result in followup_results.values() if result.get('status') == 'success')
        total_followup_tests = len(followup_results)
        
        return {
            'services_healthy': f"{healthy_services}/{total_services}",
            'pinecone_status': pinecone_results.get('status', 'unknown'),
            'rag_success_rate': f"{successful_rag_tests}/{total_rag_tests}",
            'followup_success_rate': f"{successful_followup_tests}/{total_followup_tests}",
            'overall_status': 'healthy' if (healthy_services == total_services and 
                                          pinecone_results.get('status') == 'healthy' and
                                          successful_rag_tests > 0) else 'issues_detected'
        }
    
    def _print_summary(self, results):
        """Print a formatted summary of test results."""
        summary = results['summary']
        
        logger.info("\n" + "=" * 60)
        logger.info("COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Services Health: {summary['services_healthy']} services healthy")
        logger.info(f"Pinecone Status: {summary['pinecone_status']}")
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
        tester = ServiceConnectivityTester()
        results = await tester.run_comprehensive_test()
        
        # Return exit code based on overall status
        if results['summary']['overall_status'] == 'healthy':
            logger.info("✅ All tests passed successfully!")
            return 0
        else:
            logger.warning("⚠️ Some tests failed. Check the results above.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 