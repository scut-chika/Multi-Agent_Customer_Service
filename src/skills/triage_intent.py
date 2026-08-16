# -*- coding: utf-8 -*-
"""triage.intent：意图识别、分类分级、信息补全（规则实现 + 可选 LLM 增强）。"""
import re

from engine.llm import chat_json
from .base import Skill

INTENT_RULES = [
    ("refund", ["退款", "退钱", "少件", "漏发", "缺件", "退差价", "refund"]),
    ("exchange", ["换货", "质量问题", "坏了", "换一个", "exchange"]),
    ("account_change", ["改手机", "改地址", "修改账户", "账户变更", "更新联系方式"]),
    ("password_reset", ["密码", "登录不上", "重置密码"]),
]

URGENT_WORDS = ["紧急", "马上", "投诉", "立刻", "尽快", "加急"]


class TriageIntent(Skill):
    name = "triage.intent"
    purpose = "意图识别、分类分级与信息补全"

    def call(self, ctx, raw_text):
        result = self._rules(raw_text)
        llm_out = chat_json([
            {"role": "system", "content": "你是客服工单分诊器，输出JSON：{intent, risk_level, urgency, confidence, slots}"},
            {"role": "user", "content": raw_text},
        ])
        if llm_out and isinstance(llm_out.get("intent"), str) and llm_out.get("confidence", 0) > result["confidence"]:
            result = {**result, **llm_out, "llm_enhanced": True}
        else:
            result["llm_enhanced"] = False
        return result

    def _rules(self, text):
        intent, score = "unknown", 0.0
        for name, words in INTENT_RULES:
            hits = sum(1 for w in words if w in text)
            if hits > score:
                intent, score = name, hits
        slots = {}
        m = re.search(r"(\d{8,})", text)
        if m:
            slots["order_id"] = m.group(1)
        risk = {"refund": "high", "account_change": "high", "exchange": "medium",
                "password_reset": "medium"}.get(intent, "low")
        urgency = "high" if any(w in text for w in URGENT_WORDS) else "medium"
        confidence = round(0.55 + 0.13 * score + (0.15 if slots else 0), 2)
        if intent == "unknown":
            confidence = 0.4
        return {"intent": intent, "risk_level": risk, "urgency": urgency,
                "confidence": min(confidence, 0.99), "slots": slots}
