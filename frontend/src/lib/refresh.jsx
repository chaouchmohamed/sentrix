import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

const RefreshContext = createContext(null);

export function RefreshProvider({ children }) {
  const [refreshKey, setRefreshKey] = useState(0);
  const [auto, setAuto] = useState(true);
  const [interval, setIntervalSeconds] = useState(10);

  const refresh = useCallback(() => {
    setRefreshKey((value) => value + 1);
  }, []);

  useEffect(() => {
    if (!auto) return undefined;
    const timer = window.setInterval(refresh, interval * 1000);
    return () => window.clearInterval(timer);
  }, [auto, interval, refresh]);

  const value = useMemo(
    () => ({
      refreshKey,
      refresh,
      auto,
      setAuto,
      interval,
      setIntervalSeconds,
    }),
    [refreshKey, refresh, auto, interval]
  );

  return (
    <RefreshContext.Provider value={value}>
      {children}
    </RefreshContext.Provider>
  );
}

export function useRefresh() {
  const value = useContext(RefreshContext);
  if (!value) {
    throw new Error("useRefresh must be used inside RefreshProvider");
  }
  return value;
}
