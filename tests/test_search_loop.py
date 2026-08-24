"""Searching until the footage passes, and knowing when the seam is dry.

The properties worth pinning are the ones that cost something when they break:
a hunt that stops early reports it rather than rounding up; a candidate nobody
looked at never counts as a find; and the agent is told *why* its own phrasings
failed, because a round that only says "6 rejected" teaches it nothing and it
will search the same genre again.
"""

from __future__ import annotations

import json

import pytest

from video_searching_agent.agent.search_loop import DRY_ROUNDS, run_search_loop


class Verdict:
    """A SightVerdict as the screen hands one back."""

    def __init__(self, viewpoint="egocentric", looked=True, why="", off_task=False, cost=0.002):
        self.viewpoint = viewpoint
        self.looked = looked
        self.why = why
        self.confidence = 0.95
        self.cost_usd = cost
        self.task_reading = "other_kind" if off_task else "doing"
        self._off_task = off_task

    def misses_task(self):
        return self._off_task


class FakeAgent:
    """Proposes scripted rounds of searches, then answers."""

    def __init__(self, rounds: list[list[str]]):
        self.rounds = rounds
        self.turn = 0
        self.observations: list[str] = []

    def new_conversation(self, opening):
        self.turn = 0
        return [{"role": "user", "content": opening}]

    async def create_message_async(self, messages, system=None, max_tokens=1200):
        for message in reversed(messages):
            if message.get("role") == "user" and message["content"] not in self.observations:
                if message["content"].startswith("Round ") or "budget" in message["content"]:
                    self.observations.append(message["content"])
                break
        if self.turn < len(self.rounds):
            queries = self.rounds[self.turn]
            self.turn += 1
            return json.dumps({"tool": "search", "arguments": {"queries": queries}})
        return json.dumps({"done": True, "found": 0, "what_worked": "", "what_did_not": "tried"})

    def get_text_response(self, response):
        return response

    def append_model_response(self, messages, response):
        messages.append({"role": "assistant", "content": response})

    def append_user_text(self, messages, text):
        messages.append({"role": "user", "content": text})

    def append_user_images(self, messages, text, images):
        messages.append({"role": "user", "content": text})


def _search_returning(pools: dict[str, list[dict]]):
    async def search(query: str, wanted: str):
        return pools.get(query, [])

    return search


def _screen_by_url(verdicts: dict[str, Verdict]):
    async def screen(candidates, task):
        return [verdicts.get(c["url"], Verdict(viewpoint="exocentric")) for c in candidates]

    return screen


def _rows(*urls):
    return [{"url": u, "title": f"a video at {u}", "platform": "youtube"} for u in urls]


async def test_it_stops_as_soon_as_the_target_is_met():
    agent = FakeAgent([["one"], ["two"]])
    result = await run_search_loop(
        "fixing bikes",
        target=2,
        llm=agent,
        search=_search_returning({"one": _rows("a", "b"), "two": _rows("c")}),
        screen=_screen_by_url({"a": Verdict(), "b": Verdict()}),
    )
    assert result.met_target
    assert len(result.kept) == 2
    assert result.rounds == 1, "a met target must not pay for another round"


async def test_falling_short_is_reported_not_rounded_up():
    agent = FakeAgent([["one"]])
    result = await run_search_loop(
        "fixing bikes",
        target=5,
        llm=agent,
        search=_search_returning({"one": _rows("a")}),
        screen=_screen_by_url({"a": Verdict()}),
    )
    assert not result.met_target
    assert len(result.kept) == 1
    assert result.stopped_because
    assert result.what_did_not == "tried"


async def test_a_candidate_nobody_looked_at_is_not_a_find():
    """The screen is the only thing between a genre and a download."""
    agent = FakeAgent([["one"]])
    result = await run_search_loop(
        "fixing bikes",
        target=1,
        llm=agent,
        search=_search_returning({"one": _rows("a")}),
        screen=_screen_by_url({"a": Verdict(looked=False)}),
    )
    assert result.kept == []


