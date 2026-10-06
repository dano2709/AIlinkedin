"use client";

import { useEffect, useState } from "react";

type Preferences = {
  enabled: boolean;
  email: string;
  min_fit_score: number;
};

type PreferencesResponse = {
  exists: boolean;
  preferences: Preferences;
};

type NotificationItem = {
  id: string;
  type: string;
  fingerprint: string;
  payload: {
    title?: string;
    company_name?: string;
    fit_score?: number;
    job_url?: string;
  };
  created_at: string;
};

type Delivery = {
  notification_id: string;
  channel: string;
  status: string;
  sent_at: string | null;
  error: string | null;
};

type HistoryResponse = {
  notifications: NotificationItem[];
  deliveries: Delivery[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getPreferences(): Promise<PreferencesResponse> {
  const response = await fetch(API_URL + "/api/v1/notifications/preferences", { cache: "no-store" });
  if (!response.ok) throw new Error("API " + response.status);
  return response.json() as Promise<PreferencesResponse>;
}

async function getHistory(): Promise<HistoryResponse> {
  const response = await fetch(API_URL + "/api/v1/notifications?limit=10", { cache: "no-store" });
  if (!response.ok) throw new Error("API " + response.status);
  return response.json() as Promise<HistoryResponse>;
}

export default function NotificationsClient() {
  const [preferences, setPreferences] = useState<Preferences>({
    enabled: false,
    email: "",
    min_fit_score: 80,
  });
  const [history, setHistory] = useState<HistoryResponse>({
    notifications: [],
    deliveries: [],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function load() {
    setLoading(true);
    setMessage("");
    try {
      const [preferenceData, historyData] = await Promise.all([getPreferences(), getHistory()]);
      setPreferences(preferenceData.preferences);
      setHistory(historyData);
    } catch {
      setMessage("Notifications could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, []);

  async function save() {
    setSaving(true);
    setMessage("");
    try {
      const response = await fetch(API_URL + "/api/v1/notifications/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preferences),
      });
      if (!response.ok) throw new Error("API " + response.status);
      setMessage("Notification settings saved.");
      await load();
    } catch {
      setMessage("Notification settings could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  const deliveryByNotification = new Map(
    history.deliveries.map((delivery) => [delivery.notification_id, delivery]),
  );

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Notifications</span>
          <h2>High-fit job alerts</h2>
        </div>
        <span className="status">{loading ? "Loading" : preferences.enabled ? "Enabled" : "Disabled"}</span>
      </div>

      {!loading ? (
        <>
          <div className="profile-grid">
            <label>
              Alert email
              <input
                type="email"
                value={preferences.email}
                placeholder="you@example.com"
                onChange={(event) =>
                  setPreferences({ ...preferences, email: event.target.value })
                }
              />
            </label>
            <label>
              Minimum Fit Score
              <input
                type="number"
                min={0}
                max={100}
                value={preferences.min_fit_score}
                onChange={(event) =>
                  setPreferences({
                    ...preferences,
                    min_fit_score: Number(event.target.value),
                  })
                }
              />
            </label>
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={preferences.enabled}
                onChange={(event) =>
                  setPreferences({ ...preferences, enabled: event.target.checked })
                }
              />
              Send email alerts for high-fit jobs
            </label>
          </div>

          <div className="profile-actions">
            <button className="refresh-button" onClick={() => void save()} disabled={saving}>
              {saving ? "Saving…" : "Save notification settings"}
            </button>
            {message ? <span className="save-message">{message}</span> : null}
          </div>

          <div className="table-wrap" style={{ marginTop: 20 }}>
            <table>
              <thead>
                <tr>
                  <th>Job</th>
                  <th>Fit</th>
                  <th>Delivery</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {history.notifications.length ? (
                  history.notifications.map((notification) => {
                    const delivery = deliveryByNotification.get(notification.id);
                    return (
                      <tr key={notification.id}>
                        <td>
                          <strong>{notification.payload.title ?? "Job"}</strong>
                          <small>{notification.payload.company_name ?? "Unknown company"}</small>
                        </td>
                        <td>{notification.payload.fit_score ?? "—"}</td>
                        <td>
                          {delivery?.status ?? "—"}
                          {delivery?.error ? <small>{delivery.error}</small> : null}
                        </td>
                        <td>{new Date(notification.created_at).toLocaleString()}</td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={4}>No notifications yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="empty-state">Loading notification settings…</div>
      )}
    </section>
  );
}
