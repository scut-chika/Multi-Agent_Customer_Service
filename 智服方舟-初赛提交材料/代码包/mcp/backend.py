# -*- coding: utf-8 -*-
"""5 类外部系统的内存参考实现：工单 / 支付 / CRM / 知识库 / 通知。

每个 Backend 暴露 tools（名称、描述、输入 Schema、处理函数），
server.py 将其包装为 tools/list 与 tools/call 协议。
"""
import json
import time


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S+08:00")


class TicketingBackend:
    name = "ticketing"

    def __init__(self):
        self.tickets = {}
        self.by_fingerprint = {}

    def _ticket(self, ticket_id):
        return self.tickets.get(ticket_id)

    def get(self, ticket_id):
        t = self._ticket(ticket_id)
        if not t:
            return {"found": False}
        return {"found": True, "ticket": t}

    def find_by_fingerprint(self, fingerprint):
        tid = self.by_fingerprint.get(fingerprint)
        return {"found": bool(tid), "ticket_id": tid}

    def create(self, ticket_id, channels, fingerprint, raw_snippet):
        existing = self._ticket(ticket_id)
        if existing:
            return {"created": False, "ticket": existing, "note": "已存在，幂等返回"}
        record = {
            "ticket_id": ticket_id,
            "channels": channels,
            "fingerprint": fingerprint,
            "status": "NEW",
            "raw_snippet": raw_snippet,
            "created_at": _now(),
        }
        self.tickets[ticket_id] = record
        self.by_fingerprint[fingerprint] = ticket_id
        return {"created": True, "ticket": record}

    def update(self, ticket_id, status=None, note=None):
        t = self._ticket(ticket_id)
        if not t:
            return {"updated": False, "reason": "ticket not found"}
        if status:
            t["status"] = status
        if note:
            t.setdefault("notes", []).append({"at": _now(), "note": note})
        return {"updated": True, "ticket": t}

    tools = [
        {
            "name": "ticket.get",
            "description": "按工单号查询工单",
            "inputSchema": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]},
            "handler": lambda self, a: self.get(a["ticket_id"]),
        },
        {
            "name": "ticket.find_by_fingerprint",
            "description": "按会话指纹查找工单（去重用）",
            "inputSchema": {"type": "object", "properties": {"fingerprint": {"type": "string"}}, "required": ["fingerprint"]},
            "handler": lambda self, a: self.find_by_fingerprint(a["fingerprint"]),
        },
        {
            "name": "ticket.create",
            "description": "创建标准工单",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "channels": {"type": "array", "items": {"type": "string"}},
                    "fingerprint": {"type": "string"},
                    "raw_snippet": {"type": "string"},
                },
                "required": ["ticket_id", "channels", "fingerprint", "raw_snippet"],
            },
            "handler": lambda self, a: self.create(a["ticket_id"], a.get("channels", []), a["fingerprint"], a.get("raw_snippet", "")),
        },
        {
            "name": "ticket.update",
            "description": "更新工单状态或追加备注",
            "inputSchema": {
                "type": "object",
                "properties": {"ticket_id": {"type": "string"}, "status": {"type": "string"}, "note": {"type": "string"}},
                "required": ["ticket_id"],
            },
            "handler": lambda self, a: self.update(a["ticket_id"], a.get("status"), a.get("note")),
        },
    ]


