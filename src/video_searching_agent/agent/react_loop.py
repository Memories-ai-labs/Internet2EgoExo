"""A small ReAct runtime: think, act, observe, until there is an answer.

The agents in this repo started as single-shot calls — build a prompt, read one
JSON answer back — and that shape has a specific weakness. It forces the caller
to decide in advance what evidence the model gets. If a span's captions are
ambiguous, a single-shot agent cannot go and look at the frames; it can only
answer badly, from what it was handed.

This loop lets the agent decide what to examine next. It gets a set of tools —
read the captions for a window, look at frames of a span, search the collection
for a moment — and on each turn it either calls one and receives the result as
an observation, or it answers. Every step lands in the shared `AgentTrace`, so
the reasoning is inspectable afterwards rather than being a black box that
emitted a label.

Three bounds keep it honest and affordable:

* **steps** — a loop that has not converged in a handful of turns is not going
  to, and each turn costs a model call;
* **money** — tools that spend (a cut is $0.005) report it, and the loop stops
  when the budget is gone rather than when it feels finished;
* **the answer contract** — the loop ends when the model emits a JSON object
  with the shape the caller asked for. Running out of steps is *not* an answer:
  it returns None, and the caller abstains.

The tool protocol is deliberately plain text rather than provider function
calling, because both matter here and only one of the two providers exposes tool
calls the same way. The model writes a JSON object with `tool` and `arguments`,
or one with the answer.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.agent.react import AgentTrace, parse_json_object

logger = logging.getLogger(__name__)

# A loop that has not answered by here is looping, not thinking.
DEFAULT_MAX_STEPS = 6


@dataclass
class ToolResult:
    """What a tool hands back to the loop."""

    observation: str
    images: list[bytes] = field(default_factory=list)
    cost_usd: float = 0.0


ToolFn = Callable[[dict[str, Any]], Awaitable[ToolResult]]


@dataclass
class Tool:
    """One thing the agent can do, described to it in its own prompt."""

    name: str
    description: str
    arguments: str
    run: ToolFn


@dataclass
class LoopResult:
    """The outcome of a loop."""

    answer: dict[str, Any] | None = None
    steps_taken: int = 0
    cost_usd: float = 0.0
    tools_called: list[str] = field(default_factory=list)
    stopped_because: str = ""

    @property
    def answered(self) -> bool:
        return self.answer is not None


def tool_instructions(tools: list[Tool]) -> str:
    """The part of a system prompt that tells the agent how to act."""

    if not tools:
        return ""
    lines = ["You may use these tools, one per turn:", ""]
    for tool in tools:
        lines.append(f"- `{tool.name}` — {tool.description}")
        lines.append(f"  arguments: {tool.arguments}")
    lines += [
        "",
        "To use one, reply with ONLY this JSON:",
        '{"thought": "why this tool, in one clause", "tool": "<name>", "arguments": {...}}',
        "",
        "When you have enough to answer, reply with ONLY the answer object the "
        "task asked for. Do not mix a tool call and an answer in one reply.",
        "",
        "Look before you conclude when the evidence you have is thin. Do not "
        "call a tool you have already called with the same arguments — you have "
        "its answer already. If a tool tells you it could not see, say so in "
        "your answer rather than guessing what it would have shown.",
    ]
    return "\n".join(lines)


async def run_loop(
    client: Any,
    system_prompt: str,
    opening: str,
    tools: list[Tool],
    *,
    trace: AgentTrace | None = None,
    agent: str = "",
    max_steps: int = DEFAULT_MAX_STEPS,
    budget_usd: float | None = None,
    answer_keys: tuple[str, ...] = (),
    max_tokens: int = 1200,
) -> LoopResult:
    """Run think-act-observe until the model answers or a bound is hit.

    Args:
        client: An LLM client with the shared conversation helpers.
        system_prompt: The task. `tool_instructions` is appended to it.
        opening: The first user turn — what to judge.
        tools: What the agent may call.
        trace: Where to record the steps. One is created when omitted.
        agent: Name recorded against each step.
        max_steps: Turns before giving up. Giving up is not an answer.
        budget_usd: Stop once the tools have spent this much.
        answer_keys: Keys that mark a reply as the answer rather than a tool
            call. Empty means anything without a `tool` key is the answer.
        max_tokens: Per reply.

    Returns:
        A LoopResult. `answer` None means the loop did not converge, and the
        caller should abstain rather than invent a verdict.
    """
    by_name = {tool.name: tool for tool in tools}
    trace = trace if trace is not None else AgentTrace(agent=agent)
    result = LoopResult()

    system = f"{system_prompt}\n\n{tool_instructions(tools)}" if tools else system_prompt
    messages = client.new_conversation(opening)

    for step in range(1, max_steps + 1):
        result.steps_taken = step
        try:
            response = await client.create_message_async(
                messages, system=system, max_tokens=max_tokens
            )
        except Exception as exc:  # noqa: BLE001 - a dead call ends the loop
            result.stopped_because = f"model call failed: {str(exc)[:150]}"
            trace.add(
                thought="Ask the model what to do next.",
                action="model",
                observation=result.stopped_because,
            )
            return result

        text = ""
        if hasattr(client, "get_text_response"):
            text = client.get_text_response(response) or ""
        try:
            reply = parse_json_object(text)
        except Exception:  # noqa: BLE001 - unparseable is a dead end, not an answer
            result.stopped_because = f"unreadable reply: {text[:120]}"
            trace.add(
                thought="Read the model's reply.",
                action="parse",
                observation=result.stopped_because,
            )
            return result

        tool_name = reply.get("tool")
        if not tool_name:
            if answer_keys and not any(key in reply for key in answer_keys):
                result.stopped_because = (
                    f"reply is neither a tool call nor an answer: {sorted(reply)[:6]}"
                )
                trace.add(
                    thought="Read the model's reply.",
                    action="parse",
                    observation=result.stopped_because,
                )
                return result
            result.answer = reply
            result.stopped_because = "answered"
            trace.add(
                thought=str(reply.get("thought") or "Enough to answer."),
                action="answer",
                observation=json.dumps(
                    {k: v for k, v in reply.items() if k != "thought"}, default=str
                )[:300],
            )
            return result

        tool = by_name.get(str(tool_name))
        arguments = reply.get("arguments") if isinstance(reply.get("arguments"), dict) else {}
        thought = str(reply.get("thought") or f"Use {tool_name}.")

        if tool is None:
            observation = (
                f"there is no tool called {tool_name!r}; the ones you have are {sorted(by_name)}"
            )
        elif budget_usd is not None and result.cost_usd >= budget_usd:
            observation = (
                f"the budget for looking is spent (${result.cost_usd:.3f}); answer "
                "from what you already have, and say what you could not check"
            )
        else:
            try:
                outcome = await tool.run(arguments)
            except Exception as exc:  # noqa: BLE001 - a broken tool is an observation
                outcome = ToolResult(observation=f"{tool.name} failed: {str(exc)[:150]}")
            result.cost_usd += outcome.cost_usd
            result.tools_called.append(tool.name)
            observation = outcome.observation
            client.append_model_response(messages, response)
            if outcome.images and hasattr(client, "append_user_images"):
                client.append_user_images(messages, observation, outcome.images)
            else:
                client.append_user_text(messages, observation)
            trace.add(
                thought=thought,
                action=tool.name,
                action_input=arguments,
                observation=observation[:300],
            )
            continue

        # The paths that did not run a tool still have to be told to the model.
        client.append_model_response(messages, response)
        client.append_user_text(messages, observation)
        trace.add(
            thought=thought,
            action=str(tool_name),
            action_input=arguments,
            observation=observation[:300],
        )

    result.stopped_because = f"no answer in {max_steps} steps"
    trace.add(
        thought="Stop rather than keep paying for turns.",
        action="give_up",
        observation=result.stopped_because,
    )
    return result
