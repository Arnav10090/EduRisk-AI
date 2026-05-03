"use client";

import { useState, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert } from "@/components/ui/alert";
import { Upload, FileText, CheckCircle, XCircle, Loader2, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ParsedStudent {
  name: string;
  course_type: string;
  institute_tier: number;
  cgpa: number;
  year_of_grad: number;
  loan_amount: number;
  loan_emi: number;
  // Optional fields with defaults
  cgpa_scale?: number;
  institute_name?: string;
  internship_count?: number;
  internship_months?: number;
  internship_employer_type?: string;
  certifications?: number;
  region?: string;
}

interface ValidationError {
  row: number;
  field: string;
  message: string;
}

interface BatchResult {
  student_id: string;
  name: string;
  risk_level: string;
  risk_score: number;
  prediction_id: string;
}

interface BatchResponse {
  results: BatchResult[];
  summary: {
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
  };
}

const REQUIRED_COLUMNS = [
  "name",
  "course_type",
  "institute_tier",
  "cgpa",
  "year_of_grad",
  "loan_amount",
  "loan_emi",
];

const MAX_BATCH_SIZE = 500;

export function BatchUpload() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [parsedStudents, setParsedStudents] = useState<ParsedStudent[]>([]);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [batchResults, setBatchResults] = useState<BatchResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Handle file selection
  const handleFileSelect = useCallback((selectedFile: File) => {
    if (!selectedFile.name.endsWith(".csv")) {
      setValidationErrors([
        { row: 0, field: "file", message: "Please select a CSV file" },
      ]);
      return;
    }

    setFile(selectedFile);
    setValidationErrors([]);
    setBatchResults(null);
    setSubmitError(null);
    parseCSV(selectedFile);
  }, []);

  // Parse CSV file
  const parseCSV = (file: File) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split("\n").filter((line) => line.trim());

        if (lines.length === 0) {
          setValidationErrors([
            { row: 0, field: "file", message: "CSV file is empty" },
          ]);
          return;
        }

        // Parse header
        const header = lines[0].split(",").map((col) => col.trim());

        // Validate required columns
        const missingColumns = REQUIRED_COLUMNS.filter(
          (col) => !header.includes(col)
        );

        if (missingColumns.length > 0) {
          setValidationErrors([
            {
              row: 0,
              field: "header",
              message: `Missing required columns: ${missingColumns.join(", ")}`,
            },
          ]);
          return;
        }

        // Parse data rows
        const students: ParsedStudent[] = [];
        const errors: ValidationError[] = [];

        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(",").map((val) => val.trim());

          if (values.length !== header.length) {
            errors.push({
              row: i + 1,
              field: "row",
              message: `Row has ${values.length} columns, expected ${header.length}`,
            });
            continue;
          }

          const student: any = {};

          // Map values to fields
          header.forEach((col, idx) => {
            const value = values[idx];

            // Parse numeric fields
            if (
              [
                "institute_tier",
                "cgpa",
                "year_of_grad",
                "loan_amount",
                "loan_emi",
                "internship_count",
                "internship_months",
                "certifications",
                "cgpa_scale",
              ].includes(col)
            ) {
              const numValue = parseFloat(value);
              if (isNaN(numValue)) {
                errors.push({
                  row: i + 1,
                  field: col,
                  message: `Invalid number: ${value}`,
                });
              } else {
                student[col] = numValue;
              }
            } else {
              student[col] = value;
            }
          });

          // Validate required fields
          for (const reqCol of REQUIRED_COLUMNS) {
            if (!student[reqCol] && student[reqCol] !== 0) {
              errors.push({
                row: i + 1,
                field: reqCol,
                message: `Missing required field: ${reqCol}`,
              });
            }
          }

          // Add defaults for optional fields
          if (!student.cgpa_scale) student.cgpa_scale = 10.0;
          if (!student.internship_count) student.internship_count = 0;
          if (!student.internship_months) student.internship_months = 0;
          if (!student.certifications) student.certifications = 0;

          students.push(student as ParsedStudent);
        }

        // Check batch size limit
        if (students.length > MAX_BATCH_SIZE) {
          errors.push({
            row: 0,
            field: "batch",
            message: `Batch size ${students.length} exceeds maximum of ${MAX_BATCH_SIZE} students`,
          });
        }

        setParsedStudents(students);
        setValidationErrors(errors);
      } catch (error) {
        console.error("Error parsing CSV:", error);
        setValidationErrors([
          {
            row: 0,
            field: "file",
            message: "Failed to parse CSV file. Please check the format.",
          },
        ]);
      }
    };

    reader.onerror = () => {
      setValidationErrors([
        { row: 0, field: "file", message: "Failed to read file" },
      ]);
    };

    reader.readAsText(file);
  };

  // Handle drag and drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        handleFileSelect(droppedFile);
      }
    },
    [handleFileSelect]
  );

  // Handle file input change
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  // Submit batch
  const handleSubmitBatch = async () => {
    if (parsedStudents.length === 0 || validationErrors.length > 0) {
      return;
    }

    setIsProcessing(true);
    setSubmitError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/batch-score`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          students: parsedStudents,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to process batch: ${response.statusText}`
        );
      }

      const result: BatchResponse = await response.json();
      setBatchResults(result);
    } catch (error) {
      console.error("Error submitting batch:", error);
      setSubmitError(
        error instanceof Error ? error.message : "Failed to submit batch"
      );
    } finally {
      setIsProcessing(false);
    }
  };

  // Reset form
  const handleReset = () => {
    setFile(null);
    setParsedStudents([]);
    setValidationErrors([]);
    setBatchResults(null);
    setSubmitError(null);
  };

  return (
    <div className="space-y-6">
      {/* File Upload Area */}
      {!file && (
        <Card>
          <CardContent className="pt-6">
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-muted hover:border-primary/50"
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">
                Drag and drop your CSV file here
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                or click to browse files
              </p>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileInputChange}
                className="hidden"
                id="csv-upload"
              />
              <label htmlFor="csv-upload">
                <Button variant="outline" asChild>
                  <span>
                    <FileText className="h-4 w-4 mr-2" />
                    Select CSV File
                  </span>
                </Button>
              </label>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <div className="ml-2">
            <h4 className="font-semibold mb-2">Validation Errors</h4>
            <ul className="list-disc list-inside space-y-1 text-sm">
              {validationErrors.slice(0, 10).map((error, idx) => (
                <li key={idx}>
                  {error.row > 0 && `Row ${error.row}: `}
                  {error.message}
                </li>
              ))}
              {validationErrors.length > 10 && (
                <li className="text-muted-foreground">
                  ... and {validationErrors.length - 10} more errors
                </li>
              )}
            </ul>
          </div>
        </Alert>
      )}

      {/* Preview Table */}
      {file && parsedStudents.length > 0 && !batchResults && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Preview: {file.name}</CardTitle>
                <CardDescription>
                  {parsedStudents.length} students ready for processing
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={handleReset}>
                Clear
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Course</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>CGPA</TableHead>
                    <TableHead>Year</TableHead>
                    <TableHead>Loan Amount</TableHead>
                    <TableHead>EMI</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {parsedStudents.slice(0, 10).map((student, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">{student.name}</TableCell>
                      <TableCell>{student.course_type}</TableCell>
                      <TableCell>{student.institute_tier}</TableCell>
                      <TableCell>{student.cgpa}</TableCell>
                      <TableCell>{student.year_of_grad}</TableCell>
                      <TableCell>₹{student.loan_amount.toLocaleString()}</TableCell>
                      <TableCell>₹{student.loan_emi.toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {parsedStudents.length > 10 && (
              <p className="text-sm text-muted-foreground mt-2 text-center">
                Showing first 10 of {parsedStudents.length} students
              </p>
            )}

            {/* Submit Button */}
            <div className="mt-6 flex justify-end gap-4">
              <Button
                onClick={handleSubmitBatch}
                disabled={isProcessing || validationErrors.length > 0}
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing {parsedStudents.length} students...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Submit Batch
                  </>
                )}
              </Button>
            </div>

            {/* Submit Error */}
            {submitError && (
              <Alert variant="destructive" className="mt-4">
                <XCircle className="h-4 w-4" />
                <div className="ml-2">
                  <h4 className="font-semibold">Submission Failed</h4>
                  <p className="text-sm">{submitError}</p>
                </div>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results Summary */}
      {batchResults && (
        <Card>
          <CardHeader>
            <CardTitle>Batch Processing Complete</CardTitle>
            <CardDescription>
              Successfully processed {batchResults.results.length} students
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Summary Statistics */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="rounded-lg border p-4 text-center">
                <div className="text-3xl font-bold text-green-600">
                  {batchResults.summary.low_risk_count}
                </div>
                <div className="text-sm text-muted-foreground">Low Risk</div>
              </div>
              <div className="rounded-lg border p-4 text-center">
                <div className="text-3xl font-bold text-amber-600">
                  {batchResults.summary.medium_risk_count}
                </div>
                <div className="text-sm text-muted-foreground">Medium Risk</div>
              </div>
              <div className="rounded-lg border p-4 text-center">
                <div className="text-3xl font-bold text-red-600">
                  {batchResults.summary.high_risk_count}
                </div>
                <div className="text-sm text-muted-foreground">High Risk</div>
              </div>
            </div>

            {/* Results Table */}
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student Name</TableHead>
                    <TableHead>Risk Level</TableHead>
                    <TableHead>Risk Score</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {batchResults.results.slice(0, 20).map((result, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">{result.name}</TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            result.risk_level === "high"
                              ? "bg-red-100 text-red-800"
                              : result.risk_level === "medium"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-green-100 text-green-800"
                          }`}
                        >
                          {result.risk_level.toUpperCase()}
                        </span>
                      </TableCell>
                      <TableCell>{result.risk_score}</TableCell>
                      <TableCell>
                        <Button
                          variant="link"
                          size="sm"
                          onClick={() => router.push(`/student/${result.student_id}`)}
                        >
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {batchResults.results.length > 20 && (
              <p className="text-sm text-muted-foreground mt-2 text-center">
                Showing first 20 of {batchResults.results.length} results
              </p>
            )}

            {/* Action Buttons */}
            <div className="mt-6 flex justify-between">
              <Button variant="outline" onClick={handleReset}>
                Upload Another Batch
              </Button>
              <Button onClick={() => router.push("/dashboard")}>
                Go to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
