export function formatNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString("en-US") : "0";
}

export function formatTimestamp(value) {
  if (!value) return "—";
  return String(value).replace("T", " ").replace("Z", " UTC");
}

export function formatBucketTime(value) {
  if (!value) return "";
  const text = String(value);
  const time = text.includes("T") ? text.split("T")[1] : text;
  return time.slice(0, 5);
}

export function formatEventType(value) {
  if (!value) return "—";
  return String(value).replaceAll("_", " ");
}

export function severityKey(value) {
  const key = String(value || "unknown").toLowerCase();
  return ["critical", "high", "medium", "low"].includes(key) ? key : "unknown";
}

export function splitStages(value) {
  if (!value) return [];
  return String(value)
    .split(",")
    .map((stage) => stage.trim())
    .filter(Boolean);
}

export function uniqueCount(rows, key) {
  return new Set(rows.map((row) => row[key]).filter(Boolean)).size;
}

function csvCell(value) {
  const text = value === null || value === undefined ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function downloadCsv(filename, columns, rows) {
  const header = columns.map((column) => csvCell(column.header)).join(",");
  const body = rows.map((row) =>
    columns.map((column) => csvCell(column.value(row))).join(",")
  );
  const blob = new Blob([`${header}\n${body.join("\n")}`], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
