"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { TrendingUp, Info } from "lucide-react";

interface SalaryRangeCardProps {
  salaryMin?: number | null;
  salaryMax?: number | null;
  salaryConfidence?: number | null;
  emiAffordability?: number | null;
}

export function SalaryRangeCard({
  salaryMin,
  salaryMax,
  salaryConfidence,
  emiAffordability,
}: SalaryRangeCardProps) {
  const isFiniteNumber = (value: number | null | undefined): value is number =>
    typeof value === "number" && Number.isFinite(value);

  // Format salary values in LPA (Requirement 26.3)
  const formatSalary = (value: number | null | undefined) => {
    return isFiniteNumber(value) ? value.toFixed(2) : "N/A";
  };

  // Determine EMI affordability status (Requirement 11)
  const getAffordabilityStatus = (affordability: number) => {
    if (affordability < 0.3) {
      return { 
        label: 'Good', 
        color: 'bg-green-100 text-green-800', 
        textColor: 'text-green-600' 
      };
    } else if (affordability <= 0.5) {
      return { 
        label: 'Moderate', 
        color: 'bg-amber-100 text-amber-800', 
        textColor: 'text-amber-600' 
      };
    } else {
      return { 
        label: 'High Risk', 
        color: 'bg-red-100 text-red-800', 
        textColor: 'text-red-600' 
      };
    }
  };

  const affordabilityPct = isFiniteNumber(emiAffordability)
    ? (emiAffordability * 100).toFixed(1) 
    : null;
  const affordabilityStatus = isFiniteNumber(emiAffordability)
    ? getAffordabilityStatus(emiAffordability) 
    : null;
  const confidencePct = isFiniteNumber(salaryConfidence)
    ? `${salaryConfidence.toFixed(0)}%`
    : "N/A";
  const confidenceWidth = isFiniteNumber(salaryConfidence)
    ? `${Math.min(Math.max(salaryConfidence, 0), 100)}%`
    : "0%";

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
                {confidencePct}
              </p>
            </div>
            <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-[#3B82F6] rounded-full transition-all"
                style={{ width: confidenceWidth }}
              />
            </div>
          </div>

          {/* EMI Affordability (Requirement 11) */}
          {affordabilityPct && affordabilityStatus && (
            <div className="pt-3 border-t">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium">EMI Affordability</span>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-4 w-4 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs">
                          EMI Affordability: Percentage of expected salary required for loan repayment. Lower is better.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className={`text-xl font-bold ${affordabilityStatus.textColor}`}>
                    {affordabilityPct}%
                  </span>
                  <Badge className={affordabilityStatus.color}>
                    {affordabilityStatus.label}
                  </Badge>
                </div>
              </div>
            </div>
          )}

          <p className="text-xs text-muted-foreground">
            All values in LPA (Lakhs Per Annum)
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
