"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface PlacementProbChartProps {
  prob3m: number;
  prob6m: number;
  prob12m: number;
}

export function PlacementProbChart({
  prob3m,
  prob6m,
  prob12m,
}: PlacementProbChartProps) {
  // Format data for Recharts (Requirement 26.2)
  const data = [
    {
      name: "3 Months",
      probability: Number((prob3m * 100).toFixed(1)),
      fill: "#1D9E75",
    },
    {
      name: "6 Months",
      probability: Number((prob6m * 100).toFixed(1)),
      fill: "#3B82F6",
    },
    {
      name: "12 Months",
      probability: Number((prob12m * 100).toFixed(1)),
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
