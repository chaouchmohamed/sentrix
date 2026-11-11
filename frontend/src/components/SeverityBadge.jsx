import { severityKey } from "../lib/format";

const LABELS = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  unknown: "Unknown",
};

export default function SeverityBadge({ severity }) {
  const key = severityKey(severity);
  return (
    <span className={`severity-badge severity-${key}`}>
      <span className="severity-dot" />
      {LABELS[key]}
    </span>
  );
}
