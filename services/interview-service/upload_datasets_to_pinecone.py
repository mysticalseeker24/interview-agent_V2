#!/usr/bin/env python3
"""
Script to upload all datasets from the data directory to Pinecone.
This script will process all JSON datasets and create embeddings for questions.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

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


class DatasetUploader:
    """Handles uploading datasets to Pinecone."""
    
    def __init__(self):
        """Initialize the uploader with Pinecone service."""
        self.settings = get_settings()
        self.pinecone_service = PineconeService()
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        
        # Dataset mapping
        self.dataset_mapping = {
            "SWE_dataset.json": "Software Engineering",
            "ML_dataset.json": "Machine Learning", 
            "DSA_dataset.json": "Data Structures & Algorithms",
            "Resume_dataset.json": "Resume Analysis",
            "Resumes_dataset.json": "Resume Analysis"
        }
        
        logger.info("Dataset uploader initialized")
    
    def load_dataset(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load a dataset from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} items from {file_path.name}")
            return data
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []
    
    def process_question(self, question: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Process a single question for Pinecone upload."""
        try:
            # Extract question data
            question_id = question.get('id', 'unknown')
            question_text = question.get('text', '')
            question_type = question.get('type', 'conceptual')
            difficulty = question.get('difficulty', 'medium')
            follow_up_templates = question.get('follow_up_templates', [])
            ideal_answer = question.get('ideal_answer_summary', '')
            
            # Create metadata
            metadata = {
                'question_id': question_id,
                'domain': domain,
                'type': question_type,
                'difficulty': difficulty,
                'text': question_text,
                'has_follow_ups': len(follow_up_templates) > 0,
                'follow_up_count': len(follow_up_templates),
                'has_ideal_answer': bool(ideal_answer)
            }
            
            return {
                'id': question_id,
                'text': question_text,
                'metadata': metadata,
                'follow_up_templates': follow_up_templates,
                'ideal_answer': ideal_answer
            }
            
        except Exception as e:
            logger.error(f"Error processing question {question.get('id', 'unknown')}: {e}")
            return None
    
    async def upload_dataset(self, file_path: Path) -> int:
        """Upload a single dataset to Pinecone."""
        domain = self.dataset_mapping.get(file_path.name, "General")
        logger.info(f"Processing dataset: {file_path.name} (Domain: {domain})")
        
        # Load dataset
        questions = self.load_dataset(file_path)
        if not questions:
            logger.warning(f"No questions found in {file_path.name}")
            return 0
        
        uploaded_count = 0
        
        for i, question in enumerate(questions):
            try:
                # Process question
                processed_question = self.process_question(question, domain)
                if not processed_question:
                    continue
                
                # Upload to Pinecone
                await self.pinecone_service.sync_question_to_pinecone(
                    question_id=processed_question['id'],
                    question_text=processed_question['text'],
                    domain=domain,
                    question_type=processed_question['metadata']['type'],
                    difficulty=processed_question['metadata']['difficulty']
                )
                
                uploaded_count += 1
                
                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"Uploaded {i + 1}/{len(questions)} questions from {file_path.name}")
                
            except Exception as e:
                logger.error(f"Error uploading question {question.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully uploaded {uploaded_count}/{len(questions)} questions from {file_path.name}")
        return uploaded_count
    
    async def upload_all_datasets(self) -> Dict[str, int]:
        """Upload all datasets to Pinecone."""
        logger.info("Starting upload of all datasets to Pinecone")
        
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
                    uploaded = await self.upload_dataset(file_path)
                    results[file_path.name] = uploaded
                    total_uploaded += uploaded
                except Exception as e:
                    logger.error(f"Error uploading {file_path.name}: {e}")
                    results[file_path.name] = 0
        
        logger.info(f"Upload complete! Total questions uploaded: {total_uploaded}")
        return results
    
    async def verify_upload(self) -> Dict[str, Any]:
        """Verify the upload by checking Pinecone index stats."""
        try:
            # Get index stats
            index_stats = self.pinecone_service.questions_index.describe_index_stats()
            
            logger.info("Pinecone index statistics:")
            logger.info(f"Total vectors: {index_stats.total_vector_count}")
            logger.info(f"Index dimension: {index_stats.dimension}")
            logger.info(f"Index metric: {index_stats.metric}")
            
            return {
                'total_vectors': index_stats.total_vector_count,
                'dimension': index_stats.dimension,
                'metric': index_stats.metric
            }
            
        except Exception as e:
            logger.error(f"Error verifying upload: {e}")
            return {}
    
    async def test_rag_pipeline(self) -> Dict[str, Any]:
        """Test the RAG pipeline with sample queries."""
        test_queries = [
            "What is the difference between a process and a thread?",
            "Explain machine learning bias-variance tradeoff",
            "How do you implement a binary search tree?",
            "What are the SOLID principles?",
            "How does garbage collection work?"
        ]
        
        results = {}
        
        for query in test_queries:
            try:
                logger.info(f"Testing RAG pipeline with query: {query}")
                
                # Search for similar questions
                similar_questions = await self.pinecone_service.search_similar_questions(
                    query_text=query,
                    top_k=3
                )
                
                results[query] = {
                    'found_questions': len(similar_questions),
                    'top_match': similar_questions[0] if similar_questions else None,
                    'all_matches': similar_questions
                }
                
                logger.info(f"Found {len(similar_questions)} similar questions for '{query}'")
                
            except Exception as e:
                logger.error(f"Error testing query '{query}': {e}")
                results[query] = {'error': str(e)}
        
        return results


async def main():
    """Main function to run the dataset upload and verification."""
    try:
        uploader = DatasetUploader()
        
        # Upload all datasets
        logger.info("=" * 50)
        logger.info("STEP 1: Uploading datasets to Pinecone")
        logger.info("=" * 50)
        
        upload_results = await uploader.upload_all_datasets()
        
        # Print upload summary
        logger.info("\n" + "=" * 50)
        logger.info("UPLOAD SUMMARY")
        logger.info("=" * 50)
        for dataset, count in upload_results.items():
            logger.info(f"{dataset}: {count} questions uploaded")
        
        # Verify upload
        logger.info("\n" + "=" * 50)
        logger.info("STEP 2: Verifying upload")
        logger.info("=" * 50)
        
        verification = await uploader.verify_upload()
        
        # Test RAG pipeline
        logger.info("\n" + "=" * 50)
        logger.info("STEP 3: Testing RAG pipeline")
        logger.info("=" * 50)
        
        rag_test_results = await uploader.test_rag_pipeline()
        
        # Final summary
        logger.info("\n" + "=" * 50)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total questions uploaded: {sum(upload_results.values())}")
        logger.info(f"Pinecone index vectors: {verification.get('total_vectors', 'Unknown')}")
        logger.info(f"RAG pipeline tests: {len(rag_test_results)} queries tested")
        
        # Check for any errors in RAG tests
        rag_errors = sum(1 for result in rag_test_results.values() if 'error' in result)
        if rag_errors > 0:
            logger.warning(f"RAG pipeline had {rag_errors} errors")
        else:
            logger.info("RAG pipeline tests completed successfully")
        
        logger.info("Dataset upload and verification complete!")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 