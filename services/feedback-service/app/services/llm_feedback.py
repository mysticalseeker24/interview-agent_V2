import os
import requests
import logging
from fastapi import FastAPI, APIRouter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BLACKBOX_API_KEY = os.getenv("BLACKBOX_API_KEY")
if not BLACKBOX_API_KEY:
    logging.error("BLACKBOX_API_KEY is not set in the environment variables.")
    raise ValueError("Missing API key for Blackbox AI.")

BLACKBOX_MODEL = os.getenv("BLACKBOX_MODEL", "blackboxai/openai/o4-mini")
BLACKBOX_API_URL = "https://api.blackbox.ai/chat/completions"

app = FastAPI()
router = APIRouter()

@router.get("/health")
def health_check():
    """
    Standardized health check endpoint.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy"}

app.include_router(router)

def generate_feedback_report(session_data: dict) -> str:
    """
    Generate a feedback report using Blackbox AI.
    Args:
        session_data (dict): Contains candidate answers, scores, and metadata.
    Returns:
        str: AI-generated feedback report text.
    """
    prompt = f"""
    You are an expert technical interviewer. Given the following session data, generate a detailed feedback report for the candidate. Highlight strengths, areas for improvement, and provide actionable recommendations.

    Session Data:
    {session_data}

    Feedback Report:
    """
    headers = {
        "Authorization": f"Bearer {BLACKBOX_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": BLACKBOX_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful technical interview coach."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    try:
        logging.info("Sending request to Blackbox AI API.")
        resp = requests.post(BLACKBOX_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        report = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if not report:
            logging.warning("Blackbox AI returned an empty response.")
            report = "[Blackbox AI returned an empty response.]"
        logging.info("Feedback report generated successfully.")
        return report
    except Exception as e:
        logging.error(f"Blackbox AI API error: {e}")
        return f"[Blackbox AI API error: {e}]"
