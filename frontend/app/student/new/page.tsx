"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowLeft, ArrowRight, CheckCircle, Loader2 } from "lucide-react";
import { z } from "zod";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Base schema object without refinements
const baseStudentSchema = z.object({
  // Step 1: Academic Info
  name: z.string().min(1, "Name is required").max(255, "Name is too long"),
  course_type: z.string().min(1, "Course type is required").max(100, "Course type is too long"),
  institute_tier: z.coerce
    .number()
    .int()
    .min(1, "Institute tier must be between 1 and 3")
    .max(3, "Institute tier must be between 1 and 3"),
  institute_name: z.string().max(255, "Institute name is too long").optional(),
  cgpa: z.coerce
    .number()
    .nonnegative("CGPA must be non-negative")
    .optional()
    .nullable(),
  cgpa_scale: z.coerce
    .number()
    .positive("CGPA scale must be positive")
    .default(10.0),
  year_of_grad: z.coerce
    .number()
    .int()
    .min(2020, "Year of graduation must be between 2020 and 2030")
    .max(2030, "Year of graduation must be between 2020 and 2030"),

  // Step 2: Internship & Skills
  internship_count: z.coerce
    .number()
    .int()
    .nonnegative("Internship count must be non-negative")
    .default(0),
  internship_months: z.coerce
    .number()
    .int()
    .nonnegative("Internship months must be non-negative")
    .default(0),
  internship_employer_type: z.string().max(100, "Employer type is too long").optional(),
  certifications: z.coerce
    .number()
    .int()
    .nonnegative("Certifications must be non-negative")
    .default(0),
  region: z.string().max(100, "Region is too long").optional(),

  // Step 3: Loan Details
  loan_amount: z.coerce
    .number()
    .nonnegative("Loan amount must be non-negative")
    .optional()
    .nullable(),
  loan_emi: z.coerce
    .number()
    .nonnegative("Loan EMI must be non-negative")
    .optional()
    .nullable(),
});

// Full schema with CGPA validation refinement
const studentSchema = baseStudentSchema.refine(
  (data) => {
    // CGPA must be <= cgpa_scale
    if (data.cgpa !== null && data.cgpa !== undefined && data.cgpa > data.cgpa_scale) {
      return false;
    }
    return true;
  },
  {
    message: "CGPA cannot exceed CGPA scale",
    path: ["cgpa"],
  }
);

type StudentFormData = z.infer<typeof studentSchema>;

// Step-specific schemas for validation
const step1Schema = baseStudentSchema.pick({
  name: true,
  course_type: true,
  institute_tier: true,
  institute_name: true,
  cgpa: true,
  cgpa_scale: true,
  year_of_grad: true,
}).refine(
  (data) => {
    // CGPA must be <= cgpa_scale
    if (data.cgpa !== null && data.cgpa !== undefined && data.cgpa > data.cgpa_scale) {
      return false;
    }
    return true;
  },
  {
    message: "CGPA cannot exceed CGPA scale",
    path: ["cgpa"],
  }
);

const step2Schema = baseStudentSchema.pick({
  internship_count: true,
  internship_months: true,
  internship_employer_type: true,
  certifications: true,
  region: true,
});

const step3Schema = baseStudentSchema.pick({
  loan_amount: true,
  loan_emi: true,
});

