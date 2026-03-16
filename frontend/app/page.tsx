"use client";

import { useState, useEffect, useCallback } from "react";
import { Stats, DecisionReceipt, fetchStats, fetchDecisions } from "@/lib/utils";
import { StatsCards } from "@/components/StatsCards";
import { DecisionFeed } from "@/components/DecisionFeed";
import { PromptSandbox } from "@/components/PromptSandbox";
import { RedTeamPanel } from "@/components/RedTeamPanel";
import {
  LayoutDashboard, Activity, Terminal, Shield, RefreshCw, Loader2
} from "lucide-react";

type Tab = "overview" | "decisions" | "sandbox" | "redteam";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "overview", label: "Overview", icon: <LayoutDashboard className="w-4 h-4" /> },
  { id: "decisions", label: "Decision Feed", icon: <Activity className="w-4 h-4" /> },
  { id: "sandbox", label: "Prompt Sandbox", icon: <Terminal className="w-4 h-4" /> },
  { id: "redteam", label: "Red Team", icon: <Shield className="w-4 h-4" /> },
];

export default function Home() {
  const [tab, setTab] = useState<Tab>("overview");
  const [stats, setStats] = useState<Stats | null>(null);
  const [decisions, setDecisions] = useState<DecisionReceipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, d] = await Promise.all([
        fetchStats(),
        fetchDecisions({ limit: 50 }),
      ]);
      setStats(s);
      setDecisions(d);
      setLastRefresh(new Date());
    } catch {
      setError("Cannot connect to AEGIS backend. Make sure the server is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  return (
    <div className="min-h-screen" style={{ background: "var(--background)" }}>
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-[#1e1e2e] backdrop-blur-sm" style={{ background: "rgba(10,10,15,0.9)" }}>
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-600">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-bold text-white text-sm tracking-tight">AEGIS</span>
              <span className="text-slate-500 text-xs ml-2">AI Governance Proxy Hub</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {stats && (
              <div className="hidden md:flex items-center gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                  {stats.total_requests.toLocaleString()} total
                </span>
                <span>•</span>
                <span>Updated {lastRefresh.toLocaleTimeString()}</span>
              </div>
            )}
            <button
              onClick={loadData}
              disabled={loading}
              className="p-1.5 rounded-lg hover:bg-[#1e1e2e] text-slate-400 hover:text-white transition-colors"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Navigation tabs */}
      <div className="border-b border-[#1e1e2e]" style={{ background: "rgba(10,10,15,0.95)" }}>
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex gap-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  tab === t.id
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-slate-500 hover:text-slate-300"
                }`}
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-sm flex items-center gap-3">
            <Shield className="w-5 h-5 shrink-0" />
            <div>
              <p className="font-medium">Backend Connection Error</p>
              <p className="text-xs text-red-400/70 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {loading && !stats ? (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-400 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">Loading AEGIS dashboard...</p>
            </div>
          </div>
        ) : (
          <>
            {tab === "overview" && stats && <StatsCards stats={stats} />}
            {tab === "decisions" && <DecisionFeed initial={decisions} />}
            {tab === "sandbox" && <PromptSandbox />}
            {tab === "redteam" && <RedTeamPanel />}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1e1e2e] mt-12 py-4 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-slate-600">
          <span>AEGIS v1.0.0 — AI Governance Proxy Hub</span>
          <span>Team Neo • Geetanjali College Hackathon 2024</span>
        </div>
      </footer>
    </div>
  );
}
