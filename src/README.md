# 可执行 AgentTeams 代码包（初赛骨架 / 复赛可运行化）

> 初赛阶段代码非强制；本包提供复赛可直接展开的骨架：运行入口、依赖说明、配置文件、样例输入输出与运行证据。

## 运行入口

| 操作 | 命令 | 说明 |
| --- | --- | --- |
| 校验样例输入输出（可立即运行） | `py scripts/check_examples.py` | 校验 7 个环节样例数据一致性与状态机流转，输出运行证据 |
| 重新生成方案 PPT | `py scripts/build_ppt.py` | 需要 `python-pptx` |
| 部署 AgentTeams 实例 | 官方安装器 | 见下方“复赛落地步骤” |

## 依赖说明

- Python 3.10+（仅样例校验与 PPT 生成需要）
- Docker + 4 GB 可用内存（AgentTeams 本地部署）
- LLM API Key：阿里云百炼/Qwen 或任意 OpenAI 兼容服务
- python-pptx（可选，仅用于重新生成 PPT）

## 目录结构

```text
src/
├── README.md
├── config/
│   ├── agentteams.yaml      # AgentTeams 实例 / 团队 / Worker / MCP 配置示例
│   └── skills.yaml          # 7 个核心 Skill 注册清单
├── identities/
│   └── identities.yaml      # 各 Agent 身份定义（附录 A 机器可读版）
├── skills/
│   └── skills.yaml          # Skill 九要素完整定义（机器可读）
├── mcp/
│   └── tools.json           # 外部工具集成契约（迁移 MCP 的前置设计）
└── data/examples/
    ├── 01_ticket.json       # 聚合：标准工单
    ├── 02_triage.json       # 分诊：意图与分级
    ├── 03_plan.json         # 方案：处理方案与证据引用
    ├── 04_approval.json     # 审批：人工审批记录
    ├── 05_execution.json    # 执行：幂等执行结果
    ├── 06_verification.json # 核验：核验报告与满意度
    ├── 07_review.json       # 复盘：经验沉淀
    └── 校验报告.txt         # 由校验脚本生成（运行证据）
```

## 复赛落地步骤

1. 安装 AgentTeams：
   ```bash
   bash <(curl -sSL https://raw.githubusercontent.com/agentscope-ai/AgentTeams/main/install/agentteams-install.sh)
   ```
2. 在 Element Web 中创建 Manager（主控）与 6 个 Worker，角色与权限参考 `config/agentteams.yaml`。
3. 按 `config/skills.yaml` 将 Skill 挂载到对应 Worker。
4. 按 `mcp/tools.json` 启动 MCP Server（先以仿真/桩服务验证）。
5. 使用 `data/examples/` 作为输入输出基准，跑通
   `NEW → TRIAGED → PLANNED → APPROVED → EXECUTED → VERIFIED → CLOSED` 闭环。
6. 采集 Trace / 日志 / 截图作为运行证据归档到 `docs/运行证据/`。
