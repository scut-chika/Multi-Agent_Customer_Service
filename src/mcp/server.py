# -*- coding: utf-8 -*-
"""MCP Server 参考实现：HTTP + JSON-RPC 风格，暴露 tools/list 与 tools/call。

协议与标准 MCP 对齐：工具发现 + 结构化调用；迁移官方 MCP SDK 时仅需替换传输层。
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class McpRequestHandler(BaseHTTPRequestHandler):
    server_version = "McpReference/0.1"

    def log_message(self, *args):
        pass  # 静默访问日志，避免刷屏

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._reply({"jsonrpc": "2.0", "error": {"code": -32700, "message": "parse error"}, "id": None})
            return
        method = payload.get("method")
        params = payload.get("params") or {}
        rid = payload.get("id")
        if method == "tools/list":
            result = {"tools": self.server.backend_tools()}
            self._reply({"jsonrpc": "2.0", "result": result, "id": rid})
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            spec = self.server.tool_spec(name)
            if not spec:
                self._reply({"jsonrpc": "2.0", "error": {"code": -32602, "message": f"tool not found: {name}"}, "id": rid})
                return
            missing = [k for k in spec.get("inputSchema", {}).get("required", []) if k not in arguments]
            if missing:
                self._reply({"jsonrpc": "2.0", "error": {"code": -32602, "message": f"missing params: {missing}"}, "id": rid})
                return
            try:
                data = spec["handler"](self.server.backend, arguments)
                ok = True
            except Exception as exc:
                data, ok = {"error": str(exc)}, False
            result = {
                "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
                "structured": data,
                "ok": ok,
            }
            self._reply({"jsonrpc": "2.0", "result": result, "id": rid})
        else:
            self._reply({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"method not found: {method}"}, "id": rid})

    def _reply(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class McpServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr, backend, name):
        self.backend = backend
        self.server_name = name
        super().__init__(addr, McpRequestHandler)

    def backend_tools(self):
        return [{"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]} for t in self.backend.tools]

    def tool_spec(self, name):
        for t in self.backend.tools:
            if t["name"] == name:
                return t
        return None
