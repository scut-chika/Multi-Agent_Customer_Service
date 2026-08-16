# -*- coding: utf-8 -*-
"""plan.policy_rag：基于 RAG 检索策略并生成合规方案（带证据引用）。"""
import re
import time

from .base import Skill

AMOUNT_RE = re.compile(r"(\d+(?:\.\d{1,2})?)\s*(?:元|块)")


class PlanPolicyRag(Skill):
    name = "plan.policy_rag"
    purpose = "基于 RAG 检索策略并生成合规处理方案"

    def call(self, ctx, intent, risk_level, slots, raw_text, amount_limit=5000.0):
        query = f"{intent} {' '.join(slots.values())} {raw_text[:40]}".strip()
        hits = ctx.tool("kb", "kb.search", {"query": query, "top_k": 3}).get("hits", [])
        good_hits = [h for h in hits if h.get("score", 0) > 0]
        plan_id = f"P-{time.strftime('%Y%m%d')}-{int(time.time()) % 100000:05d}"
        if not good_hits:
            return {"plan_id": plan_id, "insufficient_evidence": True,
                    "evidence_refs": [], "risk_level": risk_level, "approval_required": True,
                    "actions": [], "reason": "检索证据不足，转人工"}
        amount = None
        m = AMOUNT_RE.search(raw_text)
        if m:
            amount = float(m.group(1))
        if intent == "refund":
            actions = [{"action": "refund", "params": {"order_id": slots.get("order_id"),
                                                       "amount": amount, "currency": "CNY"}}]
        elif intent == "exchange":
            actions = [{"action": "exchange", "params": {"order_id": slots.get("order_id")}}]
        elif intent == "account_change":
            actions = [{"action": "account_change", "params": {"customer_id": slots.get("customer_id", "C-10001"),
                                                               "field": "address"}}]
        else:
            actions = [{"action": "manual_review", "params": {}}]
        approval_required = risk_level == "high" or (amount or 0) > amount_limit
        missing_params = []
        if intent == "refund" and amount is None:
            missing_params.append("amount")
        return {
            "plan_id": plan_id,
            "insufficient_evidence": False,
            "actions": actions,
            "missing_params": missing_params,
            "evidence_refs": [h["doc_id"] for h in good_hits[:2]],
            "citations": [{"doc_id": h["doc_id"], "title": h["title"]} for h in good_hits[:2]],
            "risk_level": risk_level,
            "approval_required": approval_required,
        }
