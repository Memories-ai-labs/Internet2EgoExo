"""Search the words uploaders use, not the words the requester used.

A training-data request arrives as a task: *someone doing the laundry, loading a
machine and folding clothes*. Sent to YouTube verbatim, that returns exactly what
those words select for — beginner guides, appliance reviews, a presenter talking
to a tripod. Which is why several task queries came back with nothing accepted:
not because the gates are harsh, but because the candidates were never the right
kind of video.

The footage that *is* wanted exists, and it is titled differently, because the
people who upload it are describing a recording rather than a task. They write
`POV Wash and Fold With Me`, `handcam`, `first person`, `no talking`, `raw`,
`full build`, `ASMR`, `GoPro`. None of that vocabulary appears in the request,
and all of it is what separates a continuous take of two hands working from a
lesson about the same subject.

So a request is rewritten into several searches along different angles. Several,
because no single phrasing covers the space: the POV-idiom search finds the
enthusiast recordings, the equipment search finds the ones named after the
camera, and a plain search still catches what the idiom misses. Ranking then
sorts out what came back — the rewrite widens the net, it does not decide.

The deterministic templates below are the floor, and they work with no model at
all. A model, when there is one, adds the domain vocabulary no template can know
("mise en place", "derailleur", "flat-pack"), and its suggestions are merged
rather than trusted: a rewrite that drops the subject of the request is worse
than no rewrite.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.curation.viewpoint import Viewpoint

logger = logging.getLogger(__name__)

# The idiom uploaders use for worn-camera footage, roughly in order of how
# reliably it selects for a continuous take of hands working.
EGOCENTRIC_IDIOM = (
    "POV",
    "first person",
    "handcam",
    "GoPro",
    "head mounted",
    "chest mounted",
)

# The idiom for a fixed camera watching someone work.
EXOCENTRIC_IDIOM = (
    "fixed camera",
    "static camera",
    "overhead camera",
    "tripod",
    "multi view",
)

# Words that select for an unedited recording over a produced lesson. These are
# the highest-value terms in the whole module: "no talking" alone removes most
# of what makes a tutorial useless as manipulation data.
RAW_FOOTAGE_IDIOM = (
    "no talking",
    "no commentary",
    "real time",
    "full process",
    "uncut",
    "raw footage",
)

# Words in the *request* that are about the asking rather than the footage, and
# would only dilute a search.
# Longest alternative first: "with hands visible" matched on "with hands" would
# leave a stray "visible" in the search.
_REQUEST_NOISE = re.compile(
    r"\b(?:with hands visible|hands visible|with hands|someone|a person|people|"
    r"find|show me|footage of|videos? of|clips? of|i need|looking for)\b",
    re.IGNORECASE,
)

REWRITE_PROMPT = """You turn a training-data request into search queries that
find the actual footage.

The request describes a task. The footage that shows that task well is titled by
whoever recorded it, and they name a recording, not a task: "POV Wash and Fold
With Me", "handcam soldering no talking", "GoPro bike service full build". The
request's own words select for tutorials and reviews instead.

Write {count} search queries for {platform}. Rules:

- Keep the subject of the request in every query. A query that drops it finds
  the wrong footage confidently.
- Vary the angle: one using point-of-view idiom, one naming the equipment
  (GoPro, Insta360, head-mounted), one selecting for an unedited take (no
  talking, real time, full process), one using the domain's own vocabulary for
  the task.
- Use the vocabulary a practitioner would: the specific tool, part or step, not
  a generic description.
- Short. Search engines are not sentences.
- Do not add a licence, duration or date filter; those are applied separately.

