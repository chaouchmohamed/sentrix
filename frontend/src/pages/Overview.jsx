import { Link } from "react-router-dom";
import DataTable from "../components/DataTable";
import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import Panel from "../components/Panel";
import SeverityBadge from "../components/SeverityBadge";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { EventActivityChart, SeverityChart } from "../components/charts";
import {
  ActivityIcon,
  AlertIcon,
  DatabaseIcon,
  LayersIcon,
  LockIcon,
  UserIcon,
} from "../components/Icons";
import { api } from "../lib/api";
import { formatNumber, formatTimestamp } from "../lib/format";
import { useRefresh } from "../lib/refresh";
import { useApi } from "../lib/useApi";

const SOURCE_COLUMNS = [
  {
    key: "src_ip",
    header: "Source IP",
    render: (row) => (
      <span className="mono cell-strong">{row.src_ip || "—"}</span>
    ),
  },
  {
    key: "n",
    header: "Events",
    align: "right",
    render: (row) => <span className="mono">{formatNumber(row.n)}</span>,
  },
];

const USERNAME_COLUMNS = [
  {
    key: "username",
    header: "Username",
    render: (row) => (
      <span className="mono cell-strong">{row.username || "—"}</span>
    ),
  },
  {
    key: "n",
    header: "Events",
    align: "right",
    render: (row) => <span className="mono">{formatNumber(row.n)}</span>,
  },
];

export default function Overview() {
  const { refreshKey } = useRefresh();
  const { data, loading, error, reload } = useApi(
    (signal) => api.overview(signal),
    [refreshKey]
  );

  const totals = data?.totals ?? { events: 0, alerts: 0, incidents: 0 };
  const recentAlerts = data?.recent_alerts ?? [];

  return (
    <div className="page">
      <PageHeader
        eyebrow="Command Center / 01"
        title="Security overview"
        description="Monitor honeypot telemetry, detection activity, and correlated threats from the existing SENTRIX database."
        actions={
          <span className="system-chip">
            <DatabaseIcon size={14} />
            Read-only telemetry
          </span>
        }
      />

      {error ? <ErrorState message={error} onRetry={reload} /> : null}
      {loading && !data ? <LoadingState /> : null}

      {data ? (
        <>
          <div className="metric-grid">
            <MetricCard
              label="Events ingested"
              value={formatNumber(totals.events)}
              hint="Normalized honeypot records"
              icon={DatabaseIcon}
            />
            <MetricCard
              label="Detection alerts"
              value={formatNumber(totals.alerts)}
              hint="Rule triggers with evidence"
              icon={AlertIcon}
              tone="cyan"
            />
            <MetricCard
              label="Correlated incidents"
              value={formatNumber(totals.incidents)}
              hint="Grouped by source and idle gap"
              icon={LayersIcon}
              tone="teal"
            />
          </div>

          <div className="grid-2">
            <Panel
              title="Severity distribution"
              subtitle="Alert volume grouped by severity."
            >
              {data.severity_distribution.length ? (
                <SeverityChart data={data.severity_distribution} />
              ) : (
                <EmptyState
                  title="No detection alerts"
                  message="No alerts have been recorded by the backend yet."
                />
              )}
            </Panel>

            <Panel
              title="Event activity"
              subtitle="Recorded events over time, grouped by minute."
            >
              {data.events_over_time.length ? (
                <EventActivityChart data={data.events_over_time} />
              ) : (
                <EmptyState
                  title="No event history"
                  message="No normalized events are available yet."
                />
              )}
            </Panel>
          </div>

          <div className="grid-3">
            <Panel
              title="Top source IPs"
              subtitle="Most active telemetry sources."
              flush
            >
              <DataTable
                columns={SOURCE_COLUMNS}
                rows={data.top_sources}
                rowKey={(row) => row.src_ip}
                emptyMessage="No source IPs recorded."
              />
            </Panel>

            <Panel
              title="Top usernames"
              subtitle="Attempted account names in telemetry."
              flush
            >
              <DataTable
                columns={USERNAME_COLUMNS}
                rows={data.top_usernames}
                rowKey={(row) => row.username}
                emptyMessage="No usernames recorded."
              />
            </Panel>

            <Panel
              title="Recent alerts"
              subtitle="Latest rule triggers from the detection engine."
              flush
            >
              {recentAlerts.length ? (
                <div className="alert-list">
                  {recentAlerts.map((alert) => (
                    <Link
                      key={alert.id}
                      to="/alerts"
                      className="alert-list-item"
                    >
                      <div className="alert-list-top">
                        <SeverityBadge severity={alert.severity} />
                        <span className="mono alert-rule">{alert.rule_id}</span>
                        <span className="mono alert-ip">{alert.src_ip}</span>
                      </div>
                      <div className="alert-list-explanation">
                        {alert.explanation}
                      </div>
                      <div className="alert-list-time mono">
                        {formatTimestamp(alert.ts_utc)}
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No recent alerts"
                  message="Detection alerts will appear here."
                />
              )}
            </Panel>
          </div>

          <div className="notice">
            <LockIcon size={16} />
            <div>
              <strong>Credential telemetry policy.</strong> Password values are
              never selected or returned by the API. Only usernames, event
              metadata, and detection evidence are exposed. The API connects to
              the SENTRIX database in strict read-only mode.
            </div>
          </div>

          <div className="overview-footnote">
            <span>
              <ActivityIcon size={14} /> Data source: existing SENTRIX SQLite
              database
            </span>
            <span>
              <UserIcon size={14} /> Source: {data.top_sources[0]?.src_ip ?? "—"}
            </span>
          </div>
        </>
      ) : null}
    </div>
  );
}
