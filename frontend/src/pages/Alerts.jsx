import { useEffect, useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import Panel from "../components/Panel";
import SeverityBadge from "../components/SeverityBadge";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import {
  DownloadIcon,
  LockIcon,
  RadarIcon,
  SearchIcon,
  ServerIcon,
  TerminalIcon,
} from "../components/Icons";
import { api } from "../lib/api";
import {
  downloadCsv,
  formatEventType,
  formatNumber,
  formatTimestamp,
  uniqueCount,
} from "../lib/format";
import { useRefresh } from "../lib/refresh";
import { useApi } from "../lib/useApi";

const ALERT_COLUMNS = [
  {
    key: "id",
    header: "ID",
    render: (row) => <span className="mono cell-strong">#{row.id}</span>,
  },
  {
    key: "ts_utc",
    header: "Timestamp",
    render: (row) => (
      <span className="mono cell-muted">{formatTimestamp(row.ts_utc)}</span>
    ),
  },
  {
    key: "rule_id",
    header: "Rule",
    render: (row) => <span className="mono cell-strong">{row.rule_id}</span>,
  },
  {
    key: "severity",
    header: "Severity",
    render: (row) => <SeverityBadge severity={row.severity} />,
  },
  {
    key: "src_ip",
    header: "Source IP",
    render: (row) => <span className="mono">{row.src_ip || "—"}</span>,
  },
  {
    key: "technique",
    header: "Technique",
    render: (row) => (
      <span className="mono cell-muted">{row.technique || "—"}</span>
    ),
  },
  {
    key: "explanation",
    header: "Explanation",
    className: "explanation-cell",
    render: (row) => <span className="explanation-cell">{row.explanation}</span>,
  },
];

const EVIDENCE_COLUMNS = [
  {
    key: "id",
    header: "Event ID",
    render: (row) => <span className="mono cell-strong">#{row.id}</span>,
  },
  {
    key: "ts_utc",
    header: "Timestamp",
    render: (row) => (
      <span className="mono cell-muted">{formatTimestamp(row.ts_utc)}</span>
    ),
  },
  {
    key: "event_type",
    header: "Event type",
    render: (row) => (
      <span className="mono">{formatEventType(row.event_type)}</span>
    ),
  },
  {
    key: "username",
    header: "Username",
    render: (row) => <span className="mono">{row.username || "—"}</span>,
  },
  {
    key: "command",
    header: "Command evidence",
    render: (row) =>
      row.command ? (
        <code className="command-code">{row.command}</code>
      ) : (
        <span className="cell-muted">—</span>
      ),
  },
];

const CSV_COLUMNS = [
  { header: "id", value: (row) => row.id },
  { header: "ts_utc", value: (row) => row.ts_utc },
  { header: "rule_id", value: (row) => row.rule_id },
  { header: "severity", value: (row) => row.severity },
  { header: "src_ip", value: (row) => row.src_ip },
  { header: "technique", value: (row) => row.technique },
  { header: "explanation", value: (row) => row.explanation },
];

export default function Alerts() {
  const { refreshKey } = useRefresh();
  const [severity, setSeverity] = useState("");
  const [rule, setRule] = useState("");
  const [srcIp, setSrcIp] = useState("");
  const [since, setSince] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  const filtersApi = useApi((signal) => api.alertFilters(signal), [refreshKey]);
  const alertsApi = useApi(
    (signal) =>
      api.alerts(
        { severity, rule_id: rule, src_ip: srcIp, since },
        signal
      ),
    [refreshKey, severity, rule, srcIp, since]
  );

  const items = alertsApi.data?.items ?? [];

  useEffect(() => {
    if (!selectedId && items.length) {
      setSelectedId(items[0].id);
    }
  }, [items, selectedId]);

  const evidenceApi = useApi(
    (signal) =>
      selectedId
        ? api.evidence(selectedId, signal)
        : Promise.resolve({ items: [], count: 0 }),
    [refreshKey, selectedId]
  );

  const metrics = useMemo(
    () => ({
      matching: items.length,
      sources: uniqueCount(items, "src_ip"),
      rules: uniqueCount(items, "rule_id"),
    }),
    [items]
  );

  const severityOptions = filtersApi.data?.severities ?? [];
  const ruleOptions = filtersApi.data?.rules ?? [];
  const evidence = evidenceApi.data?.items ?? [];

  const clearFilters = () => {
    setSeverity("");
    setRule("");
    setSrcIp("");
    setSince("");
  };

  const hasFilters = severity || rule || srcIp || since;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Threat Monitoring / 02"
        title="Detection center"
        description="Search, filter, and inspect individual rule triggers and their linked evidence. All evidence is read directly from the existing database."
        actions={
          <button
            type="button"
            className="ghost-button"
            onClick={() =>
              downloadCsv("sentrix_alerts.csv", CSV_COLUMNS, items)
            }
            disabled={!items.length}
          >
            <DownloadIcon size={15} />
            Export CSV
          </button>
        }
      />

      <Panel
        title="Query filters"
        subtitle="Narrow results by severity, rule, source IP, or timestamp."
        className="filter-panel"
      >
        <div className="filters">
          <div className="field">
            <label htmlFor="severity-filter">Severity</label>
            <select
              id="severity-filter"
              className="select"
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
            >
              <option value="">(any)</option>
              {severityOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="rule-filter">Detection rule</label>
            <select
              id="rule-filter"
              className="select"
              value={rule}
              onChange={(event) => setRule(event.target.value)}
            >
              <option value="">(any)</option>
              {ruleOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="ip-filter">Source IP contains</label>
            <input
              id="ip-filter"
              className="input"
              value={srcIp}
              onChange={(event) => setSrcIp(event.target.value)}
              placeholder="e.g. 172.28"
            />
          </div>

          <div className="field">
            <label htmlFor="since-filter">Since (UTC ISO)</label>
            <input
              id="since-filter"
              className="input"
              value={since}
              onChange={(event) => setSince(event.target.value)}
              placeholder="e.g. 2026-10-26T00:00:00"
            />
          </div>

          <button
            type="button"
            className="ghost-button filter-reset"
            onClick={clearFilters}
            disabled={!hasFilters}
          >
            <SearchIcon size={15} />
            Clear
          </button>
        </div>
      </Panel>

      {alertsApi.error ? (
        <ErrorState message={alertsApi.error} onRetry={alertsApi.reload} />
      ) : null}
      {alertsApi.loading && !alertsApi.data ? <LoadingState /> : null}

      {alertsApi.data ? (
        <>
          <div className="metric-grid">
            <MetricCard
              label="Matching alerts"
              value={formatNumber(metrics.matching)}
              hint="Current filter result set"
              icon={RadarIcon}
              tone="cyan"
            />
            <MetricCard
              label="Source IPs"
              value={formatNumber(metrics.sources)}
              hint="Unique telemetry sources"
              icon={ServerIcon}
            />
            <MetricCard
              label="Rules triggered"
              value={formatNumber(metrics.rules)}
              hint="Distinct detection rules"
              icon={TerminalIcon}
              tone="teal"
            />
          </div>

          <Panel
            title="Detection results"
            subtitle="Select an alert to inspect its linked evidence."
            flush
          >
            <DataTable
              columns={ALERT_COLUMNS}
              rows={items}
              rowKey={(row) => row.id}
              onRowClick={(row) => setSelectedId(row.id)}
              selectedKey={selectedId}
              emptyMessage="No alerts match the current filters."
            />
          </Panel>

          <Panel
            title={
              selectedId ? `Evidence for alert #${selectedId}` : "Evidence inspector"
            }
            subtitle="Linked event records in their original query order."
            action={
              selectedId ? (
                <span className="mono evidence-count">
                  {formatNumber(evidence.length)} records
                </span>
              ) : null
            }
            flush
          >
            {!selectedId ? (
              <EmptyState
                title="Select an alert"
                message="Choose a detection result to inspect its evidence."
              />
            ) : evidenceApi.error ? (
              <ErrorState
                message={evidenceApi.error}
                onRetry={evidenceApi.reload}
              />
            ) : evidenceApi.loading && !evidenceApi.data ? (
              <LoadingState label="Loading evidence..." />
            ) : evidence.length ? (
              <DataTable
                columns={EVIDENCE_COLUMNS}
                rows={evidence}
                rowKey={(row) => row.id}
                emptyMessage="No evidence records are linked to this alert."
              />
            ) : (
              <EmptyState
                title="No linked evidence"
                message="This alert has no evidence records in the database."
              />
            )}
          </Panel>

          <div className="notice">
            <LockIcon size={16} />
            <div>
              Evidence responses never include password fields. Every linked
              evidence record is returned in the order produced by the existing
              read-only query layer.
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
