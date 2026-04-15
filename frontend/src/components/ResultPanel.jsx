export default function ResultPanel({ result }) {
  if (!result) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2>Result Summary</h2>
          <p>The backend response will appear here after a successful request.</p>
        </div>
      </section>
    )
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Result Summary</h2>
        <p>Review the returned violation count, message, and delivery status.</p>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span className="stat-label">Success</span>
          <strong>{String(result.success)}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Violations</span>
          <strong>{result.violation_count}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Zalo Sent</span>
          <strong>{String(result.zalo_sent)}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Alert ID</span>
          <strong>{result.alert_id ?? 'N/A'}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Mode</span>
          <strong>{result.mode ?? 'image'}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Active Seconds</span>
          <strong>{result.active_violation_seconds ?? 'N/A'}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Threshold</span>
          <strong>{result.threshold_seconds ?? 'N/A'}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Alert Armed</span>
          <strong>{typeof result.alert_armed === 'boolean' ? String(result.alert_armed) : 'N/A'}</strong>
        </article>
      </div>

      <div className="result-message-block">
        <span className="stat-label">Backend Message</span>
        <p>{result.message}</p>
      </div>

      {result.image_url ? (
        <div className="result-link-block">
          <span className="stat-label">Stored Image URL</span>
          <a href={result.image_url} target="_blank" rel="noreferrer">
            {result.image_url}
          </a>
        </div>
      ) : null}
    </section>
  )
}
