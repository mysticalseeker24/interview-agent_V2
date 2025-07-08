import os
import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o4-mini")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_feedback_report(session_data: dict) -> str:
    """
    Generate a feedback report using OpenAI o4-mini LLM.
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
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": "You are a helpful technical interview coach."},
                  {"role": "user", "content": prompt}],
        max_completion_tokens=500
    )
    return response.choices[0].message.content.strip()
