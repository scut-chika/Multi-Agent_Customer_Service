# -*- coding: utf-8 -*-
"""样例输入输出校验：验证 src/data/examples 各环节数据一致性与状态机流转，并生成运行证据。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX_DIR = os.path.join(ROOT, "src", "data", "examples")
REPORT = os.path.join(EX_DIR, "校验报告.txt")

REQUIRED = {
    "01_ticket.json": ["ticket_id", "channels", "fingerprint", "dedup", "status"],
    "02_triage.json": ["ticket_id", "intent", "risk_level", "urgency", "confidence", "slots", "status"],
    "03_plan.json": ["ticket_id", "plan_id", "actions", "evidence_refs", "risk_level", "approval_required", "status"],
    "04_approval.json": ["ticket_id", "approved", "approved_by", "approval_evidence", "action_hash", "status"],
    "05_execution.json": ["ticket_id", "idempotency_key", "tool", "result_status", "evidence", "status"],
    "06_verification.json": ["ticket_id", "check_items", "verdict", "satisfaction", "status"],
    "07_review.json": ["ticket_id", "case_tags", "root_cause", "kb_updates", "status"],
}
CHAIN = ["NEW", "TRIAGED", "PLANNED", "APPROVED", "EXECUTED", "VERIFIED", "CLOSED"]


def main():
    lines = []
    errors = []
    ok = True
    ticket_ids = set()
    for name in sorted(REQUIRED):
        path = os.path.join(EX_DIR, name)
        if not os.path.exists(path):
            errors.append(f"{name}: 文件缺失")
            ok = False
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        missing = [k for k in REQUIRED[name] if k not in data]
        if missing:
            errors.append(f"{name}: 缺少字段 {missing}")
            ok = False
        ticket_ids.add(data.get("ticket_id"))
        lines.append(f"[{name}] 字段齐全, status={data.get('status')}, ticket_id={data.get('ticket_id')}")
    # 一致性：所有环节同一工单
    if len(ticket_ids) != 1:
        errors.append(f"工单号不一致: {ticket_ids}")
        ok = False
    else:
        lines.append(f"[一致性] 全部环节共享同一工单: {ticket_ids.pop()}")
    # 状态机
    states = []
    for name in sorted(REQUIRED):
        with open(os.path.join(EX_DIR, name), "r", encoding="utf-8") as f:
            states.append(json.load(f).get("status"))
    if states == CHAIN:
        lines.append("[状态机] 流转正确: " + " → ".join(states))
    else:
        errors.append(f"状态机流转不正确: 期望 {CHAIN}，实际 {states}")
        ok = False
    # 关键业务一致性
    with open(os.path.join(EX_DIR, "03_plan.json"), "r", encoding="utf-8") as f:
        plan = json.load(f)
    with open(os.path.join(EX_DIR, "05_execution.json"), "r", encoding="utf-8") as f:
        execution = json.load(f)
    with open(os.path.join(EX_DIR, "06_verification.json"), "r", encoding="utf-8") as f:
        verification = json.load(f)
    exp_amount = plan["actions"][0]["params"]["amount"]
    if execution["evidence"]["amount"] != exp_amount:
        errors.append(f"执行金额与方案不一致: {execution['evidence']['amount']} != {exp_amount}")
        ok = False
    if verification["check_items"][0]["pass"] is not True or verification["verdict"] != "PASS":
        errors.append("核验结果未通过但工单状态为 VERIFIED")
        ok = False
    lines.append(f"[业务校验] 方案金额 {exp_amount} = 执行金额 {execution['evidence']['amount']} = 核验金额 {verification['check_items'][0]['actual']}")
    # 审批与执行一致性
    with open(os.path.join(EX_DIR, "04_approval.json"), "r", encoding="utf-8") as f:
        approval = json.load(f)
    if approval["approved"] is not True:
        errors.append("高风险退款未审批即执行")
        ok = False
    lines.append("[审批校验] 高风险退款已通过人工审批（human-supervisor-l1）")
    # 结论
    if ok:
        lines.insert(0, "样例校验结果：PASS（全部检查通过）")
        lines.append("结论：样例数据完整、状态机流转正确、业务与审批链路一致。")
    else:
        lines.insert(0, "样例校验结果：FAIL")
        lines.extend(["错误："] + errors)
    report = "\n".join(lines)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)
    print("\n运行证据已写入:", REPORT)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
