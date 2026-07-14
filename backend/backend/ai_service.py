"""
ai_service.py
Handles all AI text tasks using the Groq API (free tier, OpenAI-compatible SDK):
1. Generating interview questions
2. Evaluating a candidate's answer (relevance, grammar, confidence)
3. Generating the final report (strengths, weaknesses, suggestions)
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Free, fast Groq model — good enough for question generation + evaluation
MODEL_NAME = "llama-3.3-70b-versatile"

TOTAL_QUESTIONS = 5  # fixed number of questions per interview, keeps flow simple


def generate_question(interview_type: str, resume_text: str, previous_qna: list, question_number: int) -> str:
    """
    Generates ONE interview question at a time based on interview type
    and (optionally) resume content + previous Q&A for context.
    """
    context = ""
    if resume_text:
        context += f"Candidate resume summary: {resume_text[:800]}\n"

    if previous_qna:
        context += "Previous questions and answers so far:\n"
        for qa in previous_qna:
            context += f"Q: {qa['question']}\nA: {qa['answer']}\n"

    prompt = f"""
You are an interviewer conducting a {interview_type} interview.
This is question number {question_number} out of {TOTAL_QUESTIONS}.

{context}

Generate ONE clear, concise interview question suitable for a {interview_type} interview.
Do not include any explanation, numbering, or extra text — return ONLY the question text.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100,
    )

    return response.choices[0].message.content.strip()


def evaluate_answer(question: str, answer_text: str, interview_type: str) -> dict:
    """
    Evaluates a single answer for relevance, grammar, and confidence.
    Returns a dict with scores (0-10) and a short comment.
    Used to build up scoring context for the final report.
    """
    prompt = f"""
You are evaluating a candidate's answer in a {interview_type} interview.

Question: {question}
Answer: {answer_text}

Evaluate the answer strictly on:
1. Relevance (0-10) - does it answer the question?
2. Grammar (0-10) - language quality
3. Confidence (0-10) - how confidently/clearly it reads

Return ONLY valid JSON in this exact format, no extra text:
{{
  "relevance": <number>,
  "grammar": <number>,
  "confidence": <number>,
  "comment": "<one short sentence feedback>"
}}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()

    # Groq sometimes wraps JSON in ```json fences — strip them if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Safe fallback so one bad AI response doesn't crash the interview
        return {"relevance": 5, "grammar": 5, "confidence": 5, "comment": "Evaluation unavailable."}


def generate_final_report(interview_type: str, qna_with_scores: list) -> dict:
    """
    Takes all questions, answers, and per-answer scores from the session
    and generates the final overall report: scores + strengths + weaknesses + suggestions.
    """
    summary = ""
    for item in qna_with_scores:
        summary += (
            f"Q: {item['question']}\n"
            f"A: {item['answer']}\n"
            f"Scores - Relevance: {item['relevance']}, Grammar: {item['grammar']}, "
            f"Confidence: {item['confidence']}\n\n"
        )

    prompt = f"""
You are preparing a final interview performance report for a {interview_type} interview.

Here is the full interview transcript with per-answer scores:
{summary}

Based on this, generate an overall report.
Return ONLY valid JSON in this exact format, no extra text:
{{
  "overall_score": <number 0-100>,
  "communication_score": <number 0-100>,
  "technical_score": <number 0-100>,
  "confidence_score": <number 0-100>,
  "strengths": ["<point1>", "<point2>"],
  "weaknesses": ["<point1>", "<point2>"],
  "suggestions": ["<point1>", "<point2>"]
}}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: average the per-answer scores if the AI report generation fails
        avg_relevance = sum(i["relevance"] for i in qna_with_scores) / len(qna_with_scores)
        avg_grammar = sum(i["grammar"] for i in qna_with_scores) / len(qna_with_scores)
        avg_confidence = sum(i["confidence"] for i in qna_with_scores) / len(qna_with_scores)
        return {
            "overall_score": round((avg_relevance + avg_grammar + avg_confidence) / 3 * 10, 1),
            "communication_score": round(avg_grammar * 10, 1),
            "technical_score": round(avg_relevance * 10, 1),
            "confidence_score": round(avg_confidence * 10, 1),
            "strengths": ["Completed the interview"],
            "weaknesses": ["Detailed feedback unavailable"],
            "suggestions": ["Try again for more detailed AI feedback"],
        }
