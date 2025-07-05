"""Post-interview feedback generation tasks using o4-mini."""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

from celery import current_task
from celery.exceptions import Retry
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import openai
from sentence_transformers import SentenceTransformer

from app.tasks import celery_app
from app.core.config import get_settings
from app.models.session import Session
from app.models.question import Question
from app.models.response import Response
from app.models.score import Score
from app.models.feedback_report import FeedbackReport

logger = logging.getLogger(__name__)

# Initialize embedding model (will be loaded once per worker)
embed_model = None

def get_embedding_model():
    """Get or initialize the sentence transformer model."""
    global embed_model
    if embed_model is None:
        embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return embed_model

def get_embedding_model():
    """Get or initialize the sentence transformer model."""
    global embed_model
    if embed_model is None:
        embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return embed_model


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def generate_feedback(self, session_id: int) -> Dict[str, Any]:
    """
    Generate comprehensive feedback report for a completed interview session.
    
    Args:
        session_id: The session ID to generate feedback for
        
    Returns:
        Dictionary containing feedback generation results
        
    Raises:
        Exception: If feedback generation fails after retries
    """
    try:
        start_time = time.time()
        logger.info(f"Starting feedback generation for session {session_id}")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 7,
                'status': 'Initializing feedback generation...'
            }
        )
        
        # Run the async feedback generation
        result = asyncio.run(_generate_feedback_async(session_id, self))
        
        processing_time = time.time() - start_time
        result['processing_time_seconds'] = processing_time
        
        logger.info(f"Feedback generation completed for session {session_id} in {processing_time:.2f}s")
        return result
        
    except Exception as exc:
        logger.error(f"Error generating feedback for session {session_id}: {str(exc)}")
        
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(exc),
                'session_id': session_id,
                'retry_count': self.request.retries
            }
        )
        
        # Retry if we haven't exhausted retries
        if self.request.retries < 3:
            logger.info(f"Retrying feedback generation for session {session_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60)
        
        raise exc


async def _generate_feedback_async(session_id: int, task=None) -> Dict[str, Any]:
    """
    Async implementation of feedback generation.
    
    Args:
        session_id: Session to generate feedback for
        task: Celery task instance for progress updates
        
    Returns:
        Feedback generation results
    """
    settings = get_settings()
    
    # Create async database session
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Step 1: Validate session and load data
            if task:
                task.update_state(
                    state='PROGRESS',
                    meta={'current': 1, 'total': 7, 'status': 'Loading session data...'}
                )
            
            session, responses = await _load_session_data(db, session_id)
            if not responses:
                raise ValueError(f"No responses found for session {session_id}")
            
            # Step 2: Compute semantic similarities and fluency metrics
            if task:
                task.update_state(
                    state='PROGRESS',
                    meta={'current': 2, 'total': 7, 'status': 'Computing response metrics...'}
                )
            
            scores_data = await _compute_response_metrics(db, responses)
            
            # Step 3: Store individual scores
            if task:
                task.update_state(
                    state='PROGRESS',
                    meta={'current': 3, 'total': 7, 'status': 'Storing individual scores...'}
                )
            
            await _store_scores(db, session_id, scores_data)
            
            # Step 4: Calculate percentiles using historical data
            if task:
                task.update_state(
                    state='PROGRESS',
                    meta={'current': 4, 'total': 7, 'status': 'Computing percentile rankings...'}
                )
            
            percentiles = await _calculate_percentiles(db, scores_data, session.module_id)
            
            # Step 5: Generate aggregate metrics
            if task:
                task.update_state(
                    state='PROGRESS',
                    meta={'current': 5, 'total': 7, 'status': 'Aggregating session metrics...'}
                )
            
            aggregates = _calculate_aggregates(scores_data)
            
            # Step 6: Generate AI narrative feedback using o4-mini
            if task:
                task.update_state(
                    state='PROGRESS',
                    meta={'current': 6, 'total': 7, 'status': 'Generating AI feedback narrative...'}
                )
            
            narrative_data = await _generate_ai_feedback(
                session_id, aggregates, percentiles, responses, settings
            )
            
            # Step 7: Save complete feedback report
            if task:
                task.update_state(
                    state='PROGRESS',
                    meta={'current': 7, 'total': 7, 'status': 'Saving feedback report...'}
                )
            
            feedback_report = await _save_feedback_report(
                db, session_id, aggregates, percentiles, narrative_data, len(responses)
            )
            
            await db.commit()
            
            return {
                'status': 'success',
                'session_id': session_id,
                'feedback_report_id': feedback_report.id,
                'overall_score': aggregates['overall_score'],
                'percentiles': percentiles,
                'questions_analyzed': len(responses),
                'narrative_length': len(narrative_data['report_text'])
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Database error in feedback generation: {str(e)}")
            raise
        finally:
            await engine.dispose()


async def _load_session_data(db: AsyncSession, session_id: int) -> Tuple[Session, List[Response]]:
    """Load session and associated responses with questions."""
    
    # Load session
    session_result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise ValueError(f"Session {session_id} not found")
    
    if session.status != "completed":
        raise ValueError(f"Session {session_id} is not completed (status: {session.status})")
    
    # Load responses with questions
    responses_query = text("""
        SELECT r.id as response_id, r.session_id, r.question_id, r.answer_text, 
               r.duration_seconds, r.started_at, r.submitted_at,
               q.text as question_text, q.ideal_answer_summary, q.domain, q.difficulty_level,
               q.type as question_type
        FROM responses r 
        JOIN questions q ON r.question_id = q.id
        WHERE r.session_id = :session_id
        ORDER BY r.started_at
    """)
    
    result = await db.execute(responses_query, {"session_id": session_id})
    responses = []
    
    for row in result.fetchall():
        response_data = {
            'id': row.response_id,
            'session_id': row.session_id,
            'question_id': row.question_id,
            'answer_text': row.answer_text,
            'duration_seconds': row.duration_seconds,
            'question_text': row.question_text,
            'ideal_answer_summary': row.ideal_answer_summary,
            'domain': row.domain,
            'difficulty_level': row.difficulty_level,
            'question_type': row.question_type
        }
        responses.append(response_data)
    
    return session, responses


async def _compute_response_metrics(db: AsyncSession, responses: List[Dict]) -> List[Dict[str, Any]]:
    """Compute semantic similarity, fluency, and other metrics for each response."""
    
    embed_model = get_embedding_model()
    scores_data = []
    
    for response in responses:
        try:
            answer_text = response['answer_text']
            ideal_answer = response['ideal_answer_summary']
            
            if not answer_text or not ideal_answer:
                logger.warning(f"Missing text data for response {response['id']}")
                continue
            
            # Compute semantic similarity using sentence transformers
            answer_embedding = embed_model.encode([answer_text])
            ideal_embedding = embed_model.encode([ideal_answer])
            
            # Calculate cosine similarity
            similarity = float(np.dot(answer_embedding[0], ideal_embedding[0]) / 
                             (np.linalg.norm(answer_embedding[0]) * np.linalg.norm(ideal_embedding[0])))
            
            # Convert to 0-100 scale
            correctness_score = max(0, min(100, similarity * 100))
            
            # Calculate fluency metrics
            word_count = len(answer_text.split())
            duration_minutes = (response['duration_seconds'] or 60) / 60.0  # Default to 1 minute if no duration
            words_per_minute = word_count / duration_minutes if duration_minutes > 0 else 0
            
            # Fluency score based on WPM (normal conversational range: 120-150 WPM)
            # Scale: 0-50 WPM = 0-30, 50-120 WPM = 30-80, 120-180 WPM = 80-100, >180 WPM = decrease
            if words_per_minute <= 50:
                fluency_score = (words_per_minute / 50) * 30
            elif words_per_minute <= 120:
                fluency_score = 30 + ((words_per_minute - 50) / 70) * 50
            elif words_per_minute <= 180:
                fluency_score = 80 + ((words_per_minute - 120) / 60) * 20
            else:
                fluency_score = max(70, 100 - ((words_per_minute - 180) / 50) * 30)
            
            fluency_score = max(0, min(100, fluency_score))
            
            # Depth score based on word count and technical terms
            # Basic heuristic: longer, more detailed answers score higher
            depth_base = min(100, (word_count / 50) * 60)  # 50 words = 60% base score
            
            # Bonus for technical terms (simple keyword matching)
            technical_keywords = _count_technical_terms(answer_text, response['domain'])
            technical_bonus = min(40, technical_keywords * 8)  # Up to 40 points for technical terms
            
            depth_score = max(0, min(100, depth_base + technical_bonus))
            
            score_data = {
                'response_id': response['id'],
                'question_id': response['question_id'],
                'correctness': correctness_score,
                'fluency': fluency_score,
                'depth': depth_score,
                'semantic_similarity': similarity,
                'word_count': word_count,
                'words_per_minute': words_per_minute,
                'technical_terms_count': technical_keywords,
                'duration_seconds': response['duration_seconds']
            }
            
            scores_data.append(score_data)
            
        except Exception as e:
            logger.error(f"Error computing metrics for response {response['id']}: {str(e)}")
            continue
    
    return scores_data


def _count_technical_terms(text: str, domain: str) -> int:
    """Count technical terms in the response based on domain."""
    
    text_lower = text.lower()
    
    # Domain-specific technical terms
    technical_terms = {
        'software_engineering': [
            'algorithm', 'api', 'database', 'framework', 'library', 'microservices',
            'docker', 'kubernetes', 'react', 'node', 'python', 'javascript', 'sql',
            'nosql', 'redis', 'cache', 'scalability', 'performance', 'optimization',
            'testing', 'unit test', 'integration', 'deployment', 'ci/cd', 'git',
            'architecture', 'design pattern', 'mvc', 'rest', 'graphql', 'json'
        ],
        'machine_learning': [
            'neural network', 'deep learning', 'supervised', 'unsupervised', 'model',
            'training', 'validation', 'overfitting', 'underfitting', 'feature',
            'dataset', 'algorithm', 'regression', 'classification', 'clustering',
            'gradient descent', 'backpropagation', 'tensorflow', 'pytorch', 'sklearn',
            'numpy', 'pandas', 'matplotlib', 'cross-validation', 'hyperparameter'
        ],
        'data_structures': [
            'array', 'linked list', 'stack', 'queue', 'tree', 'binary tree', 'heap',
            'hash table', 'graph', 'sorting', 'searching', 'algorithm', 'complexity',
            'big o', 'time complexity', 'space complexity', 'recursion', 'iteration',
            'dynamic programming', 'greedy', 'divide and conquer', 'bfs', 'dfs'
        ]
    }
    
    # Get relevant technical terms for the domain
    domain_terms = technical_terms.get(domain.lower(), [])
    
    # Count occurrences
    count = 0
    for term in domain_terms:
        if term in text_lower:
            count += 1
    
    return count


async def _store_scores(db: AsyncSession, session_id: int, scores_data: List[Dict[str, Any]]) -> None:
    """Store individual response scores in the database."""
    
    for score_data in scores_data:
        try:
            # Check if score already exists
            existing_score = await db.execute(
                select(Score).where(
                    Score.session_id == session_id,
                    Score.question_id == score_data['question_id'],
                    Score.response_id == score_data['response_id']
                )
            )
            
            if existing_score.scalar_one_or_none():
                logger.info(f"Score already exists for response {score_data['response_id']}, skipping")
                continue
            
            # Create new score record
            score = Score(
                session_id=session_id,
                question_id=score_data['question_id'],
                response_id=score_data['response_id'],
                correctness=score_data['correctness'],
                fluency=score_data['fluency'],
                depth=score_data['depth'],
                word_count=score_data['word_count'],
                words_per_minute=score_data['words_per_minute'],
                duration_seconds=score_data['duration_seconds']
            )
            
            db.add(score)
            
        except Exception as e:
            logger.error(f"Error storing score for response {score_data['response_id']}: {str(e)}")
            continue
    
    await db.flush()  # Flush to get IDs without committing


async def _calculate_percentiles(
    db: AsyncSession, 
    scores_data: List[Dict[str, Any]], 
    module_id: int
) -> Dict[str, float]:
    """Calculate percentile rankings based on historical data."""
    
    try:
        # Calculate averages for this session
        current_correctness = np.mean([s['correctness'] for s in scores_data])
        current_fluency = np.mean([s['fluency'] for s in scores_data])
        current_depth = np.mean([s['depth'] for s in scores_data])
        current_overall = (current_correctness + current_fluency + current_depth) / 3
        
        # Get historical data for the same module (last 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        historical_query = text("""
            SELECT 
                AVG(s.correctness) as avg_correctness,
                AVG(s.fluency) as avg_fluency, 
                AVG(s.depth) as avg_depth,
                (AVG(s.correctness) + AVG(s.fluency) + AVG(s.depth)) / 3 as overall_score
            FROM scores s
            JOIN sessions sess ON s.session_id = sess.id  
            WHERE sess.module_id = :module_id 
                AND s.computed_at >= :cutoff_date
                AND sess.status = 'completed'
            GROUP BY s.session_id
            HAVING COUNT(s.id) >= 3  -- At least 3 questions answered
        """)
        
        result = await db.execute(historical_query, {
            "module_id": module_id, 
            "cutoff_date": cutoff_date
        })
        
        historical_data = result.fetchall()
        
        if len(historical_data) < 10:  # Need at least 10 historical sessions for meaningful percentiles
            logger.warning(f"Insufficient historical data for module {module_id}: {len(historical_data)} sessions")
            return {
                'correctness_percentile': None,
                'fluency_percentile': None,
                'depth_percentile': None,
                'overall_percentile': None,
                'historical_sample_size': len(historical_data)
            }
        
        # Calculate percentiles
        historical_correctness = [row.avg_correctness for row in historical_data]
        historical_fluency = [row.avg_fluency for row in historical_data]
        historical_depth = [row.avg_depth for row in historical_data]
        historical_overall = [row.overall_score for row in historical_data]
        
        correctness_percentile = _calculate_percentile(current_correctness, historical_correctness)
        fluency_percentile = _calculate_percentile(current_fluency, historical_fluency)
        depth_percentile = _calculate_percentile(current_depth, historical_depth)
        overall_percentile = _calculate_percentile(current_overall, historical_overall)
        
        return {
            'correctness_percentile': correctness_percentile,
            'fluency_percentile': fluency_percentile,
            'depth_percentile': depth_percentile,
            'overall_percentile': overall_percentile,
            'historical_sample_size': len(historical_data)
        }
        
    except Exception as e:
        logger.error(f"Error calculating percentiles: {str(e)}")
        return {
            'correctness_percentile': None,
            'fluency_percentile': None,
            'depth_percentile': None,
            'overall_percentile': None,
            'historical_sample_size': 0
        }


def _calculate_percentile(value: float, historical_values: List[float]) -> float:
    """Calculate percentile ranking for a value against historical data."""
    if not historical_values:
        return None
    
    # Count how many historical values are less than current value
    count_below = sum(1 for v in historical_values if v < value)
    total_count = len(historical_values)
    
    # Calculate percentile (0-100)
    percentile = (count_below / total_count) * 100
    return round(percentile, 1)


def _calculate_aggregates(scores_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate aggregate metrics for the session."""
    
    if not scores_data:
        return {
            'correctness_avg': 0.0,
            'fluency_avg': 0.0,
            'depth_avg': 0.0,
            'overall_score': 0.0
        }
    
    correctness_avg = np.mean([s['correctness'] for s in scores_data])
    fluency_avg = np.mean([s['fluency'] for s in scores_data])
    depth_avg = np.mean([s['depth'] for s in scores_data])
    
    # Weighted overall score (can be customized)
    overall_score = (correctness_avg * 0.4 + fluency_avg * 0.3 + depth_avg * 0.3)
    
    return {
        'correctness_avg': round(correctness_avg, 2),
        'fluency_avg': round(fluency_avg, 2),
        'depth_avg': round(depth_avg, 2),
        'overall_score': round(overall_score, 2)
    }


async def _generate_ai_feedback(
    session_id: int,
    aggregates: Dict[str, float],
    percentiles: Dict[str, float],
    responses: List[Dict],
    settings
) -> Dict[str, Any]:
    """Generate narrative feedback using o4-mini."""
    
    try:
        # Prepare context for o4-mini
        performance_context = _build_performance_context(aggregates, percentiles, responses)
        
        # Enhanced system prompt for o4-mini reasoning
        system_prompt = """You are an expert technical interview feedback analyst. Your task is to provide constructive, specific feedback based on interview performance data.

ANALYSIS FRAMEWORK:
1. Review the quantitative performance metrics
2. Identify specific strengths demonstrated by the candidate
3. Pinpoint concrete areas for improvement
4. Provide actionable recommendations

OUTPUT REQUIREMENTS:
- Professional, encouraging tone
- Specific, evidence-based observations
- 3 distinct strengths (bullet points)
- 3 distinct improvement areas (bullet points)
- Focus on technical competencies and communication skills
- Avoid generic statements; be specific to the performance data

STRUCTURE your response as:
[NARRATIVE PARAGRAPH: 2-3 sentences summarizing overall performance]

**Key Strengths:**
• [Specific strength 1 with evidence]
• [Specific strength 2 with evidence]  
• [Specific strength 3 with evidence]

**Areas for Improvement:**
• [Specific area 1 with actionable advice]
• [Specific area 2 with actionable advice]
• [Specific area 3 with actionable advice]"""

        # Detailed user prompt with performance data
        user_prompt = f"""INTERVIEW PERFORMANCE ANALYSIS

Session ID: {session_id}
Questions Analyzed: {len(responses)}

PERFORMANCE METRICS:
• Overall Score: {aggregates['overall_score']:.1f}/100
• Technical Correctness: {aggregates['correctness_avg']:.1f}/100
• Communication Fluency: {aggregates['fluency_avg']:.1f}/100  
• Answer Depth: {aggregates['depth_avg']:.1f}/100

PERCENTILE RANKINGS (vs. similar candidates):
• Overall Performance: {percentiles.get('overall_percentile', 'N/A')}th percentile
• Technical Accuracy: {percentiles.get('correctness_percentile', 'N/A')}th percentile
• Communication: {percentiles.get('fluency_percentile', 'N/A')}th percentile
• Answer Detail: {percentiles.get('depth_percentile', 'N/A')}th percentile

RESPONSE ANALYSIS:
{performance_context}

Please provide comprehensive feedback following the specified structure."""

        # Call o4-mini for feedback generation
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,  # o4-mini
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS * 2,  # Allow longer feedback
            temperature=0.3,  # Slightly higher for more natural language
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.2
        )
        
        narrative_text = response.choices[0].message.content.strip()
        
        # Parse strengths and improvements from the narrative
        strengths, improvements = _parse_feedback_sections(narrative_text)
        
        return {
            'report_text': narrative_text,
            'strengths': strengths,
            'improvements': improvements,
            'model_used': settings.OPENAI_CHAT_MODEL,
            'generation_method': 'o4_mini_reasoning'
        }
        
    except Exception as e:
        logger.error(f"Error generating AI feedback: {str(e)}")
        raise  # Re-raise the exception instead of using fallback


def _build_performance_context(
    aggregates: Dict[str, float], 
    percentiles: Dict[str, float], 
    responses: List[Dict]
) -> str:
    """Build detailed context about candidate performance for o4-mini."""
    
    context_parts = []
    
    # Overall performance summary
    if aggregates['overall_score'] >= 80:
        performance_level = "excellent"
    elif aggregates['overall_score'] >= 60:
        performance_level = "solid"
    elif aggregates['overall_score'] >= 40:
        performance_level = "developing"
    else:
        performance_level = "needs improvement"
    
    context_parts.append(f"Overall performance level: {performance_level}")
    
    # Response quality analysis
    word_counts = []
    domains = set()
    
    for response in responses[:3]:  # Analyze first 3 responses for context
        if 'answer_text' in response:
            word_count = len(response['answer_text'].split())
            word_counts.append(word_count)
            domains.add(response.get('domain', 'general'))
    
    if word_counts:
        avg_response_length = np.mean(word_counts)
        context_parts.append(f"Average response length: {avg_response_length:.0f} words")
    
    if domains:
        context_parts.append(f"Technical domains covered: {', '.join(domains)}")
    
    # Percentile context
    if percentiles.get('overall_percentile') is not None:
        percentile = percentiles['overall_percentile']
        if percentile >= 80:
            rank_description = "top 20% of candidates"
        elif percentile >= 60:
            rank_description = "above average performance"
        elif percentile >= 40:
            rank_description = "average performance range"
        else:
            rank_description = "below average, room for growth"
        
        context_parts.append(f"Ranking: {rank_description}")
    
    return " | ".join(context_parts)


def _parse_feedback_sections(narrative_text: str) -> Tuple[List[str], List[str]]:
    """Parse strengths and improvements from the AI-generated narrative."""
    
    strengths = []
    improvements = []
    
    lines = narrative_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        if 'strength' in line.lower() and ('**' in line or '#' in line):
            current_section = 'strengths'
        elif 'improvement' in line.lower() and ('**' in line or '#' in line):
            current_section = 'improvements'
        elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
            item = line[1:].strip()
            if current_section == 'strengths' and item:
                strengths.append(item)
            elif current_section == 'improvements' and item:
                improvements.append(item)
    
    # Fallback: extract from bullet points if structured parsing fails
    if not strengths and not improvements:
        bullet_lines = [line for line in lines if line.strip().startswith(('•', '-', '*'))]
        mid_point = len(bullet_lines) // 2
        strengths = [line[1:].strip() for line in bullet_lines[:mid_point]]
        improvements = [line[1:].strip() for line in bullet_lines[mid_point:]]
    
    return strengths[:3], improvements[:3]  # Limit to 3 each


async def _save_feedback_report(
    db: AsyncSession,
    session_id: int,
    aggregates: Dict[str, float],
    percentiles: Dict[str, float],
    narrative_data: Dict[str, Any],
    total_questions: int
) -> FeedbackReport:
    """Save the complete feedback report to the database."""
    
    # Check if feedback report already exists
    existing_report = await db.execute(
        select(FeedbackReport).where(FeedbackReport.session_id == session_id)
    )
    
    if existing_report.scalar_one_or_none():
        raise ValueError(f"Feedback report already exists for session {session_id}")
    
    # Create new feedback report
    feedback_report = FeedbackReport(
        session_id=session_id,
        avg_correctness=aggregates['correctness_avg'],
        avg_fluency=aggregates['fluency_avg'],
        avg_depth=aggregates['depth_avg'],
        overall_score=aggregates['overall_score'],
        correctness_percentile=percentiles.get('correctness_percentile'),
        fluency_percentile=percentiles.get('fluency_percentile'),
        depth_percentile=percentiles.get('depth_percentile'),
        overall_percentile=percentiles.get('overall_percentile'),
        report_text=narrative_data['report_text'],
        strengths=narrative_data['strengths'],
        areas_for_improvement=narrative_data['improvements'],
        model_used=narrative_data['model_used'],
        generation_version="1.0",
        total_questions=total_questions
    )
    
    db.add(feedback_report)
    await db.flush()  # Get the ID
    
    return feedback_report
