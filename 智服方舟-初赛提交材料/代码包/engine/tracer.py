# -*- coding: utf-8 -*-
"""全链路追踪：记录 Agent / Skill / MCP 工具 / LLM 推理各环节，产出可回放证据。"""
import json
import time


class Span:
    def __init__(self, name, kind, agent=None):
        self.name = name
        self.kind = kind            # agent / skill / tool / llm
        self.agent = agent
        self.started = time.time()
        self.finished = None
        self.duration_ms = None
        self.detail = None

    def end(self, detail=None):
        self.finished = time.time()
        self.duration_ms = round((self.finished - self.started) * 1000, 1)
        self.detail = detail
        return self

    def to_dict(self):
        return {
            "name": self.name,
            "kind": self.kind,
            "agent": self.agent,
            "duration_ms": self.duration_ms,
            "detail": self.detail,
        }


class Tracer:
    def __init__(self, trace_id):
        self.trace_id = trace_id
        self.spans = []

    def start(self, name, kind="agent", agent=None):
        span = Span(name, kind, agent)
        self.spans.append(span)
        return span

    def finish(self, span, detail=None):
        span.end(detail)

    def tool_call(self, tool, args, result, ok=True):
        self.spans.append(
            Span(tool, "tool").end({
                "arguments": args,
                "result": result if isinstance(result, dict) else {"value": result},
                "ok": ok,
            })
        )

    def export(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "trace_id": self.trace_id,
                "spans": [s.to_dict() for s in self.spans],
            }, f, ensure_ascii=False, indent=2)
        return path

    def summary(self):
        lines = []
        for s in self.spans:
            icon = {"agent": "Agent", "skill": "Skill", "tool": "MCP", "llm": "LLM"}.get(s.kind, s.kind)
            lines.append(f"  [{icon}] {s.name} ({s.duration_ms}ms) {s.agent or ''}".strip())
        return "\n".join(lines)
