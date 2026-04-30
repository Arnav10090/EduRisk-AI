"use client";

import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

interface AlertBannerProps {
  alertCount: number;
}

export function AlertBanner({ alertCount }: AlertBannerProps) {
  const router = useRouter();

  if (alertCount === 0) {
    return null;
  }

  return (
    <Alert variant="destructive" className="bg-[#E24B4A] text-white border-[#E24B4A]">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>High-Risk Alerts</AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>
          {alertCount} student{alertCount !== 1 ? "s" : ""} require immediate attention
        </span>
        <Button
          variant="outline"
          size="sm"
          className="ml-4 bg-white text-[#E24B4A] hover:bg-white/90"
          onClick={() => router.push("/alerts")}
        >
          View Alerts
        </Button>
      </AlertDescription>
    </Alert>
  );
}