Reply with ONLY this JSON:
{{"queries": [{{"text": "...", "angle": "pov|equipment|raw|domain"}}]}}"""


@dataclass
class SearchQuery:
    """One rewritten search, and why it exists."""

    text: str
    angle: str = "plain"
    source: str = "template"

    def as_dict(self) -> dict[str, Any]:
        return {"text": self.text, "angle": self.angle, "source": self.source}


@dataclass
class Rewrite:
    """What a request was turned into."""

    original: str
    queries: list[SearchQuery] = field(default_factory=list)
    cost_usd: float = 0.0
    error: str | None = None

    @property
    def texts(self) -> list[str]:
        return [query.text for query in self.queries]

    def as_dict(self) -> dict[str, Any]:
        return {
            "original": self.original,
            "queries": [query.as_dict() for query in self.queries],
            "cost_usd": round(self.cost_usd, 5),
            "error": self.error,
        }


def core_subject(query: str) -> str:
    """The request with the asking stripped out.

    "someone doing the laundry, loading a machine and folding clothes" becomes
    "doing the laundry, loading a machine and folding clothes" — what the footage
    has to show, without the words that describe wanting it.
    """
    cleaned = _REQUEST_NOISE.sub(" ", query)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;:")
    return cleaned or query.strip()


def template_queries(
    query: str,
    viewpoint: Viewpoint | None = None,
    limit: int = 4,
) -> list[SearchQuery]:
    """Rewrites that need no model, and are the floor for the ones that do."""

    subject = core_subject(query)
    short = " ".join(subject.split()[:8])
    idiom = EGOCENTRIC_IDIOM if viewpoint is not Viewpoint.EXOCENTRIC else EXOCENTRIC_IDIOM

    candidates = [
        SearchQuery(f"{idiom[0]} {short}", angle="pov"),
        SearchQuery(f"{short} {idiom[2 if len(idiom) > 2 else 1]}", angle="equipment"),
        SearchQuery(f"{short} {RAW_FOOTAGE_IDIOM[0]}", angle="raw"),
        # The plain search stays in: idiom is a filter, and a filter can exclude
        # the one good recording that never used the word.
        SearchQuery(short, angle="plain"),
    ]
    seen: set[str] = set()
    out: list[SearchQuery] = []
    for candidate in candidates:
        key = candidate.text.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(candidate)
    return out[:limit]


async def rewrite_query(
    query: str,
    *,
    viewpoint: Viewpoint | None = None,
    platform: str = "YouTube",
    count: int = 4,
    llm: Any | None = None,
) -> Rewrite:
    """Turn a request into several footage-shaped searches.

    Args:
        query: The request, in the words it arrived in.
        viewpoint: Which idiom to reach for.
        platform: Named in the prompt, because the idiom differs by platform.
        count: How many queries to aim for.
        llm: A model to add domain vocabulary. None uses templates alone.

    Returns:
        A Rewrite. The templates are always present; a model's suggestions are
        merged in front of them when they keep the subject, and dropped when
        they do not.
    """
    result = Rewrite(original=query)
    templates = template_queries(query, viewpoint, limit=count)
    if llm is None:
        result.queries = templates
        return result

    prompt = REWRITE_PROMPT.format(count=count, platform=platform)
    try:
        messages = llm.new_conversation(
            f"Request: {query}\n"
            + (f"Wanted viewpoint: {viewpoint.value}\n" if viewpoint else "")
            + "Write the queries."
        )
        response = await llm.create_message_async(messages, system=prompt, max_tokens=600)
    except Exception as exc:  # noqa: BLE001 - templates are a working answer
        result.error = str(exc)[:200]
        result.queries = templates
        return result

    if hasattr(llm, "get_cost_usd"):
        try:
            result.cost_usd = float(llm.get_cost_usd(response) or 0.0)
        except Exception:  # noqa: BLE001
            result.cost_usd = 0.0

    text = ""
    if hasattr(llm, "get_text_response"):
        text = llm.get_text_response(response) or ""
    suggestions = _read_suggestions(text, query)
    if not suggestions:
        result.error = result.error or "the model returned no usable queries"
        result.queries = templates
        return result

    # Model suggestions first, templates behind them as the guaranteed floor.
    seen = {query.text.lower() for query in suggestions}
    result.queries = suggestions + [t for t in templates if t.text.lower() not in seen]
    return result


def _read_suggestions(text: str, original: str) -> list[SearchQuery]:
    """Parse the model's queries, keeping only the ones that kept the subject."""

    from video_searching_agent.agent.react import parse_json_object

    try:
        parsed = parse_json_object(text)
    except Exception:  # noqa: BLE001
        return []

    raw = parsed.get("queries")
    if not isinstance(raw, list):
        return []

    # There is deliberately no lexical "did it keep the subject" filter here.
    # The first version had one, and it dropped `POV wash and fold routine` for
    # a laundry request — which is the single best rewrite of that request and
    # shares not one word with it. A word-overlap test cannot tell a domain
    # synonym from a query that wandered off, and the cost of the two mistakes
    # is not symmetric: a wandering query wastes one search whose results the
    # frame check and the gates then reject, while dropping the synonym loses
    # the footage entirely. Relevance is decided downstream, by ranking against
    # what came back, where it can be decided on evidence.
    out: list[SearchQuery] = []
    for entry in raw:
        if isinstance(entry, str):
            entry = {"text": entry}
        if not isinstance(entry, dict):
            continue
        candidate = str(entry.get("text") or "").strip()
        # Length is a real signal: a search engine is not a sentence, and a
        # 300-character "query" is the model having written prose.
        if not candidate or len(candidate) > 160:
            logger.info("dropped an unusable rewrite: %r", candidate[:60])
            continue
        out.append(
            SearchQuery(
                text=candidate,
                angle=str(entry.get("angle") or "domain"),
                source="model",
            )
        )
    return out
