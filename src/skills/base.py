# -*- coding: utf-8 -*-
"""Skill 基类与调用上下文。Skill = 任务能力抽象层，内部编排 MCP 工具。"""


class SkillContext:
    """Skill 执行环境：工单上下文 + MCP 客户端 + 全链路追踪。"""

    def __init__(self, ticket, clients, tracer):
        self.ticket = ticket
        self.clients = clients          # {server_name: McpClient}
        self.tracer = tracer

    def tool(self, server, tool, arguments):
        client = self.clients[server]
        result = client.call_tool(tool, arguments)
        self.tracer.tool_call(f"{server}.{tool}", arguments, result)
        return result

    def note(self, text):
        self.ticket.add_message("skill", text)


class Skill:
    name = None
    purpose = ""

    def call(self, ctx, **kwargs):
        raise NotImplementedError
