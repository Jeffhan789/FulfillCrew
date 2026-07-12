/**
 * OrderStatusTimeline.tsx
 * Vertical timeline visualising each agent decision step.
 * Uses simple DOM + CSS; no external icon libraries beyond lucide-react.
 */
import React from "react";
import {
  Bot,
  Package,
  Truck,
  TrendingUp,
  ShieldCheck,
  ClipboardList,
  UserCheck,
  AlertTriangle,
} from "lucide-react";

export interface DecisionLogEntry {
  agent: string;
  message: string;
}

interface OrderStatusTimelineProps {
  logs: DecisionLogEntry[];
}

/** Map agent names to an icon and colour. */
function getAgentMeta(agentName: string) {
  const name = agentName.toLowerCase();
  if (name.includes("order")) return { icon: ClipboardList, color: "#256d57" };
  if (name.includes("inventory")) return { icon: Package, color: "#4e8a7a" };
  if (name.includes("coordinator")) return { icon: Bot, color: "#5b7a9e" };
  if (name.includes("warehouse")) return { icon: Truck, color: "#c9a227" };
  if (name.includes("demand")) return { icon: TrendingUp, color: "#7a5eb5" };
  if (name.includes("fraud")) return { icon: ShieldCheck, color: "#c44536" };
  if (name.includes("user")) return { icon: UserCheck, color: "#256d57" };
  return { icon: AlertTriangle, color: "#6c7c75" };
}

/** Generate a synthetic timestamp for each log entry (relative offsets). */
function buildTimeline(logs: DecisionLogEntry[]) {
  const now = Date.now();
  const stepMs = 3500; // each step ~3.5s apart
  return logs.map((log, i) => {
    const time = new Date(now - (logs.length - i) * stepMs);
    return {
      ...log,
      timeLabel: time.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      relativeTime: `+${(i * 3.5).toFixed(1)}s`,
    };
  });
}

const OrderStatusTimeline: React.FC<OrderStatusTimelineProps> = ({ logs }) => {
  if (!logs || logs.length === 0) {
    return <p className="muted">No decision log available.</p>;
  }

  const timeline = buildTimeline(logs);

  return (
    <div style={{ display: "grid", gap: 0 }}>
      {timeline.map((entry, index) => {
        const meta = getAgentMeta(entry.agent);
        const Icon = meta.icon;
        const isLast = index === timeline.length - 1;

        return (
          <div
            key={`${entry.agent}-${index}`}
            className="timeline-item"
            style={{
              display: "flex",
              gap: 12,
              padding: "8px 0",
              borderBottom: isLast ? "none" : "1px solid #edf0eb",
              alignItems: "flex-start",
            }}
          >
            {/* Icon bubble */}
            <div
              style={{
                minWidth: 32,
                height: 32,
                borderRadius: "50%",
                background: `${meta.color}15`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: meta.color,
                marginTop: 2,
              }}
            >
              <Icon size={16} />
            </div>

            {/* Content */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  gap: 8,
                }}
              >
                <strong
                  style={{
                    fontSize: "0.88rem",
                    color: "#15201b",
                    fontWeight: 600,
                  }}
                >
                  {entry.agent}
                </strong>
                <span
                  style={{
                    fontSize: "0.72rem",
                    color: "#6c7c75",
                    whiteSpace: "nowrap",
                  }}
                >
                  {entry.relativeTime}
                </span>
              </div>
              <p
                style={{
                  fontSize: "0.82rem",
                  color: "#4e5d56",
                  margin: "4px 0 0 0",
                  lineHeight: 1.4,
                  wordBreak: "break-word",
                }}
              >
                {entry.message}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default OrderStatusTimeline;
