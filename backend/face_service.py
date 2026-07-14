"""
face_service.py
Handles face analysis using OpenCV + MediaPipe Face Mesh.

Approach: The frontend captures a few snapshot frames (e.g. every 2-3 seconds)
from the webcam while the user is answering — NOT continuous video recording.
This keeps bandwidth low and processing simple. Each frame is analyzed individually,
then results are averaged into one final face metric per answer.

Metrics are computed using simple, explainable geometry rules on facial landmarks
(distances/ratios) rather than a trained deep-learning emotion classifier —
consistent with the rule-based approach used in speech_service.py, and much
easier to explain in a project viva.
"""

import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh

# Key landmark indices used from MediaPipe's 468-point face mesh
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH_LEFT = 61
MOUTH_RIGHT = 291
MOUTH_TOP = 13
MOUTH_BOTTOM = 14
NOSE_TIP = 1
LEFT_EYE_OUTER = 33
RIGHT_EYE_OUTER = 263


def _landmark_xy(landmarks, index, image_w, image_h):
    lm = landmarks[index]
    return np.array([lm.x * image_w, lm.y * image_h])


def _analyze_single_frame(image_path: str, face_mesh) -> dict:
    """
    Runs MediaPipe Face Mesh on a single image and returns raw geometric measurements.
    Returns None if no face is detected in the frame.
    """
    image = cv2.imread(image_path)
    if image is None:
        return None

    h, w = image.shape[:2]
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)

    if not results.multi_face_landmarks:
        return None

    landmarks = results.multi_face_landmarks[0].landmark

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
    # If nose tip is roughly centered between the eyes horizontally, user is facing camera
    nose = _landmark_xy(landmarks, NOSE_TIP, w, h)
    eye_center = (face_left + face_right) / 2
    horizontal_offset = abs(nose[0] - eye_center[0]) / face_width if face_width > 0 else 1

    looking_at_camera = horizontal_offset < 0.15  # small offset = facing forward

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

    frame_results = []

    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    ) as face_mesh:
        for path in image_paths:
            result = _analyze_single_frame(path, face_mesh)
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

    # --- Dominant emotion (simple rule based on smile + eye contact) ---
    if smile_percentage > 50:
        dominant_emotion = "Happy / Positive"
    elif eye_contact_percentage < 40:
        dominant_emotion = "Nervous / Distracted"
    else:
        dominant_emotion = "Neutral / Focused"

    # --- Confidence score: combination of eye contact + face detection consistency ---
    detection_rate = detected_frames / total_frames
    confidence = (eye_contact_percentage / 100 * 6) + (detection_rate * 4)
    confidence = round(min(confidence, 10.0), 1)

    return {
        "eye_contact": eye_contact_percentage,
        "smile_percentage": smile_percentage,
        "dominant_emotion": dominant_emotion,
        "confidence": confidence,
    }
