# -*- coding: utf-8 -*-
"""工单状态机：保证闭环每一步可恢复、可审计。"""

STATES = [
    "NEW", "TRIAGED", "PLANNED", "APPROVED",
    "EXECUTED", "VERIFIED", "CLOSED", "ESCALATED",
]

TRANSITIONS = {
    "NEW": ["TRIAGED", "ESCALATED"],
    "TRIAGED": ["PLANNED", "ESCALATED"],
    "PLANNED": ["APPROVED", "ESCALATED"],
    "APPROVED": ["EXECUTED", "ESCALATED"],
    "EXECUTED": ["VERIFIED", "ESCALATED"],
    "VERIFIED": ["CLOSED", "ESCALATED"],
    "CLOSED": [],
    "ESCALATED": [],
}


class StateError(RuntimeError):
    pass


class StateMachine:
    def __init__(self, initial="NEW"):
        self.state = initial

    def can(self, target):
        return target in TRANSITIONS.get(self.state, [])

    def transition(self, target):
        if not self.can(target):
            raise StateError(f"非法状态迁移: {self.state} -> {target}")
        self.state = target
        return self.state
