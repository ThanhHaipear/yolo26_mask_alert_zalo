import { useState } from 'react'

import { predictImage } from './api'
import DetectionList from './components/DetectionList'
import ImageUploader from './components/ImageUploader'
import ResultPanel from './components/ResultPanel'
import StatusMessage from './components/StatusMessage'
import WebcamMonitor from './components/WebcamMonitor'

export default function App() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [realtimeStatus, setRealtimeStatus] = useState('Realtime monitor is idle.')

  const handleFileSelect = (selectedFile, nextPreviewUrl) => {
    setFile(selectedFile)
    setPreviewUrl(nextPreviewUrl)
    setResult(null)
    setError('')
  }

  const handleRealtimeResult = (data) => {
    setResult(data)
    setError('')
    setRealtimeStatus(
      data?.backend_connected
        ? `Backend connected. Last response: ${data.message}`
        : 'Waiting for backend response...',
    )
  }

  const handleSubmit = async () => {
    if (!file) {
      setError('Please choose an image before sending it to the backend.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const data = await predictImage(file)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Request failed. Please try again.')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-shell">
      <main className="page-content">
        <section className="hero">
          <div className="hero-copy-block">
            <p className="eyebrow">Mask Detection Console</p>
            <h1>Monitor webcam violations in one place and fall back to manual image checks when needed.</h1>
            <p className="hero-copy">
              Realtime monitoring is the primary workflow. The backend tracks continuous violations, returns
              detections, and can trigger Zalo alerts after the configured threshold.
            </p>
          </div>

          <div className="hero-status-grid">
            <article className="hero-status-card">
              <span className="hero-status-label">Realtime Status</span>
              <strong>{realtimeStatus}</strong>
            </article>
            <article className="hero-status-card">
              <span className="hero-status-label">Latest Mode</span>
              <strong>{result?.mode ?? 'idle'}</strong>
            </article>
            <article className="hero-status-card">
              <span className="hero-status-label">Violations</span>
              <strong>{result?.violation_count ?? 0}</strong>
            </article>
            <article className="hero-status-card">
              <span className="hero-status-label">Zalo Alert</span>
              <strong>{typeof result?.zalo_sent === 'boolean' ? (result.zalo_sent ? 'sent' : 'not sent') : 'idle'}</strong>
            </article>
          </div>
        </section>

        <section className="workspace workspace-primary">
          <div className="monitor-column">
            <WebcamMonitor onResult={handleRealtimeResult} onError={setError} onStatusChange={setRealtimeStatus} />
          </div>

          <div className="insight-column">
            <StatusMessage error={error} loading={loading} message={result?.message} success={result?.success} />
            <ResultPanel result={result} />
            <DetectionList detections={result?.detections || []} />
          </div>
        </section>

        <section className="workspace workspace-secondary">
          <div className="upload-column">
            <ImageUploader
              file={file}
              previewUrl={previewUrl}
              loading={loading}
              onFileSelect={handleFileSelect}
              onSubmit={handleSubmit}
            />
          </div>
          <section className="panel workflow-panel">
            <div className="panel-header">
              <h2>How To Use</h2>
              <p>Use the webcam for live monitoring. Keep manual upload for one-off checks and debugging.</p>
            </div>

            <div className="workflow-list">
              <article className="workflow-step">
                <span className="workflow-index">1</span>
                <div>
                  <strong>Open the webcam feed</strong>
                  <p>Choose the correct camera source, then start realtime monitoring.</p>
                </div>
              </article>
              <article className="workflow-step">
                <span className="workflow-index">2</span>
                <div>
                  <strong>Watch the detection state</strong>
                  <p>Violations, active seconds, and alert state update from backend responses.</p>
                </div>
              </article>
              <article className="workflow-step">
                <span className="workflow-index">3</span>
                <div>
                  <strong>Use upload only when needed</strong>
                  <p>Manual image checks are useful for model validation and edge-case debugging.</p>
                </div>
              </article>
            </div>
          </section>
        </section>
      </main>
    </div>
  )
}
