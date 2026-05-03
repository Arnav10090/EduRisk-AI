"use client";

import { useEffect, useState } from "react";
import { RiskScoreCard } from "@/components/dashboard/RiskScoreCard";
import { PortfolioHeatmap } from "@/components/dashboard/PortfolioHeatmap";
import { StudentTable } from "@/components/dashboard/StudentTable";
import { AlertBanner } from "@/components/dashboard/AlertBanner";
import { EmptyState } from "@/components/dashboard/EmptyState";
import { Button } from "@/components/ui/button";
import { RefreshCw, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/auth";
import { useAuth } from "@/hooks/useAuth";

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

interface HeatmapStudent {
  student_id: string;
  name: string;
  risk_level: string | null;
  risk_score: number | null;
}

interface DashboardHeatmapData {
  students: HeatmapStudent[];
  high_risk_count: number;
  total_students: number;
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

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [heatmapStudents, setHeatmapStudents] = useState<HeatmapStudent[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortColumn, setSortColumn] = useState("risk_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  
  // Pagination state (Task 28.1)
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const totalPages = Math.ceil(totalCount / pageSize);

  // Check authentication on mount
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  const fetchDashboardData = async () => {
    if (!isAuthenticated) {
      return;
    }

    try {
      setError(null);
      
      // Calculate offset from current page (Task 28.3.1)
      const offset = (currentPage - 1) * pageSize;
      
      const [studentsResponse, alertsResponse, heatmapResponse] = await Promise.all([
        apiClient(
          `/api/students?limit=${pageSize}&offset=${offset}&sort=${sortColumn}&order=${sortOrder}`
        ),
        apiClient("/api/alerts?threshold=high&limit=100"),
        apiClient("/api/dashboard/heatmap"),
      ]);

      if (!studentsResponse.ok) {
        throw new Error(`Failed to fetch students: ${studentsResponse.statusText}`);
      }

      if (!alertsResponse.ok) {
        throw new Error(`Failed to fetch alerts: ${alertsResponse.statusText}`);
      }

      if (!heatmapResponse.ok) {
        throw new Error(`Failed to fetch heatmap: ${heatmapResponse.statusText}`);
      }

      const studentsData: DashboardData = await studentsResponse.json();
      const alertsData: Alert[] = await alertsResponse.json();
      const heatmapData: DashboardHeatmapData = await heatmapResponse.json();

      setStudents(studentsData.students);
      setHeatmapStudents(heatmapData.students);
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
    if (!authLoading && isAuthenticated) {
      void fetchDashboardData();
    }
  }, [authLoading, isAuthenticated, sortColumn, sortOrder, currentPage, pageSize]);

  // Auto-refresh every 30 seconds (Requirement 25.4)
  useEffect(() => {
    if (authLoading || !isAuthenticated) {
      return;
    }

    const interval = setInterval(() => {
      void fetchDashboardData();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [authLoading, isAuthenticated, sortColumn, sortOrder, currentPage, pageSize]);

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
    void fetchDashboardData();
  };

  const handleAddStudent = () => {
    router.push("/student/new");
  };

  // Pagination handlers (Task 28.3)
  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // Reset to page 1 when page size changes (Task 28.3.3)
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
            <Button
              onClick={handleAddStudent}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Student
            </Button>
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
        {students.length > 0 && <AlertBanner alertCount={alerts.length} />}

        {/* Show empty state when no students exist */}
        {students.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {/* Aggregate Statistics (Requirement 25.2) */}
            <RiskScoreCard
              totalStudents={totalCount}
              highRiskCount={highRiskCount}
              mediumRiskCount={mediumRiskCount}
              lowRiskCount={lowRiskCount}
            />

            {/* Portfolio Heatmap (Requirement 25.1) */}
            <div className="rounded-lg border bg-card p-6">
              <PortfolioHeatmap students={heatmapStudents} />
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
              
              {/* Pagination Controls (Task 28.2) */}
              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {/* Student count display (Task 28.2.4) */}
                  <p className="text-sm text-muted-foreground">
                    Showing {Math.min((currentPage - 1) * pageSize + 1, totalCount)}-
                    {Math.min(currentPage * pageSize, totalCount)} of {totalCount} students
                  </p>
                  
                  {/* Page size selector (Task 28.2.2) */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Show:</span>
                    <select
                      value={pageSize}
                      onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      <option value={5}>5</option>
                      <option value={20}>20</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                    </select>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  {/* Current page display (Task 28.2.3) */}
                  <p className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </p>
                  
                  {/* Previous and Next buttons (Task 28.2.1) */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePreviousPage}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleNextPage}
                    disabled={currentPage >= totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
