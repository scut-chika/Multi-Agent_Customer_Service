# -*- coding: utf-8 -*-
"""分诊 Agent（Triage）：意图识别、分类分级、信息补全。"""
from .base import Agent


class TriageAgent(Agent):
    id = "triage-agent"
    role = "triage"
    identity = "分诊护士：意图识别、分类分级、情绪与紧急度评估"
    can = ["意图/槽位提取", "紧急度与风险分级", "信息补全追问"]
    cannot = ["生成处理动作"]

    def run(self, ctx, env):
        span = self._span(env)
        result = env.skills["triage.intent"].call(env.skill_context(ctx), raw_text=ctx.raw_text)
        ctx.update(
            intent=result["intent"],
            risk_level=result["risk_level"],
            urgency=result["urgency"],
            confidence=result["confidence"],
            slots=result["slots"],
        )
        if result["confidence"] < 0.5:
            ctx.update(escalated=True, escalate_reason=f"意图置信度过低({result['confidence']})，转人工分诊")
            self._log(ctx, f"意图={result['intent']} 置信度={result['confidence']} 过低，升级人工")
        else:
            self._log(ctx, f"意图={result['intent']} 风险={result['risk_level']} 紧急度={result['urgency']} 置信度={result['confidence']}")
        env.tracer.finish(span, {"intent": result["intent"], "confidence": result["confidence"], "llm": result.get("llm_enhanced", False)})
        return result
