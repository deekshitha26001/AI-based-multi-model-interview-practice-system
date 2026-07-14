# AI-Based Multimodal Interview Practice System

A final year B.E. AI & ML project that simulates a mock interview using AI-generated
questions, speech analysis, and face analysis to provide candidates with a scored,
detailed feedback report.

---

## Tech Stack

**Frontend:** React + Vite + Tailwind CSS
**Backend:** Python + FastAPI
**Database:** SQLite
**AI (Question Generation + Evaluation):** Groq API (Llama 3.3 70B) — free tier
**Speech Recognition:** Groq Whisper API (whisper-large-v3) — free tier
**Face Detection:** OpenCV + MediaPipe

> Note: The original spec mentioned the OpenAI API/Whisper API. This project uses
> **Groq's API instead**, since it is free, has no credit card requirement, and is
> fully compatible with the same request/response pattern — ideal for a student project
> with no budget. The Groq Python SDK is used the same way the OpenAI SDK would be.

---

## Project Structure
