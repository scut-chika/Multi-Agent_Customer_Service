# -*- coding: utf-8 -*-
"""审批闸门：高风险动作必须携带人工审批凭证，凭证进入执行上下文。"""
import hashlib
import json
import time


def action_hash(ticket_id, plan_id, action):
    raw = f"{ticket_id}:{plan_id}:{json.dumps(action, ensure_ascii=False, sort_keys=True)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ApprovalGate:
    """auto=True 时模拟人工审批员（演示用）；否则从文件读取审批记录。"""

    def __init__(self, mode="auto", file_path=None, approver="human-supervisor-l1"):
        self.mode = mode
        self.file_path = file_path
        self.approver = approver

    def approve(self, ctx, plan):
        actions = plan.get("actions", [])
        hash_ = action_hash(ctx.ticket_id, plan.get("plan_id"), actions)
        if self.mode == "file" and self.file_path:
            with open(self.file_path, "r", encoding="utf-8") as f:
                record = json.load(f)
            approved = bool(record.get("approved"))
            evidence = record.get("approval_evidence", {})
            by = record.get("approved_by", self.approver)
        else:
            approved = True  # 演示模式：模拟审批通过（限额内单人审批）
            evidence = {"channel": "approval-console", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00")}
            by = self.approver
        return {
            "approved": approved,
            "approved_by": by,
            "approval_evidence": evidence,
            "action_hash": hash_,
            "mode": self.mode,
        }
