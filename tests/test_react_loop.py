"""The think-act-observe runtime both agents run on.

The agents started as single-shot calls, which forces the caller to decide in
advance what evidence the model gets. If a span's captions are ambiguous, a
single-shot agent cannot go and look — it can only answer badly from what it was
handed. These tests are mostly about the bounds: a loop that can spend money and
call tools has to stop for the right reasons, and running out of steps must never
look like an answer.
"""

from __future__ import annotations

from typing import Any

import pytest

from video_searching_agent.agent.react import AgentTrace
from video_searching_agent.agent.react_loop import (
    Tool,
    ToolResult,
    run_loop,
    tool_instructions,
)


class _Model:
    """Replies with a scripted sequence, recording what it was shown."""

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.turns: list[Any] = []
        self.images_seen = 0

    def new_conversation(self, text: str) -> list[dict[str, Any]]:
        return [{"role": "user", "content": text}]

    def append_user_text(self, messages: list[dict[str, Any]], text: str) -> None:
        messages.append({"role": "user", "content": text})

    def append_user_images(
        self, messages: list[dict[str, Any]], text: str, images: list[bytes], **_: Any
    ) -> None:
        self.images_seen += len(images)
        messages.append({"role": "user", "content": text})

    def append_model_response(self, messages: list[dict[str, Any]], response: Any) -> None:
        messages.append({"role": "assistant", "content": response["text"]})

    async def create_message_async(self, messages: list[dict[str, Any]], **_: Any) -> Any:
        self.turns.append(list(messages))
        if not self.replies:
            raise AssertionError("the loop asked for more replies than were scripted")
        return {"text": self.replies.pop(0)}

    def get_text_response(self, response: Any) -> str:
        return response["text"]


def _tool(name="look", observation="saw something", images=None, cost=0.0, calls=None):
    async def run(arguments: dict[str, Any]) -> ToolResult:
        if calls is not None:
            calls.append(arguments)
        return ToolResult(observation=observation, images=images or [], cost_usd=cost)

    return Tool(name=name, description="d", arguments="{}", run=run)


@pytest.mark.asyncio
async def test_a_direct_answer_ends_the_loop():
    model = _Model(['{"label": "chop-onion", "usable": true}'])
    result = await run_loop(model, "sys", "open", [], answer_keys=("label",))
    assert result.answered
    assert result.answer["label"] == "chop-onion"
    assert result.steps_taken == 1
    assert result.stopped_because == "answered"


@pytest.mark.asyncio
async def test_a_tool_call_is_run_and_its_result_comes_back_as_a_turn():
    calls: list[dict] = []
    model = _Model(
        [
            '{"thought": "need to see it", "tool": "look", "arguments": {"start": 1}}',
            '{"label": "chop-onion", "usable": true}',
        ]
    )
    result = await run_loop(
        model, "sys", "open", [_tool(calls=calls)], answer_keys=("label",)
    )
    assert calls == [{"start": 1}]
    assert result.tools_called == ["look"]
    assert result.answered
    # The observation has to reach the model, or the loop is theatre.
    assert any("saw something" in str(turn) for turn in model.turns[-1])


@pytest.mark.asyncio
async def test_frames_are_shown_as_images_not_described():
    model = _Model(
        ['{"tool": "look", "arguments": {}}', '{"label": "x", "usable": true}']
    )
    await run_loop(
        model,
        "sys",
        "open",
        [_tool(images=[b"jpegbytes", b"more"])],
        answer_keys=("label",),
    )
    assert model.images_seen == 2


@pytest.mark.asyncio
async def test_running_out_of_steps_is_not_an_answer():
    """The caller must abstain, not receive a half-formed verdict."""

    model = _Model(['{"tool": "look", "arguments": {}}'] * 3)
    result = await run_loop(
        model, "sys", "open", [_tool()], max_steps=3, answer_keys=("label",)
    )
    assert result.answered is False
    assert result.answer is None
    assert "no answer in 3 steps" in result.stopped_because


