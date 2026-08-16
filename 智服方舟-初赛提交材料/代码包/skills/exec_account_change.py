# -*- coding: utf-8 -*-
"""exec.account_change：账户白名单字段变更（幂等 + 敏感字段审批）。"""
from .base import Skill


class ExecAccountChange(Skill):
    name = "exec.account_change"
    purpose = "账户信息变更执行（幂等，二次确认/审批）"

    def call(self, ctx, customer_id, field, old, new, approval=None, risk_level="high"):
        if risk_level == "high" and not (approval and approval.get("approved")):
            return {"status": "BLOCKED", "reason": "敏感账户变更缺少审批凭证", "evidence": {}}
        approval_token = approval.get("action_hash") if approval else None
        result = ctx.tool("crm", "account.update", {
            "customer_id": customer_id, "field": field, "old": old, "new": new,
            "approval_token": approval_token,
        })
        if result.get("updated"):
            return {"status": "SUCCESS", "evidence": result.get("audit", {})}
        return {"status": "FAILED", "reason": result.get("reason"), "evidence": {}}
