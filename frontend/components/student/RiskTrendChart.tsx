"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/auth";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

interface RiskTrendChartProps {
  studentId: string;
}

interface PredictionHistory {
  prediction_id: string;
  risk_score: number;
  risk_level: string;
  created_at: string;
}

export function RiskTrendChart({ studentId }: RiskTrendChartProps) {
  const [predictions, setPredictions] = useState<PredictionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPredictionHistory();
  }, [studentId]);

  const fetchPredictionHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient(`/api/students/${studentId}/predictions`);

      if (!response.ok) {
        throw new Error("Failed to fetch prediction history");
      }

      const data: PredictionHistory[] = await response.json();
      setPredictions(data);
    } catch (err) {
      console.error("Error fetching prediction history:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  // Handle edge cases (Requirement 26.3)
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Risk Score Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px]">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Risk Score Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px]">
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Handle empty prediction history (Requirement 26.3)
  if (predictions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Risk Score Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px]">
            <p className="text-sm text-muted-foreground">No historical data</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Handle single prediction (Requirement 26.3)
  if (predictions.length === 1) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Risk Score Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[200px]">
            <p className="text-sm text-muted-foreground">No historical data</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare data for chart (Requirement 26.2)
  // Reverse to show oldest to newest (left to right)
  const chartData = [...predictions]
    .reverse()
    .map((pred) => ({
      date: new Date(pred.created_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      risk_score: pred.risk_score,
      fullDate: new Date(pred.created_at).toLocaleString(),
    }));

  // Determine trend direction (Requirement 26.2)
  // Compare first and last risk scores
  const firstScore = predictions[predictions.length - 1].risk_score; // Oldest
  const lastScore = predictions[0].risk_score; // Newest
  const isImproving = lastScore < firstScore; // Risk decreasing = improving
  const isDeclining = lastScore > firstScore; // Risk increasing = declining

  // Set line color based on trend (Requirements 26.2.4, 26.2.5)
  const lineColor = isImproving ? "#10b981" : isDeclining ? "#ef4444" : "#6b7280";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Risk Score Trend</CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          {isImproving && "Trend: Improving (risk decreasing)"}
          {isDeclining && "Trend: Declining (risk increasing)"}
          {!isImproving && !isDeclining && "Trend: Stable"}
        </p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickLine={false}
              label={{ value: "Date", position: "insideBottom", offset: -5, fontSize: 12 }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickLine={false}
              domain={[0, 100]}
              ticks={[0, 25, 50, 75, 100]}
              label={{
                value: "Risk Score",
                angle: -90,
                position: "insideLeft",
                fontSize: 12,
              }}
            />
            <Tooltip
              formatter={(value: number) => [`${value}`, "Risk Score"]}
              labelFormatter={(label, payload) => {
                if (payload && payload.length > 0) {
                  return payload[0].payload.fullDate;
                }
                return label;
              }}
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #e5e7eb",
                borderRadius: "6px",
                fontSize: "12px",
              }}
            />
            <Line
              type="monotone"
              dataKey="risk_score"
              stroke={lineColor}
              strokeWidth={2}
              dot={{ fill: lineColor, r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
