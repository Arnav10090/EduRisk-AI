"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowUpDown, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Student {
  student_id: string;
  name: string;
  course_type: string;
  institute_tier: number;
  risk_score: number | null;
  risk_level: string | null;
  alert_triggered: boolean | null;
}

interface StudentTableProps {
  students: Student[];
  onSort?: (column: string) => void;
}

const getRiskBadgeVariant = (riskLevel: string | null) => {
  switch (riskLevel) {
    case "low":
      return "default";
    case "medium":
      return "secondary";
    case "high":
      return "destructive";
    default:
      return "outline";
  }
};

const getRiskBadgeColor = (riskLevel: string | null) => {
  switch (riskLevel) {
    case "low":
      return "bg-[#1D9E75] hover:bg-[#1D9E75]/80 text-white";
    case "medium":
      return "bg-[#F59E0B] hover:bg-[#F59E0B]/80 text-white";
    case "high":
      return "bg-[#E24B4A] hover:bg-[#E24B4A]/80 text-white";
    default:
      return "";
  }
};

export function StudentTable({ students, onSort }: StudentTableProps) {
  const router = useRouter();
  const [sortColumn, setSortColumn] = useState<string>("risk_score");

  const handleSort = (column: string) => {
    setSortColumn(column);
    onSort?.(column);
  };

  const handleRowClick = (studentId: string) => {
    router.push(`/student/${studentId}`);
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <Button
                variant="ghost"
                onClick={() => handleSort("name")}
                className="h-8 px-2"
              >
                Name
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            </TableHead>
            <TableHead>
              <Button
                variant="ghost"
                onClick={() => handleSort("course_type")}
                className="h-8 px-2"
              >
                Course Type
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            </TableHead>
            <TableHead>
              <Button
                variant="ghost"
                onClick={() => handleSort("institute_tier")}
                className="h-8 px-2"
              >
                Institute Tier
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            </TableHead>
            <TableHead>
              <Button
                variant="ghost"
                onClick={() => handleSort("risk_score")}
                className="h-8 px-2"
              >
                Risk Score
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            </TableHead>
            <TableHead>Risk Level</TableHead>
            <TableHead>Alert Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center">
                No students found.
              </TableCell>
            </TableRow>
          ) : (
            students.map((student) => (
              <TableRow
                key={student.student_id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => handleRowClick(student.student_id)}
              >
                <TableCell className="font-medium">{student.name}</TableCell>
                <TableCell>{student.course_type}</TableCell>
                <TableCell>Tier {student.institute_tier}</TableCell>
                <TableCell>
                  {student.risk_score !== null ? student.risk_score : "N/A"}
                </TableCell>
                <TableCell>
                  {student.risk_level ? (
                    <Badge
                      className={cn(getRiskBadgeColor(student.risk_level))}
                    >
                      {student.risk_level.toUpperCase()}
                    </Badge>
                  ) : (
                    <Badge variant="outline">No Prediction</Badge>
                  )}
                </TableCell>
                <TableCell>
                  {student.alert_triggered ? (
                    <div className="flex items-center gap-1 text-[#E24B4A]">
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">Alert</span>
                    </div>
                  ) : (
                    <span className="text-sm text-muted-foreground">—</span>
                  )}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
