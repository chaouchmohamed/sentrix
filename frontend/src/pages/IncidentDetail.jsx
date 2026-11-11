import { Link, useParams } from "react-router-dom";
import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import Panel from "../components/Panel";
import SeverityBadge from "../components/SeverityBadge";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import {
  ArrowRightIcon,
  ChevronLeftIcon,
  ClockIcon,
  DownloadIcon,
  LayersIcon,
  LockIcon,
  ServerIcon,
  TerminalIcon,
} from "../components/Icons";
import { api } from "../lib/api";
import {
  downloadCsv,
  formatEventType,
  formatNumber,
  formatTimestamp,
  splitStages,
} from "../lib/format";
import { useRefresh } from "../lib/refresh";
import { useApi } from "../lib/useApi";

const TIMELINE_CSV = [
  { header: "rule_id", value: (row) => row.rule_id },
  { header: "ts_utc", value: (row) => row.ts_utc },
  { header: "severity", value: (row) => row.severity },
  { header: "explanation", value: (row) => row.explanation },
  { header: "event_id", value: (row) => row.event_id },
  { header: "event_type", value: (row) => row.event_type },
  { header: "command", value: (row) => row.command },
];

function groupTimeline(rows) {
  const groups = [];
  for (const row of rows) {
    const key = `${row.rule_id}|${row.ts_utc}|${row.severity}|${row.explanation}`;
    const previous = groups[groups.length - 1];
    if (previous && previous.key === key) {
      previous.evidence.push(row);
    } else {
      groups.push({
        key,
        rule_id: row.rule_id,
        ts_utc: row.ts_utc,
        severity: row.severity,
        explanation: row.explanation,
        evidence: [row],
      });
    }
  }
  return groups;
}

function SummaryField({ label, value, mono = false }) {
  return (
    <div className="summary-field">
      <div className="summary-label">{label}</div>
      <div className={`summary-value ${mono ? "mono" : ""}`}>{value || "—"}</div>
    </div>
  );
}

