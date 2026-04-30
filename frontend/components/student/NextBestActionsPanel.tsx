"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen,
  Briefcase,
  FileText,
  MessageSquare,
  Users,
  LucideIcon,
} from "lucide-react";

interface Action {
  type: string;
  title: string;
  description: string;
  priority: string;
}

interface NextBestActionsPanelProps {
  actions: Action[];
}

export function NextBestActionsPanel({ actions }: NextBestActionsPanelProps) {
  // Map action types to icons (Requirement 26.6)
  const getActionIcon = (type: string): LucideIcon => {
    switch (type) {
      case "skill_up":
        return BookOpen;
      case "internship":
        return Briefcase;
      case "resume":
        return FileText;
      case "mock_interview":
        return MessageSquare;
      case "recruiter_match":
        return Users;
      default:
        return BookOpen;
    }
  };

  // Map priority to badge color (Requirement 26.6)
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-[#E24B4A] text-white";
      case "medium":
        return "bg-[#F59E0B] text-white";
      case "low":
        return "bg-[#3B82F6] text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  return (
    <div className="rounded-lg border bg-card p-6">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-xl">Recommended Actions</CardTitle>
        <p className="text-sm text-muted-foreground">
          Personalized interventions to improve placement outcomes
        </p>
      </CardHeader>
      <CardContent className="px-0 pb-0">
        <div className="grid gap-4 md:grid-cols-2">
          {actions.map((action, index) => {
            const Icon = getActionIcon(action.type);
            return (
              <Card key={index} className="border-2">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-semibold text-sm leading-tight">
                          {action.title}
                        </h3>
                        <Badge className={getPriorityColor(action.priority)}>
                          {action.priority.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {action.description}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </CardContent>
    </div>
  );
}
