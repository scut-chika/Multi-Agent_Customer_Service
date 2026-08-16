# -*- coding: utf-8 -*-
"""方案 Agent（Planner）：RAG 检索生成合规方案，标注证据与风险。"""
from .base import Agent


class PlannerAgent(Agent):
    id = "planner-agent"
    role = "planner"
    identity = "政策顾问：结合 RAG 检索生成合规处理方案"
    can = ["检索 SOP/产品手册/历史案例", "生成处理方案", "标注证据与风险", "发起审批建议"]
    cannot = ["直接执行", "绕过政策生成方案"]

    def run(self, ctx, env):
        span = self._span(env)
        result = env.skills["plan.policy_rag"].call(
            env.skill_context(ctx),
            intent=ctx.intent, risk_level=ctx.risk_level, slots=ctx.slots, raw_text=ctx.raw_text)
        ctx.update(plan=result)
        if result.get("insufficient_evidence"):
            ctx.update(escalated=True, escalate_reason="RAG 检索证据不足，转人工制定方案")
            self._log(ctx, "证据不足，标注后升级人工（防幻觉执行）")
        else:
            self._log(ctx, f"方案 {result['plan_id']} 生成，引用 {len(result['evidence_refs'])} 份证据，需审批={result['approval_required']}")
        env.tracer.finish(span, {"plan_id": result.get("plan_id"), "evidence_refs": result.get("evidence_refs"),
                                 "approval_required": result.get("approval_required")})
        return result
