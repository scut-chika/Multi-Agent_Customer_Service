# -*- coding: utf-8 -*-
"""exec.refund：退款执行（幂等 + 审批凭证校验 + 失败回滚/升级）。"""
from .base import Skill


class ExecRefund(Skill):
    name = "exec.refund"
    purpose = "退款执行（幂等），回写工单证据"

    def call(self, ctx, order_id, amount, currency, approval, idempotency_key, risk_level="high"):
        if risk_level == "high" and not (approval and approval.get("approved")):
            return {"status": "BLOCKED", "reason": "高风险退款缺少审批凭证", "evidence": {}}
        if amount is None:
            return {"status": "BLOCKED", "reason": "缺少退款金额，转人工确认", "evidence": {}}
        approval_token = approval.get("action_hash") if approval else None
        result = ctx.tool("payment", "refund.create", {
            "order_id": order_id, "amount": amount, "currency": currency,
            "idempotency_key": idempotency_key, "approval_token": approval_token,
        })
        refund = result.get("refund") or {}
        if result.get("status") in ("SUCCESS", "DUPLICATE"):
            if result.get("status") == "DUPLICATE":
                ctx.note(f"幂等命中：退款单已存在（{refund.get('refund_txn_id')}），复用既有结果")
            evidence = {
                "refund_txn_id": refund.get("refund_txn_id"),
                "amount": refund.get("amount"),
                "currency": refund.get("currency"),
                "status": refund.get("status", "SUCCESS"),
                "idempotency_key": idempotency_key,
                "duplicate": result.get("status") == "DUPLICATE",
            }
            ctx.tool("ticketing", "ticket.update",
                     {"ticket_id": ctx.ticket.ticket_id, "status": "EXECUTED",
                      "note": f"退款完成 txn={evidence['refund_txn_id']}"})
            ctx.note(f"退款完成 {evidence['refund_txn_id']}")
            return {"status": "SUCCESS", "evidence": evidence}
        # 失败：回滚/升级
        if refund.get("refund_txn_id"):
            rollback = ctx.tool("payment", "refund.rollback", {"refund_txn_id": refund["refund_txn_id"]})
            ctx.note(f"退款失败已回滚: {result.get('reason')}")
            return {"status": "FAILED", "reason": result.get("reason"),
                    "rollback": rollback, "evidence": {}}
        return {"status": "FAILED", "reason": result.get("reason"), "evidence": {}}
