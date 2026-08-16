# 智服方舟 · Agent 代码包

「聚合 → 分诊 → 方案 → 审批 → 执行 → 核验 → 复盘」多 Agent 自主闭环：
1 个 Leader + 6 个 Worker、7 个 Skill、5 个 MCP 参考 Server。

## 快速运行（零依赖，Python 3.10+）

```bash
py main.py                                          # 退款闭环（CLOSED，核验 PASS）
py main.py --input data/examples/08_escalation.json # 异常升级场景（ESCALATED）
```

Windows 可直接 `.\run_demo.ps1`。

运行后在 `data/examples/` 生成运行证据：

- `闭环运行证据.txt`
- `闭环运行trace.json`

## 接真实大模型（可选）

设置 `DASHSCOPE_API_KEY`（或 `OPENAI_API_KEY`）后分诊自动调用 LLM，未配置时降级为规则实现。

## 部署真实 AgentTeams（需 Docker + LLM Key）

1. 官方安装器安装 AgentTeams；
2. 创建 6 个 Worker（角色见 `config/agentteams.yaml`，身份见 `identities/identities.yaml`）；
3. 启动 MCP Server：`python3 -m mcp.run_servers`（5 服务，端口 8000-8004）；
4. 在 AgentTeams 控制台注册 MCP 服务，挂载 `skills/skills.yaml` 中的 Skill；
5. 以 `data/examples/01_ticket.json` 验证闭环，AgentLoop 采集 Trace。

## 目录

```text
agents/   7 个 Agent（Leader + 6 Worker）
skills/   7 个 Skill 实现 + 注册清单
mcp/      5 个 MCP 参考 Server + 客户端 + 工具契约
engine/   状态机 / Ticket Context / Trace / 审批 / LLM
main.py   运行入口
```

## 已验证

- 闭环 NEW→CLOSED，核验 PASS，满意度 5；
- 幂等：重复运行复用既有退款，不重复退款；
- 异常：低置信度意图升级人工（ESCALATED）；
- MCP：5 服务 12 工具 `tools/list` 自检通过。
