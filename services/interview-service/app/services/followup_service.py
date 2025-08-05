"""Dynamic follow-up question generation service with performance optimizations."""
import asyncio
import logging
import time
import re
from typing import List, Dict, Any, Optional
from functools import lru_cache

from openai import AsyncOpenAI

from app.core.settings import settings
from app.services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)


class DynamicFollowUpService:
    """High-performance dynamic follow-up question generation using RAG and o4-mini."""

    def __init__(self):
        """Initialize the service with performance optimizations."""
        self.settings = settings
        self.pinecone_service = PineconeService()
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Performance tracking
        self._generation_times = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Cache for generated follow-ups
        self._followup_cache = {}
        self._cache_ttl = settings.CACHE_TTL
        
        logger.info("Dynamic follow-up service initialized with performance optimizations")

    async def generate(
        self, 
        answer_text: str, 
        domain: str, 
        difficulty: str = "medium", 
        max_candidates: int = 5,
        use_llm: bool = True
    ) -> str:
        """
        Generate a follow-up question based on candidate's answer with confidence-based fallback.
        
        Args:
            answer_text: Candidate's answer text
            domain: Question domain (e.g., 'Software Engineering', 'Machine Learning')
            difficulty: Difficulty level (easy, medium, hard)
            max_candidates: Maximum candidate questions to consider
            use_llm: Whether to use LLM for refinement
            
        Returns:
            Generated follow-up question text
            
        Raises:
            Exception: If generation fails or times out
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(answer_text, domain, difficulty)
            if cache_key in self._followup_cache:
                cache_entry = self._followup_cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self._cache_ttl:
                    self._cache_hits += 1
                    logger.debug(f"Cache hit for follow-up generation")
                    return cache_entry['question']
            
            self._cache_misses += 1
            
            # Generate embedding for the answer (with timeout)
            try:
                answer_embedding = await asyncio.wait_for(
                    self.pinecone_service.get_embedding(answer_text),
                    timeout=settings.FOLLOWUP_GENERATION_TIMEOUT * 0.3  # 30% of total time for embedding
                )

                # Query Pinecone for similar follow-up templates (with timeout)
                similar_questions = await asyncio.wait_for(
                    self.pinecone_service.query(
                        vector=answer_embedding,
                        top_k=max_candidates * 2,
                        filter={"domain": domain, "type": "follow-up"}
                    ),
                    timeout=settings.FOLLOWUP_GENERATION_TIMEOUT * 0.4  # 40% of total time for query
                )
            except asyncio.TimeoutError:
                logger.warning("Pinecone operations timed out, using fallback strategy")
                similar_questions = []
                # Use fallback strategy for low latency
                followup_question = await self._generate_domain_fallback(domain, difficulty)
                generation_method = "timeout_fallback"
                
                # Cache the result
                self._followup_cache[cache_key] = {
                    'question': followup_question,
                    'timestamp': time.time(),
                    'method': generation_method
                }
                
                return followup_question

            # Filter and get candidates with confidence assessment
            candidates = self._filter_candidates_with_confidence(similar_questions, max_candidates)
            
            # Determine generation strategy based on confidence
            generation_strategy = self._determine_generation_strategy(candidates, answer_text, domain)
            
            # Generate follow-up based on strategy
            if generation_strategy["method"] == "high_confidence_llm":
                # High confidence: Use LLM to refine top candidates
                result = await asyncio.wait_for(
                    self._generate_llm_followup(answer_text, candidates, domain, difficulty),
                    timeout=settings.FOLLOWUP_GENERATION_TIMEOUT
                )
                followup_question = result["follow_up_question"]
                generation_method = "high_confidence_llm"
                
            elif generation_strategy["method"] == "low_confidence_llm":
                # Low confidence: Use LLM to generate contextual question
                result = await asyncio.wait_for(
                    self._generate_contextual_followup(answer_text, domain, difficulty),
                    timeout=settings.FOLLOWUP_GENERATION_TIMEOUT
                )
                followup_question = result["follow_up_question"]
                generation_method = "low_confidence_llm"
                
            elif generation_strategy["method"] == "fallback_rag":
                # Fallback: Use best available RAG candidate
                top_candidate = candidates[0] if candidates else None
                if top_candidate:
                    followup_question = top_candidate['text']
                    generation_method = "fallback_rag"
                else:
                    # Ultimate fallback: Generate domain-specific question
                    followup_question = await self._generate_domain_fallback(domain, difficulty)
                    generation_method = "domain_fallback"
                    
            else:
                # Default: Use top candidate
                top_candidate = candidates[0] if candidates else None
                if top_candidate:
                    followup_question = top_candidate['text']
                    generation_method = "rag"
                else:
                    followup_question = await self._generate_domain_fallback(domain, difficulty)
                    generation_method = "domain_fallback"

            # Cache the result
            self._followup_cache[cache_key] = {
                'question': followup_question,
                'timestamp': time.time(),
                'method': generation_method,
                'confidence': generation_strategy.get("confidence", 0.0)
            }
            
            # Clean cache if too large
            if len(self._followup_cache) > 500:
                self._clean_cache()

            # Track performance
            generation_time = (time.time() - start_time) * 1000
            self._generation_times.append(generation_time)
            
            # Keep only last 100 measurements
            if len(self._generation_times) > 100:
                self._generation_times = self._generation_times[-100:]
            
            logger.info(f"Generated follow-up using {generation_method} (confidence: {generation_strategy.get('confidence', 0.0):.2f}) in {generation_time:.2f}ms")
            
            return followup_question

        except asyncio.TimeoutError:
            logger.error("Follow-up generation timeout")
            raise Exception("Follow-up generation timeout")
        except Exception as e:
            logger.error(f"Error generating follow-up: {str(e)}")
            raise

    def _generate_cache_key(self, answer_text: str, domain: str, difficulty: str) -> str:
        """Generate cache key for follow-up questions."""
        # Use hash of key components for cache key
        key_components = f"{answer_text[:100]}_{domain}_{difficulty}"
        return str(hash(key_components))

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

    def _filter_candidates_with_confidence(
        self, 
        similar_questions: List[Dict[str, Any]], 
        max_candidates: int
    ) -> List[Dict[str, Any]]:
        """Filter candidates with confidence assessment and quality scoring."""
        try:
            if not similar_questions:
                return []
            
            # Enhanced filtering with confidence scoring
            scored_candidates = []
            for question in similar_questions:
                similarity_score = question.get('similarity_score', 0)
                domain_match = question.get('domain', '') == 'general' or question.get('domain', '') == 'follow-up'
                
                # Calculate confidence score based on multiple factors
                confidence_score = self._calculate_confidence_score(
                    similarity_score=similarity_score,
                    domain_match=domain_match,
                    question_length=len(question.get('text', '')),
                    question_type=question.get('type', '')
                )
                
                scored_candidates.append({
                    **question,
                    'confidence_score': confidence_score
                })
            
            # Sort by confidence score and take top candidates
            sorted_candidates = sorted(
                scored_candidates, 
                key=lambda x: x.get('confidence_score', 0), 
                reverse=True
            )
            
            return sorted_candidates[:max_candidates]

        except Exception as e:
            logger.error(f"Error filtering candidates with confidence: {str(e)}")
            return []

    def _calculate_confidence_score(
        self,
        similarity_score: float,
        domain_match: bool,
        question_length: int,
        question_type: str
    ) -> float:
        """Calculate confidence score for a candidate question."""
        try:
            # Base confidence from similarity score (0-1)
            base_confidence = similarity_score
            
            # Domain match bonus (0.1 if domain matches)
            domain_bonus = 0.1 if domain_match else 0.0
            
            # Question length bonus (optimal length 50-150 characters)
            length_bonus = 0.0
            if 50 <= question_length <= 150:
                length_bonus = 0.05
            elif question_length < 20 or question_length > 300:
                length_bonus = -0.1
            
            # Question type bonus (follow-up questions preferred)
            type_bonus = 0.05 if question_type == 'follow-up' else 0.0
            
            # Calculate final confidence score
            confidence = base_confidence + domain_bonus + length_bonus + type_bonus
            
            # Clamp to 0-1 range
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.0

    def _determine_generation_strategy(
        self,
        candidates: List[Dict[str, Any]],
        answer_text: str,
        domain: str
    ) -> Dict[str, Any]:
        """Determine the best generation strategy based on confidence and context."""
        try:
            if not candidates:
                return {
                    "method": "domain_fallback",
                    "confidence": 0.0,
                    "reason": "No candidates available"
                }
            
            # Get top candidate confidence
            top_confidence = candidates[0].get('confidence_score', 0.0)
            
            # Analyze answer complexity
            answer_complexity = self._analyze_answer_complexity(answer_text)
            
            # Determine strategy based on confidence thresholds
            if top_confidence >= 0.7:
                # High confidence: Use LLM to refine top candidates
                return {
                    "method": "high_confidence_llm",
                    "confidence": top_confidence,
                    "reason": f"High confidence ({top_confidence:.2f}) - refining with LLM"
                }
                
            elif top_confidence >= 0.4:
                # Medium confidence: Use LLM to generate contextual question
                return {
                    "method": "low_confidence_llm",
                    "confidence": top_confidence,
                    "reason": f"Medium confidence ({top_confidence:.2f}) - generating contextual question"
                }
                
            elif top_confidence >= 0.2:
                # Low confidence: Use best RAG candidate
                return {
                    "method": "fallback_rag",
                    "confidence": top_confidence,
                    "reason": f"Low confidence ({top_confidence:.2f}) - using best RAG candidate"
                }
                
            else:
                # Very low confidence: Generate domain-specific fallback
                return {
                    "method": "domain_fallback",
                    "confidence": top_confidence,
                    "reason": f"Very low confidence ({top_confidence:.2f}) - using domain fallback"
                }
                
        except Exception as e:
            logger.error(f"Error determining generation strategy: {str(e)}")
            return {
                "method": "domain_fallback",
                "confidence": 0.0,
                "reason": f"Error: {str(e)}"
            }

    def _analyze_answer_complexity(self, answer_text: str) -> float:
        """Analyze the complexity of the candidate's answer."""
        try:
            # Simple complexity analysis
            word_count = len(answer_text.split())
            technical_terms = len([word for word in answer_text.lower().split() 
                                 if word in ['algorithm', 'complexity', 'optimization', 'implementation', 
                                           'architecture', 'design', 'framework', 'library', 'api']])
            
            # Calculate complexity score (0-1)
            complexity = min(1.0, (word_count / 50) + (technical_terms * 0.1))
            return complexity
            
        except Exception as e:
            logger.error(f"Error analyzing answer complexity: {str(e)}")
            return 0.5

    async def _generate_llm_followup(
        self,
        answer_text: str,
        candidates: List[Dict[str, Any]],
        domain: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """Generate refined follow-up question using o4-mini with anti-hallucination."""
        try:
            # Extract key technical terms from the answer
            key_terms = self._extract_key_terms(answer_text)
            
            # Prepare candidate options for the prompt (limit to top 3)
            top_candidates = candidates[:3]
            candidate_texts = []
            for i, c in enumerate(top_candidates, 1):
                candidate_texts.append(f"{i}. {c['text']} (domain: {c.get('domain', 'general')})")
            candidate_options = "\n".join(candidate_texts)

            # Enhanced system prompt with anti-hallucination constraints
            system_prompt = """You are a professional technical interviewer with expertise in generating targeted follow-up questions. Your reasoning model should analyze the candidate's response and generate ONE precise follow-up question.

REASONING PROCESS:
1. Analyze the candidate's answer for specific technical details, experiences, or claims
2. Identify areas that need clarification, examples, or deeper exploration
3. Consider the interview domain and difficulty level
4. Select the most valuable follow-up direction

DOMAIN-SPECIFIC GUIDELINES:
- DSA: Focus on algorithms, time/space complexity, optimization, and problem-solving approaches
- DevOps: Emphasize CI/CD, containerization, infrastructure, monitoring, and automation
- AI Engineering: Cover model deployment, MLOps, production systems, and AI infrastructure
- Machine Learning: Focus on algorithms, model selection, evaluation, and practical applications
- Data Science: Emphasize data analysis, statistics, visualization, and business insights
- Software Engineering: Cover system design, architecture, best practices, and scalability
- Resume-based: Personalize questions based on specific experiences and skills mentioned

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
            user_prompt = f"""INTERVIEW CONTEXT:
Domain: {domain}
Difficulty Level: {difficulty}

CANDIDATE'S ANSWER:
"{answer_text}"

KEY TECHNICAL TERMS MENTIONED: {', '.join(key_terms)}

REFERENCE QUESTION TEMPLATES (for style guidance):
{candidate_options}

REASONING TASK:
Please analyze the candidate's answer and generate ONE targeted follow-up question that:

1. CONTENT ANALYSIS: What specific technical details, tools, or experiences did they mention?
2. DEPTH ASSESSMENT: What areas need more explanation or examples?
3. INTERVIEW FLOW: How can we build naturally on their response?
4. DOMAIN RELEVANCE: What {domain} concepts at {difficulty} level should we explore further?

GENERATION RULES:
- Reference ONLY what the candidate actually mentioned: {', '.join(key_terms)}
- Ask for specific examples or clarification about their stated experience
- Use {difficulty}-level {domain} terminology
- Keep it conversational and natural (15-25 words)
- Structure: "Can you describe..." / "How did you..." / "What was your approach to..."

Generate the follow-up question:"""

            # Call o4-mini with optimized parameters for reasoning
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model=settings.OPENAI_CHAT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=settings.OPENAI_MAX_TOKENS,
                    temperature=settings.OPENAI_TEMPERATURE,
                    top_p=0.85,
                    frequency_penalty=0.4,
                    presence_penalty=0.3
                ),
                timeout=settings.FOLLOWUP_GENERATION_TIMEOUT
            )

            generated_question = response.choices[0].message.content.strip()
            
            # Validate and clean the generated question
            validated_question = self._validate_and_clean_question(
                generated_question, answer_text, key_terms
            )
            
            return {
                "follow_up_question": validated_question,
                "source_ids": [c.get('question_id') for c in top_candidates],
                "generation_method": "llm",
                "confidence_score": top_candidates[0].get('similarity_score') if top_candidates else 0.0,
                "domain": domain,
                "difficulty": difficulty
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM follow-up: {str(e)}")
            raise

    async def _generate_contextual_followup(
        self,
        answer_text: str,
        domain: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """Generate contextual follow-up when confidence is low but we have answer context."""
        try:
            # Extract key terms from the answer
            key_terms = self._extract_key_terms(answer_text)
            
            # Domain-specific contextual prompts
            domain_prompts = {
                "dsa": f"Based on the candidate's mention of {', '.join(key_terms[:3])}, ask a follow-up about algorithm optimization or time complexity.",
                "devops": f"Given the candidate's experience with {', '.join(key_terms[:3])}, ask about deployment strategies or infrastructure scaling.",
                "ai-engineering": f"Considering the candidate's work with {', '.join(key_terms[:3])}, ask about model deployment challenges or MLOps practices.",
                "machine-learning": f"Based on the candidate's knowledge of {', '.join(key_terms[:3])}, ask about model evaluation or feature engineering.",
                "data-science": f"Given the candidate's experience with {', '.join(key_terms[:3])}, ask about data analysis techniques or statistical modeling.",
                "software-engineering": f"Considering the candidate's work with {', '.join(key_terms[:3])}, ask about system design or architecture decisions.",
                "resume-based": f"Based on the candidate's experience with {', '.join(key_terms[:3])}, ask for specific examples or project details."
            }
            
            contextual_prompt = domain_prompts.get(domain, f"Ask a follow-up question about {', '.join(key_terms[:2])}.")
            
            system_prompt = """You are a technical interviewer generating contextual follow-up questions. 
            Generate ONE specific question that builds on the candidate's response and explores related technical concepts.
            
            REQUIREMENTS:
            - Generate exactly ONE question (15-25 words)
            - Reference specific terms or concepts from their answer
            - Ask for clarification, examples, or deeper explanation
            - Use appropriate technical terminology for the domain
            - Keep it conversational and natural
            
            OUTPUT: Return only the question text."""
            
            user_prompt = f"""DOMAIN: {domain}
DIFFICULTY: {difficulty}
CANDIDATE'S ANSWER: "{answer_text}"
KEY TERMS: {', '.join(key_terms)}
CONTEXTUAL DIRECTION: {contextual_prompt}

Generate a follow-up question:"""

            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model=settings.OPENAI_CHAT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=settings.OPENAI_MAX_TOKENS,
                    temperature=settings.OPENAI_TEMPERATURE
                ),
                timeout=settings.FOLLOWUP_GENERATION_TIMEOUT
            )

            generated_question = response.choices[0].message.content.strip()
            
            return {
                "follow_up_question": generated_question,
                "generation_method": "contextual_llm",
                "confidence_score": 0.4,  # Medium confidence for contextual generation
                "domain": domain,
                "difficulty": difficulty
            }
            
        except Exception as e:
            logger.error(f"Error generating contextual follow-up: {str(e)}")
            raise

    async def _generate_domain_fallback(
        self,
        domain: str,
        difficulty: str
    ) -> str:
        """Generate domain-specific fallback questions when no good candidates are found."""
        try:
            # Domain-specific fallback questions
            fallback_questions = {
                "dsa": {
                    "easy": "Can you explain the difference between an array and a linked list?",
                    "medium": "How would you implement a binary search tree?",
                    "hard": "What's the time complexity of finding the shortest path in a weighted graph?"
                },
                "devops": {
                    "easy": "What is the difference between Docker and virtual machines?",
                    "medium": "How would you set up a CI/CD pipeline for a microservices application?",
                    "hard": "How do you handle database migrations in a zero-downtime deployment?"
                },
                "ai-engineering": {
                    "medium": "How do you monitor model performance in production?",
                    "hard": "What challenges do you face when deploying large language models?"
                },
                "machine-learning": {
                    "easy": "What's the difference between supervised and unsupervised learning?",
                    "medium": "How do you handle overfitting in machine learning models?",
                    "hard": "How would you implement a custom loss function for a specific problem?"
                },
                "data-science": {
                    "easy": "How do you handle missing data in a dataset?",
                    "medium": "What statistical tests would you use to validate your findings?",
                    "hard": "How do you design an A/B test for a recommendation system?"
                },
                "software-engineering": {
                    "easy": "What design patterns have you used in your projects?",
                    "medium": "How do you ensure code quality in a team environment?",
                    "hard": "How would you design a scalable microservices architecture?"
                },
                "resume-based": {
                    "medium": "Can you walk me through one of your most challenging projects?"
                }
            }
            
            # Get domain questions
            domain_questions = fallback_questions.get(domain, {})
            
            # Get difficulty-specific question
            question = domain_questions.get(difficulty)
            
            # Fallback to medium if difficulty not found
            if not question and difficulty != "medium":
                question = domain_questions.get("medium")
            
            # Ultimate fallback
            if not question:
                question = "Can you tell me more about your experience with this technology?"
            
            return question
            
        except Exception as e:
            logger.error(f"Error generating domain fallback: {str(e)}")
            return "Can you elaborate on your previous answer?"

    def _extract_key_terms(self, answer_text: str) -> List[str]:
        """Extract key technical terms from answer text."""
        try:
            # Simple keyword extraction - in production, use more sophisticated NLP
            # Remove common words and extract technical terms
            common_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
                'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
                'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours',
                'his', 'hers', 'ours', 'theirs', 'what', 'when', 'where', 'why', 'how', 'who',
                'which', 'whom', 'whose', 'if', 'then', 'else', 'while', 'for', 'as', 'since',
                'until', 'before', 'after', 'during', 'through', 'under', 'over', 'above', 'below',
                'up', 'down', 'out', 'off', 'away', 'back', 'forward', 'toward', 'towards'
            }
            
            # Extract words that look like technical terms
            words = re.findall(r'\b[A-Za-z][A-Za-z0-9_]*\b', answer_text.lower())
            technical_terms = [
                word for word in words 
                if word not in common_words 
                and len(word) > 2 
                and not word.isdigit()
            ]
            
            # Return unique terms, limited to top 10
            return list(set(technical_terms))[:10]
            
        except Exception as e:
            logger.error(f"Error extracting key terms: {str(e)}")
            return []

    def _validate_and_clean_question(
        self, 
        question: str, 
        original_answer: str, 
        key_terms: List[str]
    ) -> str:
        """Validate and clean the generated question."""
        try:
            # Remove any extra formatting or explanations
            question = question.strip()
            
            # Remove quotes if present
            if question.startswith('"') and question.endswith('"'):
                question = question[1:-1]
            
            # Ensure it ends with a question mark
            if not question.endswith('?'):
                question += '?'
            
            # Basic validation - ensure it's not too short or too long
            if len(question) < 10 or len(question) > 200:
                # Fallback to a generic question
                question = f"Can you tell me more about your experience with {key_terms[0] if key_terms else 'this topic'}?"
            
            return question
            
        except Exception as e:
            logger.error(f"Error validating question: {str(e)}")
            return "Can you provide more details about your experience?"

    def _clean_cache(self):
        """Clean old cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._followup_cache.items()
            if current_time - entry['timestamp'] > self._cache_ttl
        ]
        for key in expired_keys:
            del self._followup_cache[key]
        logger.debug(f"Cleaned {len(expired_keys)} expired follow-up cache entries")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the service."""
        if not self._generation_times:
            return {
                "avg_generation_time_ms": 0,
                "p95_generation_time_ms": 0,
                "cache_hit_rate": 0,
                "total_requests": 0
            }
        
        sorted_times = sorted(self._generation_times)
        total_requests = len(self._generation_times)
        total_cache_requests = self._cache_hits + self._cache_misses
        
        return {
            "avg_generation_time_ms": sum(self._generation_times) / total_requests,
            "p95_generation_time_ms": sorted_times[int(0.95 * total_requests)],
            "p99_generation_time_ms": sorted_times[int(0.99 * total_requests)],
            "cache_hit_rate": self._cache_hits / total_cache_requests if total_cache_requests > 0 else 0,
            "total_requests": total_requests,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            # Test basic functionality
            test_answer = "I have experience with Python and machine learning."
            test_followup = await asyncio.wait_for(
                self.generate(test_answer, "software-engineering", "medium", use_llm=False),
                timeout=settings.HEALTH_CHECK_TIMEOUT
            )
            
            return {
                "status": "healthy",
                "test_followup_generated": bool(test_followup),
                "performance_metrics": self.get_performance_metrics()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "performance_metrics": self.get_performance_metrics()
            } 