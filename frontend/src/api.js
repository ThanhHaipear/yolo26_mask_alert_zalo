const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function getApiUrl() {
  return API_URL
}

export async function predictImage(file, cameraName = 'frontend-upload') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('camera_name', cameraName)

  const response = await fetch(`${API_URL}/predict`, {
    method: 'POST',
    body: formData,
  })

  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    throw new Error(data?.detail || data?.message || 'Backend request failed')
  }

  return data
}

export async function predictFrame(blob, { sessionId, cameraName = 'browser-webcam', capturedAt }) {
  const formData = new FormData()
  formData.append('file', blob, 'frame.jpg')
  formData.append('session_id', sessionId)
  formData.append('camera_name', cameraName)
  formData.append('captured_at', capturedAt)

  const response = await fetch(`${API_URL}/predict-frame`, {
    method: 'POST',
    body: formData,
  })

  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    throw new Error(data?.detail || data?.message || 'Realtime backend request failed')
  }

  return data
}
