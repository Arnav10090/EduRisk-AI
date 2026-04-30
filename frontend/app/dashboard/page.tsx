"use client";

import { useEffect, useState } from "react";
import { RiskScoreCard } from "@/components/dashboard/RiskScoreCard";
import { PortfolioHeatmap } from "@/components/dashboard/PortfolioHeatmap";
import { StudentTable } from "@/components/dashboard/StudentTable";
import { AlertBanner } from "@/components/dashboard/AlertBanner";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

interface Student {
  student_id: string;
  name: string;
  course_type: string;
  institute_name: string | null;
  institute_tier: number;
  cgpa: number | null;
  year_of_grad: number;
  created_at: string;
  prediction_id: string | null;
  risk_score: number | null;
  risk_level: string | null;
  prob_placed_3m: number | null;
  prob_placed_6m: number | null;
  prob_placed_12m: number | null;
  alert_triggered: boolean | null;
  prediction_created_at: string | null;
}

interface DashboardData {
  students: Student[];
  total_count: number;
}

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

export default function DashboardPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortColumn, setSortColumn] = useState("risk_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchDashboardData = async () => {
    try {
      setError(null);
      
      // Fetch students with latest predictions
      const studentsResponse = await fetch(
        `${API_BASE_URL}/api/students?limit=100&sort=${sortColumn}&order=${sortOrder}`
      );
      
      if (!studentsResponse.ok) {
        throw new Error(`Failed to fetch students: ${studentsResponse.statusText}`);
      }
      
      const studentsData: DashboardData = await studentsResponse.json();
      
      // Fetch high-risk alerts
      const alertsResponse = await fetch(
        `${API_BASE_URL}/api/alerts?threshold=high&limit=100`
      );
      
      if (!alertsResponse.ok) {
        throw new Error(`Failed to fetch alerts: ${alertsResponse.statusText}`);
      }
      
      const alertsData: Alert[] = await alertsResponse.json();
      
      setStudents(studentsData.students);
      setTotalCount(studentsData.total_count);
      setAlerts(alertsData);
      setLastRefresh(new Date());
      setLoading(false);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      setLoading(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchDashboardData();
  }, [sortColumn, sortOrder]);

  // Auto-refresh every 30 seconds (Requirement 25.4)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [sortColumn, sortOrder]);

  const handleSort = (column: string) => {
    if (column === sortColumn) {
      // Toggle sort order
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      // New column, default to descending
      setSortColumn(column);
      setSortOrder("desc");
    }
  };

  const handleManualRefresh = () => {
    fetchDashboardData();
  };

  // Calculate aggregate statistics (Requirement 25.2)
  const highRiskCount = students.filter(
    (s) => s.risk_level === "high" || s.alert_triggered
  ).length;
  const mediumRiskCount = students.filter((s) => s.risk_level === "medium").length;
  const lowRiskCount = students.filter((s) => s.risk_level === "low").length;

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={handleManualRefresh}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Portfolio Dashboard</h1>
            <p className="text-muted-foreground">
              Monitor placement risk across your student portfolio
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleManualRefresh}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Alert Banner (Requirement 25.5) */}
        <AlertBanner alertCount={alerts.length} />

        {/* Aggregate Statistics (Requirement 25.2) */}
        <RiskScoreCard
          totalStudents={totalCount}
          highRiskCount={highRiskCount}
          mediumRiskCount={mediumRiskCount}
          lowRiskCount={lowRiskCount}
        />

        {/* Portfolio Heatmap (Requirement 25.1) */}
        <div className="rounded-lg border bg-card p-6">
          <PortfolioHeatmap students={students} />
        </div>

        {/* Student Table (Requirement 25.3) */}
        <div className="rounded-lg border bg-card p-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold">Student Portfolio</h2>
            <p className="text-sm text-muted-foreground">
              Click on a student row to view detailed risk assessment
            </p>
          </div>
          <StudentTable students={students} onSort={handleSort} />
        </div>
      </div>
    </div>
  );
}
