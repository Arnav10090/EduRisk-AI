"use client";

import { cn } from "@/lib/utils";

interface Student {
  student_id: string;
  name: string;
  risk_level: string | null;
  risk_score: number | null;
}

interface PortfolioHeatmapProps {
  students: Student[];
}

const getRiskColor = (riskLevel: string | null): string => {
  switch (riskLevel) {
    case "low":
      return "bg-[#1D9E75] hover:bg-[#1D9E75]/80";
    case "medium":
      return "bg-[#F59E0B] hover:bg-[#F59E0B]/80";
    case "high":
      return "bg-[#E24B4A] hover:bg-[#E24B4A]/80";
    default:
      return "bg-gray-300 hover:bg-gray-400";
  }
};

export function PortfolioHeatmap({ students }: PortfolioHeatmapProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-2">Portfolio Heatmap</h3>
        <p className="text-sm text-muted-foreground">
          Color-coded risk distribution across all students
        </p>
      </div>

      <div className="grid grid-cols-10 sm:grid-cols-15 md:grid-cols-20 lg:grid-cols-25 gap-1">
        {students.map((student) => (
          <div
            key={student.student_id}
            className={cn(
              "aspect-square rounded-sm cursor-pointer transition-colors",
              getRiskColor(student.risk_level)
            )}
            title={`${student.name} - ${student.risk_level || "No prediction"} risk (Score: ${student.risk_score || "N/A"})`}
          />
        ))}
      </div>

      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-sm bg-[#1D9E75]" />
          <span>Low Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-sm bg-[#F59E0B]" />
          <span>Medium Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-sm bg-[#E24B4A]" />
          <span>High Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-sm bg-gray-300" />
          <span>No Prediction</span>
        </div>
      </div>
    </div>
  );
}
