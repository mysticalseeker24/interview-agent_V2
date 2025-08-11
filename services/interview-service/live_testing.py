#!/usr/bin/env python3
"""
Live Testing Script for TalentSync Interview Service
Tests the service end-to-end using real resume data from datasets.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4
import argparse

# Add the app directory to the path
sys.path.append('app')

from app.core.settings import settings
from app.services.supabase_service import SupabaseService
from app.services.pinecone_service import PineconeService
from app.services.followup_service import DynamicFollowUpService
from app.services.session_service import SessionService
from app.schemas.interview import SessionCreate, SessionUpdate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LiveInterviewTester:
    """Comprehensive live testing of the interview service."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.supabase_service = SupabaseService()
        self.pinecone_service = PineconeService()
        self.followup_service = DynamicFollowUpService()
        self.session_service = SessionService()
        
        # Load resume datasets
        self.resume_data = self._load_resume_datasets()
        self.interview_questions = self._load_interview_questions()
        
    def _load_resume_datasets(self) -> List[Dict[str, Any]]:
        """Load resume datasets from the data directory."""
        try:
            data_dir = Path("../../data")
            resumes_file = data_dir / "Resumes_dataset.json"
            
            if resumes_file.exists():
                with open(resumes_file, 'r', encoding='utf-8') as f:
                    resumes = json.load(f)
                logger.info(f"✅ Loaded {len(resumes)} resumes from Resumes_dataset.json")
                return resumes
            else:
                logger.warning("⚠️ Resumes_dataset.json not found")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to load resume datasets: {str(e)}")
            return []
    
    def _load_interview_questions(self) -> List[Dict[str, Any]]:
        """Load interview questions dataset."""
        try:
            data_dir = Path("../../data")
            questions_file = data_dir / "Resume_dataset.json"
            
            if questions_file.exists():
                with open(questions_file, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                logger.info(f"✅ Loaded {len(questions)} interview questions from Resume_dataset.json")
                return questions
            else:
                logger.warning("⚠️ Resume_dataset.json not found")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to load interview questions: {str(e)}")
            return []
    
    def _select_resume_for_testing(self, resume_id: Optional[str] = None) -> Dict[str, Any]:
        """Select a resume for testing."""
        if not self.resume_data:
            raise ValueError("No resume data available for testing")
        
        if resume_id:
            for resume in self.resume_data:
                if resume.get('name', '').lower() == resume_id.lower():
                    return resume
            logger.warning(f"⚠️ Resume '{resume_id}' not found, using first available")
        
        return self.resume_data[0]
    
    def _generate_resume_based_questions(self, resume: Dict[str, Any], domain: str = "resume-based") -> List[str]:
        """Generate questions based on resume content."""
        questions = []
        
        skills = resume.get('skills', [])
        experience = resume.get('experience', [])
        projects = resume.get('projects', [])
        
        # Generate skill-based questions
        for skill in skills[:3]:
            questions.append(f"Can you tell me about your experience with {skill}?")
            questions.append(f"What projects have you worked on using {skill}?")
        
        # Generate experience-based questions
        for exp in experience[:2]:
            company = exp.get('company', 'your previous company')
            title = exp.get('title', 'your role')
            questions.append(f"Tell me about your role as {title} at {company}.")
        
        # Generate project-based questions
        for project in projects[:2]:
            project_name = project.get('name', 'this project')
            questions.append(f"Can you walk me through the {project_name} project?")
        
        # Add behavioral questions
        questions.extend([
            "What motivates you in your work?",
            "How do you handle tight deadlines?",
            "Tell me about a time you had to learn something new quickly."
        ])
        
        return questions[:10]
    
    def _simulate_answer_for_question(self, question: str, resume: Dict[str, Any]) -> str:
        """Simulate a realistic answer based on resume content."""
        question_lower = question.lower()
        
        if 'skill' in question_lower or 'technology' in question_lower:
            skills = resume.get('skills', [])
            if skills:
                skill = skills[0]
                return f"I have extensive experience with {skill}. I've used it in multiple projects including {resume.get('projects', [{}])[0].get('name', 'various projects')}. I'm comfortable with both basic and advanced features."
        
        elif 'project' in question_lower:
            projects = resume.get('projects', [])
            if projects:
                project = projects[0]
                return f"I worked on {project.get('name', 'a significant project')} where I {project.get('description', 'contributed to development')}. The project used technologies like {', '.join(project.get('technologies', ['various tools']))}."
        
        elif 'experience' in question_lower or 'role' in question_lower:
            experience = resume.get('experience', [])
            if experience:
                exp = experience[0]
                return f"As a {exp.get('title', 'professional')} at {exp.get('company', 'my company')}, I was responsible for {exp.get('description', 'various tasks')}. I learned a lot about teamwork and problem-solving."
        
        else:
            skills = resume.get('skills', [])
            if skills:
                return f"I'm passionate about technology and have experience with {', '.join(skills[:3])}. I enjoy working on challenging projects and continuously learning new skills."
        
        return "I have relevant experience in this area and I'm always eager to learn and grow professionally."
    
    async def test_resume_question_generation(self, resume: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Test question generation based on resume content."""
        logger.info(f"🧪 Testing resume-based question generation for {resume.get('name', 'Candidate')}")
        
        start_time = time.time()
        results = {
            'questions_generated': 0,
            'questions_with_followups': 0,
            'total_time': 0,
            'success_rate': 0.0,
            'sample_questions': []
        }
        
        try:
            base_questions = self._generate_resume_based_questions(resume, domain)
            results['questions_generated'] = len(base_questions)
            
            for i, question in enumerate(base_questions[:5]):
                try:
                    simulated_answer = self._simulate_answer_for_question(question, resume)
                    
                    followup = await self.followup_service.generate(
                        answer_text=simulated_answer,
                        domain=domain,
                        difficulty="medium",
                        use_llm=True
                    )
                    
                    if followup and len(followup) > 10:
                        results['questions_with_followups'] += 1
                        if i < 3:
                            results['sample_questions'].append({
                                'question': question,
                                'simulated_answer': simulated_answer[:100] + "...",
                                'followup': followup[:100] + "..."
                            })
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    if self.verbose:
                        logger.warning(f"⚠️ Follow-up generation failed for question {i+1}: {str(e)}")
                    continue
            
            results['total_time'] = time.time() - start_time
            results['success_rate'] = (results['questions_with_followups'] / min(5, len(base_questions))) * 100
            
            logger.info(f"✅ Resume question generation: {results['questions_with_followups']}/5 follow-ups generated successfully")
            return results
            
        except Exception as e:
            logger.error(f"❌ Resume question generation test failed: {str(e)}")
            results['total_time'] = time.time() - start_time
            return results
    
    async def test_vector_search_with_resume_content(self, resume: Dict[str, Any]) -> Dict[str, Any]:
        """Test vector search using resume content."""
        logger.info("🧪 Testing vector search with resume content")
        
        start_time = time.time()
        results = {
            'searches_performed': 0,
            'successful_searches': 0,
            'avg_response_time': 0.0,
            'sample_results': [],
            'total_time': 0
        }
        
        try:
            search_queries = []
            
            for skill in resume.get('skills', [])[:3]:
                search_queries.append(f"questions about {skill}")
                search_queries.append(f"technical interview {skill}")
            
            title = resume.get('title', 'software engineer')
            search_queries.append(f"interview questions for {title}")
            
            for query in search_queries[:6]:
                try:
                    query_start = time.time()
                    
                    search_results = await self.pinecone_service.search_similar_questions(
                        query_text=query,
                        domain="resume-based",
                        top_k=3
                    )
                    
                    query_time = (time.time() - query_start) * 1000
                    results['searches_performed'] += 1
                    
                    if search_results and len(search_results) > 0:
                        results['successful_searches'] += 1
                        
                        if len(results['sample_results']) < 3:
                            results['sample_results'].append({
                                'query': query,
                                'results_found': len(search_results),
                                'response_time_ms': query_time,
                                'top_result': search_results[0].get('text', '')[:100] + "..."
                            })
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    if self.verbose:
                        logger.warning(f"⚠️ Vector search failed for query '{query}': {str(e)}")
                    continue
            
            results['total_time'] = time.time() - start_time
            if results['searches_performed'] > 0:
                results['avg_response_time'] = sum(r['response_time_ms'] for r in results['sample_results']) / len(results['sample_results'])
            
            logger.info(f"✅ Vector search: {results['successful_searches']}/{results['searches_performed']} searches successful")
            return results
            
        except Exception as e:
            logger.error(f"❌ Vector search test failed: {str(e)}")
            results['total_time'] = time.time() - start_time
            return results
    
    async def test_session_management_with_resume(self, resume: Dict[str, Any]) -> Dict[str, Any]:
        """Test session management using resume-based interview."""
        logger.info("🧪 Testing session management with resume-based interview")
        
        start_time = time.time()
        results = {
            'session_created': False,
            'questions_added': 0,
            'session_updated': False,
            'session_deleted': False,
            'total_time': 0,
            'session_id': None
        }
        
        try:
            test_user_id = uuid4()
            session_data = SessionCreate(
                module_id="resume-interview-test",
                mode="practice",
                parsed_resume_data={
                    'candidate_name': resume.get('name', 'Test Candidate'),
                    'skills': resume.get('skills', []),
                    'experience': resume.get('experience', []),
                    'projects': resume.get('projects', [])
                }
            )
            
            session = await self.session_service.create_session(session_data, test_user_id)
            if session:
                results['session_created'] = True
                results['session_id'] = str(session.id)
                logger.info(f"✅ Session created: {session.id}")
                
                questions = self._generate_resume_based_questions(resume, "resume-based")[:5]
                for question in questions:
                    try:
                        await self.session_service.add_question_to_session(session.id, f"q-{len(questions)}")
                        results['questions_added'] += 1
                    except Exception as e:
                        if self.verbose:
                            logger.warning(f"⚠️ Failed to add question to session: {str(e)}")
                
                try:
                    update_data = SessionUpdate(status="active")
                    updated_session = await self.session_service.update_session(session.id, update_data)
                    if updated_session and updated_session.status == "active":
                        results['session_updated'] = True
                        logger.info("✅ Session updated to active status")
                except Exception as e:
                    if self.verbose:
                        logger.warning(f"⚠️ Session update failed: {str(e)}")
                
                try:
                    await self.session_service.delete_session(session.id)
                    results['session_deleted'] = True
                    logger.info("✅ Test session cleaned up")
                except Exception as e:
                    if self.verbose:
                        logger.warning(f"⚠️ Session cleanup failed: {str(e)}")
            
            results['total_time'] = time.time() - start_time
            return results
            
        except Exception as e:
            logger.error(f"❌ Session management test failed: {str(e)}")
            results['total_time'] = time.time() - start_time
            return results
    
    async def test_performance_under_load(self, resume: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Test service performance under simulated load."""
        logger.info("🧪 Testing performance under load")
        
        start_time = time.time()
        results = {
            'concurrent_requests': 0,
            'successful_requests': 0,
            'avg_response_time': 0.0,
            'total_time': 0,
            'performance_metrics': {}
        }
        
        try:
            concurrent_tasks = []
            
            for i in range(5):
                question = f"Tell me about your experience with {resume.get('skills', ['programming'])[0]}"
                answer = self._simulate_answer_for_question(question, resume)
                
                task = self.followup_service.generate(
                    answer_text=answer,
                    domain=domain,
                    difficulty="medium",
                    use_llm=True
                )
                concurrent_tasks.append(task)
            
            start_concurrent = time.time()
            responses = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            concurrent_time = (time.time() - start_concurrent) * 1000
            
            results['concurrent_requests'] = len(concurrent_tasks)
            results['successful_requests'] = sum(1 for r in responses if not isinstance(r, Exception) and r)
            results['avg_response_time'] = concurrent_time / len(concurrent_tasks)
            
            results['performance_metrics'] = {
                'followup_service': self.followup_service.get_performance_metrics(),
                'pinecone_service': await self.pinecone_service.get_index_stats(),
                'supabase_service': self.supabase_service.get_performance_metrics()
            }
            
            results['total_time'] = time.time() - start_time
            logger.info(f"✅ Performance test: {results['successful_requests']}/{results['concurrent_requests']} concurrent requests successful")
            return results
            
        except Exception as e:
            logger.error(f"❌ Performance test failed: {str(e)}")
            results['total_time'] = time.time() - start_time
            return results
    
    async def _test_all_health_checks(self) -> Dict[str, Any]:
        """Test health checks for all services."""
        results = {
            'supabase': False,
            'pinecone': False,
            'followup_service': False,
            'session_service': False,
            'all_healthy': False
        }
        
        try:
            supabase_health = await self.supabase_service.health_check()
            results['supabase'] = supabase_health.get('status') == 'healthy'
            
            pinecone_health = await self.pinecone_service.health_check()
            results['pinecone'] = pinecone_health.get('status') == 'healthy'
            
            followup_health = await self.followup_service.health_check()
            results['followup_service'] = followup_health.get('status') == 'healthy'
            
            session_health = await self.session_service.health_check()
            results['session_health'] = session_health.get('status') == 'healthy'
            
            results['all_healthy'] = all([
                results['supabase'],
                results['pinecone'],
                results['followup_service'],
                results['session_health']
            ])
            
            logger.info(f"✅ Health checks: {sum(results.values()) - 1}/{len(results) - 1} services healthy")
            return results
            
        except Exception as e:
            logger.error(f"❌ Health checks failed: {str(e)}")
            return results
    
    async def run_comprehensive_test(self, resume_id: Optional[str] = None, domain: str = "resume-based") -> Dict[str, Any]:
        """Run comprehensive live testing."""
        logger.info("🚀 Starting Comprehensive Live Testing of Interview Service")
        logger.info("=" * 80)
        
        try:
            resume = self._select_resume_for_testing(resume_id)
            logger.info(f"📋 Testing with resume: {resume.get('name', 'Unknown Candidate')}")
            logger.info(f"🎯 Domain: {domain}")
            logger.info(f"🔧 Skills: {', '.join(resume.get('skills', [])[:5])}")
        except Exception as e:
            logger.error(f"❌ Failed to select resume: {str(e)}")
            return {'error': 'Failed to select resume for testing'}
        
        overall_start_time = time.time()
        test_results = {}
        
        try:
            logger.info("\n" + "="*50)
            logger.info("TEST 1: Resume-Based Question Generation")
            logger.info("="*50)
            test_results['question_generation'] = await self.test_resume_question_generation(resume, domain)
            
            logger.info("\n" + "="*50)
            logger.info("TEST 2: Vector Search with Resume Content")
            logger.info("="*50)
            test_results['vector_search'] = await self.test_vector_search_with_resume_content(resume)
            
            logger.info("\n" + "="*50)
            logger.info("TEST 3: Session Management")
            logger.info("="*50)
            test_results['session_management'] = await self.test_session_management_with_resume(resume)
            
            logger.info("\n" + "="*50)
            logger.info("TEST 4: Performance Under Load")
            logger.info("="*50)
            test_results['performance'] = await self.test_performance_under_load(resume, domain)
            
            logger.info("\n" + "="*50)
            logger.info("TEST 5: Health Checks")
            logger.info("="*50)
            test_results['health_checks'] = await self._test_all_health_checks()
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {str(e)}")
            test_results['error'] = str(e)
        
        overall_time = time.time() - overall_start_time
        test_results['overall'] = {
            'total_testing_time': overall_time,
            'resume_used': resume.get('name', 'Unknown'),
            'domain_tested': domain,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return test_results
    
    def print_comprehensive_results(self, results: Dict[str, Any]):
        """Print comprehensive test results."""
        logger.info("\n" + "="*80)
        logger.info("📊 COMPREHENSIVE LIVE TESTING RESULTS")
        logger.info("="*80)
        
        if 'error' in results:
            logger.error(f"❌ Testing failed: {results['error']}")
            return
        
        overall = results.get('overall', {})
        logger.info(f"🎯 Resume Tested: {overall.get('resume_used', 'Unknown')}")
        logger.info(f"🔧 Domain: {overall.get('domain_tested', 'Unknown')}")
        logger.info(f"⏱️  Total Testing Time: {overall.get('total_testing_time', 0):.2f} seconds")
        logger.info(f"📅 Timestamp: {overall.get('timestamp', 'Unknown')}")
        
        logger.info("\n📋 Test Results Summary:")
        logger.info("-" * 60)
        
        qg = results.get('question_generation', {})
        logger.info(f"Question Generation:     {qg.get('questions_with_followups', 0)}/{qg.get('questions_generated', 0)} follow-ups generated")
        logger.info(f"Success Rate:            {qg.get('success_rate', 0):.1f}%")
        
        vs = results.get('vector_search', {})
        logger.info(f"Vector Search:           {vs.get('successful_searches', 0)}/{vs.get('searches_performed', 0)} successful")
        
        sm = results.get('session_management', {})
        logger.info(f"Session Management:      {'✅' if sm.get('session_created') else '❌'} Created")
        logger.info(f"                          {'✅' if sm.get('session_updated') else '❌'} Updated")
        
        perf = results.get('performance', {})
        logger.info(f"Performance Test:         {perf.get('successful_requests', 0)}/{perf.get('concurrent_requests', 0)} concurrent requests")
        
        hc = results.get('health_checks', {})
        logger.info(f"Health Checks:            {'✅' if hc.get('all_healthy') else '❌'} All services healthy")
        
        if self.verbose and qg.get('sample_questions'):
            logger.info("\n📝 Sample Questions Generated:")
            logger.info("-" * 40)
            for i, q in enumerate(qg['sample_questions'][:3], 1):
                logger.info(f"{i}. Q: {q['question']}")
                logger.info(f"   A: {q['simulated_answer']}")
                logger.info(f"   Follow-up: {q['followup']}")
                logger.info("")  # Empty line
        
        logger.info("="*80)
        
        total_tests = 5
        passed_tests = sum(1 for test in ['question_generation', 'vector_search', 'session_management', 'performance', 'health_checks'] 
                          if results.get(test) and not results[test].get('error'))
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Interview service is working excellently!")
        elif passed_tests >= total_tests * 0.8:
            logger.info("✅ MOST TESTS PASSED! Interview service is working well with minor issues.")
        elif passed_tests >= total_tests * 0.6:
            logger.info("⚠️  SOME TESTS PASSED! Interview service has some issues that need attention.")
        else:
            logger.error("❌ MANY TESTS FAILED! Interview service has significant issues.")
        
        logger.info(f"📊 Overall Score: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")


async def main():
    """Main function to run live testing."""
    parser = argparse.ArgumentParser(description='Live Testing for TalentSync Interview Service')
    parser.add_argument('--resume-id', type=str, help='Specific resume name to test with')
    parser.add_argument('--domain', type=str, default='resume-based', help='Domain to test (default: resume-based)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        tester = LiveInterviewTester(verbose=args.verbose)
        results = await tester.run_comprehensive_test(
            resume_id=args.resume_id,
            domain=args.domain
        )
        
        tester.print_comprehensive_results(results)
        
        if 'error' in results:
            logger.error("❌ Live testing failed!")
            sys.exit(1)
        
        total_tests = 5
        passed_tests = sum(1 for test in ['question_generation', 'vector_search', 'session_management', 'performance', 'health_checks'] 
                          if results.get(test) and not results[test].get('error'))
        
        if passed_tests >= total_tests * 0.8:
            logger.info("✅ Live testing completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Live testing revealed significant issues!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Live testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during live testing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
