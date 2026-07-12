/**
 * ModelEvaluationPanel.tsx
 * Visualises ML model evaluation metrics from /agents/model-evaluations.
 * Uses Recharts BarChart + RadarChart (toggleable) for metric comparison.
 */
import React, { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";

export interface ModelEvaluation {
  model_name: string;
  course_topic: string;
  metric: string;
  score: number;
  interpretation: string;
  training_mode: string;
  online_mode: string;
  mae?: number;
  mape?: number;
  r2?: number;
  roc_auc?: number;
  pr_auc?: number;
  shap_explanation?: Record<string, any>;
}

interface ModelEvaluationPanelProps {
  evaluations: ModelEvaluation[];
}

/** Normalise a score to 0–1 for radar chart comparison. */
function normaliseScore(evalItem: ModelEvaluation): number {
  const { metric, score } = evalItem;
  const m = metric.toLowerCase();
  if (m.includes("mae")) {
    // Lower MAE is better; assume typical range 0–10
    return Math.max(0, 1 - score / 10);
  }
  if (m.includes("accuracy") || m.includes("auc")) {
    // Already roughly 0–1
    return Math.max(0, Math.min(1, score));
  }
  // Fallback: clamp
  return Math.max(0, Math.min(1, score));
}

const ModelEvaluationPanel: React.FC<ModelEvaluationPanelProps> = ({
  evaluations,
}) => {
  const [view, setView] = useState<"bar" | "radar">("bar");

  if (!evaluations || evaluations.length === 0) {
    return <p className="muted">No model evaluations available.</p>;
  }

  // Bar chart data: each model = one row
  const barData = evaluations.map((e) => ({
    name: e.model_name.replace(" Interface", ""),
    rawScore: e.score,
    metric: e.metric,
    normalised: Number(normaliseScore(e).toFixed(3)),
    course_topic: e.course_topic,
  }));

  // Radar chart data: one entry per model, axes = metrics
  const radarData = evaluations.map((e) => ({
    subject: e.model_name.replace(" Interface", "").replace(" Classifier", ""),
    A: Number((normaliseScore(e) * 100).toFixed(1)),
    fullMark: 100,
  }));

  return (
    <div>
      {/* View toggle */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 12,
          justifyContent: "flex-end",
        }}
      >
        <button
          onClick={() => setView("bar")}
          style={{
            background: view === "bar" ? "#256d57" : "#e1e7df",
            color: view === "bar" ? "#ffffff" : "#1b2a22",
            fontSize: "0.75rem",
            padding: "4px 10px",
            borderRadius: 6,
            border: "none",
            cursor: "pointer",
          }}
        >
          Bar
        </button>
        <button
          onClick={() => setView("radar")}
          style={{
            background: view === "radar" ? "#256d57" : "#e1e7df",
            color: view === "radar" ? "#ffffff" : "#1b2a22",
            fontSize: "0.75rem",
            padding: "4px 10px",
            borderRadius: 6,
            border: "none",
            cursor: "pointer",
          }}
        >
          Radar
        </button>
      </div>

      {view === "bar" ? (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={barData} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e5dd" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: "#4e5d56" }}
              axisLine={{ stroke: "#d9ded8" }}
              tickLine={false}
              interval={0}
              angle={-15}
              textAnchor="end"
              height={50}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#4e5d56" }}
              axisLine={false}
              tickLine={false}
              label={{
                value: "Score",
                angle: -90,
                position: "insideLeft",
                fill: "#66766e",
                fontSize: 11,
              }}
            />
            <Tooltip
              formatter={(value: number, _name: string, props: any) => {
                const metric = props?.payload?.metric || "";
                return [`${value} (${metric})`, "Score"];
              }}
              contentStyle={{
                background: "#ffffff",
                border: "1px solid #d9ded8",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar
              dataKey="rawScore"
              fill="#256d57"
              radius={[4, 4, 0, 0]}
              name="Raw Score"
            />
            <Bar
              dataKey="normalised"
              fill="#b7d9c2"
              radius={[4, 4, 0, 0]}
              name="Normalised (0-1)"
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
            <PolarGrid stroke="#e0e5dd" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fontSize: 10, fill: "#4e5d56" }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fontSize: 9, fill: "#6c7c75" }}
            />
            <Radar
              name="Model Performance"
              dataKey="A"
              stroke="#256d57"
              fill="#256d57"
              fillOpacity={0.25}
            />
            <Tooltip
              formatter={(value: number) => [`${value}%`, "Performance"]}
              contentStyle={{
                background: "#ffffff",
                border: "1px solid #d9ded8",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
          </RadarChart>
        </ResponsiveContainer>
      )}

      {/* Interpretation strip */}
      <div
        style={{
          display: "grid",
          gap: 8,
          marginTop: 12,
          paddingTop: 12,
          borderTop: "1px solid #edf0eb",
        }}
      >
        {evaluations.map((e) => (
          <div
            key={e.model_name}
            style={{
              fontSize: "0.78rem",
              color: "#4e5d56",
              lineHeight: 1.4,
            }}
          >
            <strong style={{ color: "#15201b" }}>
              {e.model_name.replace(" Interface", "")}
            </strong>{" "}
            — {e.interpretation}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ModelEvaluationPanel;
