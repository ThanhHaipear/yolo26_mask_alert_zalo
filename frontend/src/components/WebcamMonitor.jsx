import { useEffect, useRef, useState } from 'react'

import { getApiUrl, predictFrame } from '../api'

const FRAME_INTERVAL_MS = 300

function createSessionId() {
  return `session-${Math.random().toString(36).slice(2, 10)}`
}

function waitForVideoReady(video) {
  return new Promise((resolve, reject) => {
    let settled = false

    const cleanup = () => {
      video.removeEventListener('loadedmetadata', handleReady)
      video.removeEventListener('canplay', handleReady)
      clearTimeout(timeoutId)
    }

    const finish = (callback) => {
      if (settled) return
      settled = true
      cleanup()
      callback()
    }

    const handleReady = () => {
      if (video.videoWidth > 0 && video.videoHeight > 0) {
        finish(resolve)
      }
    }

    const timeoutId = setTimeout(() => {
      finish(() => reject(new Error('Camera stream was received but the video preview did not become ready.')))
    }, 8000)

    video.addEventListener('loadedmetadata', handleReady)
    video.addEventListener('canplay', handleReady)
    handleReady()
  })
}

function dataUrlToBlob(dataUrl) {
  const [meta, base64] = dataUrl.split(',')
  const mimeMatch = meta.match(/data:(.*?);base64/)
  const mime = mimeMatch ? mimeMatch[1] : 'image/jpeg'
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return new Blob([bytes], { type: mime })
}

