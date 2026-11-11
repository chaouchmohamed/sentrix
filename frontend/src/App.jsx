import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import { RefreshProvider } from "./lib/refresh";
import Alerts from "./pages/Alerts";
import IncidentDetail from "./pages/IncidentDetail";
import Incidents from "./pages/Incidents";
import Overview from "./pages/Overview";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <RefreshProvider>
      <div className="app-shell">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className="app-main">
          <Topbar onMenu={() => setSidebarOpen(true)} />
          <ScrollToTop />
          <main className="page-shell">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/incidents" element={<Incidents />} />
              <Route path="/incidents/:incidentId" element={<IncidentDetail />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <footer className="app-footer">
            <span>SENTRIX / SECURITY OPERATIONS</span>
            <span>Read-only telemetry / existing SENTRIX backend</span>
          </footer>
        </div>
      </div>
    </RefreshProvider>
  );
}
