"""
models.py
Pydantic schemas used to validate incoming requests and shape outgoing responses.
Keeping all schemas in one file since the project is small.
"""

from pydantic import BaseModel
from typing import List, Optional


# ---------- AUTH ----------

class LoginRequest(BaseModel):
    name: str
    email: str


class LoginResponse(BaseModel):
    id: int
    name: str
    email: str


# ---------- INTERVIEW SESSION ----------

class StartInterviewRequest(BaseModel):
    user_id: int
    interview_type: str       # "HR" / "Technical" / "Behavioral"
    resume_text: Optional[str] = None


class StartInterviewResponse(BaseModel):
    session_id: int
    first_question: str
    question_id: int
    question_number: int


# ---------- QUESTION FLOW ----------

class NextQuestionRequest(BaseModel):
    session_id: int


class NextQuestionResponse(BaseModel):
    question_id: int
    question_text: str
    question_number: int
    is_last: bool


# ---------- ANSWER SUBMISSION ----------

class AnswerTextRequest(BaseModel):
    """Used when the frontend sends already-transcribed text (fallback / typed answer)."""
    question_id: int
    answer_text: str


class VoiceMetrics(BaseModel):
    clarity: float
    speaking_speed: str        # e.g. "Normal", "Fast", "Slow"
    pauses: int
    confidence: float


class FaceMetrics(BaseModel):
    eye_contact: float
    smile_percentage: float
    dominant_emotion: str
    confidence: float


# ---------- FINAL REPORT ----------

class ScoreReport(BaseModel):
    session_id: int
    overall_score: float
    communication_score: float
    technical_score: float
    confidence_score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


# ---------- DASHBOARD ----------

class DashboardResponse(BaseModel):
    total_interviews: int
    average_score: float
    recent_interviews: List[dict]


# ---------- HISTORY ----------

class HistoryItem(BaseModel):
    session_id: int
    interview_type: str
    overall_score: float
    created_at: str
