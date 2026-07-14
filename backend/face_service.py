"""
face_service.py
Handles face analysis using OpenCV + MediaPipe FaceLandmarker (Tasks API).

Note: Newer mediapipe versions (0.10.30+) removed the older mp.solutions.face_mesh
API and replaced it with the Tasks API (mp.tasks.vision.FaceLandmarker). This file
uses that newer API. It downloads a small pretrained face landmark model file the
first time it runs (cached in a temp folder), then uses it for all further requests.

Approach: The frontend captures a few snapshot frames (e.g. every 2-3 seconds)
from the webcam while the user is answering — NOT continuous video recording.
Each frame is analyzed individually, then results are averaged into one final
face metric per answer.

Metrics are computed using simple, explainable geometry rules on facial landmarks
(distances/ratios) rather than a trained deep-learning emotion classifier —
easy to explain in a project viva.
"""

import os
import tempfile
import urllib.request

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# --- Model setup ---
# The Tasks API needs a small model file (.task). We download it once and cache
# it in the system temp folder, instead of bundling it in the repo (keeps the
# repo small and avoids committing binary files).
MODEL_PATH = os.path.join(tempfile.gettempdir(), "face_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)

# Key landmark indices used from MediaPipe's 468-point face mesh
# (same indices work in both the old and new MediaPipe APIs)
MOUTH_LEFT = 61
MOUTH_RIGHT = 291
MOUTH_TOP = 13
MOUTH_BOTTOM = 14
NOSE_TIP = 1
LEFT_EYE_OUTER = 33
RIGHT_EYE_OUTER = 263

_landmarker = None  # cached singleton, created on first use


def _ensure_model_downloaded():
    """
    Downloads the face landmark model file if it isn't already cached locally.
    If a previous download attempt left a partial/corrupt file, it is removed
    and re-downloaded.
    """
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
        return
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    except Exception as e:
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        raise RuntimeError(
            "Could not download the face landmark model. "
            "Check that the server has internet access. Original error: " + str(e)
        )


def _get_landmarker():
    """
    Returns a cached FaceLandmarker instance, creating it on first call.
    Reusing one instance across requests avoids reloading the model every time.
    """
    global _landmarker
    if _landmarker is None:
        _ensure_model_downloaded()
        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1,
            min_face_detection_confidence=0.5,
            running_mode=vision.RunningMode.IMAGE,
        )
        _landmarker = vision.FaceLandmarker.create_from_options(options)
    return _landmarker


def _landmark_xy(landmarks, index, image_w, image_h):
    lm = landmarks[index]
    return np.array([lm.x * image_w, lm.y * image_h])


def _analyze_single_frame(image_path: str, landmarker) -> dict:
    """
    Runs FaceLandmarker on a single image and returns raw geometric measurements.
    Returns None if no face is detected in the frame.
    """
    image = cv2.imread(image_path)
    if image is None:
        return None

    h, w = image.shape[:2]
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

    result = landmarker.detect(mp_image)

    if not result.face_landmarks:
        return None

    landmarks = result.face_landmarks[0]  # first detected face

    # --- Smile detection: mouth width-to-face-width ratio ---
    mouth_left = _landmark_xy(landmarks, MOUTH_LEFT, w, h)
    mouth_right = _landmark_xy(landmarks, MOUTH_RIGHT, w, h)
    mouth_top = _landmark_xy(landmarks, MOUTH_TOP, w, h)
    mouth_bottom = _landmark_xy(landmarks, MOUTH_BOTTOM, w, h)
    face_left = _landmark_xy(landmarks, LEFT_EYE_OUTER, w, h)
    face_right = _landmark_xy(landmarks, RIGHT_EYE_OUTER, w, h)

    mouth_width = np.linalg.norm(mouth_right - mouth_left)
    mouth_open = np.linalg.norm(mouth_bottom - mouth_top)
    face_width = np.linalg.norm(face_right - face_left)

    smile_ratio = mouth_width / face_width if face_width > 0 else 0
    is_smiling = smile_ratio > 0.45 and mouth_open < (mouth_width * 0.5)

    # --- Eye contact estimation: nose position relative to eye-line center ---
    nose = _landmark_xy(landmarks, NOSE_TIP, w, h)
    eye_center = (face_left + face_right) / 2
    horizontal_offset = abs(nose[0] - eye_center[0]) / face_width if face_width > 0 else 1

    looking_at_camera = horizontal_offset < 0.15

    return {
        "is_smiling": is_smiling,
        "looking_at_camera": looking_at_camera,
    }


def analyze_face(image_paths: list) -> dict:
    """
    Takes a list of snapshot image file paths (captured during one answer),
    runs face analysis on each, and aggregates into final metrics.
    """
    if not image_paths:
        return {
            "eye_contact": 0.0,
            "smile_percentage": 0.0,
            "dominant_emotion": "Not Detected",
            "confidence": 0.0,
        }

    landmarker = _get_landmarker()
    frame_results = []

    for path in image_paths:
        result = _analyze_single_frame(path, landmarker)
        if result:
            frame_results.append(result)

    total_frames = len(image_paths)
    detected_frames = len(frame_results)

    if detected_frames == 0:
        return {
            "eye_contact": 0.0,
            "smile_percentage": 0.0,
            "dominant_emotion": "Face Not Detected",
            "confidence": 3.0,
        }

    smiling_count = sum(1 for r in frame_results if r["is_smiling"])
    looking_count = sum(1 for r in frame_results if r["looking_at_camera"])

    eye_contact_percentage = round((looking_count / detected_frames) * 100, 1)
    smile_percentage = round((smiling_count / detected_frames) * 100, 1)

    if smile_percentage > 50:
        dominant_emotion = "Happy / Positive"
    elif eye_contact_percentage < 40:
        dominant_emotion = "Nervous / Distracted"
    else:
        dominant_emotion = "Neutral / Focused"

    detection_rate = detected_frames / total_frames
    confidence = (eye_contact_percentage / 100 * 6) + (detection_rate * 4)
    confidence = round(min(confidence, 10.0), 1)

    return {
        "eye_contact": eye_contact_percentage,
        "smile_percentage": smile_percentage,
        "dominant_emotion": dominant_emotion,
        "confidence": confidence,
    }
