"use client";

import { usePathname } from "next/navigation";
import { NavigationBar } from "./NavigationBar";

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const pathname = usePathname();
  const showNavigation = pathname !== "/" && pathname !== "/login";

  return (
    <div className="min-h-screen flex flex-col">
      {showNavigation && <NavigationBar />}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}
