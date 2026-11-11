import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useRefresh } from "../lib/refresh";
import { MenuIcon, RefreshIcon } from "./Icons";

const TITLES = {
  "/": "Security overview",
  "/alerts": "Detection center",
  "/incidents": "Incident response",
};

export default function Topbar({ onMenu }) {
  const { pathname } = useLocation();
  const { refresh, auto, setAuto, interval, refreshKey } = useRefresh();
  const [lastUpdated, setLastUpdated] = useState(() => new Date());

  useEffect(() => {
    setLastUpdated(new Date());
  }, [refreshKey]);

  const title = pathname.startsWith("/incidents/")
    ? "Incident timeline"
    : TITLES[pathname] ?? "Security operations";

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          type="button"
          className="icon-button menu-button"
          onClick={onMenu}
          aria-label="Open navigation"
        >
          <MenuIcon />
        </button>
        <div className="topbar-heading">
          <div className="topbar-eyebrow">SENTRIX / SECURITY OPERATIONS</div>
          <div className="topbar-title">{title}</div>
        </div>
      </div>

      <div className="topbar-right">
        <span className="live-pill">
          <span className="live-dot" />
          LIVE
        </span>
        <button
          type="button"
          className={`auto-button ${auto ? "is-on" : ""}`}
          onClick={() => setAuto(!auto)}
          aria-pressed={auto}
          title="Toggle automatic refresh"
        >
          AUTO {auto ? `${interval}s` : "OFF"}
        </button>
        <button
          type="button"
          className="icon-button"
          onClick={refresh}
          aria-label="Refresh data"
          title="Refresh data"
        >
          <RefreshIcon size={17} />
        </button>
        <span className="topbar-updated">
          Updated{" "}
          {lastUpdated.toLocaleTimeString("en-US", { hour12: false })}
        </span>
      </div>
    </header>
  );
}
