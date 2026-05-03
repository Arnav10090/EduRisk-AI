"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import { BatchUpload } from "@/components/forms/BatchUpload";

export default function BatchUploadPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 max-w-5xl">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push("/dashboard")}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">CSV Batch Upload</h1>
          <p className="text-muted-foreground">
            Upload a CSV file to process multiple student predictions at once
          </p>
        </div>

        {/* Instructions Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Instructions</CardTitle>
            <CardDescription>
              Follow these guidelines to prepare your CSV file
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div>
                <strong>Required Columns:</strong>
                <ul className="list-disc list-inside ml-2 mt-1 text-muted-foreground">
                  <li>name - Student full name</li>
                  <li>course_type - Course type (e.g., Engineering, MBA)</li>
                  <li>institute_tier - Institute tier (1, 2, or 3)</li>
                  <li>cgpa - CGPA score</li>
                  <li>year_of_grad - Year of graduation (2020-2030)</li>
                  <li>loan_amount - Loan amount in INR</li>
                  <li>loan_emi - Monthly EMI in INR</li>
                </ul>
              </div>
              <div>
                <strong>Batch Limit:</strong>
                <span className="text-muted-foreground ml-2">
                  Maximum 500 students per upload
                </span>
              </div>
              <div>
                <strong>File Format:</strong>
                <span className="text-muted-foreground ml-2">
                  CSV file with comma-separated values
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Batch Upload Component */}
        <BatchUpload />
      </div>
    </div>
  );
}
