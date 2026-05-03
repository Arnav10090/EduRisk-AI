"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle, AlertCircle } from "lucide-react";
import { RiskScoreGauge } from "./RiskScoreGauge";

interface RiskScoreDisplayProps {
  riskScore: number;
  riskLevel: string;
  alertTriggered: boolean;
}

export function RiskScoreDisplay({
  riskScore,
  riskLevel,
  alertTriggered,
}: RiskScoreDisplayProps) {
  // Color mapping based on risk level (Requirement 26.1)
  const getRiskColor = () => {
    switch (riskLevel) {
      case "low":
        return {
          bg: "bg-[#1D9E75]/10",
          text: "text-[#1D9E75]",
          border: "border-[#1D9E75]",
          badge: "bg-[#1D9E75] text-white",
          icon: CheckCircle,
        };
      case "medium":
        return {
          bg: "bg-[#F59E0B]/10",
          text: "text-[#F59E0B]",
          border: "border-[#F59E0B]",
          badge: "bg-[#F59E0B] text-white",
          icon: AlertCircle,
        };
      case "high":
        return {
          bg: "bg-[#E24B4A]/10",
          text: "text-[#E24B4A]",
          border: "border-[#E24B4A]",
          badge: "bg-[#E24B4A] text-white",
          icon: AlertTriangle,
        };
      default:
        return {
          bg: "bg-gray-100",
          text: "text-gray-700",
          border: "border-gray-300",
          badge: "bg-gray-500 text-white",
          icon: AlertCircle,
        };
    }
  };

  const colors = getRiskColor();
  const Icon = colors.icon;

  return (
    <Card className={`${colors.border} border-2`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Risk Assessment</CardTitle>
        <Icon className={`h-5 w-5 ${colors.text}`} />
      </CardHeader>
      <CardContent className="flex flex-col items-center space-y-4">
        {/* Circular gauge visualization */}
        <RiskScoreGauge riskScore={riskScore} size={200} />
        
        {/* Risk level badge */}
        <div className="flex flex-col items-center gap-2">
          <Badge className={colors.badge}>
            {riskLevel.toUpperCase()} RISK
          </Badge>
          {alertTriggered && (
            <Badge variant="destructive" className="text-xs">
              ALERT
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