async def test_the_right_viewpoint_doing_the_wrong_thing_does_not_count():
    """A helmet cam on a bike ride is egocentric and is not fixing a bike."""
    agent = FakeAgent([["one"]])
    result = await run_search_loop(
        "fixing bikes",
        target=1,
        llm=agent,
        search=_search_returning({"one": _rows("ride")}),
        screen=_screen_by_url({"ride": Verdict(off_task=True)}),
    )
    assert result.kept == []
    assert result.candidates[0].reason == "wrong activity"


async def test_the_agent_is_told_which_phrasing_failed_and_how():
    """'6 rejected' cannot be acted on; naming the phrasing can."""
    agent = FakeAgent([["POV bike repair", "bike restoration"], ["another"]])
    await run_search_loop(
        "fixing bikes",
        target=9,
        llm=agent,
        search=_search_returning(
            {"POV bike repair": _rows("x", "y"), "bike restoration": _rows("z")}
        ),
        screen=_screen_by_url({"z": Verdict()}),
    )
    first = agent.observations[0]
    assert "POV bike repair" in first
    assert "bike restoration" in first
    assert "exocentric" in first


async def test_a_seam_that_stops_yielding_is_called_dry():
    agent = FakeAgent([["one"], ["one"], ["one"], ["one"]])
    result = await run_search_loop(
        "fixing bikes",
        target=9,
        llm=agent,
        search=_search_returning({"one": _rows("a")}),
        screen=_screen_by_url({"a": Verdict()}),
    )
    # The same search returns the same url; after the first round it is not new.
    assert len(result.candidates) == 1
    assert any("nothing new" in o for o in agent.observations)
    assert any(f"{DRY_ROUNDS} rounds running" in o for o in agent.observations)


async def test_a_url_seen_once_is_never_screened_twice():
    agent = FakeAgent([["one"], ["two"]])
    screened: list[str] = []

    async def screen(candidates, task):
        screened.extend(c["url"] for c in candidates)
        return [Verdict(viewpoint="exocentric") for _ in candidates]

    await run_search_loop(
        "fixing bikes",
        target=9,
        llm=agent,
        search=_search_returning({"one": _rows("a", "b"), "two": _rows("b", "c")}),
        screen=screen,
    )
    assert screened == ["a", "b", "c"], "the screen costs money per candidate"


async def test_short_candidates_are_dropped_before_the_screen_spends():
    agent = FakeAgent([["one"]])
    screened: list[str] = []

    async def screen(candidates, task):
        screened.extend(c["url"] for c in candidates)
        return [Verdict() for _ in candidates]

    rows = [
        {"url": "short", "title": "brief", "platform": "youtube", "duration_seconds": 12},
        {"url": "long", "title": "a take", "platform": "youtube", "duration_seconds": 600},
    ]

    async def search(query, wanted):
        return rows

    result = await run_search_loop(
        "fixing bikes",
        target=1,
        min_duration_seconds=300,
        llm=agent,
        search=search,
        screen=screen,
    )
    assert screened == ["long"]
    assert [c.viewpoint for c in result.candidates if c.url == "short"] == ["too short"]


async def test_the_screening_budget_stops_the_hunt():
    agent = FakeAgent([["one"], ["two"], ["three"]])
    result = await run_search_loop(
        "fixing bikes",
        target=99,
        budget_usd=0.003,
        llm=agent,
        search=_search_returning(
            {"one": _rows("a", "b"), "two": _rows("c"), "three": _rows("d")}
        ),
        screen=_screen_by_url({"a": Verdict(), "b": Verdict()}),
    )
    assert "budget" in result.stopped_because


async def test_a_round_with_no_searches_asks_for_some():
    agent = FakeAgent([[]])
    result = await run_search_loop(
        "fixing bikes", target=1, llm=agent, search=_search_returning({}), screen=_screen_by_url({})
    )
    assert result.rounds == 0
    assert any("at least one phrasing" in o for o in agent.observations) or result.candidates == []


@pytest.mark.parametrize("failing", ["one"])
async def test_one_broken_search_does_not_end_the_hunt(failing):
    agent = FakeAgent([["one", "two"]])

    async def search(query, wanted):
        if query == failing:
            raise RuntimeError("the platform said no")
        return _rows("good")

    result = await run_search_loop(
        "fixing bikes",
        target=1,
        llm=agent,
        search=search,
        screen=_screen_by_url({"good": Verdict()}),
    )
    assert len(result.kept) == 1
