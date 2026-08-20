import { useEffect, useRef } from 'react';
import { api } from '../services/api';

const STORAGE_KEY = 'oraculo:notified-alert-ids';

function readSeen(): Set<string> {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    return new Set(Array.isArray(parsed) ? parsed.map(String) : []);
  } catch {
    return new Set();
  }
}

function persistSeen(seen: Set<string>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...seen].slice(-250)));
  } catch {
    // Notifications are an enhancement; storage failure must not break the cockpit.
  }
}

export function useAlertNotifications() {
  const baselineReady = useRef(false);
  const polling = useRef(false);

  useEffect(() => {
    let disposed = false;

    async function poll() {
      if (disposed || polling.current || document.visibilityState !== 'visible') return;
      polling.current = true;
      try {
        const alerts = await api.alerts.list();
        const seen = readSeen();

        if (!baselineReady.current) {
          alerts.forEach((alert) => seen.add(String(alert.id)));
          persistSeen(seen);
          baselineReady.current = true;
          return;
        }

        const fresh = alerts.filter((alert) => !seen.has(String(alert.id)));
        fresh.forEach((alert) => {
          seen.add(String(alert.id));
          if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification(`Oráculo · ${alert.severity}`, {
              body: alert.message,
              tag: `oraculo-alert-${alert.id}`,
              silent: alert.severity !== 'CRITICAL'
            });
            notification.onclick = () => {
              window.focus();
              notification.close();
            };
          }
        });
        persistSeen(seen);
      } catch {
        // Offline state is surfaced by the pages; notification polling stays quiet.
      } finally {
        polling.current = false;
      }
    }

    void poll();
    const interval = window.setInterval(() => void poll(), 60_000);
    const onVisibility = () => {
      if (document.visibilityState === 'visible') void poll();
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      disposed = true;
      window.clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);
}
