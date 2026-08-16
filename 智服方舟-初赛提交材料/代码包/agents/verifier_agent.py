# -*- coding: utf-8 -*-
"""核验 Agent（Verifier）：执行结果核验与满意度确认。"""
from .base import Agent


class VerifierAgent(Agent):
    id = "verifier-agent"
    role = "verifier"
    identity = "质检员：校验执行结果、收集满意度确认、生成核验报告"
    can = ["比对金额/状态/凭证", "触发满意度确认", "生成核验报告与证据包"]
    cannot = ["重新执行业务动作"]

    def run(self, ctx, env):
        span = self._span(env)
        evidence = (ctx.execution or {}).get("evidence", {})
        first_action = ctx.plan.get("actions", [{}])[0]
        expected = {}
        if first_action.get("action") == "refund":
            expected = {"amount": first_action["params"].get("amount"), "status": "SUCCESS"}
        elif first_action.get("action") == "account_change":
            expected = {"field": first_action["params"].get("field")}
        result = env.skills["verify.result"].call(
            env.skill_context(ctx), expected=expected, evidence=evidence)
        ctx.update(verification=result)
        if result["verdict"] != "PASS":
            ctx.update(escalated=True, escalate_reason="核验未通过")
            self._log(ctx, f"核验未通过：{result['check_items']}")
        else:
            self._log(ctx, f"核验通过 {result['report']}，满意度={result['satisfaction']['score']}")
        env.tracer.finish(span, {"verdict": result["verdict"]})
        return result
