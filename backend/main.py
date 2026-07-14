"""
main.py
The core FastAPI application. Wires together database, AI, speech, and face services
into a small set of REST API endpoints. Kept as a single file since the project is small
and this makes the whole request flow easy to read top-to-bottom.
"""

import os
import json
import shutil
import tempfile
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_connection, get_timestamp
from models import (
    LoginRequest, LoginResponse,
    StartInterviewRequest, StartInterviewResponse,
    NextQuestionResponse,
    ScoreReport, DashboardResponse, HistoryItem,
)
from ai_service import generate_question, evaluate_answer, generate_final_report, TOTAL_QUESTIONS
from speech_service import transcribe_audio, analyze_voice
from face_service import analyze_face


app = FastAPI(title="AI-Based Multimodal Interview Practice System")

# Allow the Vercel-hosted frontend to call this API.
# In production, replace "*" with your actual Vercel URL for tighter security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# =========================================================
# 1. LOGIN
# =========================================================

@app.post("/api/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Simple email-based login — no password, no auth provider.
    If the email already exists, log the user in.
    If not, create a new user record.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (request.email,))
    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (name, email, created_at) VALUES (?, ?, ?)",
            (request.name, request.email, get_timestamp()),
        )
        conn.commit()
        user_id = cursor.lastrowid
        name = request.name
    else:
        user_id = user["id"]
        name = user["name"]

    conn.close()
    return LoginResponse(id=user_id, name=name, email=request.email)


# =========================================================
# 2. DASHBOARD
# =========================================================

