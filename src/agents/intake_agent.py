# -*- coding: utf-8 -*-
"""聚合 Agent（Intake）：多渠道接入、归一化、去重、工单建档。"""
from .base import Agent


class IntakeAgent(Agent):
    id = "intake-agent"
    role = "intake"
    identity = "前台接待员：多渠道接入、消息归一化、去重合并、工单建档"
    can = ["解析多渠道消息", "会话指纹去重", "生成标准工单"]
    cannot = ["意图判断", "业务处理"]

    def run(self, ctx, env, raw_text, channels=None, ticket_id=None):
        span = self._span(env)
        result = env.skills["intake.ingest"].call(
            env.skill_context(ctx), raw_text=raw_text, channels=channels, ticket_id=ticket_id)
        ctx.update(
            source=", ".join(channels or ["unknown"]),
            raw_text=raw_text,
            fingerprint=result["fingerprint"],
            dedup=result["dedup"],
        )
        if result.get("ticket_id") != ctx.ticket_id:
            ctx.update(ticket_id=result["ticket_id"])
        self._log(ctx, f"接入完成：{'命中重复，合并到 ' + str(result['dedup'].get('merged_ticket_id')) if result['dedup']['matched'] else '首次建档'}")
        env.tracer.finish(span, {"ticket_id": ctx.ticket_id, "dedup": result["dedup"]})
        return result
