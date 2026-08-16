# -*- coding: utf-8 -*-
"""执行 Agent（Executor）：按批准方案调用 Skill/MCP 执行，幂等、回滚。"""
from .base import Agent


class ExecutorAgent(Agent):
    id = "executor-agent"
    role = "executor"
    identity = "柜面操作员：按已批准方案调用系统完成动作"
    can = ["Skill/MCP 调用系统", "幂等控制", "重试与回滚"]
    cannot = ["擅自变更方案", "超授权额度执行"]

    def run(self, ctx, env):
        span = self._span(env)
        plan = ctx.plan
        results = []
        for idx, action in enumerate(plan.get("actions", [])):
            params = action.get("params", {})
            if action["action"] == "refund":
                key = f"refund:{ctx.ticket_id}:{params['order_id']}:{idx}"
                res = env.skills["exec.refund"].call(
                    env.skill_context(ctx),
                    order_id=params["order_id"], amount=params.get("amount"), currency=params.get("currency", "CNY"),
                    approval=ctx.approval, idempotency_key=key, risk_level=ctx.risk_level)
            elif action["action"] == "account_change":
                key = f"account:{ctx.ticket_id}:{plan['plan_id']}:{idx}"
                current = env.skill_context(ctx).tool("crm", "account.get", {"customer_id": params.get("customer_id")})
                old = (current.get("account") or {}).get(params.get("field", "address"))
                res = env.skills["exec.account_change"].call(
                    env.skill_context(ctx),
                    customer_id=params.get("customer_id"), field=params.get("field", "address"),
                    old=old, new=params.get("new", "广州市新港中路***"),
                    approval=ctx.approval, risk_level=ctx.risk_level)
            elif action["action"] == "exchange":
                env.skill_context(ctx).tool("ticketing", "ticket.update",
                                            {"ticket_id": ctx.ticket_id, "note": "换货申请已登记，转仓库处理"})
                res = {"status": "SUCCESS", "evidence": {"note": "exchange_request_logged"}}
            else:
                res = {"status": "FAILED", "reason": "需人工处理", "evidence": {}}
            results.append({"action": action["action"], "result": res})
            if res.get("status") != "SUCCESS":
                ctx.update(escalated=True, escalate_reason=f"执行失败({action['action']}): {res.get('reason')}")
                self._log(ctx, f"{action['action']} 执行失败：{res.get('reason')}")
                break
        execution = {"results": results, "summary": "SUCCESS" if all(r["result"]["status"] == "SUCCESS" for r in results) else "FAILED"}
        ctx.update(execution=execution)
        if results and results[0]["result"]["status"] == "SUCCESS" and results[0]["result"].get("evidence"):
            execution["evidence"] = results[0]["result"]["evidence"]
        self._log(ctx, f"执行完成：{execution['summary']}")
        env.tracer.finish(span, {"summary": execution["summary"]})
        return execution
