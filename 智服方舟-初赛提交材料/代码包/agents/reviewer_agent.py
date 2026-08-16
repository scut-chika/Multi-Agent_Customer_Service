# -*- coding: utf-8 -*-
"""复盘 Agent（Reviewer）：疑难案例复盘、根因分析与知识沉淀。"""
from .base import Agent


class ReviewerAgent(Agent):
    id = "reviewer-agent"
    role = "reviewer"
    identity = "分析师：疑难/失败案例复盘、根因分析、知识沉淀"
    can = ["聚类疑难工单", "根因分析", "知识库与 Skill 策略建议"]
    cannot = ["处理实时工单", "直接修改生产 Skill 配置"]

    def run(self, ctx, env, auto_approve=True):
        span = self._span(env)
        verification = ctx.verification or {}
        satisfaction = verification.get("satisfaction", {})
        result = env.skills["review.case"].call(
            env.skill_context(ctx),
            intent=ctx.intent, verdict=verification.get("verdict", "FAIL"),
            satisfaction=satisfaction, raw_text=ctx.raw_text, auto_approve=auto_approve)
        ctx.update(review=result)
        self._log(ctx, f"复盘完成：根因={result['root_cause']}，知识更新={len(result['kb_updates'])}条")
        env.tracer.finish(span, {"root_cause": result["root_cause"], "tags": result["case_tags"]})
        return result
