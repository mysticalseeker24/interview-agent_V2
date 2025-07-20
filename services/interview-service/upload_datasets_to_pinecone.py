#!/usr/bin/env python3
"""
TalentSync Dataset Upload Script for Pinecone Vector Database

This script uploads all datasets from the data directory to Pinecone with:
- Proper domain mapping based on dataset_mapping.py
- Performance optimizations with batching and caching
- Comprehensive error handling and logging
- Progress tracking and verification
- RAG pipeline testing

Usage:
    python upload_datasets_to_pinecone.py [--verify-only] [--test-rag] [--dataset <name>]
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import argparse
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables from .env file
load_dotenv()

from app.services.pinecone_service import PineconeService
from app.core.settings import settings
from app.core.dataset_mapping import (
    DATASET_DOMAIN_MAPPING, 
    DOMAIN_DESCRIPTIONS, 
    get_domain_for_dataset,
    get_datasets_for_domain,
    is_valid_domain
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dataset_upload.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class UploadStats:
    """Statistics for dataset upload."""
    total_files: int = 0
    total_questions: int = 0
    uploaded_questions: int = 0
    failed_questions: int = 0
    skipped_questions: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_questions == 0:
            return 0.0
        return (self.uploaded_questions / self.total_questions) * 100
    
    @property
    def duration_seconds(self) -> float:
        """Calculate total duration in seconds."""
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()


class DatasetUploader:
    """High-performance dataset uploader for TalentSync."""
    
    def __init__(self):
        """Initialize the uploader with performance optimizations."""
        self.settings = settings
        self.pinecone_service = PineconeService()
        
        # Data directory path
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        
        # Upload statistics
        self.stats = UploadStats()
        
        # Cache for processed questions to avoid duplicates
        self._processed_cache = set()
        
        # Batch processing configuration
        self.batch_size = 50  # Process questions in batches for better performance
        
        logger.info("Dataset uploader initialized with performance optimizations")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Supported domains: {list(DOMAIN_DESCRIPTIONS.keys())}")
    
    def load_dataset(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load a dataset from JSON file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.error(f"Invalid dataset format in {file_path.name}: expected list, got {type(data)}")
                return []
            
            logger.info(f"Loaded {len(data)} questions from {file_path.name}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path.name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading {file_path.name}: {e}")
            return []
    
    def process_question(self, question: Dict[str, Any], domain: str, dataset_name: str) -> Optional[Dict[str, Any]]:
        """Process a single question for Pinecone upload with validation."""
        try:
            # Extract and validate question data
            question_id = question.get('id')
            if not question_id:
                logger.warning(f"Question missing ID in {dataset_name}")
                return None
            
            question_text = question.get('text', '').strip()
            if not question_text:
                logger.warning(f"Question {question_id} missing text in {dataset_name}")
                return None
            
            # Get question type and difficulty with defaults
            question_type = question.get('type', 'conceptual')
            difficulty = question.get('difficulty', 'medium')
            
            # Validate difficulty
            if difficulty not in ['easy', 'medium', 'hard']:
                logger.warning(f"Invalid difficulty '{difficulty}' for question {question_id}, defaulting to 'medium'")
                difficulty = 'medium'
            
            # Validate question type
            valid_types = ['conceptual', 'behavioral', 'technical', 'coding', 'follow-up']
            if question_type not in valid_types:
                logger.warning(f"Invalid question type '{question_type}' for question {question_id}, defaulting to 'conceptual'")
                question_type = 'conceptual'
            
            # Extract additional data
            follow_up_templates = question.get('follow_up_templates', [])
            ideal_answer = question.get('ideal_answer_summary', '')
            tags = question.get('tags', [])
            
            # Create comprehensive metadata
            metadata = {
                'question_id': str(question_id),
                'domain': domain,
                'type': question_type,
                'difficulty': difficulty,
                'text': question_text,
                'dataset_source': dataset_name,
                'has_follow_ups': len(follow_up_templates) > 0,
                'follow_up_count': len(follow_up_templates),
                'has_ideal_answer': bool(ideal_answer),
                'tags': tags,
                'upload_timestamp': datetime.now().isoformat()
            }
            
            # Create cache key to avoid duplicates
            cache_key = f"{question_id}_{domain}_{question_type}"
            if cache_key in self._processed_cache:
                logger.debug(f"Skipping duplicate question: {question_id}")
                self.stats.skipped_questions += 1
                return None
            
            self._processed_cache.add(cache_key)
            
            return {
                'id': str(question_id),
                'text': question_text,
                'metadata': metadata,
                'follow_up_templates': follow_up_templates,
                'ideal_answer': ideal_answer,
                'domain': domain,
                'type': question_type,
                'difficulty': difficulty
            }
            
        except Exception as e:
            logger.error(f"Error processing question {question.get('id', 'unknown')} in {dataset_name}: {e}")
            return None
    
    async def upload_question_batch(self, questions: List[Dict[str, Any]]) -> int:
        """Upload a batch of questions to Pinecone efficiently."""
        if not questions:
            return 0
        
        try:
            # Prepare questions for batch upload with embeddings
            prepared_questions = []
            for question in questions:
                try:
                    # Generate embedding for the question text
                    embedding = await self.pinecone_service.get_embedding(question['text'])
                    
                    prepared_questions.append({
                        'id': question['id'],
                        'text': question['text'],
                        'domain': question['domain'],
                        'type': question['type'],
                        'difficulty': question['difficulty'],
                        'embedding': embedding
                    })
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to generate embedding for question {question['id']}: {e}")
                    continue
            
            if not prepared_questions:
                logger.error("No questions with valid embeddings to upload")
                return 0
            
            # Upload batch to Pinecone
            success = await self.pinecone_service.upsert_questions(prepared_questions)
            
            if success:
                return len(prepared_questions)
            else:
                logger.error(f"Failed to upload batch of {len(prepared_questions)} questions")
                return 0
                
        except Exception as e:
            logger.error(f"Error uploading question batch: {e}")
            return 0
    
    async def upload_dataset(self, file_path: Path) -> int:
        """Upload a single dataset to Pinecone with progress tracking."""
        dataset_name = file_path.name
        domain = get_domain_for_dataset(dataset_name)
        
        logger.info(f"Processing dataset: {dataset_name} (Domain: {domain})")
        
        # Load dataset
        questions = self.load_dataset(file_path)
        if not questions:
            logger.warning(f"No questions found in {dataset_name}")
            return 0
        
        self.stats.total_questions += len(questions)
        
        # Process questions
        processed_questions = []
        for question in questions:
            processed = self.process_question(question, domain, dataset_name)
            if processed:
                processed_questions.append(processed)
        
        logger.info(f"Processed {len(processed_questions)} valid questions from {dataset_name}")
        
        # Upload in batches
        uploaded_count = 0
        for i in range(0, len(processed_questions), self.batch_size):
            batch = processed_questions[i:i + self.batch_size]
            batch_uploaded = await self.upload_question_batch(batch)
            uploaded_count += batch_uploaded
            
            # Log progress
            progress = min(i + self.batch_size, len(processed_questions))
            logger.info(f"Uploaded {progress}/{len(processed_questions)} questions from {dataset_name}")
        
        self.stats.uploaded_questions += uploaded_count
        self.stats.failed_questions += (len(processed_questions) - uploaded_count)
        
        logger.info(f"Successfully uploaded {uploaded_count}/{len(processed_questions)} questions from {dataset_name}")
        return uploaded_count
    
    async def upload_all_datasets(self, specific_dataset: Optional[str] = None) -> Dict[str, int]:
        """Upload all datasets or a specific dataset to Pinecone."""
        logger.info("=" * 80)
        logger.info("STARTING DATASET UPLOAD TO PINECONE")
        logger.info("=" * 80)
        
        self.stats.start_time = datetime.now()
        
        results = {}
        
        # Find JSON files in data directory
        json_files = list(self.data_dir.glob("*.json"))
        
        if not json_files:
            logger.error(f"No JSON files found in {self.data_dir}")
            return results
        
        # Filter files if specific dataset requested
        if specific_dataset:
            json_files = [f for f in json_files if f.name == specific_dataset]
            if not json_files:
                logger.error(f"Dataset {specific_dataset} not found in {self.data_dir}")
                return results
        
        # Filter to only supported datasets
        supported_files = [f for f in json_files if f.name in DATASET_DOMAIN_MAPPING]
        unsupported_files = [f for f in json_files if f.name not in DATASET_DOMAIN_MAPPING]
        
        if unsupported_files:
            logger.warning(f"Unsupported datasets found: {[f.name for f in unsupported_files]}")
        
        self.stats.total_files = len(supported_files)
        logger.info(f"Found {len(supported_files)} supported dataset files")
        
        # Upload each dataset
        for file_path in supported_files:
            try:
                uploaded = await self.upload_dataset(file_path)
                results[file_path.name] = uploaded
                
            except Exception as e:
                logger.error(f"Error uploading {file_path.name}: {e}")
                results[file_path.name] = 0
                self.stats.failed_questions += len(self.load_dataset(file_path))
        
        self.stats.end_time = datetime.now()
        
        # Log final statistics
        self._log_upload_summary()
        
        return results
    
    def _log_upload_summary(self):
        """Log comprehensive upload summary."""
        logger.info("=" * 80)
        logger.info("DATASET UPLOAD SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total files processed: {self.stats.total_files}")
        logger.info(f"Total questions found: {self.stats.total_questions}")
        logger.info(f"Questions uploaded: {self.stats.uploaded_questions}")
        logger.info(f"Questions failed: {self.stats.failed_questions}")
        logger.info(f"Questions skipped: {self.stats.skipped_questions}")
        logger.info(f"Success rate: {self.stats.success_rate:.2f}%")
        logger.info(f"Total duration: {self.stats.duration_seconds:.2f} seconds")
        
        if self.stats.total_questions > 0:
            questions_per_second = self.stats.uploaded_questions / self.stats.duration_seconds
            logger.info(f"Upload rate: {questions_per_second:.2f} questions/second")
    
    async def verify_upload(self) -> Dict[str, Any]:
        """Verify the upload by checking Pinecone index stats."""
        logger.info("=" * 60)
        logger.info("VERIFYING UPLOAD")
        logger.info("=" * 60)
        
        try:
            # Get index stats
            index_stats = await self.pinecone_service.get_index_stats()
            
            logger.info("Pinecone index statistics:")
            logger.info(f"Total vectors: {index_stats.get('total_vector_count', 'N/A')}")
            logger.info(f"Index dimension: {index_stats.get('dimension', 'N/A')}")
            logger.info(f"Index metric: {index_stats.get('metric', 'N/A')}")
            
            # Check health
            health_status = await self.pinecone_service.health_check()
            logger.info(f"Pinecone health: {health_status.get('status', 'N/A')}")
            
            return {
                'index_stats': index_stats,
                'health_status': health_status,
                'upload_stats': {
                    'total_uploaded': self.stats.uploaded_questions,
                    'success_rate': self.stats.success_rate,
                    'duration_seconds': self.stats.duration_seconds
                }
            }
            
        except Exception as e:
            logger.error(f"Error verifying upload: {e}")
            return {}
    
    async def test_rag_pipeline(self) -> Dict[str, Any]:
        """Test the RAG pipeline with sample queries for each domain."""
        logger.info("=" * 60)
        logger.info("TESTING RAG PIPELINE")
        logger.info("=" * 60)
        
        # Test queries for each domain
        test_queries = {
            "dsa": [
                "What is the difference between an array and a linked list?",
                "How does dynamic programming work?",
                "Explain binary search tree properties"
            ],
            "devops": [
                "What is CI/CD and why is it important?",
                "How does Docker containerization work?",
                "Explain Kubernetes architecture"
            ],
            "machine-learning": [
                "What is the bias-variance tradeoff?",
                "How do neural networks learn?",
                "Explain cross-validation"
            ],
            "software-engineering": [
                "What are the SOLID principles?",
                "How do you design a scalable system?",
                "Explain microservices architecture"
            ],
            "ai-engineering": [
                "How do you deploy ML models in production?",
                "What is MLOps?",
                "How do you monitor AI systems?"
            ]
        }
        
        results = {}
        
        for domain, queries in test_queries.items():
            logger.info(f"Testing RAG for domain: {domain}")
            domain_results = []
            
            for query in queries:
                try:
                    # Search for similar questions
                    similar_questions = await self.pinecone_service.search_similar_questions(
                        query_text=query,
                        domain=domain,
                        top_k=3
                    )
                    
                    domain_results.append({
                        'query': query,
                        'results_count': len(similar_questions),
                        'top_result': similar_questions[0] if similar_questions else None,
                        'avg_similarity': sum(q.get('similarity_score', 0) for q in similar_questions) / len(similar_questions) if similar_questions else 0
                    })
                    
                    logger.info(f"  Query: '{query}' -> Found {len(similar_questions)} results")
                    
                except Exception as e:
                    logger.error(f"Error testing query '{query}' for domain {domain}: {e}")
                    domain_results.append({
                        'query': query,
                        'error': str(e)
                    })
            
            results[domain] = domain_results
        
        # Calculate overall success rate
        total_queries = sum(len(queries) for queries in test_queries.values())
        successful_queries = sum(
            len([r for r in domain_results if 'error' not in r])
            for domain_results in results.values()
        )
        
        success_rate = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
        logger.info(f"RAG pipeline test success rate: {success_rate:.2f}%")
        
        return {
            'domain_results': results,
            'overall_success_rate': success_rate,
            'total_queries': total_queries,
            'successful_queries': successful_queries
        }


async def main():
    """Main function to run the dataset upload."""
    parser = argparse.ArgumentParser(description="Upload datasets to Pinecone for TalentSync")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing upload")
    parser.add_argument("--test-rag", action="store_true", help="Test RAG pipeline after upload")
    parser.add_argument("--dataset", type=str, help="Upload specific dataset only")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for uploads")
    
    args = parser.parse_args()
    
    try:
        uploader = DatasetUploader()
        uploader.batch_size = args.batch_size
        
        if args.verify_only:
            # Only verify existing upload
            await uploader.verify_upload()
            return
        
        # Upload datasets
        results = await uploader.upload_all_datasets(specific_dataset=args.dataset)
        
        # Verify upload
        await uploader.verify_upload()
        
        # Test RAG pipeline if requested
        if args.test_rag:
            await uploader.test_rag_pipeline()
        
        logger.info("Dataset upload process completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Upload process interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error during upload: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 