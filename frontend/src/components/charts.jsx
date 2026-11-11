import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatBucketTime, severityKey } from "../lib/format";

const SEVERITY_COLORS = {
  critical: "#ff6b81",
  high: "#ffb26b",
  medium: "#ffd166",
  low: "#35d49a",
  unknown: "#6b7c93",
};

const TOOLTIP_STYLE = {
  background: "#0e1726",
  border: "1px solid #1e2d42",
  borderRadius: "10px",
  color: "#f5f8fc",
  fontSize: "12px",
  boxShadow: "0 18px 40px rgba(0,0,0,.35)",
};

export function SeverityChart({ data }) {
  const rows = data.map((item) => {
    const key = severityKey(item.severity);
    return {
      ...item,
      key,
      label: key === "unknown" ? "Unknown" : key[0].toUpperCase() + key.slice(1),
    };
  });

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={230}>
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 4, right: 24, left: 0, bottom: 0 }}
        >
          <CartesianGrid
            horizontal={false}
            stroke="rgba(30,45,66,.65)"
            strokeDasharray="3 3"
          />
          <XAxis
            type="number"
            allowDecimals={false}
            axisLine={false}
            tickLine={false}
            tick={{
              fill: "#6b7c93",
              fontSize: 11,
              fontFamily: "JetBrains Mono, monospace",
            }}
          />
          <YAxis
            type="category"
            dataKey="label"
            width={82}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#a7b4c8", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            cursor={{ fill: "rgba(53,215,255,.04)" }}
            formatter={(value) => ["Alerts", value]}
          />
          <Bar dataKey="n" radius={[0, 6, 6, 0]} barSize={20}>
            {rows.map((row) => (
              <Cell key={row.key} fill={SEVERITY_COLORS[row.key]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function EventActivityChart({ data }) {
  const rows = data.map((item) => ({
    ...item,
    label: formatBucketTime(item.bucket),
  }));

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={230}>
        <AreaChart
          data={rows}
          margin={{ top: 8, right: 12, left: -18, bottom: 0 }}
        >
          <defs>
            <linearGradient id="eventFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#35d7ff" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#35d7ff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            vertical={false}
            stroke="rgba(30,45,66,.65)"
            strokeDasharray="3 3"
          />
          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={false}
            minTickGap={24}
            tick={{
              fill: "#6b7c93",
              fontSize: 10,
              fontFamily: "JetBrains Mono, monospace",
            }}
          />
          <YAxis
            allowDecimals={false}
            axisLine={false}
            tickLine={false}
            tick={{
              fill: "#6b7c93",
              fontSize: 10,
              fontFamily: "JetBrains Mono, monospace",
            }}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            cursor={{ stroke: "rgba(53,215,255,.35)", strokeWidth: 1 }}
            formatter={(value) => ["Events", value]}
            labelFormatter={(label) => `UTC ${label}`}
          />
          <Area
            type="monotone"
            dataKey="n"
            stroke="#35d7ff"
            strokeWidth={2}
            fill="url(#eventFill)"
            dot={false}
            activeDot={{
              r: 4,
              fill: "#35d7ff",
              stroke: "#070c15",
              strokeWidth: 2,
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
