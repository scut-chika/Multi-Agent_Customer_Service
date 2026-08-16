# -*- coding: utf-8 -*-
"""MCP 客户端：工具发现 + 调用（连接失败自动重试，业务错误直接抛出）。"""
import json
import time
import urllib.request


class McpError(RuntimeError):
    pass


class McpClient:
    def __init__(self, base_url, name, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.name = name
        self.timeout = timeout

    def _post(self, payload, retries=3):
        body = json.dumps(payload).encode("utf-8")
        last_err = None
        for attempt in range(1, retries + 1):
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/mcp",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as exc:
                last_err = exc
                time.sleep(0.3 * attempt)
        raise McpError(f"[{self.name}] 连接失败(已重试{retries}次): {last_err}")

    def list_tools(self):
        resp = self._post({"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1})
        if "error" in resp:
            raise McpError(resp["error"])
        return resp["result"]["tools"]

    def call_tool(self, name, arguments):
        resp = self._post({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": name, "arguments": arguments}, "id": 2})
        if "error" in resp:
            raise McpError(f"[{self.name}] {resp['error']}")
        result = resp["result"]
        if not result.get("ok"):
            raise McpError(f"[{self.name}] 工具执行失败: {result.get('structured')}")
        return result.get("structured")
