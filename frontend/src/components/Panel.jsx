export default function Panel({
  title,
  subtitle,
  action,
  children,
  flush = false,
  className = "",
}) {
  return (
    <section className={`panel ${className}`}>
      {title || subtitle || action ? (
        <div className="panel-head">
          <div>
            {title ? <h2 className="panel-title">{title}</h2> : null}
            {subtitle ? <p className="panel-subtitle">{subtitle}</p> : null}
          </div>
          {action ? <div className="panel-action">{action}</div> : null}
        </div>
      ) : null}
      <div className={`panel-body ${flush ? "flush" : ""}`}>{children}</div>
    </section>
  );
}
