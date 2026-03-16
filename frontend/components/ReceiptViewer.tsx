"use client";

import { DecisionReceipt, DECISION_BG, CATEGORY_COLORS } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { X, Shield, AlertTriangle, Clock, User, Cpu } from "lucide-react";

interface ReceiptViewerProps {
  receipt: DecisionReceipt;
  onClose: () => void;
}

export function ReceiptViewer({ receipt, onClose }: ReceiptViewerProps) {
  const riskColor =
    receipt.risk_score >= 0.8 ? "text-red-400" :
    receipt.risk_score >= 0.5 ? "text-amber-400" : "text-green-400";

  const riskBg =
    receipt.risk_score >= 0.8 ? "bg-red-500" :
    receipt.risk_score >= 0.5 ? "bg-amber-500" : "bg-green-500";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-[#1e1e2e] bg-[#0a0a0f] shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between p-5 border-b border-[#1e1e2e] bg-[#0a0a0f]">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-indigo-400" />
            <div>
              <h2 className="text-base font-bold text-white">Decision Receipt</h2>
              <p className="text-xs text-slate-500 font-mono">{receipt.request_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[#1e1e2e] text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Decision + Risk */}
          <div className="flex items-center gap-4">
            <Badge className={`text-sm px-4 py-2 ${DECISION_BG[receipt.decision]}`}>
              {receipt.decision}
            </Badge>
            <div className="flex-1">
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>Risk Score</span>
                <span className={`font-bold ${riskColor}`}>{receipt.risk_score.toFixed(3)}</span>
              </div>
              <div className="h-2 rounded-full bg-[#1e1e2e] overflow-hidden">
                <div
                  className={`h-2 rounded-full ${riskBg} transition-all`}
                  style={{ width: `${receipt.risk_score * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Meta info */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2 text-slate-400">
              <Clock className="w-4 h-4 text-slate-600" />
              <span className="text-xs">{new Date(receipt.timestamp).toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <User className="w-4 h-4 text-slate-600" />
              <span className="text-xs">{receipt.user_id || "Anonymous"}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <Shield className="w-4 h-4 text-slate-600" />
              <span className="text-xs">{receipt.department}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <Cpu className="w-4 h-4 text-slate-600" />
              <span className="text-xs">{receipt.model || "—"}</span>
            </div>
          </div>

          {/* Prompt preview */}
          {receipt.prompt_preview && (
            <div>
              <h3 className="text-xs text-slate-500 uppercase tracking-wide mb-2">Prompt Preview</h3>
              <div className="p-3 rounded-lg bg-[#1e1e2e] text-sm text-slate-300 font-mono leading-relaxed">
                {receipt.prompt_preview}
              </div>
            </div>
          )}

          {/* Explanation */}
          <div>
            <h3 className="text-xs text-slate-500 uppercase tracking-wide mb-2">Explanation</h3>
            <p className="text-sm text-slate-300 leading-relaxed">{receipt.explanation}</p>
          </div>

          {/* Detected entities */}
          {receipt.detected_entities.length > 0 && (
            <div>
              <h3 className="text-xs text-slate-500 uppercase tracking-wide mb-2">
                Detected Entities ({receipt.detected_entities.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {receipt.detected_entities.map((ent, i) => (
                  <div
                    key={i}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs ${
                      CATEGORY_COLORS[ent.category] || "bg-slate-800 text-slate-300"
                    }`}
                  >
                    <span className="font-medium">{ent.entity_type}</span>
                    <span className="opacity-60">{(ent.confidence * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Policy matches */}
          {receipt.policy_matches.length > 0 && (
            <div>
              <h3 className="text-xs text-slate-500 uppercase tracking-wide mb-2">
                Policy Rules Triggered
              </h3>
              <div className="space-y-1.5">
                {receipt.policy_matches.map((rule, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 p-2.5 rounded-lg bg-[#1e1e2e] text-xs text-slate-300"
                  >
                    <AlertTriangle className="w-3 h-3 text-amber-400 mt-0.5 shrink-0" />
                    {rule}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Remediation */}
          {receipt.remediation.length > 0 && receipt.remediation[0] !== "No remediation required." && (
            <div>
              <h3 className="text-xs text-slate-500 uppercase tracking-wide mb-2">
                Remediation Suggestions
              </h3>
              <div className="space-y-1.5">
                {receipt.remediation.map((rem, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 p-2.5 rounded-lg bg-green-500/5 border border-green-500/10 text-xs text-green-300"
                  >
                    <span className="text-green-500 mt-0.5">→</span>
                    {rem}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Perf stats */}
          <div className="flex gap-4 pt-2 border-t border-[#1e1e2e]">
            {receipt.latency_ms && (
              <div className="text-center">
                <p className="text-xs text-slate-600">Latency</p>
                <p className="text-sm font-bold text-indigo-400">{receipt.latency_ms}ms</p>
              </div>
            )}
            {receipt.tokens_input && (
              <div className="text-center">
                <p className="text-xs text-slate-600">Input Tokens</p>
                <p className="text-sm font-bold text-slate-300">{receipt.tokens_input}</p>
              </div>
            )}
            {receipt.tokens_output !== undefined && receipt.tokens_output > 0 && (
              <div className="text-center">
                <p className="text-xs text-slate-600">Output Tokens</p>
                <p className="text-sm font-bold text-slate-300">{receipt.tokens_output}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