export default function WebcamMonitor({ onResult, onError, onStatusChange }) {
  const videoRef = useRef(null)
  const captureCanvasRef = useRef(null)
  const overlayCanvasRef = useRef(null)
  const timerRef = useRef(null)
  const streamRef = useRef(null)
  const sendingRef = useRef(false)
  const videoReadyRef = useRef(false)
  const framesSentRef = useRef(0)
  const sessionIdRef = useRef(createSessionId())
  const [isRunning, setIsRunning] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [statusText, setStatusText] = useState('Camera is idle.')
  const [videoReady, setVideoReady] = useState(false)
  const [devices, setDevices] = useState([])
  const [selectedDeviceId, setSelectedDeviceId] = useState('')
  const [framesSent, setFramesSent] = useState(0)

  const loadDevices = async () => {
    if (!navigator.mediaDevices?.enumerateDevices) {
      return
    }

    const allDevices = await navigator.mediaDevices.enumerateDevices()
    const videoInputs = allDevices.filter((device) => device.kind === 'videoinput')
    setDevices(videoInputs)

    if (!selectedDeviceId && videoInputs.length > 0) {
      const preferred =
        videoInputs.find((device) => !/iriun|droidcam|obs|virtual|snap/i.test(device.label)) || videoInputs[0]
      setSelectedDeviceId(preferred.deviceId)
    }
  }

  const stopWebcam = () => {
    setIsRunning(false)
    setVideoReady(false)
    videoReadyRef.current = false
    setStatusText('Camera stopped.')
    onStatusChange?.('Realtime monitor stopped.')
    sendingRef.current = false
    framesSentRef.current = 0

    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }

    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) {
        track.stop()
      }
      streamRef.current = null
    }

    if (videoRef.current) {
      videoRef.current.pause()
      videoRef.current.srcObject = null
    }

    const overlayCanvas = overlayCanvasRef.current
    if (overlayCanvas) {
      const overlayContext = overlayCanvas.getContext('2d')
      overlayContext?.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height)
    }
  }

  const drawOverlay = (detections = []) => {
    const video = videoRef.current
    const overlayCanvas = overlayCanvasRef.current
    if (!video || !overlayCanvas) {
      return
    }

    const width = video.videoWidth || video.clientWidth
    const height = video.videoHeight || video.clientHeight
    if (!width || !height) {
      return
    }

    overlayCanvas.width = width
    overlayCanvas.height = height

    const context = overlayCanvas.getContext('2d')
    if (!context) {
      return
    }

    context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height)
    context.lineWidth = 2
    context.font = '16px Segoe UI'
    context.textBaseline = 'top'

    detections.forEach((item) => {
      let color = '#22c55e'
      if (item.class_name === 'without_mask') {
        color = '#ef4444'
      } else if (item.class_name === 'mask_weared_incorrect') {
        color = '#f59e0b'
      }

      const boxWidth = item.x2 - item.x1
      const x = overlayCanvas.width - item.x2
      const y = item.y1
      const w = boxWidth
      const h = item.y2 - item.y1
      const label = `${item.class_name} ${Number(item.confidence).toFixed(2)}`

      context.strokeStyle = color
      context.strokeRect(x, y, w, h)

      const textWidth = context.measureText(label).width
      const textHeight = 20
      context.fillStyle = color
      context.fillRect(x, Math.max(0, y - textHeight - 4), textWidth + 10, textHeight + 4)
      context.fillStyle = '#0b1220'
      context.fillText(label, x + 5, Math.max(0, y - textHeight - 2))
    })
  }

  useEffect(() => {
    void loadDevices()
    return stopWebcam
  }, [])

  const sendFrame = async () => {
    const video = videoRef.current
    const canvas = captureCanvasRef.current
    if (!video || !canvas || !videoReadyRef.current) {
      return
    }

    const width = video.videoWidth || video.clientWidth
    const height = video.videoHeight || video.clientHeight
    if (!width || !height) {
      setStatusText('Camera preview is live, but no video frame is available yet.')
      return
    }

    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) {
      onError('Canvas context is not available.')
      onStatusChange?.('Realtime monitor failed before a frame could be sent.')
      stopWebcam()
      return
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    const dataUrl = canvas.toDataURL('image/jpeg', 0.85)
    const blob = dataUrlToBlob(dataUrl)

    try {
      const nextFrameCount = framesSentRef.current + 1
      const result = await predictFrame(blob, {
        sessionId: sessionIdRef.current,
        cameraName: 'browser-webcam',
        capturedAt: new Date().toISOString(),
      })
      drawOverlay(result?.detections || [])
      framesSentRef.current = nextFrameCount
      setFramesSent(nextFrameCount)
      setStatusText(`Camera preview is active. Backend responded to ${nextFrameCount} frame(s).`)
      onStatusChange?.(`Backend connected. Last response: ${result.message}`)
      onResult(result)
    } catch (error) {
      onError(error.message || 'Realtime request failed')
      setStatusText('Realtime streaming stopped because a backend request failed.')
      onStatusChange?.('Backend request failed during realtime monitoring.')
      stopWebcam()
    }
  }

  const scheduleNextFrame = () => {
    if (!sendingRef.current) return
    timerRef.current = setTimeout(async () => {
      if (!sendingRef.current) return
      await sendFrame()
      scheduleNextFrame()
    }, FRAME_INTERVAL_MS)
  }

  const startWebcam = async () => {
    if (isStarting || isRunning) return

    setIsStarting(true)
    setVideoReady(false)
    videoReadyRef.current = false
    setFramesSent(0)
    framesSentRef.current = 0
    onError('')
    setStatusText('Requesting camera permission...')
    onStatusChange?.('Requesting webcam access...')

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('This browser does not support webcam access.')
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      })

      await loadDevices()

      const video = videoRef.current
      if (!video) {
        throw new Error('Video element is not available.')
      }

      streamRef.current = stream
      video.muted = true
      video.autoplay = true
      video.playsInline = true
      video.srcObject = stream
      setStatusText('Camera permission granted. Waiting for video preview...')
      onStatusChange?.('Camera permission granted. Waiting for local preview...')

      await waitForVideoReady(video)
      await video.play()

      setVideoReady(true)
      videoReadyRef.current = true
      setIsRunning(true)
      sendingRef.current = true
      setStatusText('Camera preview is live. Sending first frame to the backend...')
      onStatusChange?.('Camera preview is live. Sending first frame to the backend...')
      await sendFrame()
      scheduleNextFrame()
    } catch (error) {
      const message =
        error?.name === 'NotAllowedError'
          ? 'Camera permission was denied. Allow camera access in the browser and try again.'
          : error?.name === 'NotFoundError'
            ? 'No camera device was found on this machine.'
            : error.message || 'Could not access webcam'
      onError(message)
      setStatusText('Camera failed to start.')
      onStatusChange?.(`Webcam failed to start: ${message}`)
      stopWebcam()
    } finally {
      setIsStarting(false)
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Realtime Webcam</h2>
        <p>Sample webcam frames for backend detection and trigger an alert after continuous violation.</p>
        <p className="panel-note">API URL: {getApiUrl()}</p>
      </div>

      <label className="camera-select-group" htmlFor="camera-source-select">
        <span className="camera-select-label">Camera Source</span>
        <select
          id="camera-source-select"
          name="camera_source"
          className="camera-select"
          value={selectedDeviceId}
          onChange={(event) => setSelectedDeviceId(event.target.value)}
          disabled={isRunning || isStarting}
        >
          {devices.length === 0 ? <option value="">No camera detected yet</option> : null}
          {devices.map((device, index) => (
            <option key={device.deviceId || `camera-${index}`} value={device.deviceId}>
              {device.label || `Camera ${index + 1}`}
            </option>
          ))}
        </select>
      </label>

      <div className="preview-frame webcam-frame">
        <video ref={videoRef} className="preview-image webcam-video" muted playsInline autoPlay />
        <canvas ref={overlayCanvasRef} className="preview-image webcam-overlay-canvas" />
        {!videoReady ? <div className="webcam-overlay">{statusText}</div> : null}
      </div>

      <canvas ref={captureCanvasRef} className="hidden-canvas" />
      <p className="webcam-status">{statusText}</p>

      <div className="button-row">
        <button type="button" className="primary-button" onClick={startWebcam} disabled={isRunning || isStarting}>
          {isStarting ? 'Starting...' : 'Start Webcam'}
        </button>
        <button type="button" className="secondary-button" onClick={stopWebcam} disabled={!isRunning && !isStarting}>
          Stop Webcam
        </button>
      </div>
    </section>
  )
}
