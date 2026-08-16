# -*- coding: utf-8 -*-
"""智服方舟 · 多智能体客服自主闭环 —— 运行入口

零依赖跑通完整闭环：Leader + 6 Worker + 7 Skill + 5 个 MCP 参考 Server（真实 HTTP 调用）。
可选增强：设置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY（+ LLM_BASE_URL/LLM_MODEL）后，
分诊环节会使用真实大模型，未设置时自动降级为规则实现。

用法：
  py main.py                                    # 跑通示例工单
  py main.py --input data/examples/01_ticket.json --evidence-dir data/examples
  py main.py --approval file --approval-file data/examples/04_approval.json
"""
import argparse
import json
import pathlib
import sys
import time
import uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.base import AgentEnv            # noqa: E402
from agents.leader import LeaderAgent       # noqa: E402
from engine.approval import ApprovalGate    # noqa: E402
from engine.ticket_context import TicketContext  # noqa: E402
from engine.tracer import Tracer            # noqa: E402
from mcp.run_servers import client_for, start_servers, stop_servers  # noqa: E402
from skills import SKILLS                   # noqa: E402


def build_report(ctx, tracer, trace_path, report_path, started):
    lines = [
        "=" * 66,
        "智服方舟 · 多 Agent 客服自主闭环 —— 运行证据",
        "=" * 66,
        f"工单号：{ctx.ticket_id}",
        f"TraceID：{ctx.trace_id}",
        f"运行时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"最终状态：{ctx.status}",
        "",
        "--- 协作过程（Ticket Context 消息流）---",
    ]
    for msg in ctx.messages:
        lines.append(f"  [{msg['status']}] {msg['sender']}: {msg['text']}")
    lines += [
        "",
        "--- 结果摘要 ---",
        f"  意图：{ctx.intent}（置信度 {ctx.confidence}）风险：{ctx.risk_level}",
        f"  方案：{ctx.plan.get('plan_id') if ctx.plan else '-'}，证据引用：{len(ctx.plan.get('evidence_refs', [])) if ctx.plan else 0} 份",
        f"  审批：{ctx.approval.get('approved') if ctx.approval else '-'}（{ctx.approval.get('approved_by') if ctx.approval else '-'}）",
        f"  执行：{ctx.execution.get('summary') if ctx.execution else '-'}",
        f"  核验：{ctx.verification.get('verdict') if ctx.verification else '-'}，满意度：{ctx.verification.get('satisfaction', {}).get('score') if ctx.verification else '-'}",
        f"  复盘：根因={ctx.review.get('root_cause') if ctx.review else '-'}，知识更新={len(ctx.review.get('kb_updates', [])) if ctx.review else 0} 条",
        f"  升级：{'是（' + str(ctx.escalate_reason) + '）' if ctx.escalated else '否'}",
        f"  总耗时：{ctx.duration_ms} ms",
        "",
        "--- 全链路追踪（Trace）---",
        tracer.summary(),
        "",
        f"Trace 明细：{trace_path}",
        f"证据报告：{report_path}",
        "",
        "说明：本证据由本地零依赖闭环生成；MCP 为参考实现，迁移真实系统仅需替换工具后端。",
        "=" * 66,
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="智服方舟多Agent客服自主闭环（本地可运行）")
    parser.add_argument("--input", default=str(ROOT / "data" / "examples" / "01_ticket.json"),
                        help="输入样例 JSON（聚合后的标准工单）")
    parser.add_argument("--approval", choices=["auto", "file"], default="auto",
                        help="审批方式：auto=模拟人工审批；file=从审批记录读取")
    parser.add_argument("--approval-file", default=str(ROOT / "data" / "examples" / "04_approval.json"))
    parser.add_argument("--evidence-dir", default=str(ROOT / "data" / "examples"))
    args = parser.parse_args()

    data = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    raw = data.get("raw_snippet") or data.get("raw_text")
    channels = data.get("channels", ["web_im"])
    ticket_id = data.get("ticket_id") or f"T-{time.strftime('%Y%m%d')}-00001"

    servers, _ = start_servers(state_dir=ROOT / ".runtime")
    try:
        clients = client_for(servers)
        for name, client in clients.items():
            tools = client.list_tools()
            print(f"[MCP] {name} 在线，工具：{len(tools)} 个")

        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        tracer = Tracer(trace_id)
        ctx = TicketContext(ticket_id, trace_id)
        approval = ApprovalGate(mode=args.approval,
                                file_path=args.approval_file if args.approval == "file" else None)
        env = AgentEnv(clients, tracer, SKILLS, approval, config={"auto_approve_review": True})

        started = time.time()
        LeaderAgent().run(ctx, env, raw_text=raw, channels=channels, ticket_id=ticket_id)
        ctx.duration_ms = ctx.duration_ms or round((time.time() - started) * 1000, 1)

        evidence_dir = pathlib.Path(args.evidence_dir)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        trace_path = evidence_dir / "闭环运行trace.json"
        report_path = evidence_dir / "闭环运行证据.txt"
        tracer.export(trace_path)
        report = build_report(ctx, tracer, trace_path, report_path, started)
        report_path.write_text(report, encoding="utf-8")

        print(report)
        print(f"\n运行证据已写入：{report_path}")
        print(f"Trace 明细已写入：{trace_path}")
        return 0 if ctx.status in ("CLOSED", "ESCALATED") else 1
    finally:
        stop_servers(servers)


if __name__ == "__main__":
    sys.exit(main())
