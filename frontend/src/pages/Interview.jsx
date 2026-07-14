import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar.jsx'
import { startInterview, submitAnswer } from '../api.js'

/**
 * Interview.jsx
 * Handles the full interview flow:
 * 1. Setup screen: choose interview type + optional resume text
 * 2. Interview screen: shows one question at a time, records mic audio +
 *    periodic webcam snapshots while the user answers
 * 3. On last question, redirects to the Report page
 */
function Interview() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)

  // Setup state
  const [stage, setStage] = useState('setup') // 'setup' | 'interview'
  const [interviewType, setInterviewType] = useState('HR')
  const [resumeText, setResumeText] = useState('')
  const [setupError, setSetupError] = useState('')
  const [starting, setStarting] = useState(false)

  // Interview state
  const [sessionId, setSessionId] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null) // { question_id, question_text, question_number }
  const [isRecording, setIsRecording] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [interviewError, setInterviewError] = useState('')

  // Media refs
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const snapshotIntervalRef = useRef(null)
  const capturedFramesRef = useRef([])

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      navigate('/')
      return
    }
    setUser(JSON.parse(storedUser))

    // Cleanup camera/mic on unmount
    return () => stopMediaStream()
  }, [])

  // ---------- SETUP: Start Interview ----------

  const handleStartInterview = async () => {
    setSetupError('')
    setStarting(true)
    try {
      const storedUser = JSON.parse(localStorage.getItem('user'))
      const data = await startInterview(storedUser.id, interviewType, resumeText)
      setSessionId(data.session_id)
      setCurrentQuestion({
        question_id: data.question_id,
        question_text: data.first_question,
        question_number: data.question_number,
      })
      setStage('interview')
      await setupMediaStream()
    } catch (err) {
      setSetupError('Could not start interview. Please try again.')
    } finally {
      setStarting(false)
    }
  }

  // ---------- MEDIA: Camera + Mic Setup ----------

  const setupMediaStream = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch (err) {
      setInterviewError('Camera/Microphone access is required. Please allow permissions and refresh.')
    }
  }

  const stopMediaStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
    }
    if (snapshotIntervalRef.current) {
      clearInterval(snapshotIntervalRef.current)
    }
  }

  // ---------- RECORDING: Start ----------

  const handleStartRecording = () => {
    if (!streamRef.current) return
    setInterviewError('')
    audioChunksRef.current = []
    capturedFramesRef.current = []

    // Audio recording
    const audioOnlyStream = new MediaStream(streamRef.current.getAudioTracks())
    const recorder = new MediaRecorder(audioOnlyStream)
    recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data)
    recorder.start()
    mediaRecorderRef.current = recorder

    // Capture a webcam snapshot every 2.5 seconds while recording
    snapshotIntervalRef.current = setInterval(() => {
      captureSnapshot()
    }, 2500)

    setIsRecording(true)
  }

  const captureSnapshot = () => {
    if (!videoRef.current) return
    const canvas = document.createElement('canvas')
    canvas.width = videoRef.current.videoWidth
    canvas.height = videoRef.current.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height)
    canvas.toBlob((blob) => {
      if (blob) capturedFramesRef.current.push(blob)
    }, 'image/jpeg', 0.8)
  }

  // ---------- RECORDING: Stop + Submit ----------

  const handleStopAndSubmit = async () => {
    if (!mediaRecorderRef.current) return

    setIsRecording(false)
    clearInterval(snapshotIntervalRef.current)

    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
      setIsSubmitting(true)
      setInterviewError('')

      try {
        const result = await submitAnswer({
          sessionId,
          questionId: currentQuestion.question_id,
          questionNumber: currentQuestion.question_number,
          audioBlob,
          faceImageBlobs: capturedFramesRef.current,
        })

        if (result.is_complete) {
          stopMediaStream()
          navigate(`/report/${sessionId}`)
        } else {
          setCurrentQuestion({
            question_id: result.next_question.question_id,
            question_text: result.next_question.question_text,
            question_number: result.next_question.question_number,
          })
        }
      } catch (err) {
        setInterviewError('Failed to submit your answer. Please try recording again.')
      } finally {
        setIsSubmitting(false)
      }
    }

    mediaRecorderRef.current.stop()
  }

  // ---------- RENDER: Setup Screen ----------

  if (stage === 'setup') {
    return (
      <div className="min-h-screen bg-offwhite px-6 py-6 max-w-3xl mx-auto">
        <Navbar />
        <div className="app-card">
          <h2 className="text-xl font-semibold text-brown-dark mb-4">
            Set Up Your Interview
          </h2>

          <label className="block text-sm font-medium text-brown-dark mb-1">
            Interview Type
          </label>
          <select
            value={interviewType}
            onChange={(e) => setInterviewType(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-brown"
          >
            <option value="HR">HR Interview</option>
            <option value="Technical">Technical Interview</option>
            <option value="Behavioral">Behavioral Interview</option>
          </select>

          <label className="block text-sm font-medium text-brown-dark mb-1">
            Resume Text (Optional)
          </label>
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste a short summary of your resume/skills here (optional)..."
            rows={5}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-brown"
          />

          {setupError && <p className="text-red-600 text-sm mb-4">{setupError}</p>}

          <button className="btn-primary w-full" disabled={starting} onClick={handleStartInterview}>
            {starting ? 'Starting...' : 'Begin Interview'}
          </button>
        </div>
      </div>
    )
  }

  // ---------- RENDER: Interview Screen ----------

  return (
    <div className="min-h-screen bg-offwhite px-6 py-6 max-w-3xl mx-auto">
      <Navbar />

      <div className="app-card mb-4">
        <p className="text-xs text-gray-500 mb-1">
          Question {currentQuestion?.question_number} of 5 — {interviewType} Interview
        </p>
        <h2 className="text-lg font-semibold text-brown-dark">
          {currentQuestion?.question_text}
        </h2>
      </div>

      <div className="app-card mb-4">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full rounded-lg bg-black"
          style={{ maxHeight: '360px', objectFit: 'cover' }}
        />
      </div>

      {interviewError && <p className="text-red-600 text-sm mb-4">{interviewError}</p>}

      <div className="app-card flex flex-col items-center gap-3">
        {!isRecording && !isSubmitting && (
          <button className="btn-primary w-full" onClick={handleStartRecording}>
            Start Answer
          </button>
        )}

        {isRecording && (
          <button
            className="btn-primary w-full bg-red-700 hover:bg-red-800"
            onClick={handleStopAndSubmit}
          >
            Stop & Submit Answer
          </button>
        )}

        {isSubmitting && (
          <p className="text-brown-dark text-sm">
            Analyzing your answer... this may take a few seconds.
          </p>
        )}
      </div>
    </div>
  )
}

export default Interview
