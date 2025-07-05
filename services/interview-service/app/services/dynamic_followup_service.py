"""Dynamic follow-up question generation service using RAG and o4-mini."""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from openai import OpenAI

from app.core.config import get_settings
from app.models.question import Question
from app.models.session import Session
from app.models.session_question import SessionQuestion
from app.services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)


class DynamicFollowUpService:
    """Service for generating dynamic follow-up questions using RAG and LLM."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.pinecone_service = PineconeService()
        self.openai_client = OpenAI(api_key=self.settings.OPENAI_API_KEY)

    async def generate_followup_question(
        self,
        session_id: int,
        answer_text: str,
        use_llm: bool = False,
        max_candidates: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a follow-up question based on candidate's answer.

        Args:
            session_id: Current session ID
            answer_text: Candidate's answer text
            use_llm: Whether to use GPT-4.1 for refinement
            max_candidates: Maximum candidate questions to consider

        Returns:
            Dictionary with follow-up question and metadata

        Raises:
            Exception: If generation fails
        """
        try:
            # 1. Get session context and already asked questions
            session_context = await self._get_session_context(session_id)
            excluded_ids = await self._get_asked_question_ids(session_id)

            logger.info(f"Generating follow-up for session {session_id}, "
                       f"excluding {len(excluded_ids)} already asked questions")

            # 2. Embed the answer using OpenAI
            answer_embedding = await self._embed_text(answer_text)

            # 3. Query Pinecone for similar follow-up templates
            similar_questions = await self.pinecone_service.search_similar_questions_by_vector(
                query_vector=answer_embedding,
                domain=session_context.get('domain'),
                question_type='follow-up',
                top_k=max_candidates * 2  # Get more to filter
            )

            # 4. Filter out already asked questions and get candidates
            candidates = await self._filter_and_fetch_candidates(
                similar_questions, excluded_ids, max_candidates
            )

            if not candidates:
                raise Exception("No suitable follow-up questions found")

            # 5. Select question (with or without LLM refinement)
            if use_llm and len(candidates) > 1:
                result = await self._generate_llm_followup(
                    answer_text, candidates, session_context
                )
            else:
                # Use the top candidate
                top_candidate = candidates[0]
                result = {
                    "follow_up_question": top_candidate['text'],
                    "source_ids": [top_candidate['id']],
                    "generation_method": "rag",
                    "confidence_score": top_candidate.get('score')
                }

            # 6. Log the chosen follow-up to SessionQuestions
            await self._log_session_question(
                session_id=session_id,
                question_id=result["source_ids"][0],
                source=result["generation_method"]
            )

            logger.info(f"Generated follow-up question for session {session_id} "
                       f"using method: {result['generation_method']}")

            return result

        except Exception as e:
            logger.error(f"Error generating follow-up for session {session_id}: {str(e)}")
            raise

    async def _get_session_context(self, session_id: int) -> Dict[str, Any]:
        """Get session context including domain and module info."""
        try:
            query = select(Session).where(Session.id == session_id)
            result = await self.db.execute(query)
            session = result.scalar_one_or_none()

            if not session:
                raise Exception(f"Session {session_id} not found")

            # Get module info for domain context
            module_query = text("""
                SELECT m.name, m.category, m.difficulty_level
                FROM modules m
                WHERE m.id = :module_id
            """)
            
            module_result = await self.db.execute(
                module_query, {"module_id": session.module_id}
            )
            module_row = module_result.fetchone()

            return {
                "domain": module_row.category if module_row else "general",
                "difficulty": module_row.difficulty_level if module_row else "intermediate",
                "module_name": module_row.name if module_row else "Unknown"
            }

        except Exception as e:
            logger.error(f"Error getting session context: {str(e)}")
            return {"domain": "general", "difficulty": "intermediate"}

    async def _get_asked_question_ids(self, session_id: int) -> List[int]:
        """Get list of question IDs already asked in this session."""
        try:
            query = select(SessionQuestion.question_id).where(
                SessionQuestion.session_id == session_id
            )
            result = await self.db.execute(query)
            return [row[0] for row in result.fetchall()]

        except Exception as e:
            logger.error(f"Error getting asked questions: {str(e)}")
            return []

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

    async def _filter_and_fetch_candidates(
        self, 
        similar_questions: List[Dict[str, Any]], 
        excluded_ids: List[int],
        max_candidates: int
    ) -> List[Dict[str, Any]]:
        """Filter similar questions and fetch full details from database."""
        try:
            # Extract question IDs from Pinecone results, excluding already asked
            candidate_ids = []
            for item in similar_questions:
                question_id = item.get('question_id')
                if question_id and question_id not in excluded_ids:
                    candidate_ids.append(question_id)
                    if len(candidate_ids) >= max_candidates:
                        break

            if not candidate_ids:
                return []

            # Fetch full question details from database
            query = select(Question).where(Question.id.in_(candidate_ids))
            result = await self.db.execute(query)
            questions = result.scalars().all()

            # Convert to dictionaries with scores
            candidates = []
            for question in questions:
                # Find the score from Pinecone results
                score = None
                for item in similar_questions:
                    if item.get('question_id') == question.id:
                        score = item.get('score')
                        break

                candidates.append({
                    'id': question.id,
                    'text': question.text,
                    'domain': question.domain,
                    'type': question.type,
                    'score': score
                })

            return candidates

        except Exception as e:
            logger.error(f"Error filtering candidates: {str(e)}")
            return []

    async def _generate_llm_followup(
        self,
        answer_text: str,
        candidates: List[Dict[str, Any]],
        session_context: Dict[str, Any]
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
            domain = session_context.get('domain', 'general')
            difficulty = session_context.get('difficulty', 'intermediate')
            module_name = session_context.get('module_name', 'Interview')
            
            # Extract key technical terms from the answer to ground the model
            answer_keywords = self._extract_key_terms(answer_text)
            
            user_prompt = f"""INTERVIEW CONTEXT:
Domain: {domain}
Difficulty Level: {difficulty}
Module: {module_name}

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
                "source_ids": [c['id'] for c in top_candidates],
                "generation_method": "llm_enhanced",
                "confidence_score": None,
                "model_used": self.settings.OPENAI_CHAT_MODEL
            }

        except Exception as e:
            logger.error(f"Error generating LLM follow-up: {str(e)}")
            # Fallback to template with better error handling
            if candidates:
                return {
                    "follow_up_question": candidates[0]['text'],
                    "source_ids": [candidates[0]['id']],
                    "generation_method": "template_fallback",
                    "confidence_score": candidates[0].get('score'),
                    "fallback_reason": str(e)
                }
            else:
                raise Exception(f"LLM generation failed and no fallback templates available: {str(e)}")

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

    async def _log_session_question(
        self, 
        session_id: int, 
        question_id: int, 
        source: str
    ) -> None:
        """Log the asked question to SessionQuestions table."""
        try:
            session_question = SessionQuestion(
                session_id=session_id,
                question_id=question_id,
                question_type="follow_up",
                source=source
            )
            
            self.db.add(session_question)
            await self.db.commit()

            logger.info(f"Logged follow-up question {question_id} for session {session_id}")

        except Exception as e:
            logger.error(f"Error logging session question: {str(e)}")
            await self.db.rollback()

    async def get_session_question_history(self, session_id: int) -> List[Dict[str, Any]]:
        """Get history of questions asked in a session."""
        try:
            query = text("""
                SELECT sq.id, sq.question_id, sq.question_type, sq.asked_at, sq.source,
                       q.text as question_text, q.domain, q.type
                FROM session_questions sq
                JOIN questions q ON sq.question_id = q.id
                WHERE sq.session_id = :session_id
                ORDER BY sq.asked_at
            """)
            
            result = await self.db.execute(query, {"session_id": session_id})
            
            history = []
            for row in result.fetchall():
                history.append({
                    "id": row.id,
                    "question_id": row.question_id,
                    "question_type": row.question_type,
                    "asked_at": row.asked_at.isoformat(),
                    "source": row.source,
                    "question_text": row.question_text,
                    "domain": row.domain,
                    "type": row.type
                })
            
            return history

        except Exception as e:
            logger.error(f"Error getting session question history: {str(e)}")
            return []
