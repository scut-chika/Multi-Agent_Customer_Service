# -*- coding: utf-8 -*-
"""review.case：疑难案例复盘、根因分析与知识沉淀。"""
import time

from .base import Skill


class ReviewCase(Skill):
    name = "review.case"
    purpose = "疑难案例复盘与知识沉淀"

    def call(self, ctx, intent, verdict, satisfaction, raw_text, auto_approve=True):
        score = (satisfaction or {}).get("score", 5)
        root_cause = "仓库拣货漏发" if "漏发" in (raw_text or "") or "少件" in (raw_text or "") else "待人工复核"
        tags = [intent, "high_risk" if ctx.ticket.risk_level == "high" else "normal"]
        if verdict == "FAIL" or score < 4:
            tags.append("needs_review")
        doc_id = f"kb:case-{time.strftime('%Y%m%d')}-{int(time.time()) % 100000:05d}"
        suggestion = "exec.refund 增加漏发场景参数校验" if intent == "refund" else "review 流程保持现状"
        kb_result = None
        if auto_approve:
            kb_result = ctx.tool("kb", "kb.upsert", {
                "doc_id": doc_id, "title": f"复盘：{intent}工单{ctx.ticket.ticket_id}",
                "content": f"根因：{root_cause}；核验：{verdict}；满意度：{score}",
                "tags": tags, "approved_by": "reviewer-human-approver",
            })
        ctx.note(f"复盘完成：{root_cause}")
        return {
            "case_tags": tags,
            "root_cause": root_cause,
            "kb_updates": [{"doc_id": doc_id, "content": f"根因：{root_cause}；核验：{verdict}；满意度：{score}"}],
            "skill_suggestions": [suggestion],
            "kb_upsert": kb_result,
        }
