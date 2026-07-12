/**
 * DemandPredictionChart.tsx
 * Visualises the demand prediction and restock recommendation.
 * Since we only have a single current value, we render a
 * "metric gauge" card + a simple historical projection bar chart.
 */
import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";

interface DemandPredictionChartProps {
  predictedDemand: number;
  recommendation: string;
}

/**
 * Build a small synthetic dataset for the chart:
 * current prediction + 6 days of forward estimate (linear drift).
 */
function buildDemandData(predicted: number) {
  const data = [];
  const labels = ["Day -3", "Day -2", "Day -1", "Today", "Day +1", "Day +2", "Day +3"];
  // Synthetic historical values (reverse drift from predicted)
  for (let i = 0; i < 7; i++) {
    const drift = (i - 3) * (predicted * 0.05); // ±5% per day
    data.push({
      label: labels[i],
      demand: Math.max(0, Math.round(predicted + drift)),
      isCurrent: i === 3,
    });
  }
  return data;
}

const DemandPredictionChart: React.FC<DemandPredictionChartProps> = ({
  predictedDemand,
  recommendation,
}) => {
  const data = buildDemandData(predictedDemand);

  return (
    <div>
      {/* Top metric row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 12,
          gap: 12,
        }}
      >
        <div style={{ textAlign: "center", flex: 1 }}>
          <div
            style={{
              fontSize: "2rem",
              fontWeight: 700,
              color: "#15201b",
            }}
          >
            {predictedDemand}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#6c7c75" }}>
            Predicted Demand (7 days)
          </div>
        </div>
        <div
          style={{
            textAlign: "center",
            flex: 1,
            padding: "8px 12px",
            background: "#f7f9f4",
            borderRadius: 8,
            border: "1px solid #dce4dc",
          }}
        >
          <div style={{ fontSize: "0.8rem", color: "#256d57", fontWeight: 600 }}>
            {recommendation}
          </div>
          <div style={{ fontSize: "0.7rem", color: "#6c7c75", marginTop: 2 }}>
            Restock Recommendation
          </div>
        </div>
      </div>

      {/* Trend chart */}
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e5dd" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "#4e5d56" }}
            axisLine={{ stroke: "#d9ded8" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#4e5d56" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: number) => [`${value} units`, "Demand"]}
            contentStyle={{
              background: "#ffffff",
              border: "1px solid #d9ded8",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <ReferenceLine
            x="Today"
            stroke="#256d57"
            strokeDasharray="4 4"
            label={{
              value: "Current",
              position: "top",
              fill: "#256d57",
              fontSize: 10,
            }}
          />
          <Bar dataKey="demand" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.isCurrent ? "#256d57" : "#b7d9c2"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default DemandPredictionChart;
