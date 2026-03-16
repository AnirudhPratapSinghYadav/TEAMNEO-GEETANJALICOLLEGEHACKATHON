"""Receipt generator — produces audit receipts (JSON / PDF) for each intercepted request."""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ReceiptGenerator:
    """Generates comprehensive, explainable governance receipts for every processed prompt."""

    GOVERNANCE_VERSION = "AEGIS v1.0.0"
    POLICY_ENGINE_VERSION = "1.0.0"
    AEGIS_NODE = "aegis-proxy-01"

    # Emoji indicators for decisions in human-readable output
    _DECISION_ICONS: Dict[str, str] = {
        "ALLOW": "✅",
        "BLOCK": "🚫",
        "REDACT": "⚠️",
        "TRANSFORM": "🔄",
    }

    # Risk level ordering for sensitivity mapping
    _RISK_TO_SENSITIVITY: Dict[str, str] = {
        "CRITICAL": "CRITICAL",
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
        "MINIMAL": "LOW",
    }

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def generate(
        self,
        request_id: str,
        user_info: dict,
        original_prompt: str,
        sanitized_prompt: Optional[str],
        detected_entities: List[dict],
        matched_policies: List[dict],
        risk_assessment: dict,
        decision: dict,
        redaction_map: Optional[dict],
        processing_time_ms: int,
        target_model: str,
        forwarded: bool,
        llm_response: Optional[str],
    ) -> dict:
        """Build and return the structured governance receipt."""

        timestamp = datetime.now(timezone.utc)
        receipt_id = self._make_receipt_id(timestamp)

        return {
            "receipt_id": receipt_id,
            "request_id": request_id,
            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "governance_version": self.GOVERNANCE_VERSION,
            "user": self._build_user(user_info),
            "prompt_analysis": self._build_prompt_analysis(
                original_prompt, detected_entities, risk_assessment
            ),
            "policy_evaluation": self._build_policy_evaluation(
                matched_policies, decision
            ),
            "risk_assessment": self._build_risk_assessment(risk_assessment),
            "decision": self._build_decision(decision),
            "redaction_details": self._build_redaction_details(redaction_map),
            "audit_metadata": self._build_audit_metadata(
                processing_time_ms,
                detected_entities,
                target_model,
                forwarded,
                llm_response,
            ),
        }

    def generate_human_readable(self, receipt: dict) -> str:
        """Return a formatted plain-text version of the receipt."""

        sep = "═" * 47

        # --- Header ---
        lines = [
            "",
            sep,
            "  AEGIS GOVERNANCE DECISION RECEIPT",
            f"  Receipt: {receipt['receipt_id']}",
            sep,
            "",
        ]

        # --- Decision summary ---
        action = receipt["decision"]["action"]
        icon = self._DECISION_ICONS.get(action, "")
        risk = receipt["risk_assessment"]
        risk_score = int(round(risk["overall_score"] * 100))
        risk_level = risk["risk_level"]
        lines += [
            f"  Decision: {action} {icon}",
            f"  Risk Score: {risk_score}/100 ({risk_level})",
            "",
        ]

        # --- User / time ---
        user = receipt["user"]
        ts_raw = receipt["timestamp"]
        try:
            dt = datetime.strptime(ts_raw, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            ts_display = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except ValueError:
            ts_display = ts_raw

        lines += [
            f"  User: {user['name']} ({user['department']} Department)",
            f"  Time: {ts_display}",
            "",
        ]

        # --- Detected entities ---
        entities = receipt["prompt_analysis"]["detected_entities"]
        if entities:
            lines.append("  Detected Entities:")
            for ent in entities:
                conf = ent["confidence"]
                preview = ent["value_preview"]
                lines.append(
                    f"  • {ent['type']} (confidence: {conf:.2f}) — \"{preview}\""
                )
            lines.append("")

        # --- Policies matched ---
        policies = receipt["policy_evaluation"]["policies_matched"]
        if policies:
            lines.append("  Policies Matched:")
            for pol in policies:
                sev = pol["severity"]
                lines.append(f"  • {pol['policy_name']} ({sev})")
            lines.append("")

        # --- Action taken ---
        lines.append("  Action Taken:")
        redaction = receipt.get("redaction_details")
        if redaction and redaction.get("applied"):
            count = redaction["entities_redacted"]
            lines.append(
                f"  {count} {'entity' if count == 1 else 'entities'} redacted"
                " with reversible tokens."
            )
        meta = receipt["audit_metadata"]
        if meta["forwarded"]:
            lines.append(
                f"  Sanitized prompt forwarded to {meta['target_model']}."
            )
        else:
            lines.append("  Prompt was NOT forwarded.")
        lines.append("")

        # --- Remediation ---
        remediation = receipt["decision"].get("remediation_suggestion", "")
        if remediation:
            lines.append("  Remediation:")
            # Wrap at ~42 chars
            for chunk in self._wrap(remediation, width=42):
                lines.append(f"  {chunk}")
            lines.append("")

        # --- Processing time ---
        lines += [
            f"  Processing Time: {meta['processing_time_ms']}ms",
            sep,
            "",
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _make_receipt_id(timestamp: datetime) -> str:
        date_part = timestamp.strftime("%Y%m%d")
        rand_part = secrets.token_hex(3)  # 6 hex chars, cryptographically secure
        return f"rcpt_{date_part}_{rand_part}"

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _mask_value(value: str) -> str:
        """Return first 3 chars + '***'."""
        prefix = value[:3] if len(value) >= 3 else value
        return prefix + "***"

    @staticmethod
    def _build_user(user_info: dict) -> dict:
        return {
            "id": user_info.get("id", ""),
            "name": user_info.get("name", ""),
            "department": user_info.get("department", ""),
            "role": user_info.get("role", ""),
        }

    def _build_prompt_analysis(
        self,
        original_prompt: str,
        detected_entities: List[dict],
        risk_assessment: dict,
    ) -> dict:
        risk_level = risk_assessment.get("risk_level", "LOW")
        sensitivity_level = self._RISK_TO_SENSITIVITY.get(
            risk_level.upper(), risk_level
        )

        entity_previews = [
            {
                "type": e.get("type", "UNKNOWN"),
                "value_preview": self._mask_value(str(e.get("value", ""))),
                "confidence": float(e.get("confidence", 0.0)),
                "detection_method": e.get("detection_method", "unknown"),
                "severity": int(e.get("severity", 0)),
            }
            for e in detected_entities
        ]

        return {
            "original_prompt_hash": self._sha256(original_prompt),
            "character_count": len(original_prompt),
            "word_count": len(original_prompt.split()),
            "detected_entities": entity_previews,
            "entity_count": len(entity_previews),
            "sensitivity_level": sensitivity_level,
        }

    @staticmethod
    def _build_policy_evaluation(
        matched_policies: List[dict], decision: dict
    ) -> dict:
        action = decision.get("action", "ALLOW")
        if not matched_policies:
            compliance_status = "COMPLIANT"
        elif action == "BLOCK":
            compliance_status = "VIOLATION_DETECTED"
        else:
            compliance_status = "REVIEW_REQUIRED"

        policy_records = [
            {
                "policy_id": p.get("policy_id", p.get("id", "")),
                "policy_name": p.get("policy_name", p.get("name", "")),
                "department_scope": p.get("department_scope", p.get("department", "")),
                "severity": p.get("severity", ""),
                "recommended_action": p.get("recommended_action", p.get("action", "")),
                "description": p.get("description", ""),
            }
            for p in matched_policies
        ]

        return {
            "policies_checked": len(matched_policies),
            "policies_matched": policy_records,
            "compliance_status": compliance_status,
        }

    @staticmethod
    def _build_risk_assessment(risk_assessment: dict) -> dict:
        raw_score = risk_assessment.get("overall_score", 0.0)
        # Normalize: accept both 0-1 and 0-100 scales
        score_f = float(raw_score)
        score = score_f / 100.0 if score_f > 1.0 else score_f
        return {
            "overall_score": score,
            "risk_level": risk_assessment.get("risk_level", "LOW"),
            "breakdown": risk_assessment.get("breakdown", {}),
            "confidence": float(risk_assessment.get("confidence", 1.0)),
        }

    @staticmethod
    def _build_decision(decision: dict) -> dict:
        return {
            "action": decision.get("action", "ALLOW"),
            "rationale": decision.get("rationale", ""),
            "factors": decision.get("factors", []),
            "remediation_suggestion": decision.get("remediation_suggestion", ""),
            "alternative_considered": decision.get("alternative_considered"),
        }

    @staticmethod
    def _build_redaction_details(redaction_map: Optional[dict]) -> Optional[dict]:
        if not redaction_map:
            return None
        tokens = list(redaction_map.keys())
        return {
            "applied": True,
            "entities_redacted": len(tokens),
            "redaction_tokens": tokens,
            "reversible": True,
        }

    @staticmethod
    def _build_audit_metadata(
        processing_time_ms: int,
        detected_entities: List[dict],
        target_model: str,
        forwarded: bool,
        llm_response: Optional[str],
    ) -> dict:
        methods_used = list(
            {e.get("detection_method", "unknown") for e in detected_entities}
        )
        return {
            "processing_time_ms": processing_time_ms,
            "detection_methods_used": methods_used,
            "policy_engine_version": ReceiptGenerator.POLICY_ENGINE_VERSION,
            "target_model": target_model,
            "forwarded": forwarded,
            "response_received": llm_response is not None,
            "aegis_node": ReceiptGenerator.AEGIS_NODE,
        }

    @staticmethod
    def _wrap(text: str, width: int = 42) -> List[str]:
        """Very simple word-wrap."""
        words = text.split()
        lines: List[str] = []
        current = ""
        for word in words:
            if current and len(current) + 1 + len(word) > width:
                lines.append(current)
                current = word
            else:
                current = (current + " " + word).lstrip()
        if current:
            lines.append(current)
        return lines
