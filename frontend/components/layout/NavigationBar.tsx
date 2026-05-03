"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Menu, X, User as UserIcon, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/lib/auth";

interface NavigationLink {
  href: string;
  label: string;
  icon?: React.ReactNode;
}

const navigationLinks: NavigationLink[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/student/new", label: "New Student" },
  { href: "/student/batch", label: "Batch Upload" },
  { href: "/alerts", label: "Alerts" },
];

export function NavigationBar() {
  const pathname = usePathname();
  const [highRiskCount, setHighRiskCount] = useState<number>(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, loading, logout } = useAuth();

  // Fetch high-risk alert count
  useEffect(() => {
    if (loading || !isAuthenticated) {
      setHighRiskCount(0);
      return;
    }

    const fetchAlertCount = async () => {
      try {
        const response = await apiClient("/api/alerts?threshold=high&limit=500");
        if (response.ok) {
          const alerts = await response.json();
          setHighRiskCount(Array.isArray(alerts) ? alerts.length : 0);
        } else {
          setHighRiskCount(0);
        }
      } catch (error) {
        console.error("Failed to fetch alert count:", error);
        setHighRiskCount(0);
      }
    };

    void fetchAlertCount();
    
    // Refresh alert count every 30 seconds
    const interval = setInterval(fetchAlertCount, 30000);
    return () => clearInterval(interval);
  }, [isAuthenticated, loading, pathname]);

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/" || pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  };

  const handleLinkClick = () => {
    setMobileMenuOpen(false);
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo/Brand */}
          <Link 
            href="/dashboard" 
            className="flex items-center space-x-2 font-bold text-xl hover:opacity-80 transition-opacity"
          >
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary text-primary-foreground">
              <span className="text-sm font-bold">ER</span>
            </div>
            <span className="hidden sm:inline-block">EduRisk AI</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navigationLinks.map((link) => {
              const active = isActive(link.href);
              const isAlertsLink = link.href === "/alerts";
              
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "relative px-4 py-2 rounded-md text-sm font-medium transition-colors",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <span className="flex items-center gap-2">
                    {link.icon}
                    {link.label}
                    {isAlertsLink && highRiskCount > 0 && (
                      <Badge 
                        variant="destructive" 
                        className="ml-1 px-2 py-0.5 text-xs"
                      >
                        {highRiskCount}
                      </Badge>
                    )}
                  </span>
                </Link>
              );
            })}
            {/* User Info and Logout (Requirement 24.5) */}
            {isAuthenticated && user && (
              <div className="flex items-center space-x-2 border-l pl-4 ml-2">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent/50">
                  <UserIcon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{user.username}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="gap-2 hover:bg-destructive/10 hover:text-destructive"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden lg:inline">Logout</span>
                </Button>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 space-y-1 border-t">
            {navigationLinks.map((link) => {
              const active = isActive(link.href);
              const isAlertsLink = link.href === "/alerts";
              
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={handleLinkClick}
                  className={cn(
                    "flex items-center justify-between px-4 py-3 rounded-md text-sm font-medium transition-colors",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <span className="flex items-center gap-2">
                    {link.icon}
                    {link.label}
                  </span>
                  {isAlertsLink && highRiskCount > 0 && (
                    <Badge 
                      variant="destructive" 
                      className="px-2 py-0.5 text-xs"
                    >
                      {highRiskCount}
                    </Badge>
                  )}
                </Link>
              );
            })}
            {/* User Info and Logout - Mobile (Requirement 24.5) */}
            {isAuthenticated && user && (
              <div className="pt-4 mt-4 border-t space-y-2">
                <div className="flex items-center gap-2 px-4 py-2 rounded-md bg-accent/50">
                  <UserIcon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{user.username}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    handleLinkClick();
                    logout();
                  }}
                  className="w-full justify-start gap-2 hover:bg-destructive/10 hover:text-destructive"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
