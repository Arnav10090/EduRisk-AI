"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  ArrowLeft,
  AlertCircle,
  BellRing,
  CheckCircle,
  Clock3,
  Eye,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import { apiClient } from "@/lib/auth";
import { useAuth } from "@/hooks/useAuth";

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

// Local storage key for acknowledged alerts
const ACKNOWLEDGED_ALERTS_KEY = "edurisk_acknowledged_alerts";
type AlertThreshold = "high" | "medium" | "low" | "all";

async function fetchAlertsByThreshold(threshold: "high" | "medium" | "low"): Promise<Alert[]> {
  const response = await apiClient(`/api/alerts?threshold=${threshold}&limit=100`);

  if (!response.ok) {
    throw new Error(`Failed to fetch ${threshold} alerts`);
  }

  return response.json();
}

async function fetchAlerts(threshold: AlertThreshold): Promise<Alert[]> {
  if (threshold === "all") {
    const results = await Promise.all([
      fetchAlertsByThreshold("high"),
      fetchAlertsByThreshold("medium"),
      fetchAlertsByThreshold("low"),
    ]);

    const uniqueAlerts = new Map<string, Alert>();

    for (const group of results) {
      for (const alert of group) {
        uniqueAlerts.set(alert.prediction_id, alert);
      }
    }

    return Array.from(uniqueAlerts.values()).sort((a, b) => b.risk_score - a.risk_score);
  }

  return fetchAlertsByThreshold(threshold);
}

