"""
LLM 配置与实例化模块。

该文件暴露 ``lm`` 对象，供 DSPy 在其他脚本中统一使用：

>>> import dspy
>>> import config
>>> dspy.settings.configure(lm=config.lm)
"""

from __future__ import annotations

import os
from typing import Any, Dict

import dspy
import litellm

# LLM配置
LLM_CONFIG: Dict[str, Any] = {
    "base_url": "https://api.chatanywhere.tech",
    "headers": {
        "Authorization": "Bearer sk-V3NEKZqHyWRjcU5UjzJdFCPAIudX1G8ReWd0DeyMYPjeo2Y5",
        "Content-Type": "application/json",
    },
    "method": "POST",
    "endpoint": "/v1/chat/completions",
    "model": "deepseek-v3-2-exp",
    "provider": "openai",
}


def _resolve_api_key() -> str:
    """优先从环境变量读取 Token，失败则回退到配置文件中的值。"""
    env_key = os.getenv("CHATANYWHERE_API_KEY")
    if env_key:
        return env_key
    raw_header = LLM_CONFIG["headers"].get("Authorization", "")
    if raw_header.lower().startswith("bearer "):
        return raw_header.split(" ", maxsplit=1)[1]
    raise RuntimeError("无法在配置或环境变量中找到可用的 API Key。")


def _configure_litellm(api_key: str) -> None:
    """Against LiteLLM bridge so DSPy can route到自定义 OpenAI 兼容端点。"""
    litellm.api_key = api_key
    base_url = LLM_CONFIG.get("base_url")
    if base_url:
        litellm.api_base = base_url
    # LiteLLM 默认认为 OpenAI 风格接口，因此无需额外 headers/endpoint 配置。


def _build_model_name() -> str:
    """生成符合 dspy.LM 约定的模型名称（provider/model）。"""
    provider = LLM_CONFIG.get("provider", "openai")
    model_id = LLM_CONFIG["model"]
    if "/" in model_id:
        return model_id
    return f"{provider}/{model_id}"


# 供外部引用的 LLM 对象
_API_KEY = _resolve_api_key()
_configure_litellm(_API_KEY)

lm = dspy.LM(
    model=_build_model_name(),
    max_tokens=1024,
    temperature=0.3,
)