@app.get("/api/dashboard/{user_id}", response_model=DashboardResponse)
def get_dashboard(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.overall_score, sess.interview_type, sess.created_at
        FROM scores s
        JOIN interview_sessions sess ON s.session_id = sess.id
        WHERE sess.user_id = ?
        ORDER BY sess.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    total_interviews = len(rows)
    average_score = round(sum(r["overall_score"] for r in rows) / total_interviews, 1) if total_interviews > 0 else 0.0

    recent_interviews = [
        {
            "interview_type": r["interview_type"],
            "overall_score": r["overall_score"],
            "created_at": r["created_at"],
        }
        for r in rows[:5]  # only the 5 most recent
    ]

    return DashboardResponse(
        total_interviews=total_interviews,
        average_score=average_score,
        recent_interviews=recent_interviews,
    )


# =========================================================
# 3. START INTERVIEW
# =========================================================

@app.post("/api/interview/start", response_model=StartInterviewResponse)
def start_interview(request: StartInterviewRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO interview_sessions (user_id, interview_type, resume_text, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (request.user_id, request.interview_type, request.resume_text, "in_progress", get_timestamp()),
    )
    conn.commit()
    session_id = cursor.lastrowid

    # Generate the first question (no previous Q&A yet)
    question_text = generate_question(
        interview_type=request.interview_type,
        resume_text=request.resume_text or "",
        previous_qna=[],
        question_number=1,
    )

    cursor.execute(
        "INSERT INTO questions (session_id, question_text, question_number, created_at) VALUES (?, ?, ?, ?)",
        (session_id, question_text, 1, get_timestamp()),
    )
    conn.commit()
    question_id = cursor.lastrowid
    conn.close()

    return StartInterviewResponse(
        session_id=session_id,
        first_question=question_text,
        question_id=question_id,
        question_number=1,
    )


# =========================================================
# 4. SUBMIT ANSWER (audio + face snapshots) -> returns next question OR final report
# =========================================================

@app.post("/api/interview/submit-answer")
async def submit_answer(
    session_id: int = Form(...),
    question_id: int = Form(...),
    question_number: int = Form(...),
    audio: UploadFile = File(...),
    face_images: List[UploadFile] = File(default=[]),
):
    """
    Accepts:
    - The recorded answer audio (single file)
    - A few webcam snapshot images taken during the answer
    Processes them through speech + face services, evaluates the answer with AI,
    stores everything, then either returns the NEXT question or triggers the FINAL REPORT
    if this was the last question.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # --- Save uploaded audio to a temp file for Whisper processing ---
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "answer_audio.webm")
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    # --- Save uploaded face snapshots to temp files ---
    image_paths = []
    for idx, img in enumerate(face_images):
        img_path = os.path.join(temp_dir, f"frame_{idx}.jpg")
        with open(img_path, "wb") as f:
            shutil.copyfileobj(img.file, f)
        image_paths.append(img_path)

    try:
        # --- Speech: transcribe + analyze ---
        transcription_result = transcribe_audio(audio_path)
        answer_text = transcription_result["text"]
        voice_metrics = analyze_voice(transcription_result)

        # --- Face: analyze snapshots ---
        face_metrics = analyze_face(image_paths)

        # --- Fetch question text and interview type for AI evaluation ---
        cursor.execute("SELECT question_text FROM questions WHERE id = ?", (question_id,))
        question_row = cursor.fetchone()
        question_text = question_row["question_text"]

        cursor.execute("SELECT interview_type FROM interview_sessions WHERE id = ?", (session_id,))
        session_row = cursor.fetchone()
        interview_type = session_row["interview_type"]

        # --- AI evaluation of this specific answer ---
        eval_result = evaluate_answer(question_text, answer_text, interview_type)

        # --- Save answer + metrics to DB ---
        cursor.execute(
            """INSERT INTO answers (question_id, answer_text, voice_metrics, face_metrics, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (question_id, answer_text, json.dumps(voice_metrics), json.dumps(face_metrics), get_timestamp()),
        )
        conn.commit()

    finally:
        # Clean up temp files regardless of success/failure
        shutil.rmtree(temp_dir, ignore_errors=True)

    # --- Decide: next question, or final report? ---
    if question_number >= TOTAL_QUESTIONS:
        report = _generate_and_save_report(session_id, interview_type, cursor, conn)
        conn.close()
        return {"is_complete": True, "report": report}

    # --- Otherwise generate the next question, using all previous Q&A as context ---
    cursor.execute("""
        SELECT q.question_text as question, a.answer_text as answer
        FROM questions q JOIN answers a ON q.id = a.question_id
        WHERE q.session_id = ? ORDER BY q.question_number
    """, (session_id,))
    previous_qna = [dict(row) for row in cursor.fetchall()]

    next_question_number = question_number + 1
    next_question_text = generate_question(
        interview_type=interview_type,
        resume_text="",
        previous_qna=previous_qna,
        question_number=next_question_number,
    )

    cursor.execute(
        "INSERT INTO questions (session_id, question_text, question_number, created_at) VALUES (?, ?, ?, ?)",
        (session_id, next_question_text, next_question_number, get_timestamp()),
    )
    conn.commit()
    next_question_id = cursor.lastrowid
    conn.close()

    return {
        "is_complete": False,
        "next_question": {
            "question_id": next_question_id,
            "question_text": next_question_text,
            "question_number": next_question_number,
        },
    }


def _generate_and_save_report(session_id: int, interview_type: str, cursor, conn) -> dict:
    """
    Internal helper: builds the full transcript with scores, asks the AI for a final
    report, saves it, and marks the session as completed.
    """
    cursor.execute("""
        SELECT q.question_text as question, a.answer_text as answer, a.id as answer_id
        FROM questions q JOIN answers a ON q.id = a.question_id
        WHERE q.session_id = ? ORDER BY q.question_number
    """, (session_id,))
    qna_rows = [dict(row) for row in cursor.fetchall()]

    # Re-evaluate each answer to build the scored transcript for the final report.
    # (In submit_answer we already evaluated each one — for simplicity here we
    # re-run evaluate_answer so this helper stays self-contained.)
    qna_with_scores = []
    for row in qna_rows:
        eval_result = evaluate_answer(row["question"], row["answer"], interview_type)
        qna_with_scores.append({
            "question": row["question"],
