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


# --- the head phrase --------------------------------------------------------
#
# A fixed word count cuts through a clause. "packing a suitcase, folding and
# placing clothes into luggage" truncated to eight words ends on "into", and
# searching that returned "IMPOSSIBLE 💀🍷" and a Toca Boca clip. Every template
# query for every request was damaged this way; it only surfaced when the model
# reply failed to parse and the templates were the whole answer.


@pytest.mark.parametrize(
    ("request_text", "head"),
    [
        # The first clause names the task; the rest elaborates.
        (
            "packing a suitcase, folding and placing clothes into luggage",
            "packing a suitcase",
        ),
        ("fixing a bike, hands on the chain and brakes", "fixing a bike"),
        # One clause, so the word cap applies — and must not leave "and an".
        (
            "assembling flat-pack furniture with a screwdriver and an allen key",
            "assembling flat-pack furniture with a screwdriver",
        ),
        # A leading category label is not a task. Searching "kitchen tasks"
        # finds listicles.
        ("kitchen tasks - chopping, stirring, washing up", "chopping"),
        # Nothing but a category: there is no better clause to fall back to,
        # so it stands rather than becoming empty.
        ("household chores", "household chores"),
        ("soldering", "soldering"),
    ],
)
def test_the_head_phrase_ends_on_a_real_word(request_text: str, head: str) -> None:
    from video_searching_agent.curation.query_rewrite import core_subject, head_phrase

    assert head_phrase(core_subject(request_text)) == head


def test_no_template_query_ends_on_a_function_word() -> None:
    """The property that actually matters, over every request we run."""

    from video_searching_agent.curation.query_rewrite import (
        _DANGLING,
        template_queries,
    )
    from video_searching_agent.curation.viewpoint import Viewpoint

    requests = [
        "packing a suitcase, folding and placing clothes into luggage",
        "someone doing the laundry, loading a machine and folding clothes",
        "assembling flat-pack furniture with a screwdriver and an allen key",
        "kitchen tasks - chopping, stirring, washing up",
        "fixing a bike, hands on the chain and brakes",
        "welding a steel frame with a MIG torch and a grinder",
    ]
    for request_text in requests:
        for query in template_queries(request_text, Viewpoint.EGOCENTRIC):
            last = query.text.split()[-1].lower()
            assert last not in _DANGLING, f"{request_text!r} -> {query.text!r}"


@pytest.mark.asyncio
async def test_an_unparseable_reply_is_asked_once_more() -> None:
    """The templates are a floor, not an equal, so one bad reply is not the end."""

    from video_searching_agent.curation.query_rewrite import rewrite_query
    from video_searching_agent.curation.viewpoint import Viewpoint

    replies = [
        "Sure! Here are some queries you could try:",  # prose, unparseable
        '{"queries": [{"text": "POV ranger roll packing cubes", "angle": "domain"}]}',
    ]

    class Flaky:
        def __init__(self) -> None:
            self.calls = 0

        def new_conversation(self, text: str) -> list[dict]:
            return [{"role": "user", "content": text}]

        async def create_message_async(self, messages, **_):
            self.calls += 1
            return {"text": replies[min(self.calls - 1, len(replies) - 1)]}

        def get_text_response(self, response) -> str:
            return response["text"]

        def get_cost_usd(self, response) -> float:
            return 0.0005

    llm = Flaky()
    rewrite = await rewrite_query("packing a suitcase", viewpoint=Viewpoint.EGOCENTRIC, llm=llm)

    assert llm.calls == 2
    assert rewrite.error is None
    assert "POV ranger roll packing cubes" in rewrite.texts
    # Both calls are paid for, and both are counted.
    assert rewrite.cost_usd == pytest.approx(0.001)


@pytest.mark.asyncio
async def test_two_unparseable_replies_fall_back_rather_than_loop() -> None:
    from video_searching_agent.curation.query_rewrite import rewrite_query
    from video_searching_agent.curation.viewpoint import Viewpoint

    class Prose:
        def __init__(self) -> None:
            self.calls = 0

        def new_conversation(self, text: str) -> list[dict]:
            return [{"role": "user", "content": text}]

        async def create_message_async(self, messages, **_):
            self.calls += 1
            return {"text": "I'd be happy to help you search for that!"}

        def get_text_response(self, response) -> str:
            return response["text"]

    llm = Prose()
    rewrite = await rewrite_query("packing a suitcase", viewpoint=Viewpoint.EGOCENTRIC, llm=llm)

    assert llm.calls == 2, "one retry, not a loop"
    assert rewrite.error == "the model returned no usable queries"
    assert rewrite.texts, "the templates still answer"
    assert all(q.source == "template" for q in rewrite.queries)
