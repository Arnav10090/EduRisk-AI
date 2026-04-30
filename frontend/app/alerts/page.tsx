"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { ArrowLeft, AlertCircle, CheckCircle, RefreshCw } from "lucide-react";

interface Alert {
  student_id: string;
  student_name: string;
  course_type: string;
  institute_tier: number;
  risk_score: number;
  risk_level: string;
  emi_affordability: number | null;
  top_risk_driver: string;
  prediction_id: string;
  created_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fetcher function for SWR
const fetcher = (url: string) => fetch(url).then((res) => res.json());

// Local storage key for acknowledged alerts
const ACKNOWLEDGED_ALERTS_KEY = "edurisk_acknowledged_alerts";

export default function AlertsPage() {
  const router = useRouter();
  const [selectedThreshold, setSelectedThreshold] = useState<string>("high");
  const [acknowledgedAlerts, setAcknowledgedAlerts] = useState<Set<string>>(new Set());

  // Load acknowledged alerts from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(ACKNOWLEDGED_ALERTS_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setAcknowledgedAlerts(new Set(parsed));
      } catch (e) {
        console.error("Failed to parse acknowledged alerts:", e);
      }
    }
  }, []);

  // Fetch alerts with SWR and 10-second refresh interval (Requirement 28.6)
  const { data: alerts, error, isLoading, mutate } = useSWR<Alert[]>(
    `${API_BASE_URL}/api/alerts?threshold=${selectedThreshold}&limit=100`,
    fetcher,
    {
      refreshInterval: 10000, // 10 seconds
      revalidateOnFocus: true,
    }
  );

  // Filter out acknowledged alerts (Requirement 28.5)
  const activeAlerts = alerts?.filter(
    (alert) => !acknowledgedAlerts.has(alert.prediction_id)
  ) || [];

  // Calculate unacknowledged count for badge (Requirement 28.6)
  const unacknowledgedCount = activeAlerts.length;

  // Handle acknowledge button click (Requirement 28.4, 28.5)
  const handleAcknowledge = (predictionId: string) => {
    const newAcknowledged = new Set(acknowledgedAlerts);
    newAcknowledged.add(predictionId);
    setAcknowledgedAlerts(newAcknowledged);
    
    // Persist to localStorage
    localStorage.setItem(
      ACKNOWLEDGED_ALERTS_KEY,
      JSON.stringify(Array.from(newAcknowledged))
    );
  };

  // Get risk level badge color
  const getRiskBadgeVariant = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case "high":
        return "destructive";
      case "medium":
        return "default";
      case "low":
        return "secondary";
      default:
        return "outline";
    }
  };

  // Get recommended action from alert
  const getRecommendedAction = (alert: Alert): string => {
    // Since the backend doesn't return next_best_actions in the alerts endpoint,
    // we'll generate a simple recommendation based on the top risk driver
    const driver = alert.top_risk_driver.toLowerCase();
    
    if (driver.includes("internship")) {
      return "Complete at least 1 industry internship or substantial project work";
    } else if (driver.includes("cgpa") || driver.includes("gpa")) {
      return "Focus on improving academic performance and maintaining consistent grades";
    } else if (driver.includes("job_demand") || driver.includes("demand")) {
      return "Enroll in skill-up certification courses to improve job market alignment";
    } else if (driver.includes("tier") || driver.includes("institute")) {
      return "Leverage institute placement cell and alumni network for opportunities";
    } else {
      return "Schedule a consultation to discuss personalized intervention strategies";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push("/dashboard")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">High-Risk Alerts</h1>
              <p className="text-muted-foreground">
                Students requiring immediate attention
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Unacknowledged count badge (Requirement 28.6) */}
            <Badge variant="destructive" className="text-lg px-3 py-1">
              {unacknowledgedCount} Active
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => mutate()}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Filter Bar (Requirement 28.1) */}
        <div className="flex items-center gap-2 p-4 rounded-lg border bg-card">
          <span className="text-sm font-medium mr-2">Filter by Risk Level:</span>
          <Button
            variant={selectedThreshold === "high" ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedThreshold("high")}
          >
            High Risk
          </Button>
          <Button
            variant={selectedThreshold === "medium" ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedThreshold("medium")}
          >
            Medium Risk
          </Button>
          <Button
            variant={selectedThreshold === "all" ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedThreshold("all")}
          >
            All
          </Button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="rounded-lg border bg-card p-6 text-center">
            <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
            <p className="text-destructive">Failed to load alerts</p>
            <Button variant="outline" size="sm" onClick={() => mutate()} className="mt-4">
              Retry
            </Button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && activeAlerts.length === 0 && (
          <div className="rounded-lg border bg-card p-12 text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">No Active Alerts</h2>
            <p className="text-muted-foreground">
              All alerts have been acknowledged or there are no students matching the selected filter.
            </p>
          </div>
        )}

        {/* Alert Cards Grid (Requirement 28.3) */}
        {!isLoading && !error && activeAlerts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeAlerts.map((alert) => (
              <Card key={alert.prediction_id} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 
                        className="font-semibold text-lg mb-1 cursor-pointer hover:text-primary"
                        onClick={() => router.push(`/student/${alert.student_id}`)}
                      >
                        {alert.student_name}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {alert.course_type} • Tier {alert.institute_tier}
                      </p>
                    </div>
                    <Badge variant={getRiskBadgeVariant(alert.risk_level)}>
                      {alert.risk_level.toUpperCase()}
                    </Badge>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-3">
                  {/* Risk Score */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Risk Score:</span>
                    <span className="font-semibold text-lg">{alert.risk_score}</span>
                  </div>

                  {/* Top Risk Driver */}
                  <div>
                    <span className="text-sm text-muted-foreground">Top Risk Driver:</span>
                    <p className="text-sm font-medium mt-1">
                      {alert.top_risk_driver.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                    </p>
                  </div>

                  {/* Recommended Action */}
                  <div>
                    <span className="text-sm text-muted-foreground">Recommended Action:</span>
                    <p className="text-sm mt-1 text-foreground">
                      {getRecommendedAction(alert)}
                    </p>
                  </div>
                </CardContent>

                <CardFooter className="pt-3">
                  {/* Acknowledge Button (Requirement 28.4) */}
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => handleAcknowledge(alert.prediction_id)}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Acknowledge
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
