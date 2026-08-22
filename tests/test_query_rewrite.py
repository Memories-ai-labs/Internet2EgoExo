"""Searching the words uploaders use, not the words the requester used.

A request describes a task. Sent to YouTube verbatim it selects for exactly what
those words mean — beginner guides, appliance reviews, a presenter talking to a
tripod — which is why several task queries came back with nothing accepted. Not
because the gates were harsh: the candidates were never the right kind of video.

Measured on real YouTube results, judged by their frames: a plain search for
"packing a suitcase, folding and placing clothes into luggage" returned 0 of 6
first-person videos; the rewritten searches returned 5 of 11.
"""

from __future__ import annotations

from typing import Any

import pytest

from video_searching_agent.curation.query_rewrite import (
    core_subject,
    rewrite_query,
    template_queries,
)
from video_searching_agent.curation.viewpoint import Viewpoint


class _Model:
    def __init__(self, reply: str, cost: float = 0.001) -> None:
        self.reply = reply
        self.cost = cost
        self.prompts: list[Any] = []

    def new_conversation(self, text: str) -> list[dict[str, Any]]:
        return [{"role": "user", "content": text}]

    async def create_message_async(self, messages, system=None, **_):
        self.prompts.append({"system": system, "user": messages[0]["content"]})
        return {"text": self.reply}

    def get_text_response(self, response):
        return response["text"]

    def get_cost_usd(self, response):
        return self.cost


class _Dead(_Model):
    async def create_message_async(self, messages, system=None, **_):
        raise RuntimeError("429 rate limited")


def test_the_asking_is_stripped_out_of_the_subject():
    """ "someone doing the laundry" is about wanting it, not about the footage."""

    assert core_subject("someone doing the laundry, loading a machine") == (
        "doing the laundry, loading a machine"
    )
    assert core_subject("find footage of chopping onions") == "chopping onions"
    assert core_subject("first-person cooking with hands visible") == "first-person cooking"


def test_a_query_that_is_all_asking_keeps_something():
    """Stripping everything would search for nothing."""

    assert core_subject("show me videos of people") != ""


def test_the_templates_cover_distinct_angles():
    queries = template_queries("doing the laundry", Viewpoint.EGOCENTRIC)
    angles = {query.angle for query in queries}
    assert {"pov", "raw", "plain"} <= angles
    # The plain search stays in: idiom is a filter, and a filter can exclude the
    # one good recording that never used the word.
    assert any(query.angle == "plain" for query in queries)


def test_the_exocentric_idiom_is_used_when_that_is_what_was_asked():
    queries = template_queries("assembling furniture", Viewpoint.EXOCENTRIC)
    text = " ".join(query.text.lower() for query in queries)
    assert "fixed camera" in text or "static camera" in text
    assert "pov" not in text


def test_every_template_keeps_the_subject():
    queries = template_queries("servicing a bike derailleur", Viewpoint.EGOCENTRIC)
    assert all("derailleur" in query.text.lower() for query in queries)


@pytest.mark.asyncio
async def test_no_model_still_produces_searches():
    """The templates are the floor, and they work with no model at all."""

    rewrite = await rewrite_query("doing the laundry", viewpoint=Viewpoint.EGOCENTRIC)
    assert rewrite.queries
    assert all(query.source == "template" for query in rewrite.queries)
    assert rewrite.cost_usd == 0.0


@pytest.mark.asyncio
async def test_model_suggestions_come_first_with_templates_behind_them():
    model = _Model(
        '{"queries": [{"text": "POV wash and fold routine", "angle": "pov"}, '
        '{"text": "laundry handcam no talking", "angle": "raw"}]}'
    )
    rewrite = await rewrite_query("doing the laundry", viewpoint=Viewpoint.EGOCENTRIC, llm=model)
    assert rewrite.queries[0].source == "model"
    assert rewrite.queries[0].text == "POV wash and fold routine"
    assert any(query.source == "template" for query in rewrite.queries)
    assert rewrite.cost_usd == pytest.approx(0.001)


@pytest.mark.asyncio
async def test_a_domain_synonym_is_kept_even_though_it_shares_no_word():
    """The first version of this filtered rewrites by word overlap with the
    request, and dropped `POV wash and fold routine` for a laundry request —
    the single best rewrite of it, sharing not one word. A word-overlap test
    cannot tell a domain synonym from a query that wandered off, and the two
    mistakes do not cost the same: a wandering query wastes one search whose
    results the gates reject, while dropping the synonym loses the footage."""

    model = _Model('{"queries": [{"text": "POV wash and fold routine", "angle": "domain"}]}')
    rewrite = await rewrite_query("doing the laundry", viewpoint=Viewpoint.EGOCENTRIC, llm=model)
    texts = [query.text for query in rewrite.queries if query.source == "model"]
    assert texts == ["POV wash and fold routine"]


@pytest.mark.asyncio
async def test_a_dead_model_falls_back_to_the_templates():
    rewrite = await rewrite_query("doing the laundry", llm=_Dead(""))
    assert rewrite.queries
    assert rewrite.error and "429" in rewrite.error
    assert all(query.source == "template" for query in rewrite.queries)


@pytest.mark.asyncio
async def test_an_unreadable_reply_falls_back_to_the_templates():
    rewrite = await rewrite_query("doing the laundry", llm=_Model("I'd rather not"))
    assert rewrite.queries
    assert all(query.source == "template" for query in rewrite.queries)
    assert rewrite.error


@pytest.mark.asyncio
async def test_absurdly_long_suggestions_are_dropped():
    model = _Model('{"queries": [{"text": "laundry ' + "x" * 300 + '"}]}')
    rewrite = await rewrite_query("doing the laundry", llm=model)
    assert all(query.source == "template" for query in rewrite.queries)


@pytest.mark.asyncio
async def test_the_prompt_says_to_keep_the_subject_and_vary_the_angle():
    model = _Model('{"queries": [{"text": "laundry POV"}]}')
    await rewrite_query("doing the laundry", viewpoint=Viewpoint.EGOCENTRIC, llm=model)
    system = model.prompts[0]["system"]
    assert "Keep the subject of the request in every query" in system
    assert "Vary the angle" in system
    # Filters are applied elsewhere; a rewrite that adds them narrows twice.
    assert "Do not add a licence, duration or date filter" in system
