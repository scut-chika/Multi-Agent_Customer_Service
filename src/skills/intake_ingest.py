# -*- coding: utf-8 -*-
"""intake.ingest：多渠道接入、归一化、去重、工单建档。"""
import hashlib
import time

from .base import Skill


def fingerprint_of(text):
    normalized = "".join(text.split()).lower()
    return "fp:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class IntakeIngest(Skill):
    name = "intake.ingest"
    purpose = "多渠道消息接入、归一化与去重，生成标准工单"

    def call(self, ctx, raw_text, channels=None, ticket_id=None):
        raw = raw_text.strip()
        fingerprint = fingerprint_of(raw)
        found = ctx.tool("ticketing", "ticket.find_by_fingerprint", {"fingerprint": fingerprint})
        if found.get("found"):
            dedup = {"matched": True, "merged_ticket_id": found.get("ticket_id"),
                     "strategy": "fingerprint+semantic", "note": "重复消息合并到既有工单"}
            ticket = ctx.tool("ticketing", "ticket.get", {"ticket_id": found["ticket_id"]})
            return {"fingerprint": fingerprint, "dedup": dedup, "ticket_id": found["ticket_id"],
                    "ticket": ticket.get("ticket"), "created": False}
        tid = ticket_id or f"T-{time.strftime('%Y%m%d')}-{int(time.time()) % 100000:05d}"
        created = ctx.tool("ticketing", "ticket.create", {
            "ticket_id": tid,
            "channels": channels or ["unknown"],
            "fingerprint": fingerprint,
            "raw_snippet": raw,
        })
        ctx.note(f"新建工单 {tid}，渠道={channels}")
        return {"fingerprint": fingerprint, "dedup": {"matched": False, "note": "首次建档"},
                "ticket_id": tid, "ticket": created.get("ticket"), "created": True}
