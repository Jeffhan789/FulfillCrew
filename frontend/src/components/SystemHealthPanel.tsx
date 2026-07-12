/**
 * SystemHealthPanel.tsx
 * Fetches /health and displays system component status indicators.
 * Shows database, Redis (if reported) and ML model health.
 */
import React, { useEffect, useState } from "react";
import { Database, Wifi, Cpu, Activity } from "lucide-react";

/** API base URL shared across frontend. */
const API_BASE = (import.meta.env.VITE_API_BASE as string) || "";

export interface HealthCheck {
  status: string;
  checks: Record<string, boolean | string>;
}

interface HealthIndicatorProps {
  label: string;
  status: "healthy" | "degraded" | "unhealthy" | "unknown";
  icon: React.ReactNode;
}

const HealthIndicator: React.FC<HealthIndicatorProps> = ({
  label,
  status,
  icon,
}) => {
  const dotClass =
    status === "healthy"
      ? "healthy"
      : status === "degraded"
      ? "degraded"
      : status === "unhealthy"
      ? "unhealthy"
      : "degraded";

  const labelColor =
    status === "healthy"
      ? "#256d57"
      : status === "unhealthy"
      ? "#c44536"
      : "#c9a227";

  return (
    <div className="health-indicator" title={`${label}: ${status}`}>
      <span className={`dot ${dotClass}`} />
      {icon}
      <span style={{ fontSize: "0.85rem", color: labelColor, fontWeight: 500 }}>
        {label}
      </span>
      <span style={{ fontSize: "0.75rem", color: "#6c7c75" }}>
        ({status})
      </span>
    </div>
  );
};

const SystemHealthPanel: React.FC = () => {
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/health`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data: HealthCheck) => {
        if (!cancelled) {
          setHealth(data);
          setError(false);
        }
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="health-panel" style={{ padding: "12px 0" }}>
        <span className="muted" style={{ fontSize: "0.85rem" }}>
          Checking system health…
        </span>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="health-panel" style={{ padding: "12px 0" }}>
        <HealthIndicator
          label="API Reachable"
          status="unhealthy"
          icon={<Wifi size={14} />}
        />
        <span className="muted" style={{ fontSize: "0.8rem" }}>
          Could not connect to /health endpoint.
        </span>
      </div>
    );
  }

  // Derive individual check statuses from the response
  const dbStatus: HealthIndicatorProps["status"] =
    health.checks.database === true
      ? "healthy"
      : health.checks.database === false
      ? "unhealthy"
      : "unknown";

  const redisStatus: HealthIndicatorProps["status"] =
    health.checks.redis === true
      ? "healthy"
      : health.checks.redis === false
      ? "unhealthy"
      : "unknown";

  const mlStatus: HealthIndicatorProps["status"] =
    health.checks.ml_model === true
      ? "healthy"
      : health.checks.ml_model === false
      ? "unhealthy"
      : "unknown";

  return (
    <div className="health-panel" style={{ padding: "12px 0" }}>
      <HealthIndicator
        label="Database"
        status={dbStatus}
        icon={<Database size={14} />}
      />
      <HealthIndicator
        label="Redis"
        status={redisStatus}
        icon={<Activity size={14} />}
      />
      <HealthIndicator
        label="ML Model"
        status={mlStatus}
        icon={<Cpu size={14} />}
      />
      <HealthIndicator
        label="API"
        status={health.status === "healthy" ? "healthy" : "degraded"}
        icon={<Wifi size={14} />}
      />
    </div>
  );
};

export default SystemHealthPanel;
