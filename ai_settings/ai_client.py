# ai_settings/ai_client.py
"""Thin, provider-agnostic AI adapter.

Every AI feature in the app calls into this module and never touches the
`openai` / `anthropic` / `google-genai` SDKs directly. Which provider is used is
decided by whichever `AIProviderConfig` row is active.

Two entry points:
  - generate(system_prompt, user_prompt, temperature) -> str
  - generate_with_tools(messages, tools, system_prompt, ...) -> ToolTurn

The tool interface is normalized so callers (the Phase 4 assistant loop, the
Phase 5 MCP server) use one shape regardless of provider:

  messages: list of dicts
    {"role": "user", "content": "..."}
    {"role": "assistant", "content": "..."|None, "tool_calls": [ToolCall-like]}
    {"role": "tool", "tool_call_id": "...", "name": "...", "content": "..."}
  tools: list of {"name", "description", "parameters": <JSON schema dict>}

The return value (ToolTurn) exposes `.text`, `.tool_calls`, and `.raw`.
"""
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from .models import AIProviderConfig

DEFAULT_MAX_TOKENS = 4096


class AIConfigError(RuntimeError):
    """No active provider, or the active provider has no API key."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ToolTurn:
    """One assistant turn: free-text and/or a set of tool calls to execute."""
    text: Optional[str] = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None


def _require_active() -> AIProviderConfig:
    config = AIProviderConfig.active()
    if config is None:
        raise AIConfigError(
            "No active AI provider. Set one up in AI Settings first."
        )
    if not config.api_key:
        raise AIConfigError(
            f"The active provider ({config.get_provider_display()}) has no API key."
        )
    return config


# ---------------------------------------------------------------------------
# generate() — plain text in, plain text out
# ---------------------------------------------------------------------------
def generate(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    config = _require_active()
    model = config.effective_model
    key = config.api_key

    if config.provider == "openai":
        return _openai_generate(key, model, system_prompt, user_prompt, temperature)
    if config.provider == "anthropic":
        return _anthropic_generate(key, model, system_prompt, user_prompt, temperature)
    if config.provider == "gemini":
        return _gemini_generate(key, model, system_prompt, user_prompt, temperature)
    raise AIConfigError(f"Unknown provider: {config.provider}")


def _openai_generate(key, model, system_prompt, user_prompt, temperature) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def _anthropic_generate(key, model, system_prompt, user_prompt, temperature) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        system=system_prompt or "",
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=temperature,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def _gemini_generate(key, model, system_prompt, user_prompt, temperature) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt or None,
            temperature=temperature,
        ),
    )
    return resp.text or ""


# ---------------------------------------------------------------------------
# generate_with_tools() — normalized function/tool calling
# ---------------------------------------------------------------------------
def generate_with_tools(
    messages: list[dict],
    tools: list[dict],
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> ToolTurn:
    config = _require_active()
    model = config.effective_model
    key = config.api_key

    if config.provider == "openai":
        return _openai_tools(key, model, messages, tools, system_prompt, temperature)
    if config.provider == "anthropic":
        return _anthropic_tools(key, model, messages, tools, system_prompt, temperature, max_tokens)
    if config.provider == "gemini":
        return _gemini_tools(key, model, messages, tools, system_prompt, temperature)
    raise AIConfigError(f"Unknown provider: {config.provider}")


def _empty_schema() -> dict:
    return {"type": "object", "properties": {}}


def _openai_tools(key, model, messages, tools, system_prompt, temperature) -> ToolTurn:
    from openai import OpenAI

    client = OpenAI(api_key=key)
    oai_tools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters") or _empty_schema(),
            },
        }
        for t in tools
    ]

    oai_messages = []
    if system_prompt:
        oai_messages.append({"role": "system", "content": system_prompt})
    for m in messages:
        role = m["role"]
        if role == "tool":
            oai_messages.append({
                "role": "tool",
                "tool_call_id": m.get("tool_call_id", ""),
                "content": m.get("content", ""),
            })
        elif role == "assistant" and m.get("tool_calls"):
            oai_messages.append({
                "role": "assistant",
                "content": m.get("content"),
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])},
                    }
                    for tc in m["tool_calls"]
                ],
            })
        else:
            oai_messages.append({"role": role, "content": m.get("content", "")})

    resp = client.chat.completions.create(
        model=model,
        messages=oai_messages,
        tools=oai_tools or None,
        temperature=temperature,
    )
    msg = resp.choices[0].message
    calls = [
        ToolCall(id=tc.id, name=tc.function.name, arguments=json.loads(tc.function.arguments or "{}"))
        for tc in (msg.tool_calls or [])
    ]
    return ToolTurn(text=msg.content, tool_calls=calls, raw=resp)


def _anthropic_tools(key, model, messages, tools, system_prompt, temperature, max_tokens) -> ToolTurn:
    import anthropic

    client = anthropic.Anthropic(api_key=key)
    a_tools = [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t.get("parameters") or _empty_schema(),
        }
        for t in tools
    ]

    a_messages = []
    for m in messages:
        role = m["role"]
        if role == "tool":
            a_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id", ""),
                    "content": m.get("content", ""),
                }],
            })
        elif role == "assistant" and m.get("tool_calls"):
            blocks = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for tc in m["tool_calls"]:
                blocks.append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc["arguments"],
                })
            a_messages.append({"role": "assistant", "content": blocks})
        else:
            a_messages.append({"role": role, "content": m.get("content", "")})

    resp = client.messages.create(
        model=model,
        system=system_prompt or "",
        max_tokens=max_tokens,
        temperature=temperature,
        tools=a_tools or anthropic.NOT_GIVEN,
        messages=a_messages,
    )
    text_parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    calls = [
        ToolCall(id=b.id, name=b.name, arguments=dict(b.input))
        for b in resp.content if getattr(b, "type", None) == "tool_use"
    ]
    return ToolTurn(text="".join(text_parts) or None, tool_calls=calls, raw=resp)


def _gemini_tools(key, model, messages, tools, system_prompt, temperature) -> ToolTurn:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    fn_decls = [
        types.FunctionDeclaration(
            name=t["name"],
            description=t.get("description", ""),
            parameters=t.get("parameters") or _empty_schema(),
        )
        for t in tools
    ]
    gem_tools = [types.Tool(function_declarations=fn_decls)] if fn_decls else None

    contents = []
    for m in messages:
        role = m["role"]
        if role == "tool":
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_function_response(
                    name=m.get("name", ""),
                    response={"result": m.get("content", "")},
                )],
            ))
        elif role == "assistant" and m.get("tool_calls"):
            parts = []
            if m.get("content"):
                parts.append(types.Part(text=m["content"]))
            for tc in m["tool_calls"]:
                parts.append(types.Part.from_function_call(name=tc["name"], args=tc["arguments"]))
            contents.append(types.Content(role="model", parts=parts))
        else:
            gem_role = "model" if role == "assistant" else "user"
            contents.append(types.Content(role=gem_role, parts=[types.Part(text=m.get("content", ""))]))

    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt or None,
            temperature=temperature,
            tools=gem_tools,
        ),
    )
    text_parts, calls = [], []
    candidate = resp.candidates[0] if resp.candidates else None
    for part in (candidate.content.parts if candidate and candidate.content else []):
        if getattr(part, "function_call", None):
            fc = part.function_call
            # Gemini has no call ids; use the function name as a stable id.
            calls.append(ToolCall(id=fc.name, name=fc.name, arguments=dict(fc.args or {})))
        elif getattr(part, "text", None):
            text_parts.append(part.text)
    return ToolTurn(text="".join(text_parts) or None, tool_calls=calls, raw=resp)
