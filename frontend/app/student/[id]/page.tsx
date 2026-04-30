"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { RiskScoreDisplay } from "@/components/student/RiskScoreDisplay";
import { PlacementProbChart } from "@/components/student/PlacementProbChart";
import { SalaryRangeCard } from "@/components/student/SalaryRangeCard";
import { ShapWaterfallChart } from "@/components/student/ShapWaterfallChart";
import { AISummaryCard } from "@/components/student/AISummaryCard";
import { NextBestActionsPanel } from "@/components/student/NextBestActionsPanel";
import { AuditTrailTimeline } from "@/components/student/AuditTrailTimeline";

interface StudentDetail {
  student_id: string;
  name: string;
  course_type: string;
  institute_name: string | null;
  institute_tier: number;
  cgpa: number | null;
  year_of_grad: number;
  created_at: string;
  
  // Latest prediction
  prediction_id: string | null;
  risk_score: number | null;
  risk_level: string | null;
  prob_placed_3m: number | null;
  prob_placed_6m: number | null;
  prob_placed_12m: number | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_confidence: number | null;
  emi_affordability: number | null;
  shap_values: Record<string, number> | null;
  top_risk_drivers: Array<{
    feature: string;
    value: number;
    direction: string;
  }> | null;
  ai_summary: string | null;
  next_best_actions: Array<{
    type: string;
    title: string;
    description: string;
    priority: string;
  }> | null;
  alert_triggered: boolean | null;
  prediction_created_at: string | null;
}

interface AuditEntry {
  prediction_id: string;
  risk_score: number;
  risk_level: string;
  created_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StudentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const studentId = params.id as string;

  const [student, setStudent] = useState<StudentDetail | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStudentData = async () => {
    try {
      setError(null);
      
      // Fetch student detail with latest prediction
      const studentResponse = await fetch(
        `${API_BASE_URL}/api/students/${studentId}`
      );
      
      if (!studentResponse.ok) {
        if (studentResponse.status === 404) {
          throw new Error("Student not found");
        }
        throw new Error(`Failed to fetch student: ${studentResponse.statusText}`);
      }
      
      const studentData: StudentDetail = await studentResponse.json();
      setStudent(studentData);
      
      // Fetch audit trail (all predictions for this student)
      const auditResponse = await fetch(
        `${API_BASE_URL}/api/students/${studentId}/predictions`
      );
      
      if (auditResponse.ok) {
        const auditData: AuditEntry[] = await auditResponse.json();
        setAuditTrail(auditData);
      }
      
      setLoading(false);
    } catch (err) {
      console.error("Error fetching student data:", err);
      setError(err instanceof Error ? err.message : "Failed to load student data");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudentData();
  }, [studentId]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading student details...</p>
        </div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">{error || "Student not found"}</p>
          <Button onClick={() => router.push("/dashboard")}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  // Check if student has a prediction
  const hasPrediction = student.prediction_id !== null;

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
              <h1 className="text-3xl font-bold tracking-tight">{student.name}</h1>
              <p className="text-muted-foreground">
                {student.course_type} • Tier {student.institute_tier} • Class of {student.year_of_grad}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchStudentData}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {!hasPrediction && (
          <div className="rounded-lg border bg-card p-6">
            <p className="text-muted-foreground">
              No prediction available for this student yet.
            </p>
          </div>
        )}

        {hasPrediction && (
          <>
            {/* Risk Score and Key Metrics */}
            <div className="grid gap-6 md:grid-cols-3">
              <RiskScoreDisplay
                riskScore={student.risk_score!}
                riskLevel={student.risk_level!}
                alertTriggered={student.alert_triggered!}
              />
              <PlacementProbChart
                prob3m={student.prob_placed_3m!}
                prob6m={student.prob_placed_6m!}
                prob12m={student.prob_placed_12m!}
              />
              <SalaryRangeCard
                salaryMin={student.salary_min!}
                salaryMax={student.salary_max!}
                salaryConfidence={student.salary_confidence!}
              />
            </div>

            {/* AI Summary */}
            {student.ai_summary && (
              <AISummaryCard summary={student.ai_summary} />
            )}

            {/* SHAP Waterfall Chart */}
            {student.top_risk_drivers && student.top_risk_drivers.length > 0 && (
              <div className="rounded-lg border bg-card p-6">
                <h2 className="text-xl font-semibold mb-4">Risk Drivers Analysis</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  SHAP values show how each factor contributes to the placement risk score.
                  Green bars increase risk, red bars decrease risk.
                </p>
                <ShapWaterfallChart drivers={student.top_risk_drivers} />
              </div>
            )}

            {/* Next Best Actions */}
            {student.next_best_actions && student.next_best_actions.length > 0 && (
              <NextBestActionsPanel actions={student.next_best_actions} />
            )}

            {/* Audit Trail */}
            {auditTrail.length > 0 && (
              <div className="rounded-lg border bg-card p-6">
                <h2 className="text-xl font-semibold mb-4">Prediction History</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  Historical risk assessments for this student
                </p>
                <AuditTrailTimeline entries={auditTrail} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
