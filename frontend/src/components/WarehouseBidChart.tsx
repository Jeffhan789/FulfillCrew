/**
 * WarehouseBidChart.tsx
 * BarChart comparing warehouse bids with suitability scores.
 * Uses Recharts BarChart + Line (ComposedChart) for dual-axis display.
 */
import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export interface WarehouseBid {
  warehouse_id: string;
  bid: number;
  workload: number;
  distance: number;
  stock_level: number;
  processing_speed: number;
  suitability_score: number;
  reason: string;
}

interface WarehouseBidChartProps {
  bids: WarehouseBid[];
}

/**
 * Custom tooltip for the bid chart.
 */
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const bid = payload.find((p: any) => p.dataKey === "bid");
    const suit = payload.find((p: any) => p.dataKey === "suitability_score");
    return (
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #d9ded8",
          borderRadius: 8,
          padding: "8px 12px",
          fontSize: 13,
        }}
      >
        <strong style={{ color: "#15201b" }}>{label}</strong>
        {bid && (
          <div style={{ color: "#256d57" }}>
            Bid: {Number(bid.value).toFixed(2)}
          </div>
        )}
        {suit && (
          <div style={{ color: "#c9a227" }}>
            Suitability: {Number(suit.value).toFixed(3)}
          </div>
        )}
      </div>
    );
  }
  return null;
};

const WarehouseBidChart: React.FC<WarehouseBidChartProps> = ({ bids }) => {
  // Graceful degradation: if no bids, show raw data fallback
  if (!bids || bids.length === 0) {
    return (
      <div className="dashboard-card">
        <p className="muted">No warehouse bids available.</p>
      </div>
    );
  }

  // Transform data for Recharts
  const data = bids.map((b) => ({
    name: b.warehouse_id,
    bid: b.bid,
    suitability_score: b.suitability_score,
    stock_level: b.stock_level,
    distance: b.distance,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e5dd" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 12, fill: "#4e5d56" }}
          axisLine={{ stroke: "#d9ded8" }}
          tickLine={false}
        />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 12, fill: "#4e5d56" }}
          axisLine={false}
          tickLine={false}
          label={{ value: "Bid", angle: -90, position: "insideLeft", fill: "#66766e", fontSize: 11 }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          domain={[0, 1]}
          tick={{ fontSize: 12, fill: "#4e5d56" }}
          axisLine={false}
          tickLine={false}
          label={{ value: "Suitability", angle: 90, position: "insideRight", fill: "#66766e", fontSize: 11 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12 }}
          formatter={(value: string) =>
            value === "bid" ? "Bid Value" : "Suitability Score"
          }
        />
        <Bar
          yAxisId="left"
          dataKey="bid"
          fill="#256d57"
          radius={[4, 4, 0, 0]}
          name="bid"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="suitability_score"
          stroke="#c9a227"
          strokeWidth={2}
          dot={{ r: 4, fill: "#c9a227", strokeWidth: 0 }}
          name="suitability_score"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default WarehouseBidChart;
