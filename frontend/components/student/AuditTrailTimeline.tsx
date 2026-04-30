"use client";

import { Badge } from "@/components/ui/badge";
import { Clock } from "lucide-react";

interface AuditEntry {
  prediction_id: string;
  risk_score: number;
  risk_level: string;
  created_at: string;
}

interface AuditTrailTimelineProps {
  entries: AuditEntry[];
}

export function AuditTrailTimeline({ entries }: AuditTrailTimelineProps) {
  // Sort entries by date descending (most recent first)
  const sortedEntries = [...entries].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Get risk level badge color
  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case "low":
        return "bg-[#1D9E75] text-white";
      case "medium":
        return "bg-[#F59E0B] text-white";
      case "high":
        return "bg-[#E24B4A] text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  return (
    <div className="space-y-4">
      {sortedEntries.map((entry, index) => (
        <div key={entry.prediction_id} className="flex gap-4">
          {/* Timeline line */}
          <div className="flex flex-col items-center">
            <div className="w-3 h-3 rounded-full bg-primary" />
            {index < sortedEntries.length - 1 && (
              <div className="w-0.5 h-full bg-border mt-1" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 pb-6">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {formatDate(entry.created_at)}
              </span>
              {index === 0 && (
                <Badge variant="outline" className="text-xs">
                  Latest
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-3">
              <div>
                <p className="text-sm font-medium">Risk Assessment</p>
                <p className="text-xs text-muted-foreground">
                  Prediction ID: {entry.prediction_id.slice(0, 8)}...
                </p>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Badge className={getRiskLevelColor(entry.risk_level)}>
                  {entry.risk_level.toUpperCase()}
                </Badge>
                <span className="text-lg font-bold">{entry.risk_score}</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