@pytest.mark.asyncio
async def test_the_budget_stops_the_spending_but_still_asks_for_an_answer():
    model = _Model(
        [
            '{"tool": "look", "arguments": {}}',
            '{"tool": "look", "arguments": {"again": true}}',
            '{"label": "x", "usable": true}',
        ]
    )
    result = await run_loop(
        model,
        "sys",
        "open",
        [_tool(cost=0.01)],
        budget_usd=0.005,
        answer_keys=("label",),
    )
    # The first look spent past the budget; the second was refused, not charged.
    assert result.cost_usd == pytest.approx(0.01)
    assert result.tools_called == ["look"]
    assert result.answered, "being out of budget must not stop it answering"
    assert any("budget for looking is spent" in str(turn) for turn in model.turns[-1])


@pytest.mark.asyncio
async def test_an_unknown_tool_is_reported_back_rather_than_crashing():
    model = _Model(
        ['{"tool": "teleport", "arguments": {}}', '{"label": "x", "usable": true}']
    )
    result = await run_loop(model, "sys", "open", [_tool()], answer_keys=("label",))
    assert result.answered
    assert any("no tool called 'teleport'" in str(turn) for turn in model.turns[-1])


@pytest.mark.asyncio
async def test_a_tool_that_raises_becomes_an_observation():
    async def explode(arguments: dict[str, Any]) -> ToolResult:
        raise RuntimeError("the cut failed")

    model = _Model(
        ['{"tool": "look", "arguments": {}}', '{"label": "x", "usable": true}']
    )
    result = await run_loop(
        model,
        "sys",
        "open",
        [Tool(name="look", description="d", arguments="{}", run=explode)],
        answer_keys=("label",),
    )
    assert result.answered
    assert any("look failed: the cut failed" in str(turn) for turn in model.turns[-1])


@pytest.mark.asyncio
async def test_an_unreadable_reply_ends_the_loop_without_an_answer():
    model = _Model(["I would rather not answer in JSON, thanks"])
    result = await run_loop(model, "sys", "open", [_tool()], answer_keys=("label",))
    assert result.answered is False
    assert "unreadable reply" in result.stopped_because


@pytest.mark.asyncio
async def test_a_reply_that_is_neither_a_call_nor_an_answer_is_refused():
    """Otherwise a stray object becomes a verdict with every field missing."""

    model = _Model(['{"musing": "this video is quite long"}'])
    result = await run_loop(model, "sys", "open", [_tool()], answer_keys=("label",))
    assert result.answered is False
    assert "neither a tool call nor an answer" in result.stopped_because


@pytest.mark.asyncio
async def test_a_dead_model_ends_the_loop_cleanly():
    class Dead(_Model):
        async def create_message_async(self, messages, **_):
            raise RuntimeError("429 rate limited")

    result = await run_loop(Dead([]), "sys", "open", [_tool()], answer_keys=("label",))
    assert result.answered is False
    assert "429" in result.stopped_because


@pytest.mark.asyncio
async def test_every_step_lands_in_the_trace():
    trace = AgentTrace(agent="test")
    model = _Model(
        ['{"tool": "look", "arguments": {"start": 3}}', '{"label": "x", "usable": true}']
    )
    await run_loop(model, "sys", "open", [_tool()], trace=trace, answer_keys=("label",))
    actions = [step["action"] for step in trace.as_list()]
    assert actions == ["look", "answer"]
    assert trace.as_list()[0]["action_input"] == {"start": 3}


def test_the_tool_instructions_name_every_tool_and_the_answer_contract():
    text = tool_instructions([_tool(name="look"), _tool(name="read_captions")])
    assert "`look`" in text and "`read_captions`" in text
    assert "Do not mix a tool call and an answer" in text
    assert "Look before you conclude" in text


def test_no_tools_means_no_instructions():
    assert tool_instructions([]) == ""
