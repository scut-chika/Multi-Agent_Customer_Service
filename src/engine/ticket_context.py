# -*- coding: utf-8 -*-
"""工单上下文（Ticket Context）：多 Agent 协作的单一事实源（SSOT）。"""


class TicketContext:
    """一个工单从接入到复盘的全部中间状态，由 Leader 统一维护。"""

    def __init__(self, ticket_id, trace_id):
        self.ticket_id = ticket_id
        self.trace_id = trace_id
        self.source = None            # 来源渠道
        self.raw_text = None          # 原始消息（脱敏后）
        self.fingerprint = None       # 会话指纹
        self.dedup = {}               # 去重记录
        self.status = "NEW"           # 状态机当前位置
        self.intent = None            # 意图
        self.risk_level = None        # 风险等级
        self.urgency = None           # 紧急度
        self.confidence = None        # 置信度
        self.slots = {}               # 槽位（订单号等）
        self.plan = None              # 处理方案
        self.approval = None          # 审批记录
        self.execution = None         # 执行证据
        self.verification = None      # 核验报告
        self.review = None            # 复盘结论
        self.escalated = False        # 是否升级人工
        self.escalate_reason = None
        self.duration_ms = None        # 全流程耗时
        self.messages = []            # Agent 间传递的中间消息

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise AttributeError(f"TicketContext 无字段: {k}")

    def add_message(self, sender, text):
        self.messages.append({"sender": sender, "text": text, "status": self.status})

    def to_dict(self):
        return {
            "ticket_id": self.ticket_id,
            "trace_id": self.trace_id,
            "source": self.source,
            "raw_text": self.raw_text,
            "fingerprint": self.fingerprint,
            "dedup": self.dedup,
            "status": self.status,
            "intent": self.intent,
            "risk_level": self.risk_level,
            "urgency": self.urgency,
            "confidence": self.confidence,
            "slots": self.slots,
            "plan": self.plan,
            "approval": self.approval,
            "execution": self.execution,
            "verification": self.verification,
            "review": self.review,
            "escalated": self.escalated,
            "escalate_reason": self.escalate_reason,
            "duration_ms": self.duration_ms,
            "messages": self.messages,
        }
