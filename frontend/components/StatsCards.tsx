"use client";

import { Stats, DECISION_COLORS } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import {
  ShieldCheck, ShieldAlert, ShieldX, AlertTriangle,
  Activity, Clock, Zap,
} from "lucide-react";

interface StatsCardsProps {
  stats: Stats;
}

const DECISION_ICONS: Record<string, React.ReactNode> = {
  APPROVE: <ShieldCheck className="w-5 h-5 text-green-400" />,
  REDACT: <ShieldAlert className="w-5 h-5 text-amber-400" />,
  BLOCK: <ShieldX className="w-5 h-5 text-red-400" />,
  ESCALATE: <AlertTriangle className="w-5 h-5 text-purple-400" />,
};

const DECISION_TEXT: Record<string, string> = {
  APPROVE: "text-green-400",
  REDACT: "text-amber-400",
  BLOCK: "text-red-400",
  ESCALATE: "text-purple-400",
};

export function StatsCards({ stats }: StatsCardsProps) {
  const decisions = Object.entries(stats.by_decision);
  const pieData = decisions.map(([name, value]) => ({ name, value }));
  const deptData = Object.entries(stats.by_department).map(([name, value]) => ({ name, value }));

  const blockRate = stats.total_requests
    ? (((stats.by_decision.BLOCK || 0) / stats.total_requests) * 100).toFixed(1)
    : "0";

  return (
    <div className="space-y-6">
      {/* Top KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10">
                <Activity className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Total Requests</p>
                <p className="text-2xl font-bold text-white">{stats.total_requests.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/10">
                <ShieldX className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Block Rate</p>
                <p className="text-2xl font-bold text-red-400">{blockRate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <Zap className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Avg Risk Score</p>
                <p className="text-2xl font-bold text-amber-400">{stats.avg_risk_score.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <Clock className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Avg Latency</p>
                <p className="text-2xl font-bold text-green-400">{stats.avg_latency_ms.toFixed(0)}ms</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Decision breakdown + department */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Decision counts */}
        <Card>
          <CardHeader>
            <CardTitle>Decisions by Type</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-3">
              {decisions.map(([decision, count]) => (
                <div key={decision} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {DECISION_ICONS[decision]}
                    <span className={`text-sm font-medium ${DECISION_TEXT[decision] || "text-slate-300"}`}>
                      {decision}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 rounded-full bg-[#1e1e2e]">
                      <div
                        className="h-1.5 rounded-full"
                        style={{
                          width: `${(count / stats.total_requests) * 100}%`,
                          backgroundColor: DECISION_COLORS[decision as keyof typeof DECISION_COLORS] || "#64748b",
                        }}
                      />
                    </div>
                    <span className="text-sm font-bold text-white w-12 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Pie chart */}
        <Card>
          <CardHeader>
            <CardTitle>Decision Distribution</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 flex justify-center">
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={DECISION_COLORS[entry.name as keyof typeof DECISION_COLORS] || "#64748b"}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#13131a", border: "1px solid #1e1e2e", borderRadius: "8px" }}
                  labelStyle={{ color: "#e2e8f0" }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Department bar */}
        <Card>
          <CardHeader>
            <CardTitle>Requests by Department</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={deptData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748b" }} />
                <YAxis tick={{ fontSize: 10, fill: "#64748b" }} />
                <Tooltip
                  contentStyle={{ background: "#13131a", border: "1px solid #1e1e2e", borderRadius: "8px" }}
                  labelStyle={{ color: "#e2e8f0" }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Top entity types */}
      <Card>
        <CardHeader>
          <CardTitle>Top Detected Entity Types</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {stats.top_entity_types.slice(0, 10).map((e) => (
              <div key={e.type} className="flex items-center justify-between p-2 rounded-lg bg-[#1e1e2e]">
                <span className="text-xs text-slate-400 truncate">{e.type.replace(/_/g, " ")}</span>
                <span className="text-xs font-bold text-indigo-400 ml-1">{e.count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
