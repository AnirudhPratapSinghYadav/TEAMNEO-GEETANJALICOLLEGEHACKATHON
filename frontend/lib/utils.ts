import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Use Next.js proxy route so browser requests don't cross port boundaries
export const API_BASE = "/api/proxy";

export type DecisionType = "APPROVE" | "REDACT" | "BLOCK" | "ESCALATE";

export interface Entity {
  entity_type: string;
  category: string;
  value_masked: string;
  confidence: number;
}

export interface DecisionReceipt {
  request_id: string;
  timestamp: string;
  department: string;
  user_id?: string;
  model?: string;
  prompt_preview?: string;
  decision: DecisionType;
  risk_score: number;
  detected_entities: Entity[];
  policy_matches: string[];
  remediation: string[];
  explanation: string;
  latency_ms?: number;
  tokens_input?: number;
  tokens_output?: number;
  upstream_model?: string;
}

export interface Stats {
  total_requests: number;
  by_decision: Record<string, number>;
  by_department: Record<string, number>;
  avg_risk_score: number;
  avg_latency_ms: number;
  top_entity_types: { type: string; count: number }[];
  recent_decisions: DecisionReceipt[];
}

export interface AnalyzeResult {
  request_id: string;
  decision: DecisionType;
  risk_score: number;
  entities: Entity[];
  policy_matches: string[];
  remediation: string[];
  explanation: string;
  redacted_prompt?: string;
  latency_ms: number;
}

export const DECISION_COLORS: Record<DecisionType, string> = {
  APPROVE: "#22c55e",
  REDACT: "#f59e0b",
  BLOCK: "#ef4444",
  ESCALATE: "#a855f7",
};

export const DECISION_BG: Record<DecisionType, string> = {
  APPROVE: "bg-green-500/10 text-green-400 border border-green-500/20",
  REDACT: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  BLOCK: "bg-red-500/10 text-red-400 border border-red-500/20",
  ESCALATE: "bg-purple-500/10 text-purple-400 border border-purple-500/20",
};

export const CATEGORY_COLORS: Record<string, string> = {
  PII: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  CREDENTIAL: "bg-red-500/10 text-red-400 border border-red-500/20",
  INJECTION: "bg-orange-500/10 text-orange-400 border border-orange-500/20",
  SENSITIVE: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
};

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function fetchDecisions(params?: {
  limit?: number;
  offset?: number;
  department?: string;
  decision?: string;
}): Promise<DecisionReceipt[]> {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  if (params?.department) query.set("department", params.department);
  if (params?.decision) query.set("decision", params.decision);
  const res = await fetch(`${API_BASE}/decisions?${query}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch decisions");
  return res.json();
}

export async function analyzePrompt(data: {
  prompt: string;
  department?: string;
  model?: string;
}): Promise<AnalyzeResult> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to analyze prompt");
  return res.json();
}
