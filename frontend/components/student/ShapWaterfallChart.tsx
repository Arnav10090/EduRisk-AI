"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";

interface RiskDriver {
  feature: string;
  value: number;
  direction: string;
}

interface ShapWaterfallChartProps {
  drivers: RiskDriver[];
}

export function ShapWaterfallChart({ drivers }: ShapWaterfallChartProps) {
  // Format feature names for display
  const formatFeatureName = (feature: string): string => {
    return feature
      .replace(/_/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Prepare data for horizontal bar chart (Requirement 26.4)
  const chartData = drivers.map((driver) => ({
    feature: formatFeatureName(driver.feature),
    value: driver.value,
    absValue: Math.abs(driver.value),
    direction: driver.direction,
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-sm">{data.feature}</p>
          <p className={`text-sm ${data.direction === "positive" ? "text-[#1D9E75]" : "text-[#E24B4A]"}`}>
            SHAP Value: {data.value.toFixed(4)}
          </p>
          <p className="text-xs text-muted-foreground">
            {data.direction === "positive" ? "Increases" : "Decreases"} risk
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={Math.max(300, drivers.length * 60)}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
        />
        <YAxis
          type="category"
          dataKey="feature"
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: "#e5e7eb" }}
          width={140}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine x={0} stroke="#94a3b8" strokeWidth={2} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.direction === "positive" ? "#1D9E75" : "#E24B4A"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
