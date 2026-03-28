"""VLM (Vision Language Model) screenshot analysis."""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from typing import Any

from . import input

JsonDict = dict[str, Any]

_DEFAULT_MODELS: dict[str, str] = {
    "openrouter": "google/gemma-3-27b-it:free",
    "anthropic": "claude-sonnet-4-20250514",
    "ollama": "gemma3",
}

_PROVIDER_URLS: dict[str, str] = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "ollama": "http://localhost:11434/api/chat",
}

_API_KEY_ENV: dict[str, str] = {
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def _read_image_b64(path: str) -> str:
    """Read a file and return its base64-encoded contents."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _build_openrouter_payload(
    prompt: str,
    images_b64: list[str],
    model: str,
) -> tuple[str, dict[str, str], bytes]:
    """Build request for OpenRouter (OpenAI-compatible)."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    content: list[JsonDict] = []
    for img in images_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img}"},
        })
    content.append({"type": "text", "text": prompt})

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    return _PROVIDER_URLS["openrouter"], headers, json.dumps(payload).encode()


def _build_anthropic_payload(
    prompt: str,
    images_b64: list[str],
    model: str,
) -> tuple[str, dict[str, str], bytes]:
    """Build request for Anthropic Messages API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    content: list[JsonDict] = []
    for img in images_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": img},
        })
    content.append({"type": "text", "text": prompt})

    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": content}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    return _PROVIDER_URLS["anthropic"], headers, json.dumps(payload).encode()


def _build_ollama_payload(
    prompt: str,
    images_b64: list[str],
    model: str,
) -> tuple[str, dict[str, str], bytes]:
    """Build request for local Ollama API."""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": images_b64,
            }
        ],
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    return _PROVIDER_URLS["ollama"], headers, json.dumps(payload).encode()


def _extract_text(provider: str, body: bytes) -> str:
    """Extract the text response from the provider's JSON response."""
    data = json.loads(body)
    if provider == "openrouter":
        return str(data["choices"][0]["message"]["content"])
    if provider == "anthropic":
        return str(data["content"][0]["text"])
    if provider == "ollama":
        return str(data["message"]["content"])
    return ""


_PAYLOAD_BUILDERS = {
    "openrouter": _build_openrouter_payload,
    "anthropic": _build_anthropic_payload,
    "ollama": _build_ollama_payload,
}


def _send_request(url: str, headers: dict[str, str], data: bytes) -> bytes:
    """Send an HTTP POST and return the response body."""
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def analyze_screenshot(
    prompt: str,
    provider: str = "openrouter",
    model: str | None = None,
) -> JsonDict:
    """Take a screenshot and send it to a VLM for analysis.

    Parameters
    ----------
    prompt:
        The question or instruction for the VLM.
    provider:
        One of ``"openrouter"``, ``"anthropic"``, ``"ollama"``.
    model:
        Override the default model for the chosen provider.
    """
    if provider not in _PAYLOAD_BUILDERS:
        valid = ", ".join(sorted(_PAYLOAD_BUILDERS))
        return {
            "success": False,
            "error": f"Invalid provider {provider!r}. Valid providers: {valid}",
        }

    screenshot_result = input.screenshot()
    if not screenshot_result.get("success"):
        return {
            "success": False,
            "error": f"Screenshot failed: {screenshot_result.get('error', 'unknown')}",
        }

    resolved_model = model or _DEFAULT_MODELS[provider]
    try:
        img_b64 = _read_image_b64(screenshot_result["path"])
    except Exception as exc:
        return {"success": False, "error": f"Failed to read screenshot: {exc}"}

    builder = _PAYLOAD_BUILDERS[provider]
    url, headers, data = builder(prompt, [img_b64], resolved_model)

    try:
        response_body = _send_request(url, headers, data)
    except Exception as exc:
        return {"success": False, "error": f"API request failed: {exc}"}

    try:
        analysis = _extract_text(provider, response_body)
    except Exception as exc:
        return {"success": False, "error": f"Failed to parse response: {exc}"}

    return {
        "success": True,
        "action": "analyze_screenshot",
        "analysis": analysis,
        "provider": provider,
        "model": resolved_model,
    }


def compare_screenshots(
    path1: str,
    path2: str,
    prompt: str | None = None,
    provider: str = "openrouter",
    model: str | None = None,
) -> JsonDict:
    """Compare two screenshot images using a VLM.

    Parameters
    ----------
    path1, path2:
        Paths to PNG screenshots.
    prompt:
        Custom comparison instruction. Defaults to a generic diff prompt.
    provider:
        One of ``"openrouter"``, ``"anthropic"``, ``"ollama"``.
    model:
        Override the default model.
    """
    if provider not in _PAYLOAD_BUILDERS:
        valid = ", ".join(sorted(_PAYLOAD_BUILDERS))
        return {
            "success": False,
            "error": f"Invalid provider {provider!r}. Valid providers: {valid}",
        }

    resolved_model = model or _DEFAULT_MODELS[provider]
    resolved_prompt = prompt or (
        "Compare these two screenshots and describe any differences you observe."
    )

    try:
        img1_b64 = _read_image_b64(path1)
        img2_b64 = _read_image_b64(path2)
    except Exception as exc:
        return {"success": False, "error": f"Failed to read image: {exc}"}

    builder = _PAYLOAD_BUILDERS[provider]
    url, headers, data = builder(resolved_prompt, [img1_b64, img2_b64], resolved_model)

    try:
        response_body = _send_request(url, headers, data)
    except Exception as exc:
        return {"success": False, "error": f"API request failed: {exc}"}

    try:
        analysis = _extract_text(provider, response_body)
    except Exception as exc:
        return {"success": False, "error": f"Failed to parse response: {exc}"}

    return {
        "success": True,
        "action": "compare_screenshots",
        "analysis": analysis,
        "provider": provider,
        "model": resolved_model,
        "path1": path1,
        "path2": path2,
    }
