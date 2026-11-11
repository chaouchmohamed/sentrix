import { useNavigate } from "react-router-dom";
import DataTable from "../components/DataTable";
import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import Panel from "../components/Panel";
import SeverityBadge from "../components/SeverityBadge";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import {
  ArrowRightIcon,
  LayersIcon,
  ServerIcon,
  ShieldIcon,
} from "../components/Icons";
import { api } from "../lib/api";
import {
  formatNumber,
  formatTimestamp,
  splitStages,
  uniqueCount,
} from "../lib/format";
import { useRefresh } from "../lib/refresh";
import { useApi } from "../lib/useApi";

const COLUMNS = [
  {
    key: "id",
    header: "ID",
    render: (row) => <span className="mono cell-strong">#{row.id}</span>,
  },
  {
    key: "src_ip",
    header: "Source IP",
    render: (row) => <span className="mono cell-strong">{row.src_ip}</span>,
  },
  {
    key: "first_seen",
    header: "First seen",
    render: (row) => (
      <span className="mono cell-muted">{formatTimestamp(row.first_seen)}</span>
    ),
  },
  {
    key: "last_seen",
    header: "Last seen",
    render: (row) => (
      <span className="mono cell-muted">{formatTimestamp(row.last_seen)}</span>
    ),
  },
  {
    key: "severity",
    header: "Severity",
    render: (row) => <SeverityBadge severity={row.severity} />,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <span className="status-chip">{row.status}</span>,
  },
  {
    key: "stages",
    header: "Attack stages",
    render: (row) => {
      const stages = splitStages(row.stages);
      return stages.length ? (
        <div className="stage-list">
          {stages.map((stage) => (
            <span key={stage} className="stage-chip">
              {stage}
            </span>
          ))}
        </div>
      ) : (
        <span className="cell-muted">—</span>
      );
    },
  },
  {
    key: "alert_count",
    header: "Alerts",
    align: "right",
    render: (row) => <span className="mono">{formatNumber(row.alert_count)}</span>,
  },
  {
    key: "session_count",
    header: "Sessions",
    align: "right",
    render: (row) => (
      <span className="mono">{formatNumber(row.session_count)}</span>
    ),
  },
  {
    key: "action",
    header: "",
    align: "right",
    render: () => (
      <span className="row-action">
        Investigate <ArrowRightIcon size={14} />
      </span>
    ),
  },
];

export default function Incidents() {
  const { refreshKey } = useRefresh();
  const navigate = useNavigate();
  const { data, loading, error, reload } = useApi(
    (signal) => api.incidents(signal),
    [refreshKey]
  );

  const items = data?.items ?? [];
  const critical = items.filter(
    (item) => String(item.severity).toLowerCase() === "critical"
  ).length;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Incident Response / 03"
        title="Correlated incidents"
        description="Investigate attacker activity grouped by source IP and idle time. Incidents are produced by the existing SENTRIX correlation engine."
        actions={
          <span className="system-chip">
            <ShieldIcon size={14} />
            Correlation engine
          </span>
        }
      />

      {error ? <ErrorState message={error} onRetry={reload} /> : null}
      {loading && !data ? <LoadingState /> : null}

      {data ? (
        <>
          <div className="metric-grid">
            <MetricCard
              label="Total incidents"
              value={formatNumber(items.length)}
              hint="All correlated records"
              icon={LayersIcon}
              tone="cyan"
            />
            <MetricCard
              label="Critical incidents"
              value={formatNumber(critical)}
              hint="Highest severity group"
              icon={ShieldIcon}
              tone="danger"
            />
            <MetricCard
              label="Unique source IPs"
              value={formatNumber(uniqueCount(items, "src_ip"))}
              hint="Distinct attacker sources"
              icon={ServerIcon}
              tone="teal"
            />
          </div>

          <Panel
            title="Incident registry"
            subtitle="Select an incident to open its attack-chain timeline."
            flush
          >
            {items.length ? (
              <DataTable
                columns={COLUMNS}
                rows={items}
                rowKey={(row) => row.id}
                onRowClick={(row) => navigate(`/incidents/${row.id}`)}
                emptyMessage="No incidents have been correlated yet."
              />
            ) : (
              <EmptyState
                title="No incidents"
                message="Incidents will appear when the backend correlates alerts."
                hint="Run the SENTRIX processor to populate the database."
              />
            )}
          </Panel>
        </>
      ) : null}
    </div>
  );
}
