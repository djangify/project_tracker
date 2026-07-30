# ai_assistant/agent.py
"""The agent loop: send the conversation + tool schemas to the active provider,
execute whatever tool call comes back, feed the result in, repeat until the model
replies in plain text.

Conversation messages use ai_client's normalized shape (plain dicts, so they
round-trip through the Django session):
  {"role": "user"|"assistant", "content": str, ["tool_calls": [...]]}
  {"role": "tool", "tool_call_id": str, "name": str, "content": str}
"""
import json

from ai_settings import ai_client

from . import tools

MAX_STEPS = 6  # safety cap on tool round-trips per user turn

SYSTEM_PROMPT = (
    "You are the content assistant inside a personal content calendar app. "
    "You help plan, draft, schedule and review social content by calling the "
    "provided tools. Today's date is available to you from context if given. "
    "When the user asks to create, list, move, approve, or generate content, "
    "use the tools rather than only describing what to do. After acting, briefly "
    "confirm what you did in plain language. Dates are YYYY-MM-DD. If a request "
    "is ambiguous, ask a short clarifying question instead of guessing."
)


def run_turn(messages: list[dict], system_prompt: str = SYSTEM_PROMPT) -> tuple[str, list[dict]]:
    """Advance the conversation by one user turn (which may involve several tool
    calls). `messages` should already include the latest user message. Returns
    (assistant_reply_text, updated_messages)."""
    for _ in range(MAX_STEPS):
        turn = ai_client.generate_with_tools(
            messages=messages,
            tools=tools.tool_schemas(),
            system_prompt=system_prompt,
        )

        if turn.tool_calls:
            messages.append({
                "role": "assistant",
                "content": turn.text or "",
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in turn.tool_calls
                ],
            })
            for tc in turn.tool_calls:
                result = tools.execute_tool(tc.name, tc.arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result, default=str),
                })
            continue

        reply = turn.text or ""
        messages.append({"role": "assistant", "content": reply})
        return reply, messages

    fallback = "I stopped after several steps without finishing. Could you narrow the request?"
    messages.append({"role": "assistant", "content": fallback})
    return fallback, messages


def display_messages(messages: list[dict]) -> list[dict]:
    """Just the user/assistant text turns, for rendering the chat transcript."""
    out = []
    for m in messages:
        if m["role"] == "user" and m.get("content"):
            out.append({"role": "user", "content": m["content"]})
        elif m["role"] == "assistant" and m.get("content") and not m.get("tool_calls"):
            out.append({"role": "assistant", "content": m["content"]})
    return out
