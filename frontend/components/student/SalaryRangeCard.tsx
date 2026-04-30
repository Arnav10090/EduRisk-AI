"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

interface SalaryRangeCardProps {
  salaryMin: number;
  salaryMax: number;
  salaryConfidence: number;
}

export function SalaryRangeCard({
  salaryMin,
  salaryMax,
  salaryConfidence,
}: SalaryRangeCardProps) {
  // Format salary values in LPA (Requirement 26.3)
  const formatSalary = (value: number) => {
    return value.toFixed(2);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Expected Salary Range</CardTitle>
        <TrendingUp className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-baseline justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Minimum</p>
              <p className="text-2xl font-bold text-[#E24B4A]">
                ₹{formatSalary(salaryMin)}
              </p>
            </div>
            <div className="text-2xl font-bold text-muted-foreground">-</div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Maximum</p>
              <p className="text-2xl font-bold text-[#1D9E75]">
                ₹{formatSalary(salaryMax)}
              </p>
            </div>
          </div>
          <div className="pt-2 border-t">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">Confidence</p>
              <p className="text-sm font-semibold">
                {salaryConfidence.toFixed(0)}%
              </p>
            </div>
            <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-[#3B82F6] rounded-full transition-all"
                style={{ width: `${Math.min(salaryConfidence, 100)}%` }}
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            All values in LPA (Lakhs Per Annum)
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