class PaymentBackend:
    name = "payment"
    DAY_LIMIT = 5000.0

    def __init__(self, persist_path=None):
        self.refunds = {}          # idempotency_key -> record
        self.by_txn = {}
        self.persist_path = persist_path
        if persist_path:
            persist_path.parent.mkdir(parents=True, exist_ok=True)
            if persist_path.exists():
                data = json.loads(persist_path.read_text(encoding="utf-8"))
                self.refunds = data.get("refunds", {})
                self.by_txn = data.get("by_txn", {})

    def _save(self):
        if self.persist_path:
            self.persist_path.write_text(
                json.dumps({"refunds": self.refunds, "by_txn": self.by_txn},
                           ensure_ascii=False, indent=2), encoding="utf-8")

    def create(self, order_id, amount, currency, idempotency_key, approval_token=None):
        if idempotency_key in self.refunds:
            rec = self.refunds[idempotency_key]
            return {"status": "DUPLICATE", "refund": rec, "note": "幂等键命中，返回既有结果"}
        if amount <= 0:
            return {"status": "FAILED", "reason": "invalid amount"}
        if amount > self.DAY_LIMIT and not approval_token:
            return {"status": "FAILED", "reason": "LIMIT_EXCEEDED, 需人工审批凭证"}
        txn_id = f"TX-{int(time.time())}"
        rec = {
            "refund_txn_id": txn_id,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "status": "SUCCESS",
            "idempotency_key": idempotency_key,
            "created_at": _now(),
        }
        self.refunds[idempotency_key] = rec
        self.by_txn[txn_id] = rec
        self._save()
        return {"status": "SUCCESS", "refund": rec}

    def get(self, refund_txn_id):
        rec = self.by_txn.get(refund_txn_id)
        return {"found": bool(rec), "refund": rec}

    def rollback(self, refund_txn_id):
        rec = self.by_txn.get(refund_txn_id)
        if not rec:
            return {"status": "FAILED", "reason": "not found"}
        rec["status"] = "ROLLED_BACK"
        self._save()
        return {"status": "ROLLED_BACK", "refund": rec}

    tools = [
        {
            "name": "refund.create",
            "description": "创建退款（幂等：idempotency_key 全局唯一）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "amount": {"type": "number"},
                    "currency": {"type": "string"},
                    "idempotency_key": {"type": "string"},
                    "approval_token": {"type": "string"},
                },
                "required": ["order_id", "amount", "currency", "idempotency_key"],
            },
            "handler": lambda self, a: self.create(a["order_id"], a["amount"], a.get("currency", "CNY"), a["idempotency_key"], a.get("approval_token")),
        },
        {
            "name": "refund.get",
            "description": "按退款流水号查询",
            "inputSchema": {"type": "object", "properties": {"refund_txn_id": {"type": "string"}}, "required": ["refund_txn_id"]},
            "handler": lambda self, a: self.get(a["refund_txn_id"]),
        },
        {
            "name": "refund.rollback",
            "description": "退款回滚",
            "inputSchema": {"type": "object", "properties": {"refund_txn_id": {"type": "string"}}, "required": ["refund_txn_id"]},
            "handler": lambda self, a: self.rollback(a["refund_txn_id"]),
        },
    ]


class CrmBackend:
    name = "crm"

    def __init__(self):
        self.accounts = {
            "C-10001": {"customer_id": "C-10001", "phone": "138****0001", "level": "gold", "address": "广州市***"},
            "C-10002": {"customer_id": "C-10002", "phone": "139****0002", "level": "silver", "address": "深圳市***"},
        }
        self.audit = []

    def get(self, customer_id):
        acc = self.accounts.get(customer_id)
        return {"found": bool(acc), "account": acc}

    def update(self, customer_id, field, old, new, approval_token=None):
        acc = self.accounts.get(customer_id)
        if not acc:
            return {"updated": False, "reason": "account not found"}
        if field not in ("phone", "address", "level"):
            return {"updated": False, "reason": "field not in whitelist"}
        if acc.get(field) != old:
            return {"updated": False, "reason": "old value mismatch"}
        if field == "phone" and not approval_token:
            return {"updated": False, "reason": "phone change requires approval"}
        acc[field] = new
        self.audit.append({"customer_id": customer_id, "field": field, "old": old, "new": new, "at": _now()})
        return {"updated": True, "account": acc, "audit": self.audit[-1]}

    tools = [
        {
            "name": "account.get",
            "description": "查询客户账户",
            "inputSchema": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]},
            "handler": lambda self, a: self.get(a["customer_id"]),
        },
        {
            "name": "account.update",
            "description": "白名单字段变更（敏感字段需审批凭证）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "field": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                    "approval_token": {"type": "string"},
                },
                "required": ["customer_id", "field", "old", "new"],
            },
            "handler": lambda self, a: self.update(a["customer_id"], a["field"], a.get("old"), a["new"], a.get("approval_token")),
        },
    ]


