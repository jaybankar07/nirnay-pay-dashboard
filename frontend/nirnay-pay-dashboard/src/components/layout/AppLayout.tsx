import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import { HealthIndicator } from "@/components/common/HealthIndicator";
import { SimulateEventDialog } from "@/components/common/SimulateEventDialog";
import { MERCHANT_ID } from "@/lib/api/config";
import { Toaster } from "@/components/ui/sonner";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  FileText,
  BarChart3,
  History,
  ShieldCheck,
  Building2,
  Menu,
  X,
  ChevronRight,
  PlusCircle,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AppLayoutProps {
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { name: "Overview", to: "/", icon: LayoutDashboard },
  { name: "Recovery Cases", to: "/cases", icon: FileText },
  { name: "Analytics", to: "/analytics", icon: BarChart3 },
  { name: "Audit Log", to: "/audit", icon: History },
];

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [simulateOpen, setSimulateOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const isCurrentRoute = (path: string) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  const getBreadcrumbs = () => {
    const parts = location.pathname.split("/").filter(Boolean);
    if (parts.length === 0) return [{ name: "Overview", path: "/" }];

    const crumbs = [{ name: "Overview", path: "/" }];
    let currentPath = "";

    for (const part of parts) {
      currentPath += `/${part}`;
      if (part === "cases") {
        crumbs.push({ name: "Recovery Cases", path: "/cases" });
      } else if (part === "analytics") {
        crumbs.push({ name: "Analytics", path: "/analytics" });
      } else if (part === "audit") {
        crumbs.push({ name: "Audit", path: "/audit" });
      } else {
        crumbs.push({ name: `Case ${part}`, path: currentPath });
      }
    }
    return crumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col antialiased selection:bg-primary/20">
      <Toaster position="top-right" richColors />

      <SimulateEventDialog
        open={simulateOpen}
        onOpenChange={setSimulateOpen}
        merchantId={MERCHANT_ID}
        onSuccess={(caseId) => {
          navigate({ to: `/cases/${caseId}` });
        }}
      />

      {/* Top Header */}
      <header className="sticky top-0 z-40 h-14 border-b border-border/80 bg-background/95 backdrop-blur-sm flex items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="md:hidden p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 rounded-md bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs shadow-xs">
              NP
            </div>
            <div className="flex flex-col">
              <span className="font-bold tracking-tight text-sm text-foreground group-hover:text-primary transition-colors">
                Nirnay Pay
              </span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">
                RecoveryOS
              </span>
            </div>
          </Link>
        </div>

        {/* Center/Right Items: Merchant Context, Simulate Trigger, Health */}
        <div className="flex items-center gap-2.5 sm:gap-4">
          <Button
            size="sm"
            onClick={() => setSimulateOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs h-8 shadow-xs"
          >
            <PlusCircle className="w-3.5 h-3.5 mr-1.5" /> Simulate Live Event
          </Button>

          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded-md bg-muted/60 border border-border/60 text-muted-foreground">
            <Building2 className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Merchant: <strong className="text-foreground">{MERCHANT_ID}</strong></span>
          </div>

          <HealthIndicator />
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar */}
        <aside className="hidden md:flex flex-col w-60 border-r border-border/80 bg-card p-4 justify-between">
          <div className="space-y-6">
            <div>
              <p className="px-3 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Navigation
              </p>
              <nav className="space-y-1">
                {NAV_ITEMS.map((item) => {
                  const active = isCurrentRoute(item.to);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-md transition-colors",
                        active
                          ? "bg-primary text-primary-foreground font-semibold shadow-xs"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground"
                      )}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="pt-4 border-t border-border/60 text-[11px] text-muted-foreground space-y-1">
            <div className="flex items-center gap-1.5 font-medium text-foreground">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Enterprise Recovery Engine</span>
            </div>
            <p>Version 1.0.0 (Production)</p>
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 z-50 bg-background/80 backdrop-blur-xs flex">
            <div className="w-64 bg-card border-r border-border p-4 flex flex-col justify-between shadow-xl">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <span className="font-bold text-sm">Nirnay Pay Menu</span>
                  <button onClick={() => setMobileMenuOpen(false)} className="p-1 text-muted-foreground">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <nav className="space-y-1">
                  {NAV_ITEMS.map((item) => {
                    const active = isCurrentRoute(item.to);
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.to}
                        to={item.to}
                        onClick={() => setMobileMenuOpen(false)}
                        className={cn(
                          "flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-md",
                          active
                            ? "bg-primary text-primary-foreground font-semibold"
                            : "text-muted-foreground hover:bg-accent hover:text-foreground"
                        )}
                      >
                        <Icon className="w-4 h-4" />
                        <span>{item.name}</span>
                      </Link>
                    );
                  })}
                </nav>
              </div>

              <div className="pt-4 border-t border-border text-xs text-muted-foreground">
                <p className="font-mono">Merchant: {MERCHANT_ID}</p>
              </div>
            </div>
            <div className="flex-1" onClick={() => setMobileMenuOpen(false)} />
          </div>
        )}

        {/* Main Content View */}
        <main className="flex-1 overflow-y-auto bg-background/50 p-4 sm:p-6 md:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Breadcrumbs */}
            <nav className="flex items-center space-x-1.5 text-xs text-muted-foreground">
              {breadcrumbs.map((crumb, idx) => (
                <React.Fragment key={crumb.path}>
                  {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/60" />}
                  {idx === breadcrumbs.length - 1 ? (
                    <span className="font-medium text-foreground">{crumb.name}</span>
                  ) : (
                    <Link to={crumb.path} className="hover:text-foreground transition-colors">
                      {crumb.name}
                    </Link>
                  )}
                </React.Fragment>
              ))}
            </nav>

            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
