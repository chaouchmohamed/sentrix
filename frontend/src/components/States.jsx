import { AlertIcon, PulseIcon, RefreshIcon } from "./Icons";

export function LoadingState({ label = "Loading telemetry..." }) {
  return (
    <div className="state-card loading-state">
      <span className="spinner" />
      <div>
        <div className="state-title">{label}</div>
        <div className="state-message">
          Reading the existing SENTRIX database in read-only mode.
        </div>
      </div>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state-card error-state">
      <div className="state-icon">
        <AlertIcon size={20} />
      </div>
      <div className="state-copy">
        <div className="state-title">Unable to load data</div>
        <div className="state-message">{message}</div>
        {onRetry ? (
          <button type="button" className="ghost-button" onClick={onRetry}>
            <RefreshIcon size={15} />
            Retry
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function EmptyState({
  title = "Nothing to display",
  message,
  hint,
}) {
  return (
    <div className="state-card empty-state">
      <div className="state-icon">
        <PulseIcon size={20} />
      </div>
      <div className="state-copy">
        <div className="state-title">{title}</div>
        {message ? <div className="state-message">{message}</div> : null}
        {hint ? <div className="state-hint">{hint}</div> : null}
      </div>
    </div>
  );
}