export default function NewPredictionPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Form data
  const [formData, setFormData] = useState<Partial<StudentFormData>>({
    cgpa_scale: 10.0,
    internship_count: 0,
    internship_months: 0,
    certifications: 0,
  });

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  const updateField = (field: keyof StudentFormData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateStep = (step: number): boolean => {
    setErrors({});
    
    try {
      if (step === 1) {
        step1Schema.parse(formData);
      } else if (step === 2) {
        step2Schema.parse(formData);
      } else if (step === 3) {
        step3Schema.parse(formData);
      }
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: Record<string, string> = {};
        error.errors.forEach((err) => {
          if (err.path.length > 0) {
            newErrors[err.path[0] as string] = err.message;
          }
        });
        setErrors(newErrors);
      }
      return false;
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep((prev) => prev - 1);
  };

  const handleSubmit = async () => {
    // Validate all steps
    if (!validateStep(1) || !validateStep(2) || !validateStep(3)) {
      return;
    }

    // Final validation with full schema
    try {
      const validatedData = studentSchema.parse(formData);
      
      setIsSubmitting(true);
      setSubmitError(null);

      // POST to /api/predict
      const response = await fetch(`${API_BASE_URL}/api/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(validatedData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to create prediction: ${response.statusText}`
        );
      }

      const result = await response.json();
      
      // Navigate to student detail page
      if (result.student_id) {
        router.push(`/student/${result.student_id}`);
      } else {
        throw new Error("No student ID returned from API");
      }
    } catch (error) {
      console.error("Error submitting form:", error);
      setSubmitError(
        error instanceof Error ? error.message : "Failed to submit prediction"
      );
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 max-w-3xl">
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
          <h1 className="text-3xl font-bold tracking-tight">New Student Prediction</h1>
          <p className="text-muted-foreground">
            Enter student information to generate a placement risk assessment
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center flex-1">
                <div
                  className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    currentStep >= step
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-muted bg-background text-muted-foreground"
                  }`}
                >
                  {currentStep > step ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <span className="font-semibold">{step}</span>
                  )}
                </div>
                {step < 3 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
                      currentStep > step ? "bg-primary" : "bg-muted"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-sm font-medium">Academic Info</span>
            <span className="text-sm font-medium">Internship & Skills</span>
            <span className="text-sm font-medium">Loan Details</span>
          </div>
        </div>

        {/* Form Card */}
        <Card>
          <CardHeader>
            <CardTitle>
              {currentStep === 1 && "Step 1: Academic Information"}
              {currentStep === 2 && "Step 2: Internship & Skills"}
              {currentStep === 3 && "Step 3: Loan Details"}
            </CardTitle>
            <CardDescription>
              {currentStep === 1 &&
                "Enter the student's academic background and institution details"}
              {currentStep === 2 &&
                "Provide information about internships, certifications, and location"}
              {currentStep === 3 &&
                "Enter loan amount and EMI details (optional)"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Step 1: Academic Info */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    Student Name <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="name"
                    placeholder="Enter full name"
                    value={formData.name || ""}
                    onChange={(e) => updateField("name", e.target.value)}
                  />
                  {errors.name && (
                    <p className="text-sm text-destructive">{errors.name}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="course_type">
                    Course Type <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="course_type"
                    placeholder="e.g., Engineering, MBA, BBA"
                    value={formData.course_type || ""}
                    onChange={(e) => updateField("course_type", e.target.value)}
                  />
                  {errors.course_type && (
                    <p className="text-sm text-destructive">{errors.course_type}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="institute_tier">
                    Institute Tier <span className="text-destructive">*</span>
                  </Label>
                  <Select
                    value={formData.institute_tier?.toString()}
                    onValueChange={(value) => updateField("institute_tier", parseInt(value))}
                  >
                    <SelectTrigger id="institute_tier">
                      <SelectValue placeholder="Select tier (1 = highest)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">Tier 1 (Top institutions)</SelectItem>
                      <SelectItem value="2">Tier 2 (Good institutions)</SelectItem>
                      <SelectItem value="3">Tier 3 (Other institutions)</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.institute_tier && (
                    <p className="text-sm text-destructive">{errors.institute_tier}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="institute_name">Institute Name</Label>
                  <Input
                    id="institute_name"
                    placeholder="e.g., IIT Delhi, BITS Pilani"
                    value={formData.institute_name || ""}
                    onChange={(e) => updateField("institute_name", e.target.value)}
                  />
                  {errors.institute_name && (
                    <p className="text-sm text-destructive">{errors.institute_name}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cgpa">CGPA</Label>
                    <Input
                      id="cgpa"
                      type="number"
                      step="0.01"
                      placeholder="e.g., 8.5"
                      value={formData.cgpa?.toString() || ""}
                      onChange={(e) =>
                        updateField("cgpa", e.target.value ? parseFloat(e.target.value) : null)
                      }
                    />
                    {errors.cgpa && (
                      <p className="text-sm text-destructive">{errors.cgpa}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cgpa_scale">
                      CGPA Scale <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      id="cgpa_scale"
                      type="number"
                      step="0.1"
                      placeholder="e.g., 10.0 or 4.0"
                      value={formData.cgpa_scale?.toString() || ""}
                      onChange={(e) =>
                        updateField("cgpa_scale", parseFloat(e.target.value))
                      }
                    />
                    {errors.cgpa_scale && (
                      <p className="text-sm text-destructive">{errors.cgpa_scale}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="year_of_grad">
                    Year of Graduation <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="year_of_grad"
                    type="number"
                    placeholder="e.g., 2025"
                    value={formData.year_of_grad?.toString() || ""}
                    onChange={(e) =>
                      updateField("year_of_grad", parseInt(e.target.value))
                    }
                  />
                  {errors.year_of_grad && (
                    <p className="text-sm text-destructive">{errors.year_of_grad}</p>
                  )}
                </div>
              </div>
            )}

            {/* Step 2: Internship & Skills */}
            {currentStep === 2 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="internship_count">Number of Internships</Label>
                  <Input
                    id="internship_count"
                    type="number"
                    min="0"
                    placeholder="e.g., 2"
                    value={formData.internship_count?.toString() || ""}
                    onChange={(e) =>
                      updateField("internship_count", parseInt(e.target.value) || 0)
                    }
                  />
                  {errors.internship_count && (
                    <p className="text-sm text-destructive">{errors.internship_count}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="internship_months">
                    Total Internship Duration (months)
                  </Label>
                  <Input
                    id="internship_months"
                    type="number"
                    min="0"
                    placeholder="e.g., 6"
                    value={formData.internship_months?.toString() || ""}
                    onChange={(e) =>
                      updateField("internship_months", parseInt(e.target.value) || 0)
                    }
                  />
                  {errors.internship_months && (
                    <p className="text-sm text-destructive">{errors.internship_months}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="internship_employer_type">Internship Employer Type</Label>
                  <Select
                    value={formData.internship_employer_type || ""}
                    onValueChange={(value) => updateField("internship_employer_type", value)}
                  >
                    <SelectTrigger id="internship_employer_type">
                      <SelectValue placeholder="Select employer type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="MNC">MNC (Multinational Corporation)</SelectItem>
                      <SelectItem value="Startup">Startup</SelectItem>
                      <SelectItem value="PSU">PSU (Public Sector)</SelectItem>
                      <SelectItem value="NGO">NGO</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.internship_employer_type && (
                    <p className="text-sm text-destructive">
                      {errors.internship_employer_type}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="certifications">Number of Certifications</Label>
                  <Input
                    id="certifications"
                    type="number"
                    min="0"
                    placeholder="e.g., 3"
                    value={formData.certifications?.toString() || ""}
                    onChange={(e) =>
                      updateField("certifications", parseInt(e.target.value) || 0)
                    }
                  />
                  {errors.certifications && (
                    <p className="text-sm text-destructive">{errors.certifications}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="region">Region</Label>
                  <Select
                    value={formData.region || ""}
                    onValueChange={(value) => updateField("region", value)}
                  >
                    <SelectTrigger id="region">
                      <SelectValue placeholder="Select region" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="North">North</SelectItem>
                      <SelectItem value="South">South</SelectItem>
                      <SelectItem value="East">East</SelectItem>
                      <SelectItem value="West">West</SelectItem>
                      <SelectItem value="Central">Central</SelectItem>
                      <SelectItem value="Northeast">Northeast</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.region && (
                    <p className="text-sm text-destructive">{errors.region}</p>
                  )}
                </div>
              </div>
            )}

            {/* Step 3: Loan Details */}
            {currentStep === 3 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="loan_amount">Loan Amount (INR)</Label>
                  <Input
                    id="loan_amount"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="e.g., 500000"
                    value={formData.loan_amount?.toString() || ""}
                    onChange={(e) =>
                      updateField(
                        "loan_amount",
                        e.target.value ? parseFloat(e.target.value) : null
                      )
                    }
                  />
                  {errors.loan_amount && (
                    <p className="text-sm text-destructive">{errors.loan_amount}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="loan_emi">Monthly EMI (INR)</Label>
                  <Input
                    id="loan_emi"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="e.g., 15000"
                    value={formData.loan_emi?.toString() || ""}
                    onChange={(e) =>
                      updateField(
                        "loan_emi",
                        e.target.value ? parseFloat(e.target.value) : null
                      )
                    }
                  />
                  {errors.loan_emi && (
                    <p className="text-sm text-destructive">{errors.loan_emi}</p>
                  )}
                </div>

                <div className="rounded-lg bg-muted p-4">
                  <p className="text-sm text-muted-foreground">
                    <strong>Note:</strong> Loan details are optional but help in calculating
                    EMI affordability ratio for better risk assessment.
                  </p>
                </div>
              </div>
            )}

            {/* Submit Error */}
            {submitError && (
              <div className="mt-4 p-4 rounded-lg bg-destructive/10 border border-destructive">
                <p className="text-sm text-destructive">{submitError}</p>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between mt-6">
              <Button
                variant="outline"
                onClick={handleBack}
                disabled={currentStep === 1 || isSubmitting}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>

              {currentStep < 3 ? (
                <Button onClick={handleNext}>
                  Next
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button onClick={handleSubmit} disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Submit Prediction
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
