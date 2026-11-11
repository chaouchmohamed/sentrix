export default function DataTable({
  columns,
  rows,
  rowKey,
  onRowClick,
  selectedKey,
  emptyMessage = "No records.",
}) {
  if (!rows.length) {
    return <div className="table-empty">{emptyMessage}</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={column.align ? `align-${column.align}` : ""}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const key = rowKey ? rowKey(row, index) : index;
            const selected =
              selectedKey !== undefined &&
              String(selectedKey) === String(key);

            return (
              <tr
                key={key}
                className={`${onRowClick ? "clickable" : ""} ${
                  selected ? "is-selected" : ""
                }`}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                tabIndex={onRowClick ? 0 : undefined}
                onKeyDown={
                  onRowClick
                    ? (event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          onRowClick(row);
                        }
                      }
                    : undefined
                }
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={[
                      column.className,
                      column.align ? `align-${column.align}` : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    {column.render
                      ? column.render(row)
                      : row[column.key] ?? "—"}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
