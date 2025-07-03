"""
Example implementation matching Task 2.5 requirements exactly.
Demonstrates Pinecone initialization, embedding function, and upsert functionality.
"""
import os
from typing import List
import pinecone
from openai import OpenAI

# Initialization as specified in the task
pinecone.init(api_key=os.getenv('PINECONE_API_KEY'), environment='us-west1-gcp')
questions_index = pinecone.Index('questions-embeddings')

# OpenAI client for embeddings
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_embedding(text: str) -> List[float]:
    """
    Embedding function as specified in the task.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of embedding values
    """
    resp = client.embeddings.create(input=text, model='text-embedding-ada-002')
    return resp.data[0].embedding

def upsert_question_embedding(q_id: int, text: str, metadata: dict):
    """
    Upsert function as specified in the task.
    
    Args:
        q_id: Question ID
        text: Question text
        metadata: Additional metadata
    """
    emb = get_embedding(text)
    questions_index.upsert([(str(q_id), emb, metadata)])

# Example usage demonstrating the functionality
if __name__ == "__main__":
    # Example question data
    sample_questions = [
        {
            'id': 1,
            'text': 'Tell me about a challenging project you worked on and how you overcame the obstacles.',
            'metadata': {
                'domain': 'Software Engineering',
                'type': 'behavioral',
                'difficulty': 'medium'
            }
        },
        {
            'id': 2,
            'text': 'How would you design a scalable microservices architecture for a high-traffic application?',
            'metadata': {
                'domain': 'Software Engineering', 
                'type': 'technical',
                'difficulty': 'hard'
            }
        },
        {
            'id': 3,
            'text': 'Describe your experience with agile development methodologies.',
            'metadata': {
                'domain': 'Product Management',
                'type': 'experience',
                'difficulty': 'easy'
            }
        }
    ]
    
    # Upsert sample questions
    print("Upserting sample questions to Pinecone...")
    for question in sample_questions:
        try:
            upsert_question_embedding(
                q_id=question['id'],
                text=question['text'],
                metadata=question['metadata']
            )
            print(f"✓ Upserted question {question['id']}")
        except Exception as e:
            print(f"✗ Failed to upsert question {question['id']}: {str(e)}")
    
    print("\nExample implementation completed!")
    print("The following functions are now available:")
    print("- get_embedding(text: str) -> List[float]")
    print("- upsert_question_embedding(q_id: int, text: str, metadata: dict)")
    print("- questions_index: Pinecone Index object")
