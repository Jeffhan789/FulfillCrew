/**
 * RiskScoreGauge.tsx
 * A semi-circular gauge using Recharts PieChart + custom SVG overlay.
 * Displays risk score with colour coding:
 *   0.00 – 0.30  green (low)
 *   0.30 – 0.65  yellow (medium)
 *   0.65 – 1.00  red (high)
 */
import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

interface RiskScoreGaugeProps {
  riskScore: number;
  fraudStatus: string;
}

/** Clamp value between 0 and 1. */
function clamp01(v: number) {
  return Math.max(0, Math.min(1, v));
}

/** Determine colour class and hex for a risk score. */
function getRiskLevel(score: number) {
  if (score <= 0.3) return { label: "Low Risk", color: "#256d57", className: "low" };
  if (score <= 0.65) return { label: "Medium Risk", color: "#c9a227", className: "medium" };
  return { label: "High Risk", color: "#c44536", className: "high" };
}

const RiskScoreGauge: React.FC<RiskScoreGaugeProps> = ({
  riskScore,
  fraudStatus,
}) => {
  const clamped = clamp01(riskScore);
  const level = getRiskLevel(clamped);

  // Pie chart data: [filled portion, empty portion]
  // We use a semi-circle gauge by setting startAngle / endAngle.
  const data = [
    { name: "Risk", value: clamped },
    { name: "Safe", value: 1 - clamped },
  ];

  return (
    <div className="risk-gauge" style={{ position: "relative", height: 200 }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            startAngle={180}
            endAngle={0}
            innerRadius="60%"
            outerRadius="85%"
            stroke="none"
            cx="50%"
            cy="75%"
            paddingAngle={2}
          >
            <Cell fill={level.color} />
            <Cell fill="#e0e5dd" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>

      {/* Center label overlay */}
      <div
        style={{
          position: "absolute",
          top: "60%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          textAlign: "center",
        }}
      >
        <div
          className={`score ${level.className}`}
          style={{ fontSize: "2.5rem", fontWeight: 700, color: level.color, lineHeight: 1 }}
        >
          {clamped.toFixed(2)}
        </div>
        <div style={{ fontSize: "0.75rem", color: "#6c7c75", marginTop: 4 }}>
          {level.label}
        </div>
        <div
          style={{
            fontSize: "0.8rem",
            fontWeight: 600,
            color: "#15201b",
            marginTop: 6,
          }}
        >
          {fraudStatus}
        </div>
      </div>

      {/* Legend scale */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: 12,
          marginTop: -8,
          fontSize: "0.7rem",
          color: "#6c7c75",
        }}
      >
        <span>
          <span style={{ color: "#256d57" }}>●</span> 0–0.3
        </span>
        <span>
          <span style={{ color: "#c9a227" }}>●</span> 0.3–0.65
        </span>
        <span>
          <span style={{ color: "#c44536" }}>●</span> 0.65–1
        </span>
      </div>
    </div>
  );
};

export default RiskScoreGauge;