export default function IncidentDetail() {
  const { incidentId: incidentIdParam } = useParams();
  const incidentId = Number(incidentIdParam);
  const { refreshKey } = useRefresh();

  const incidentApi = useApi(
    (signal) =>
      Number.isFinite(incidentId)
        ? api.incident(incidentId, signal)
        : Promise.resolve(null),
    [refreshKey, incidentId]
  );
  const timelineApi = useApi(
    (signal) =>
      Number.isFinite(incidentId)
        ? api.timeline(incidentId, signal)
        : Promise.resolve({ items: [], count: 0 }),
    [refreshKey, incidentId]
  );

  const incident = incidentApi.data;
  const timeline = timelineApi.data?.items ?? [];
  const groups = groupTimeline(timeline);
  const stages = splitStages(incident?.stages);

  return (
    <div className="page">
      <Link to="/incidents" className="back-link">
        <ChevronLeftIcon size={15} />
        Incident registry
      </Link>

      <PageHeader
        eyebrow={`Forensic Investigation / 04 / Incident #${incidentIdParam}`}
        title={incident ? incident.src_ip : `Incident #${incidentIdParam}`}
        description="Review the incident summary, ordered detection stages, and every supporting evidence record from the existing SENTRIX database."
        actions={
          <>
            {incident ? <SeverityBadge severity={incident.severity} /> : null}
            {incident ? (
              <span className="status-chip">{incident.status}</span>
            ) : null}
            <button
              type="button"
              className="ghost-button"
              onClick={() =>
                downloadCsv(
                  `sentrix_incident_${incidentIdParam}.csv`,
                  TIMELINE_CSV,
                  timeline
                )
              }
              disabled={!timeline.length}
            >
              <DownloadIcon size={15} />
              Export timeline
            </button>
          </>
        }
      />

      {incidentApi.error ? (
        <ErrorState message={incidentApi.error} onRetry={incidentApi.reload} />
      ) : null}
      {incidentApi.loading && !incident ? <LoadingState /> : null}

      {incident ? (
        <>
          <div className="metric-grid">
            <MetricCard
              label="Source IP"
              value={<span className="mono metric-mono">{incident.src_ip}</span>}
              hint="Correlated attacker address"
              icon={ServerIcon}
            />
            <MetricCard
              label="Linked alerts"
              value={formatNumber(incident.alert_count)}
              hint="Alerts attached to this incident"
              icon={LayersIcon}
              tone="cyan"
            />
            <MetricCard
              label="Sessions"
              value={formatNumber(incident.session_count)}
              hint="Recorded honeypot sessions"
              icon={TerminalIcon}
              tone="teal"
            />
          </div>

          <Panel
            title="Incident summary"
            subtitle="Fields are shown exactly as stored by the correlation engine."
          >
            <div className="summary-grid">
              <SummaryField
                label="First observed"
                value={formatTimestamp(incident.first_seen)}
                mono
              />
              <SummaryField
                label="Last observed"
                value={formatTimestamp(incident.last_seen)}
                mono
              />
              <SummaryField label="Status" value={incident.status} />
              <SummaryField
                label="Severity"
                value={<SeverityBadge severity={incident.severity} />}
              />
            </div>

            <div className="summary-stages">
              <div className="summary-label">Observed attack stages</div>
              {stages.length ? (
                <div className="stage-list">
                  {stages.map((stage) => (
                    <span key={stage} className="stage-chip">
                      {stage}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="summary-value">No stages recorded</div>
              )}
            </div>
          </Panel>

          <Panel
            title="Attack-chain timeline"
            subtitle="Detection stages and every linked evidence record, in original query order."
            action={
              <span className="mono evidence-count">
                {formatNumber(timeline.length)} evidence records
              </span>
            }
          >
            {timelineApi.error ? (
              <ErrorState
                message={timelineApi.error}
                onRetry={timelineApi.reload}
              />
            ) : timelineApi.loading && !timelineApi.data ? (
              <LoadingState label="Loading timeline..." />
            ) : groups.length ? (
              <div className="timeline">
                {groups.map((group, index) => (
                  <article className="timeline-card" key={group.key}>
                    <div className="timeline-index mono">
                      {String(index + 1).padStart(2, "0")}
                    </div>
                    <div className="timeline-head">
                      <div>
                        <div className="timeline-rule">{group.rule_id}</div>
                        <div className="timeline-time">
                          {formatTimestamp(group.ts_utc)}
                        </div>
                      </div>
                      <SeverityBadge severity={group.severity} />
                    </div>

                    <p className="timeline-explanation">{group.explanation}</p>

                    <div className="evidence-head">
                      <span className="summary-label">Linked evidence</span>
                      <span className="mono evidence-count">
                        {formatNumber(group.evidence.length)} records
                      </span>
                    </div>
                    <div className="evidence-list">
                      {group.evidence.map((event, eventIndex) => (
                        <div
                          className="evidence-row"
                          key={`${group.key}-${eventIndex}-${event.event_id ?? "none"}`}
                        >
                          <span className="mono evidence-id">
                            {event.event_id === null
                              ? "No event"
                              : `#${event.event_id}`}
                          </span>
                          <span className="mono evidence-time">
                            {formatTimestamp(event.ts_utc)}
                          </span>
                          <span className="mono evidence-type">
                            {event.event_type
                              ? formatEventType(event.event_type)
                              : "—"}
                          </span>
                          <span className="evidence-command">
                            {event.command ? (
                              <code className="command-code">
                                {event.command}
                              </code>
                            ) : (
                              <span className="cell-muted">—</span>
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No timeline evidence"
                message="No alerts are linked to this incident."
              />
            )}
          </Panel>

          <div className="notice">
            <LockIcon size={16} />
            <div>
              Every evidence record is preserved and displayed in the order
              returned by the existing timeline query. Timestamps remain in
              stored UTC form. Password fields are never exposed by the API.
            </div>
          </div>

          <div className="detail-footer">
            <Link to="/incidents" className="ghost-button">
              <ChevronLeftIcon size={15} />
              Back to incidents
            </Link>
            <span className="detail-footer-meta">
              <ClockIcon size={14} /> Read-only forensic view
              <ArrowRightIcon size={14} />
            </span>
          </div>
        </>
      ) : null}
    </div>
  );
}
