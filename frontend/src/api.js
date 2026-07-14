/**
 * api.js
 * Single file containing all backend API calls.
 * Every page imports functions from here instead of calling axios directly —
 * keeps API logic centralized and easy to update if the backend URL changes.
 */

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL

const api = axios.create({
  baseURL: API_URL,
})

// ---------- AUTH ----------

export const loginUser = async (name, email) => {
  const response = await api.post('/api/login', { name, email })
  return response.data
}

// ---------- DASHBOARD ----------

export const getDashboard = async (userId) => {
  const response = await api.get(`/api/dashboard/${userId}`)
  return response.data
}

// ---------- INTERVIEW FLOW ----------

export const startInterview = async (userId, interviewType, resumeText) => {
  const response = await api.post('/api/interview/start', {
    user_id: userId,
    interview_type: interviewType,
    resume_text: resumeText || null,
  })
  return response.data
}

export const submitAnswer = async ({ sessionId, questionId, questionNumber, audioBlob, faceImageBlobs }) => {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  formData.append('question_id', questionId)
  formData.append('question_number', questionNumber)
  formData.append('audio', audioBlob, 'answer.webm')

  faceImageBlobs.forEach((blob, idx) => {
    formData.append('face_images', blob, `frame_${idx}.jpg`)
  })

  const response = await api.post('/api/interview/submit-answer', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

// ---------- REPORT ----------

export const getReport = async (sessionId) => {
  const response = await api.get(`/api/interview/report/${sessionId}`)
  return response.data
}

// ---------- HISTORY ----------

export const getHistory = async (userId) => {
  const response = await api.get(`/api/interview/history/${userId}`)
  return response.data
}

export default api
