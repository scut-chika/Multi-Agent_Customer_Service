# -*- coding: utf-8 -*-
"""verify.result：执行结果核验与满意度确认。"""
import time

from .base import Skill


class VerifyResult(Skill):
    name = "verify.result"
    purpose = "执行结果核验与满意度确认"

    def call(self, ctx, expected, evidence, satisfaction_score=5):
        checks = []
        for key, exp in expected.items():
            actual = evidence.get(key)
            checks.append({"item": key, "expected": exp, "actual": actual, "pass": actual == exp})
        verdict = "PASS" if all(c["pass"] for c in checks) else "FAIL"
        satisfaction = ctx.tool("notify", "notify.send", {
            "channel": "sms", "template": "satisfaction_survey",
            "params": {"ticket_id": ctx.ticket.ticket_id, "score": satisfaction_score},
            "message_id": f"sat-{ctx.ticket.ticket_id}",
        })
        report_id = f"VR-{time.strftime('%Y%m%d')}-{int(time.time()) % 100000:05d}"
        ctx.note(f"核验{verdict}，满意度={satisfaction_score}")
        return {
            "report": report_id,
            "verdict": verdict,
            "check_items": checks,
            "satisfaction": {"channel": "sms", "status": "satisfied" if satisfaction_score >= 4 else "unsatisfied",
                             "score": satisfaction_score},
            "evidence_ok": bool(evidence),
        }
