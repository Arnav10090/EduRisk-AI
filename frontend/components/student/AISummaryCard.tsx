"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles } from "lucide-react";

interface AISummaryCardProps {
  summary: string;
}

export function AISummaryCard({ summary }: AISummaryCardProps) {
  return (
    <Card className="border-2 border-[#8B5CF6]/20 bg-gradient-to-br from-[#8B5CF6]/5 to-transparent">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[#8B5CF6]" />
          <CardTitle className="text-lg">AI Risk Assessment</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-base leading-relaxed">{summary}</p>
      </CardContent>
    </Card>
  );
}
