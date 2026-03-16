"use client";

import { useState, useCallback } from "react";
import { DecisionReceipt, DECISION_BG, fetchDecisions } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ReceiptViewer } from "@/components/ReceiptViewer";
import { RefreshCw, ChevronDown, Filter } from "lucide-react";

interface DecisionFeedProps {
  initial: DecisionReceipt[];
}

const DEPARTMENTS = ["All", "HR", "Finance", "Engineering", "Legal", "Marketing", "Default"];
const DECISIONS = ["All", "APPROVE", "REDACT", "BLOCK", "ESCALATE"];

export function DecisionFeed({ initial }: DecisionFeedProps) {
  const [decisions, setDecisions] = useState<DecisionReceipt[]>(initial);
  const [selected, setSelected] = useState<DecisionReceipt | null>(null);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(initial.length);
  const [filterDept, setFilterDept] = useState("All");
  const [filterDecision, setFilterDecision] = useState("All");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchDecisions({
        limit: 50,
        offset: 0,
        department: filterDept === "All" ? undefined : filterDept,
        decision: filterDecision === "All" ? undefined : filterDecision,
      });
      setDecisions(data);
      setOffset(data.length);
    } finally {
      setLoading(false);
    }
  }, [filterDept, filterDecision]);

  const loadMore = async () => {
    setLoading(true);
    try {
      const data = await fetchDecisions({
        limit: 50,
        offset,
        department: filterDept === "All" ? undefined : filterDept,
        decision: filterDecision === "All" ? undefined : filterDecision,
      });
      setDecisions((prev) => [...prev, ...data]);
      setOffset((prev) => prev + data.length);
    } finally {
      setLoading(false);
    }
  };

  const applyFilter = async (dept: string, dec: string) => {
    setFilterDept(dept);
    setFilterDecision(dec);
    setLoading(true);
    try {
      const data = await fetchDecisions({
        limit: 50,
        offset: 0,
        department: dept === "All" ? undefined : dept,
        decision: dec === "All" ? undefined : dec,
      });
      setDecisions(data);
      setOffset(data.length);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <Filter className="w-4 h-4 text-slate-500" />
        <div className="flex gap-1 flex-wrap">
          {DEPARTMENTS.map((d) => (
            <button
              key={d}
              onClick={() => applyFilter(d, filterDecision)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                filterDept === d
                  ? "bg-indigo-600 text-white"
                  : "bg-[#1e1e2e] text-slate-400 hover:text-white"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
        <div className="w-px h-4 bg-[#1e1e2e]" />
        <div className="flex gap-1 flex-wrap">
          {DECISIONS.map((d) => (
            <button
              key={d}
              onClick={() => applyFilter(filterDept, d)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                filterDecision === d
                  ? "bg-indigo-600 text-white"
                  : "bg-[#1e1e2e] text-slate-400 hover:text-white"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
        <div className="ml-auto">
          <Button variant="outline" size="sm" onClick={refresh} disabled={loading}>
            <RefreshCw className={`w-3 h-3 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Feed table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#1e1e2e]">
                  <th className="text-left p-3 text-xs text-slate-500 uppercase tracking-wide">Time</th>
                  <th className="text-left p-3 text-xs text-slate-500 uppercase tracking-wide">Department</th>
                  <th className="text-left p-3 text-xs text-slate-500 uppercase tracking-wide">Decision</th>
                  <th className="text-left p-3 text-xs text-slate-500 uppercase tracking-wide">Risk</th>
                  <th className="text-left p-3 text-xs text-slate-500 uppercase tracking-wide">Entities</th>
                  <th className="text-left p-3 text-xs text-slate-500 uppercase tracking-wide">Preview</th>
                  <th className="text-left p-3 text-xs text-slate-500 uppercase tracking-wide">Latency</th>
                </tr>
              </thead>
              <tbody>
                {decisions.map((d) => (
                  <tr
                    key={d.request_id}
                    onClick={() => setSelected(d)}
                    className="border-b border-[#1e1e2e] hover:bg-[#1e1e2e] cursor-pointer transition-colors"
                  >
                    <td className="p-3 text-xs text-slate-500 whitespace-nowrap">
                      {new Date(d.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="p-3">
                      <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                        {d.department}
                      </span>
                    </td>
                    <td className="p-3">
                      <Badge className={DECISION_BG[d.decision]}>
                        {d.decision}
                      </Badge>
                    </td>
                    <td className="p-3">
                      <span className={`text-xs font-mono font-bold ${
                        d.risk_score >= 0.8 ? "text-red-400" :
                        d.risk_score >= 0.5 ? "text-amber-400" : "text-green-400"
                      }`}>
                        {d.risk_score.toFixed(2)}
                      </span>
                    </td>
                    <td className="p-3 text-xs text-slate-400">
                      {d.detected_entities.length > 0 ? (
                        <span className="bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded">
                          {d.detected_entities.length}
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="p-3 text-xs text-slate-400 max-w-xs">
                      <span className="truncate block" style={{ maxWidth: "200px" }}>
                        {d.prompt_preview || "—"}
                      </span>
                    </td>
                    <td className="p-3 text-xs text-slate-500">
                      {d.latency_ms ? `${d.latency_ms}ms` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {decisions.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              No decisions found for selected filters.
            </div>
          )}

          <div className="p-4 flex justify-center border-t border-[#1e1e2e]">
            <Button variant="ghost" size="sm" onClick={loadMore} disabled={loading}>
              <ChevronDown className={`w-4 h-4 mr-1.5 ${loading ? "animate-bounce" : ""}`} />
              Load More
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Receipt modal */}
      {selected && (
        <ReceiptViewer
          receipt={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
