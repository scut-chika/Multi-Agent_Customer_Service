# -*- coding: utf-8 -*-
"""启动/停止 5 个 MCP 参考 Server；main.py 在进程内启动，真实部署用 --standalone。"""
import sys
import threading

from .backend import build_backends
from .client import McpClient
from .server import McpServer

DEFAULT_PORTS = {
    "ticketing": 8000,
    "payment": 8001,
    "crm": 8002,
    "kb": 8003,
    "notify": 8004,
}


def start_servers(ports=None, host="127.0.0.1", state_dir=None):
    ports = ports or DEFAULT_PORTS
    backends = build_backends(state_dir=state_dir)
    servers, threads = {}, {}
    for name, port in ports.items():
        server = McpServer((host, port), backends[name], name)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers[name] = server
        threads[name] = thread
    return servers, threads


def stop_servers(servers):
    for server in servers.values():
        server.shutdown()
        server.server_close()


def client_for(servers, ports=None):
    ports = ports or DEFAULT_PORTS
    clients = {}
    for name, server in servers.items():
        clients[name] = McpClient(f"http://127.0.0.1:{ports[name]}", name)
    return clients


def main():
    servers, threads = start_servers()
    print("MCP 参考 Server 已启动：")
    for name, server in servers.items():
        print(f"  {name}: http://127.0.0.1:{server.server_address[1]} ({len(server.backend_tools())} tools)")
    print("\n自检 tools/list：")
    clients = client_for(servers)
    for name, client in clients.items():
        tools = client.list_tools()
        print(f"  [{name}] " + ", ".join(t["name"] for t in tools))
    print("\n按 Ctrl+C 停止")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        stop_servers(servers)
        print("已停止")


if __name__ == "__main__":
    sys.exit(main())
