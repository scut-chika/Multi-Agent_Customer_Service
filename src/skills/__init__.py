# -*- coding: utf-8 -*-
"""核心 Skill 注册表：与 skills.yaml / Skill清单.md 一一对应。"""

from .base import Skill, SkillContext
from .intake_ingest import IntakeIngest
from .triage_intent import TriageIntent
from .plan_policy_rag import PlanPolicyRag
from .exec_refund import ExecRefund
from .exec_account_change import ExecAccountChange
from .verify_result import VerifyResult
from .review_case import ReviewCase

SKILLS = {
    cls.name: cls()
    for cls in (IntakeIngest, TriageIntent, PlanPolicyRag, ExecRefund,
                ExecAccountChange, VerifyResult, ReviewCase)
}


def get_skill(name):
    if name not in SKILLS:
        raise KeyError(f"Skill 未注册: {name}")
    return SKILLS[name]
