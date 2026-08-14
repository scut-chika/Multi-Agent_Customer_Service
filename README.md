# 智服方舟 —— 多智能体客服自主闭环平台

方向二：智能客服自主闭环（初赛：方向与方案设计）

本仓库为参赛项目的初赛交付物，包含：

```text
.
├── README.md                 # 本文件：项目总览与使用说明
├── docs/
│   ├── 作品简介.md           # 500 字作品简介（必交）
│   ├── 附录A-Agent-Identity清单.md  # 各 Agent 身份属性、能力边界与协同关系
│   └── Skill清单.md          # 核心 Skill 九要素完整清单
├── ppt/
│   └── 智服方舟-初赛方案.pptx      # 方案 PPT（重点交付物，可脚本重新生成）
├── scripts/
│   ├── build_ppt.py          # PPT 生成脚本（python-pptx）
│   └── check_examples.py     # 样例输入输出校验脚本（可运行证据）
└── src/                      # 可执行 AgentTeams 代码包（复赛可运行化的骨架）
    ├── README.md             # 运行入口、依赖说明
    ├── config/               # AgentTeams / Skill 配置
    ├── identities/           # 各 Agent 身份定义
    ├── skills/               # 核心 Skill 定义
    ├── mcp/                  # 外部工具集成契约（迁移 MCP 的前置设计）
    └── data/examples/        # 样例输入输出
```

## 交付内容与对应要求

| 初赛要求 | 交付位置 |
| --- | --- |
| 作品简介（500 字以内） | `docs/作品简介.md` |
| 方案 PPT / PDF | `ppt/智服方舟-初赛方案.pptx` |
| 可执行 AgentTeams 代码包（可选） | `src/`，含运行入口、依赖说明、配置、样例输入输出与校验证据 |

## 快速使用

1. PPT：直接打开 `ppt/智服方舟-初赛方案.pptx`；如需重新生成：

   ```bash
   py -m pip install python-pptx
   py scripts/build_ppt.py
   ```

2. 样例校验（运行证据）：

   ```bash
   py scripts/check_examples.py
   ```

3. AgentTeams 本地部署（复赛阶段）：参照 `src/README.md`，使用官方安装器
   `bash <(curl -sSL https://raw.githubusercontent.com/agentscope-ai/AgentTeams/main/install/agentteams-install.sh)`
   安装后按 `src/config/` 中的 Worker / Skill 配置创建智能体团队。

## 一句话方案

以阿里云 AgentTeams（Leader-Worker 协同框架）为底座，构建
「接入聚合 → 意图分诊 → 方案生成 → 自动执行 → 结果核验 → 复盘沉淀」
的多 Agent 自主闭环，通过 Skill 抽象任务能力、MCP 连接企业系统，
高风险动作人工审批，全程可观测、可审计、可回滚。
