import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from app.core.database import get_db, AsyncSessionLocal, engine
from app.models.feedback_report import FeedbackReport
from app.models.score import Score
from app.models.base import Base
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from datetime import datetime
from app.services.llm_feedback import generate_feedback_report

app = FastAPI(title="TalentSync Feedback Service")

@app.on_event("startup")
async def startup():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/feedback/", response_model=dict)
async def create_feedback_report(report: dict):
    async with AsyncSessionLocal() as session:
        feedback = FeedbackReport(**report, generated_at=datetime.utcnow())
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return {"id": feedback.id}

@app.get("/feedback/{session_id}", response_model=dict)
async def get_feedback_report(session_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(FeedbackReport).where(FeedbackReport.session_id == session_id))
        feedback = result.scalar_one_or_none()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return {k: getattr(feedback, k) for k in feedback.__table__.columns.keys()}

@app.post("/feedback/generate", response_model=dict)
async def generate_feedback(session_data: dict):
    """
    Generate a feedback report using OpenAI o4-mini LLM and store it.
    If a report for the session_id exists, update it. Otherwise, insert new.
    """
    report_text = generate_feedback_report(session_data)
    async with AsyncSessionLocal() as session:
        # Check if feedback report exists for this session_id
        result = await session.execute(select(FeedbackReport).where(FeedbackReport.session_id == session_data.get("session_id")))
        feedback = result.scalar_one_or_none()
        if feedback:
            # Update existing report
            feedback.avg_correctness = session_data.get("avg_correctness", 0)
            feedback.avg_fluency = session_data.get("avg_fluency", 0)
            feedback.avg_depth = session_data.get("avg_depth", 0)
            feedback.overall_score = session_data.get("overall_score", 0)
            feedback.report_text = report_text
            feedback.strengths = []
            feedback.areas_for_improvement = []
            feedback.recommendations = []
            feedback.generated_at = datetime.utcnow()
            feedback.total_questions = session_data.get("total_questions", 0)
        else:
            feedback = FeedbackReport(
                session_id=session_data.get("session_id"),
                avg_correctness=session_data.get("avg_correctness", 0),
                avg_fluency=session_data.get("avg_fluency", 0),
                avg_depth=session_data.get("avg_depth", 0),
                overall_score=session_data.get("overall_score", 0),
                report_text=report_text,
                strengths=[],
                areas_for_improvement=[],
                recommendations=[],
                generated_at=datetime.utcnow(),
                total_questions=session_data.get("total_questions", 0)
            )
            session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return {"id": feedback.id, "report_text": report_text}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8010))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
