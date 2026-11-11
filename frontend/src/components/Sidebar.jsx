import { NavLink } from "react-router-dom";
import {
  GridIcon,
  HexIcon,
  LockIcon,
  RadarIcon,
  ShieldIcon,
} from "./Icons";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: GridIcon, end: true, index: "01" },
  { to: "/alerts", label: "Detection Alerts", icon: RadarIcon, index: "02" },
  { to: "/incidents", label: "Incidents", icon: ShieldIcon, index: "03" },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      <aside className={`sidebar ${open ? "is-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <HexIcon size={22} />
          </div>
          <div>
            <div className="brand-name">SENTRIX</div>
            <div className="brand-sub">Security Operations</div>
          </div>
        </div>

        <div className="nav-label">Workspace</div>
        <nav className="nav-list" aria-label="Primary navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={onClose}
                className={({ isActive }) =>
                  `nav-item ${isActive ? "active" : ""}`
                }
              >
                <Icon size={18} />
                <span>{item.label}</span>
                <span className="nav-index">{item.index}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-spacer" />

        <div className="status-panel">
          <div className="status-row">
            <span className="status-dot" />
            <span>Monitoring ready</span>
          </div>
          <div className="status-meta">
            Read-only database
            <br />
            Existing SENTRIX backend
          </div>
        </div>

        <div className="sidebar-foot">
          <LockIcon size={13} />
          <span>Password telemetry redacted</span>
        </div>
      </aside>
      <div
        className={`sidebar-scrim ${open ? "is-open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />
    </>
  );
}
