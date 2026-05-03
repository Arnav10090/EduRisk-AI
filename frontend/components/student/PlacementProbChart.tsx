"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface PlacementProbChartProps {
  prob3m?: number | null;
  prob6m?: number | null;
  prob12m?: number | null;
}

export function PlacementProbChart({
  prob3m,
  prob6m,
  prob12m,
}: PlacementProbChartProps) {
  const toPercentage = (value: number | null | undefined) =>
    typeof value === "number" && Number.isFinite(value)
      ? Number((value * 100).toFixed(1))
      : 0;

  // Format data for Recharts (Requirement 26.2)
  const data = [
    {
      name: "3 Months",
      probability: toPercentage(prob3m),
      fill: "#1D9E75",
    },
    {
      name: "6 Months",
      probability: toPercentage(prob6m),
      fill: "#3B82F6",
    },
    {
      name: "12 Months",
      probability: toPercentage(prob12m),
      fill: "#8B5CF6",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Placement Probability</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickLine={false}
              domain={[0, 100]}
              ticks={[0, 25, 50, 75, 100]}
              label={{ value: "%", position: "insideLeft", fontSize: 12 }}
            />
            <Tooltip
              formatter={(value: number) => [`${value}%`, "Probability"]}
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #e5e7eb",
                borderRadius: "6px",
                fontSize: "12px",
              }}
            />
            <Bar dataKey="probability" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
