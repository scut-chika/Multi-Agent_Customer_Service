# -*- coding: utf-8 -*-
"""Agent 基类与执行环境。身份/能力边界与附录 A Identity 清单一致。"""


class AgentEnv:
    """Leader 分发给各 Worker 的共享执行环境。"""

    def __init__(self, clients, tracer, skills, approval_gate, config=None):
        self.clients = clients
        self.tracer = tracer
        self.skills = skills
        self.approval_gate = approval_gate
        self.config = config or {}

    def skill_context(self, ticket):
        from skills.base import SkillContext
        return SkillContext(ticket, self.clients, self.tracer)


class Agent:
    id = None
    role = None
    identity = ""
    can = []
    cannot = []

    def run(self, ctx, env):
        raise NotImplementedError

    def _log(self, ctx, text):
        ctx.add_message(self.id, text)

    def _span(self, env):
        return env.tracer.start(self.id, "agent", self.id)
