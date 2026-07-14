"""
speech_service.py
Handles voice/audio analysis:
1. Transcribes audio to text using Groq's Whisper API (whisper-large-v3, free tier)
2. Computes simple voice metrics: speaking speed, pauses, clarity, confidence

Note: Deep audio signal analysis (pitch, tone, etc.) needs heavy libraries like librosa,
which are avoided here to keep the project lightweight and deployment-friendly on Render's
free tier. Instead, we derive practical metrics from transcription data (word count, audio
duration, and pause detection from Whisper's segment timestamps).
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def transcribe_audio(audio_file_path: str) -> dict:
    """
    Sends the audio file to Groq's Whisper API and returns the transcription
    along with segment-level timestamps (used later for pause detection).
    """
    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            response_format="verbose_json",  # gives us segments with start/end times
        )

    return {
        "text": transcription.text.strip(),
        "duration": transcription.duration,
        "segments": transcription.segments if hasattr(transcription, "segments") else [],
    }


def analyze_voice(transcription_result: dict) -> dict:
    """
    Computes simple, explainable voice metrics from the transcription result.
    These are intentionally straightforward calculations, not deep audio ML,
    to keep the project understandable for a college-level explanation.
    """
    text = transcription_result["text"]
    duration = transcription_result.get("duration", 0) or 1  # avoid divide-by-zero
    segments = transcription_result.get("segments", [])

    word_count = len(text.split())

    # --- Speaking speed (words per minute) ---
    words_per_minute = round((word_count / duration) * 60, 1) if duration > 0 else 0

    if words_per_minute < 100:
        speaking_speed = "Slow"
    elif words_per_minute > 160:
        speaking_speed = "Fast"
    else:
        speaking_speed = "Normal"

    # --- Pause detection (gaps between segments longer than 1 second) ---
    pauses = 0
    for i in range(1, len(segments)):
        gap = segments[i]["start"] - segments[i - 1]["end"]
        if gap > 1.0:
            pauses += 1

    # --- Clarity score (based on word count vs duration — very short/rambling answers score lower) ---
    if word_count < 10:
        clarity = 4.0
    elif word_count > 150:
        clarity = 7.0
    else:
        clarity = 8.5

    # --- Confidence score (fewer long pauses + normal speed = higher confidence) ---
    confidence = 8.0
    if speaking_speed != "Normal":
        confidence -= 1.5
    if pauses > 3:
        confidence -= 1.5
    confidence = max(confidence, 2.0)  # floor so it never looks unrealistic

    return {
        "clarity": round(clarity, 1),
        "speaking_speed": speaking_speed,
        "words_per_minute": words_per_minute,
        "pauses": pauses,
        "confidence": round(confidence, 1),
    }
