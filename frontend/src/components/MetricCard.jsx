export default function MetricCard({ label, value, hint, icon: Icon, tone }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${tone ? `tone-${tone}` : ""}`}>
        {value}
      </div>
      {hint ? <div className="metric-hint">{hint}</div> : null}
      {Icon ? (
        <div className="metric-icon">
          <Icon size={18} />
        </div>
      ) : null}
    </div>
  );
}
