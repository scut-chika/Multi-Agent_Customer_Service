# -*- coding: utf-8 -*-
"""可选 LLM 接入：兼容阿里云百炼 / OpenAI 的 chat completions 接口。

未配置 API Key 时返回 None，由各 Agent 自动降级为规则实现，
保证最小闭环在没有外部依赖时也可以完整运行。
"""
import json
import os
import urllib.request

DEFAULT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def chat_json(messages, temperature=0.2):
    """调用 OpenAI 兼容接口，返回解析后的 JSON；无 Key 或失败返回 None。"""
    api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    base = os.environ.get("LLM_BASE_URL", DEFAULT_BASE).rstrip("/")
    model = os.environ.get("LLM_MODEL", "qwen-plus")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return _extract_json(content)
    except Exception:
        return None