export default function AlertsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [selectedThreshold, setSelectedThreshold] = useState<AlertThreshold>("high");
  const [acknowledgedAlerts, setAcknowledgedAlerts] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

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

  const { data: alerts = [], error, isLoading, mutate } = useSWR<Alert[]>(
    !authLoading && isAuthenticated ? ["alerts", selectedThreshold] : null,
    ([, threshold]: [string, AlertThreshold]) => fetchAlerts(threshold),
    {
      refreshInterval: 10000, // 10 seconds
      revalidateOnFocus: true,
    }
  );

  const activeAlerts = alerts.filter(
    (alert) => !acknowledgedAlerts.has(alert.prediction_id)
  );
  const unacknowledgedCount = activeAlerts.length;
  const acknowledgedCount = alerts.length - activeAlerts.length;

  const counts = useMemo(() => {
    return activeAlerts.reduce(
      (acc, alert) => {
        if (alert.risk_level === "high") acc.high += 1;
        if (alert.risk_level === "medium") acc.medium += 1;
        if (alert.risk_level === "low") acc.low += 1;
        return acc;
      },
      { high: 0, medium: 0, low: 0 }
    );
  }, [activeAlerts]);

  const handleAcknowledge = (predictionId: string) => {
    const newAcknowledged = new Set(acknowledgedAlerts);
    newAcknowledged.add(predictionId);
    setAcknowledgedAlerts(newAcknowledged);

    localStorage.setItem(
      ACKNOWLEDGED_ALERTS_KEY,
      JSON.stringify(Array.from(newAcknowledged))
    );
  };

  const handleResetAcknowledged = () => {
    setAcknowledgedAlerts(new Set());
    localStorage.removeItem(ACKNOWLEDGED_ALERTS_KEY);
  };

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

  const getRecommendedAction = (alert: Alert): string => {
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

  const formatDriver = (value: string) =>
    value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

  const formatTimestamp = (value: string) =>
    new Date(value).toLocaleString([], {
      dateStyle: "medium",
      timeStyle: "short",
    });

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-muted-foreground">Loading alerts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-4">
            <Button variant="outline" size="sm" onClick={() => router.push("/dashboard")}>
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Alerts Center</h1>
              <p className="text-muted-foreground">
                Review students who need immediate intervention and track acknowledged items.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="destructive" className="px-3 py-1 text-sm">
              {unacknowledgedCount} Active
            </Badge>
            <Badge variant="secondary" className="px-3 py-1 text-sm">
              {acknowledgedCount} Acknowledged
            </Badge>
            <Button variant="outline" size="sm" onClick={() => mutate()} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleResetAcknowledged}>
              Reset Acknowledged
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="border-destructive/20 bg-destructive/5">
            <CardHeader className="pb-2">
              <CardDescription>Active Alerts</CardDescription>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <BellRing className="h-5 w-5 text-destructive" />
                {unacknowledgedCount}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card className="border-primary/20 bg-primary/5">
            <CardHeader className="pb-2">
              <CardDescription>High Risk</CardDescription>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <ShieldAlert className="h-5 w-5 text-primary" />
                {counts.high}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Medium Risk</CardDescription>
              <CardTitle className="text-2xl">{counts.medium}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Low Risk</CardDescription>
              <CardTitle className="text-2xl">{counts.low}</CardTitle>
            </CardHeader>
          </Card>
        </div>

        <div className="rounded-xl border bg-card p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold">Filter Alerts</h2>
              <p className="text-sm text-muted-foreground">
                Choose a risk level or combine everything into one view.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {(["high", "medium", "low", "all"] as AlertThreshold[]).map((threshold) => (
              <Button
                key={threshold}
                variant={selectedThreshold === threshold ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedThreshold(threshold)}
              >
                {threshold === "all"
                  ? "All Alerts"
                  : `${threshold.charAt(0).toUpperCase()}${threshold.slice(1)} Risk`}
              </Button>
            ))}
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Failed to load alerts</AlertTitle>
            <AlertDescription>
              The alerts feed could not be loaded right now. Try refreshing the page or logging in again.
            </AlertDescription>
          </Alert>
        )}

        {!isLoading && !error && activeAlerts.length === 0 && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <CheckCircle className="mb-4 h-12 w-12 text-green-500" />
              <h2 className="mb-2 text-xl font-semibold">No Active Alerts</h2>
              <p className="max-w-xl text-muted-foreground">
                There are no outstanding alerts for the selected filter, or every alert has already been acknowledged.
              </p>
            </CardContent>
          </Card>
        )}

        {!isLoading && !error && activeAlerts.length > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {activeAlerts.map((alert) => (
              <Card
                key={alert.prediction_id}
                className="border-primary/10 transition-all hover:-translate-y-0.5 hover:shadow-lg"
              >
                <CardHeader className="space-y-3 pb-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <button
                        type="button"
                        className="text-left text-lg font-semibold hover:text-primary"
                        onClick={() => router.push(`/student/${alert.student_id}`)}
                      >
                        {alert.student_name}
                      </button>
                      <p className="text-sm text-muted-foreground">
                        {alert.course_type} • Tier {alert.institute_tier}
                      </p>
                    </div>
                    <Badge variant={getRiskBadgeVariant(alert.risk_level)}>
                      {alert.risk_level.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock3 className="h-4 w-4" />
                    {formatTimestamp(alert.created_at)}
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-muted/50 p-3">
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">
                        Risk Score
                      </p>
                      <p className="mt-1 text-2xl font-bold">{alert.risk_score}</p>
                    </div>
                    <div className="rounded-lg bg-muted/50 p-3">
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">
                        EMI Affordability
                      </p>
                      <p className="mt-1 text-2xl font-bold">
                        {alert.emi_affordability !== null
                          ? `${Math.round(alert.emi_affordability * 100)}%`
                          : "N/A"}
                      </p>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">
                      Top Risk Driver
                    </p>
                    <p className="mt-1 font-medium">{formatDriver(alert.top_risk_driver)}</p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">
                      Recommended Action
                    </p>
                    <p className="mt-1 text-sm leading-6 text-foreground">
                      {getRecommendedAction(alert)}
                    </p>
                  </div>
                </CardContent>

                <CardFooter className="flex gap-2 pt-3">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => router.push(`/student/${alert.student_id}`)}
                  >
                    <Eye className="h-4 w-4" />
                    View Student
                  </Button>
                  <Button className="flex-1" onClick={() => handleAcknowledge(alert.prediction_id)}>
                    <CheckCircle className="h-4 w-4" />
                    Acknowledge
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {error && (
          <div className="flex">
            <Button variant="outline" size="sm" onClick={() => mutate()}>
              Retry
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
