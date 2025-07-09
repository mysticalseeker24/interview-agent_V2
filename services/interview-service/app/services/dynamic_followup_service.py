"""Dynamic follow-up question generation service using RAG and o4-mini."""
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

from app.core.config import get_settings
from app.services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)


class DynamicFollowUpService:
    """Service for generating dynamic follow-up questions using RAG and LLM."""

    def __init__(self):
        """Initialize the service with Pinecone and OpenAI clients."""
        self.settings = get_settings()
        self.pinecone_service = PineconeService()
        self.openai_client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        logger.info("Dynamic follow-up service initialized")

    async def generate_followup_question(
        self,
        answer_text: str,
        domain: str = "general",
        difficulty: str = "medium",
        use_llm: bool = True,
        max_candidates: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a follow-up question based on candidate's answer.

        Args:
            answer_text: Candidate's answer text
            domain: Question domain (e.g., 'Software Engineering', 'Machine Learning')
            difficulty: Difficulty level (easy, medium, hard)
            use_llm: Whether to use LLM for refinement
            max_candidates: Maximum candidate questions to consider

        Returns:
            Dictionary with follow-up question and metadata

        Raises:
            Exception: If generation fails
        """
        try:
            logger.info(f"Generating follow-up for domain: {domain}, difficulty: {difficulty}")

            # 1. Embed the answer using OpenAI
            answer_embedding = await self._embed_text(answer_text)

            # 2. Query Pinecone for similar follow-up templates
            similar_questions = await self.pinecone_service.search_similar_questions_by_vector(
                query_vector=answer_embedding,
                domain=domain,
                question_type='follow-up',
                top_k=max_candidates * 2  # Get more to filter
            )

            # 3. Filter and get candidates
            candidates = self._filter_candidates(similar_questions, max_candidates)

            if not candidates:
                raise Exception("No suitable follow-up questions found")

            # 4. Select question (with or without LLM refinement)
            if use_llm and len(candidates) > 1:
                result = await self._generate_llm_followup(
                    answer_text, candidates, domain, difficulty
                )
            else:
                # Use the top candidate
                top_candidate = candidates[0]
                result = {
                    "follow_up_question": top_candidate['text'],
                    "source_ids": [top_candidate['question_id']],
                    "generation_method": "rag",
                    "confidence_score": top_candidate.get('similarity_score'),
                    "domain": domain,
                    "difficulty": difficulty
                }

            logger.info(f"Generated follow-up question using method: {result['generation_method']}")

            return result

        except Exception as e:
            logger.error(f"Error generating follow-up: {str(e)}")
            raise

    def _filter_candidates(
        self, 
        similar_questions: List[Dict[str, Any]], 
        max_candidates: int
    ) -> List[Dict[str, Any]]:
        """Filter similar questions to get top candidates."""
        try:
            # Sort by similarity score and take top candidates
            sorted_questions = sorted(
                similar_questions, 
                key=lambda x: x.get('similarity_score', 0), 
                reverse=True
            )
            
            return sorted_questions[:max_candidates]

        except Exception as e:
            logger.error(f"Error filtering candidates: {str(e)}")
            return []

    async def _generate_llm_followup(
        self,
        answer_text: str,
        candidates: List[Dict[str, Any]],
        domain: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """Generate refined follow-up question using o4-mini with enhanced reasoning and context."""
        try:
            # Prepare candidate options for the prompt (limit to top 3)
            top_candidates = candidates[:3]
            candidate_texts = []
            for i, c in enumerate(top_candidates, 1):
                candidate_texts.append(f"{i}. {c['text']} (domain: {c.get('domain', 'general')})")
            candidate_options = "\n".join(candidate_texts)

            # Enhanced system prompt leveraging o4-mini's reasoning capabilities
            system_prompt = """You are a professional technical interviewer with expertise in generating targeted follow-up questions. Your reasoning model should analyze the candidate's response and generate ONE precise follow-up question.

REASONING PROCESS:
1. Analyze the candidate's answer for specific technical details, experiences, or claims
2. Identify areas that need clarification, examples, or deeper exploration
3. Consider the interview domain and difficulty level
4. Select the most valuable follow-up direction

STRICT OUTPUT REQUIREMENTS:
- Generate EXACTLY ONE question (15-25 words)
- Base the question on concrete details from the candidate's answer
- Use appropriate technical terminology for the domain/level
- Ask for specific examples, clarification, or implementation details
- Do not invent or assume information not mentioned by the candidate
- Start with phrases like: "Can you describe...", "How did you...", "What was your approach..."

ANTI-HALLUCINATION CONSTRAINTS:
- Only reference technologies, tools, or concepts the candidate mentioned
- Do not ask hypothetical scenarios unrelated to their stated experience
- Focus on their actual work/knowledge, not theoretical scenarios
- Maintain interview flow by building on their response

OUTPUT: Return only the follow-up question text with no additional formatting or explanation."""

            # Enhanced user prompt with more context and constraints
            # Extract key technical terms from the answer to ground the model
            answer_keywords = self._extract_key_terms(answer_text)
            
            user_prompt = f"""INTERVIEW CONTEXT:
Domain: {domain}
Difficulty Level: {difficulty}

CANDIDATE'S ANSWER:
"{answer_text}"

KEY TECHNICAL TERMS MENTIONED: {', '.join(answer_keywords)}

REFERENCE QUESTION TEMPLATES (for style guidance):
{candidate_options}

REASONING TASK:
Please analyze the candidate's answer and generate ONE targeted follow-up question that:

1. CONTENT ANALYSIS: What specific technical details, tools, or experiences did they mention?
2. DEPTH ASSESSMENT: What areas need more explanation or examples?
3. INTERVIEW FLOW: How can we build naturally on their response?
4. DOMAIN RELEVANCE: What {domain} concepts at {difficulty} level should we explore further?

GENERATION RULES:
- Reference ONLY what the candidate actually mentioned: {', '.join(answer_keywords)}
- Ask for specific examples or clarification about their stated experience
- Use {difficulty}-level {domain} terminology
- Keep it conversational and natural (15-25 words)
- Structure: "Can you describe..." / "How did you..." / "What was your approach to..."

Generate the follow-up question:"""

            # Call o4-mini with optimized parameters for reasoning
            response = self.openai_client.chat.completions.create(
                model=self.settings.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.settings.OPENAI_MAX_TOKENS,
                temperature=self.settings.OPENAI_TEMPERATURE,
                top_p=0.85,  # Optimized for o4-mini reasoning
                frequency_penalty=0.4,  # Reduce repetition for better quality
                presence_penalty=0.3    # Encourage focused responses
            )

            generated_question = response.choices[0].message.content.strip()
            
            # Post-process to ensure quality
            generated_question = self._validate_and_clean_question(
                generated_question, answer_text, answer_keywords
            )

            return {
                "follow_up_question": generated_question,
                "source_ids": [c['question_id'] for c in top_candidates],
                "generation_method": "llm_enhanced",
                "confidence_score": None,
                "model_used": self.settings.OPENAI_CHAT_MODEL,
                "domain": domain,
                "difficulty": difficulty
            }

        except Exception as e:
            logger.error(f"Error generating LLM follow-up: {str(e)}")
            # Fallback to template with better error handling
            if candidates:
                return {
                    "follow_up_question": candidates[0]['text'],
                    "source_ids": [candidates[0]['question_id']],
                    "generation_method": "template_fallback",
                    "confidence_score": candidates[0].get('similarity_score'),
                    "fallback_reason": str(e),
                    "domain": domain,
                    "difficulty": difficulty
                }
            else:
                raise Exception(f"LLM generation failed and no fallback templates available: {str(e)}")

    async def _embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model='text-embedding-ada-002',
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def _extract_key_terms(self, answer_text: str) -> List[str]:
        """Extract key technical terms from the candidate's answer to ground the LLM."""
        import re
        
        # Technical keywords and patterns
        technical_patterns = [
            r'\b[A-Z][a-z]+\.[a-z]+\b',  # APIs like React.useState
            r'\b[A-Z]{2,}\b',            # Acronyms like API, SQL, AWS
            r'\b[a-z]+\-[a-z]+\b',       # Hyphenated terms like test-driven
            r'\b[A-Z][a-z]*[A-Z][a-z]*\b'  # CamelCase like JavaScript
        ]
        
        # Common technical terms
        tech_terms = [
            'react', 'vue', 'angular', 'node', 'python', 'java', 'javascript', 'typescript',
            'api', 'rest', 'graphql', 'database', 'sql', 'nosql', 'mongodb', 'postgresql',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'microservices', 'architecture',
            'testing', 'unit', 'integration', 'deployment', 'ci/cd', 'git', 'agile', 'scrum',
            'frontend', 'backend', 'fullstack', 'mobile', 'web', 'application', 'framework',
            'library', 'performance', 'optimization', 'security', 'authentication', 'authorization'
        ]
        
        key_terms = []
        answer_lower = answer_text.lower()
        
        # Extract technical patterns
        for pattern in technical_patterns:
            matches = re.findall(pattern, answer_text)
            key_terms.extend(matches)
        
        # Extract known technical terms
        words = re.findall(r'\b\w+\b', answer_lower)
        for word in words:
            if word in tech_terms and len(word) > 2:
                key_terms.append(word)
        
        # Remove duplicates and limit to top 5 most relevant
        unique_terms = list(dict.fromkeys(key_terms))
        return unique_terms[:5]

    def _validate_and_clean_question(self, question: str, original_answer: str, key_terms: List[str]) -> str:
        """Validate and clean the generated question to prevent hallucinations."""
        # Remove common unwanted patterns
        question = question.strip()
        
        # Remove quotes if the entire question is quoted
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        
        # Ensure it's actually a question
        if not question.endswith('?'):
            question += '?'
        
        # Capitalize first letter
        if question:
            question = question[0].upper() + question[1:]
        
        # Length validation
        if len(question.split()) > 25:
            # Truncate to reasonable length
            words = question.split()[:25]
            question = ' '.join(words)
            if not question.endswith('?'):
                question += '?'
        
        # Minimum length check
        if len(question.split()) < 5:
            # Too short, likely hallucinated or incomplete
            return "Can you provide more details about your experience?"
        
        return question

    async def test_followup_generation(self, test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """Test follow-up generation with multiple test cases."""
        results = {}
        
        for i, test_case in enumerate(test_cases):
            try:
                answer = test_case['answer']
                domain = test_case.get('domain', 'general')
                difficulty = test_case.get('difficulty', 'medium')
                
                logger.info(f"Testing follow-up generation {i+1}/{len(test_cases)}")
                
                result = await self.generate_followup_question(
                    answer_text=answer,
                    domain=domain,
                    difficulty=difficulty,
                    use_llm=True
                )
                
                results[f"test_case_{i+1}"] = {
                    'status': 'success',
                    'generated_question': result['follow_up_question'],
                    'method': result['generation_method'],
                    'domain': domain,
                    'difficulty': difficulty
                }
                
            except Exception as e:
                logger.error(f"Error in test case {i+1}: {str(e)}")
                results[f"test_case_{i+1}"] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
