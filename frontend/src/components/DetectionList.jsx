export default function DetectionList({ detections }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Detections</h2>
        <p>Each item below comes directly from the backend response.</p>
      </div>

      {detections.length === 0 ? (
        <p className="empty-state">No detections to display.</p>
      ) : (
        <div className="detection-list">
          {detections.map((item, index) => (
            <article className="detection-card" key={`${item.class_name}-${item.x1}-${item.y1}-${index}`}>
              <div className="detection-row">
                <span className="detection-name">{item.class_name}</span>
                <span className="detection-score">{item.confidence}</span>
              </div>
              <p className="detection-box">
                Box: ({item.x1}, {item.y1}) to ({item.x2}, {item.y2})
              </p>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