class KbBackend:
    name = "kb"

    def __init__(self):
        self.docs = [
            {"doc_id": "kb:SOP-RF-2026", "title": "退款SOP-2026", "content": "漏发/缺件可直接退款；金额不超过5000元且订单可核销；需先核对订单状态。", "tags": ["refund", "sop"]},
            {"doc_id": "kb:policy-refund-window", "title": "退款时效政策", "content": "签收7日内可申请退款；退款原路返回，3个工作日内到账。", "tags": ["refund", "policy"]},
            {"doc_id": "kb:SOP-EX-2026", "title": "换货SOP-2026", "content": "质量问题支持换货；需客户确认收货地址；库存不足时登记缺货并通知。", "tags": ["exchange", "sop"]},
            {"doc_id": "kb:case-0188", "title": "历史案例C-0188", "content": "漏发退款案例：先核销订单再退款，满意度高。", "tags": ["refund", "case"]},
        ]

    def search(self, query, top_k=3):
        q = set(query.replace("，", " ").split())
        scored = []
        for d in self.docs:
            text = (d["title"] + " " + d["content"]).lower()
            score = sum(1 for w in q if w.lower() in text) + (0.5 if any(t in d["tags"] for t in q) else 0)
            scored.append({"doc_id": d["doc_id"], "title": d["title"], "score": score, "snippet": d["content"][:60]})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return {"hits": scored[:top_k]}

    def upsert(self, doc_id, title, content, tags, approved_by=None):
        if not approved_by:
            return {"updated": False, "reason": "知识写入需审批凭证"}
        doc = {"doc_id": doc_id, "title": title, "content": content, "tags": tags}
        replaced = any(d["doc_id"] == doc_id for d in self.docs)
        self.docs = [d for d in self.docs if d["doc_id"] != doc_id] + [doc]
        return {"updated": True, "replaced": replaced, "doc": doc}

    tools = [
        {
            "name": "kb.search",
            "description": "知识库检索（混合关键词评分，返回命中与来源）",
            "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}, "required": ["query"]},
            "handler": lambda self, a: self.search(a["query"], int(a.get("top_k", 3))),
        },
        {
            "name": "kb.upsert",
            "description": "知识写入（需审批凭证）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "doc_id": {"type": "string"}, "title": {"type": "string"},
                    "content": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}},
                    "approved_by": {"type": "string"},
                },
                "required": ["doc_id", "title", "content"],
            },
            "handler": lambda self, a: self.upsert(a["doc_id"], a["title"], a["content"], a.get("tags", []), a.get("approved_by")),
        },
    ]


class NotifyBackend:
    name = "notify"

    def __init__(self):
        self.messages = {}

    def send(self, channel, template, params, message_id=None):
        if message_id and message_id in self.messages:
            return {"sent": False, "message_id": message_id, "note": "消息ID去重，已存在"}
        mid = message_id or f"MSG-{int(time.time())}"
        self.messages[mid] = {"channel": channel, "template": template, "params": params, "status": "SENT", "at": _now()}
        return {"sent": True, "message_id": mid, "status": "SENT"}

    tools = [
        {
            "name": "notify.send",
            "description": "模板消息发送（按模板，禁自定义内容；消息ID去重）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string"}, "template": {"type": "string"},
                    "params": {"type": "object"}, "message_id": {"type": "string"},
                },
                "required": ["channel", "template", "params"],
            },
            "handler": lambda self, a: self.send(a["channel"], a["template"], a.get("params", {}), a.get("message_id")),
        },
    ]


def build_backends(state_dir=None):
    payment_persist = (state_dir / "payment.json") if state_dir else None
    return {
        "ticketing": TicketingBackend(),
        "payment": PaymentBackend(persist_path=payment_persist),
        "crm": CrmBackend(),
        "kb": KbBackend(),
        "notify": NotifyBackend(),
    }
