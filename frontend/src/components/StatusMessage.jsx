export default function StatusMessage({ error, loading, message, success }) {
  if (loading) {
    return <section className="status-banner status-loading">The backend is processing your image.</section>
  }

  if (error) {
    return <section className="status-banner status-error">{error}</section>
  }

  if (message) {
    return <section className={`status-banner ${success ? 'status-success' : 'status-neutral'}`}>{message}</section>
  }

  return null
}
