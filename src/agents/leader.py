# -*- coding: utf-8 -*-
"""主控 Agent（Leader）：任务拆解、编排调度、状态追踪、升级决策。

对应 AgentTeams 的 Leader-Worker 组织模型：Leader 只编排不执行业务动作。
"""
import json
import time

from engine.state_machine import StateMachine
from .base import Agent
from .intake_agent import IntakeAgent
from .triage_agent import TriageAgent
from .planner_agent import PlannerAgent
from .executor_agent import ExecutorAgent
from .verifier_agent import VerifierAgent
from .reviewer_agent import ReviewerAgent


class LeaderAgent(Agent):
    id = "leader-main"
    role = "orchestrator"
    identity = "值班长：理解任务目标，拆解并编排多 Agent 流程，维护全局状态"
    can = ["任务拆解", "编排调度", "上下文路由", "冲突仲裁", "升级决策", "结果汇总"]
    cannot = ["直接操作业务系统", "生成领域处理方案"]

    def __init__(self):
        self.workers = {
            "intake": IntakeAgent(),
            "triage": TriageAgent(),
            "planner": PlannerAgent(),
            "executor": ExecutorAgent(),
            "verifier": VerifierAgent(),
            "reviewer": ReviewerAgent(),
        }

    def _go(self, ctx, state, target, note=None):
        ctx.update(status=state.transition(target))
        if note:
            ctx.add_message(self.id, note)

    def run(self, ctx, env, raw_text, channels=None, ticket_id=None, approval_mode="auto"):
        span = self._span(env)
        state = StateMachine()
        started = time.time()
        self._log(ctx, f"任务接收：渠道={channels}，开始编排")
        try:
            # 1 任务输入 → 聚合 Agent
            self.workers["intake"].run(ctx, env, raw_text, channels, ticket_id)
            # 2 意图分诊
            self._go(ctx, state, "TRIAGED", "任务拆解：分配分诊 Agent")
            self.workers["triage"].run(ctx, env)
            if ctx.escalated:
                self._escalate(ctx, state, env)
                return ctx
            # 3 方案生成（RAG）
            self._go(ctx, state, "PLANNED", "上下文传递：意图/分级写入 Ticket Context")
            self.workers["planner"].run(ctx, env)
            if ctx.escalated:
                self._escalate(ctx, state, env)
                return ctx
            # 4 审批闸门
            if ctx.plan.get("approval_required"):
                ctx.update(approval=env.approval_gate.approve(ctx, ctx.plan))
                if not ctx.approval.get("approved"):
                    ctx.update(escalated=True, escalate_reason="人工审批未通过")
                    self._escalate(ctx, state, env)
                    return ctx
                self._log(ctx, f"审批通过：{ctx.approval['approved_by']}，凭证={ctx.approval['action_hash'][:12]}...")
            self._go(ctx, state, "APPROVED")
            # 5 自动执行（Skill/MCP）
            self.workers["executor"].run(ctx, env)
            if ctx.escalated:
                self._escalate(ctx, state, env)
                return ctx
            self._go(ctx, state, "EXECUTED")
            # 6 结果核验 + 满意度
            self.workers["verifier"].run(ctx, env)
            if ctx.escalated:
                self._escalate(ctx, state, env)
                return ctx
            self._go(ctx, state, "VERIFIED")
            # 7 复盘与知识沉淀
            self.workers["reviewer"].run(ctx, env, auto_approve=env.config.get("auto_approve_review", True))
            self._go(ctx, state, "CLOSED", "经验沉淀：复盘结论与知识库更新")
        except Exception as exc:
            ctx.update(escalated=True, escalate_reason=f"编排异常: {exc}")
            self._escalate(ctx, state, env)
        finally:
            ctx.update(duration_ms=round((time.time() - started) * 1000, 1))
            env.tracer.finish(span, {"status": ctx.status, "escalated": ctx.escalated})
        return ctx

    def _escalate(self, ctx, state, env=None):
        if not ctx.escalate_reason:
            ctx.update(escalate_reason="未知原因")
        try:
            self._go(ctx, state, "ESCALATED", f"升级人工：{ctx.escalate_reason}")
        except Exception:
            pass
        if env is not None:
            try:
                self.workers["reviewer"].run(ctx, env, auto_approve=env.config.get("auto_approve_review", True))
            except Exception:
                pass
        ctx.add_message(self.id, f"⚠ 升级人工（Human-in-the-loop）：{ctx.escalate_reason}")

    def summarize(self, ctx):
        return {
            "ticket_id": ctx.ticket_id,
            "trace_id": ctx.trace_id,
            "status": ctx.status,
            "intent": ctx.intent,
            "risk_level": ctx.risk_level,
            "plan": ctx.plan.get("plan_id") if ctx.plan else None,
            "verdict": ctx.verification.get("verdict") if ctx.verification else None,
            "escalated": ctx.escalated,
            "escalate_reason": ctx.escalate_reason,
            "duration_ms": ctx.duration_ms,
        }
