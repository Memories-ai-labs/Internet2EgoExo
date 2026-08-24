"""Keep searching until enough footage passes the frames, or the seam is dry.

One search is a guess about vocabulary. `first-person fixing bikes, hands
visible` returns twenty candidates and the frame check keeps none of them —
not because the request was wrong, but because on YouTube "POV" plus "bike"
selects for action-camera *mount reviews* and riding footage. The words that
find a continuous take of two hands working on a bicycle are somewhere else
entirely, and no single phrasing knows where.

`query_rewrite` already widens one request into several angles, and it already
knows the idiom — `handcam`, `no talking`, `raw`, `ASMR`. What it cannot do is
learn: it fires once, blind, and never finds out that twelve of its twenty
candidates came back "static tripod close-ups". The evidence that would have
told it which angle to abandon arrives after it has finished.

So this is that loop closed. Each round the agent proposes searches, the
candidates are screened on their frames before anything is downloaded, and the
agent is told **what the frames said about what its own words returned** —
grouped by reason, with the phrasings that produced them. Then it decides where
to look next. Nothing here prescribes an angle: the observation is evidence, and
choosing the next vocabulary is the agent's job, because a rule I write today is
a rule about YouTube in August.

It stops on the first of:

* **enough** — the target number of candidates have passed the frames;
* **dry** — two consecutive rounds that add nothing new, which is what a seam
  running out actually looks like;
* **the bounds** — rounds, or the money the screening has spent.

Stopping short is reported, never rounded up. A hunt that found three of a
wanted ten says so, along with what it tried, because "the footage does not
exist in this vocabulary" is a finding and quietly returning three is not.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from video_searching_agent.utils.youtube_urls import youtube_video_id

logger = logging.getLogger(__name__)

AGENT_NAME = "prospector"

# Rounds, not searches: one round may carry several phrasings. Past this the
# agent is rephrasing rather than rethinking.
DEFAULT_MAX_ROUNDS = 5

# Two rounds that surface nothing new. One can be a bad phrasing; two in a row
# is the seam, and paying for a third is paying to confirm a negative.
DRY_ROUNDS = 2

# Screening is ~$0.002 a candidate. This is the whole hunt's looking budget.
DEFAULT_BUDGET_USD = 0.60

# More than this in one round and the agent is not choosing, it is spraying.
MAX_QUERIES_PER_ROUND = 4

SYSTEM_PROMPT = """You are looking for video footage to train a model on, and \
you get more than one attempt.

The request is a task. The footage that shows that task is titled by the person \
who recorded it, in their words, not the requester's — so the words that find it \
are usually not the words in the request. A search that returns nothing usable \
is information about vocabulary, not about whether the footage exists.

Each round you propose up to {max_queries} searches. Every candidate they return \
is screened on its actual frames before anything is downloaded, and you are told \
what the frames showed — how many were kept, and for the rest, why, grouped by \
reason and attributed to the phrasing that found them.

Read that. If a phrasing returned twenty results and the frames called them all \
fixed-camera, that phrasing is finding a genre rather than a viewpoint, and \
rewording it slightly will find the same genre again. Change what you are asking \
for, not how politely you ask.

You are looking for {wanted} footage of: {request}
Target: {target} candidates that pass the frames.

Answer only when you have the target, or when you are confident further searches \
would return the same genre again. Then reply with ONLY:
{{"done": true, "found": <how many passed>, "what_worked": "<the phrasings that \
returned usable footage, or empty>", "what_did_not": "<the angles that returned \
the wrong genre, and what genre>"}}"""


@dataclass
class Candidate:
    """One screened candidate and the verdict its frames earned."""

    url: str
    title: str = ""
    platform: str = ""
    duration_seconds: float | None = None
    viewpoint: str = "unknown"
    confidence: float = 0.0
    why: str = ""
    kept: bool = False
    found_by: str = ""
    # What the frames said about the activity: `doing`, `other_kind`,
    # `unclear`, or empty when nothing was seen.
    task_reading: str = ""
    off_task: bool = False

    @property
    def reason(self) -> str:
        """One word for why this did not pass, for grouping in a report."""
        if self.kept:
            return "kept"
        if self.off_task:
            return "wrong activity"
        return self.viewpoint or "unclear"

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "platform": self.platform,
            "duration_seconds": self.duration_seconds,
            "viewpoint": self.viewpoint,
            "confidence": self.confidence,
            "why": self.why,
            "kept": self.kept,
            "found_by": self.found_by,
            "task_reading": self.task_reading,
            "off_task": self.off_task,
        }


@dataclass
class ProspectResult:
    """What the hunt found, and what it cost to find out."""

    request: str = ""
    wanted: str = ""
    target: int = 0
    rounds: int = 0
    searched: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    cost_usd: float = 0.0
    stopped_because: str = ""
    what_worked: str = ""
    what_did_not: str = ""

    @property
    def kept(self) -> list[Candidate]:
        return [c for c in self.candidates if c.kept]

    @property
    def met_target(self) -> bool:
        return len(self.kept) >= self.target

    def as_dict(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "wanted": self.wanted,
            "target": self.target,
            "rounds": self.rounds,
            "searched": self.searched,
            "found": len(self.kept),
            "screened": len(self.candidates),
            "met_target": self.met_target,
            "cost_usd": round(self.cost_usd, 4),
            "stopped_because": self.stopped_because,
            "what_worked": self.what_worked,
            "what_did_not": self.what_did_not,
            "candidates": [c.as_dict() for c in self.kept],
            "rejected": [c.as_dict() for c in self.candidates if not c.kept],
        }


def _observation(round_no: int, fresh: list[Candidate], total_kept: int, target: int) -> str:
    """What one round returned, said so the agent can act on it.

    Grouped by reason and attributed to the phrasing, because "6 rejected" tells
    an agent nothing it can change, and "everything `POV bike repair` returned
    was a fixed camera" tells it to abandon that angle.
    """
    if not fresh:
        return (
            f"Round {round_no}: nothing new — every result was one you have already "
            f"seen. Still {total_kept} of {target}."
        )

    kept = [c for c in fresh if c.kept]
    lines = [
        f"Round {round_no}: {len(fresh)} new candidates, {len(kept)} passed the frames. "
        f"{total_kept} of {target} so far."
    ]
    if kept:
        lines.append("Passed:")
        for c in kept[:6]:
            length = f"{c.duration_seconds:.0f}s" if c.duration_seconds else "length unknown"
            lines.append(f'  - [{c.found_by}] {length} — "{c.title[:70]}"')

    rejected = [c for c in fresh if not c.kept]
    if rejected:
        by_query: dict[str, Counter[str]] = {}
        for c in rejected:
            by_query.setdefault(c.found_by, Counter())[c.reason] += 1
        lines.append("Rejected, by the phrasing that found them:")
        for phrasing, counts in by_query.items():
            mix = ", ".join(f"{n} {name}" for name, n in counts.most_common())
            lines.append(f"  - [{phrasing}] {mix}")
        # One verbatim reason per round: the model's own words about the frames
        # are what tell the agent which genre it landed in.
        sample = next((c for c in rejected if c.why), None)
        if sample is not None:
            lines.append(f'  the frames said, of one: "{sample.why[:150]}"')
    return "\n".join(lines)


async def prospect(
    request: str,
    *,
    wanted: str = "egocentric",
    target: int = 5,
    min_duration_seconds: float | None = None,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    budget_usd: float = DEFAULT_BUDGET_USD,
    llm: Any = None,
    search: Any = None,
    screen: Any = None,
    on_round: Any = None,
) -> ProspectResult:
    """Search, screen, learn from the rejections, search again.

    Args:
        request: The footage wanted, in the words it arrived in.
        wanted: `egocentric` or `exocentric` — what the frames have to show.
        target: How many screened-and-passed candidates to stop at.
        min_duration_seconds: Drop shorter candidates before screening them.
            Free, and it stops the budget going on ten-second clips.
        max_rounds: Rounds of search before giving up.
        budget_usd: What the screening may spend across the whole hunt.
        llm: Model client. Resolved when omitted.
        search: `async (query: str) -> list[dict]`, for tests. The real one
            runs the unified video search.
        screen: `async (list[dict], task) -> list[SightVerdict]`, for tests.
        on_round: Optional `async (round_no, observation, result)` progress hook.

    Returns:
        A ProspectResult. `met_target` false with `stopped_because` set is the
        honest outcome of a seam that is dry, and is not an error.
    """
    from video_searching_agent.agent.react_loop import Tool, ToolResult, run_loop
    from video_searching_agent.api.llm import get_llm_client

    result = ProspectResult(request=request, wanted=wanted, target=target)
    search = search or _default_search
    screen = screen or _default_screen

    seen_urls: set[str] = set()
    dry = 0
    rounds = 0

    async def run_searches(arguments: dict[str, Any]) -> ToolResult:
        nonlocal dry, rounds
        # Enforced, not requested. Telling the agent "that is the target,
        # answer now" is a suggestion, and a suggestion costs a screening round
        # every time it is ignored. The bounds in this repo are hard ones.
        if len(result.kept) >= target:
            return ToolResult(
                observation=(
                    f"the target of {target} is already met with {len(result.kept)} "
                    "candidates; no further searches will run. Answer now."
                )
            )

        raw = arguments.get("queries")
        queries = [str(q).strip() for q in raw if str(q).strip()] if isinstance(raw, list) else []
        if not queries:
            return ToolResult(observation="no searches given; propose at least one phrasing")
        queries = queries[:MAX_QUERIES_PER_ROUND]
        rounds += 1
        result.rounds = rounds
        result.searched.extend(queries)

        found: list[Candidate] = []
        for phrasing in queries:
            try:
                rows = await search(phrasing, wanted)
            except Exception as exc:  # noqa: BLE001 - one bad search, not the hunt
                logger.info("search %r failed: %s", phrasing, exc)
                continue
            for row in rows:
                url = str(row.get("url") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                duration = row.get("duration_seconds")
                if (
                    min_duration_seconds
                    and isinstance(duration, int | float)
                    and duration < min_duration_seconds
                ):
                    # Too short to train on, and free to reject. Recorded so the
                    # agent learns that an angle finds short-form, which is a
                    # different problem from finding the wrong viewpoint.
                    found.append(
                        Candidate(
                            url=url,
                            title=str(row.get("title") or ""),
                            platform=str(row.get("platform") or ""),
                            duration_seconds=float(duration),
                            viewpoint="too short",
                            why=f"{duration:.0f}s, under the {min_duration_seconds:.0f}s floor",
                            found_by=phrasing,
                        )
                    )
                    continue
                found.append(
                    Candidate(
                        url=url,
                        title=str(row.get("title") or ""),
                        platform=str(row.get("platform") or ""),
                        duration_seconds=float(duration)
                        if isinstance(duration, int | float)
                        else None,
                        found_by=phrasing,
                    )
                )

        to_screen = [c for c in found if c.viewpoint != "too short"]
        if to_screen and result.cost_usd < budget_usd:
            # `video_id` as well as the url: the frames tier reads YouTube's
            # storyboard stills, which are addressed by id. Passing the url
            # alone is how a screen comes back "unknown" for everything at a
            # cost of zero — it never looked.
            verdicts = await screen(
                [
                    {
                        "video_id": youtube_video_id(c.url),
                        "url": c.url,
                        "duration_seconds": c.duration_seconds,
                    }
                    for c in to_screen
                ],
                request,
            )
            for candidate, verdict in zip(to_screen, verdicts, strict=False):
                candidate.confidence = float(getattr(verdict, "confidence", 0.0) or 0.0)
                candidate.why = str(getattr(verdict, "why", "") or "")
                seen_value = getattr(verdict, "viewpoint", None)
                candidate.viewpoint = str(getattr(seen_value, "value", seen_value) or "unknown")
                result.cost_usd += float(getattr(verdict, "cost_usd", 0.0) or 0.0)
                # The screen answers two questions and both matter here. A
                # helmet cam on a bike *ride* is egocentric and is not footage
                # of fixing a bike; keeping it because the viewpoint matched is
                # how a hunt reports fifteen finds and hands over five.
                #
                # `misses_task` is deliberately narrow — it fires only on
                # "this is a different kind of video", never on "the task is
                # not in these three stills" — so this tightens the hunt
                # without throwing away footage whose task is simply elsewhere
                # in the hour.
                off_task = bool(getattr(verdict, "misses_task", lambda: False)())
                candidate.off_task = off_task
                candidate.task_reading = str(getattr(verdict, "task_reading", "") or "")
                candidate.kept = (
                    bool(getattr(verdict, "looked", False))
                    and candidate.viewpoint == wanted
                    and not off_task
                )
        elif to_screen:
            return ToolResult(
                observation=(
                    f"the screening budget is spent (${result.cost_usd:.2f}); answer with "
                    "what you have and say what you could not check"
                )
            )

        result.candidates.extend(found)
        kept_now = len(result.kept)
        dry = dry + 1 if not found else 0
        observation = _observation(rounds, found, kept_now, target)

        if on_round is not None:
            await on_round(rounds, observation, result)
        if kept_now >= target:
            observation += "\n\nThat is the target. Answer now."
        elif dry >= DRY_ROUNDS:
            observation += (
                f"\n\n{dry} rounds running with nothing new. Answer now and say what "
                "the angles you tried returned instead."
            )
        return ToolResult(observation=observation)

    tools = [
        Tool(
            name="search",
            description=(
                "run these phrasings and screen everything they return on its frames. "
                "You get back what passed and, for what did not, what the frames showed "
                f"— attributed to the phrasing. Up to {MAX_QUERIES_PER_ROUND} per round"
            ),
            arguments='{"queries": ["<phrasing>", "..."]}',
            run=run_searches,
        )
    ]

    outcome = await run_loop(
        llm or get_llm_client(),
        SYSTEM_PROMPT.format(
            max_queries=MAX_QUERIES_PER_ROUND, wanted=wanted, request=request, target=target
        ),
        f"Find {target} pieces of {wanted} footage of: {request}",
        tools,
        agent=AGENT_NAME,
        max_steps=max_rounds + 1,  # the answer turn is not a round
        answer_keys=("done", "found"),
    )

    if outcome.answer is not None:
        result.what_worked = str(outcome.answer.get("what_worked") or "")
        result.what_did_not = str(outcome.answer.get("what_did_not") or "")
        result.stopped_because = "the agent stopped" if not result.met_target else "target met"
    else:
        result.stopped_because = outcome.stopped_because or "no answer"
    if result.cost_usd >= budget_usd:
        result.stopped_because = f"screening budget spent (${result.cost_usd:.2f})"
    return result


async def _default_search(query: str, wanted: str) -> list[dict[str, Any]]:
    """The unified video search, as a plain list of candidate rows."""
    from video_searching_agent.tools.video_search import VideoSearchTool

    outcome = await VideoSearchTool().execute(query=query, viewpoint=wanted, max_results=20)
    data = outcome.data if isinstance(outcome.data, dict) else {}
    rows = data.get("videos") or []
    return [row for row in rows if isinstance(row, dict)]


async def _default_screen(candidates: list[dict[str, Any]], task: str) -> list[Any]:
    """The pre-download frame check, at about $0.002 a candidate."""
    from video_searching_agent.api.llm import get_llm_client
    from video_searching_agent.curation.frame_viewpoint import check_many

    return await check_many(get_llm_client(), candidates, task=task)


def _print(result: ProspectResult) -> None:
    print(
        f"{len(result.kept)} of {result.target} found in {result.rounds} round(s), "
        f"{len(result.candidates)} screened, ${result.cost_usd:.3f}"
    )
    print(f"  stopped: {result.stopped_because}")
    if result.what_worked:
        print(f"  worked: {result.what_worked}")
    if result.what_did_not:
        print(f"  did not: {result.what_did_not}")
    for candidate in result.kept:
        length = f"{candidate.duration_seconds:.0f}s" if candidate.duration_seconds else "—"
        print(f"  + {length:>7}  {candidate.url}")
        print(f'            "{candidate.title[:66]}"')


def main() -> int:
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("request", help="the footage wanted, in your own words")
    parser.add_argument("--viewpoint", default="egocentric", choices=["egocentric", "exocentric"])
    parser.add_argument("--target", type=int, default=5, help="candidates that must pass")
    parser.add_argument("--min-duration", type=float, default=None, help="seconds")
    parser.add_argument("--rounds", type=int, default=DEFAULT_MAX_ROUNDS)
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET_USD, help="USD")
    parser.add_argument("--json", action="store_true", help="print the whole result")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    result = asyncio.run(
        prospect(
            args.request,
            wanted=args.viewpoint,
            target=args.target,
            min_duration_seconds=args.min_duration,
            max_rounds=args.rounds,
            budget_usd=args.budget,
        )
    )
    if args.json:
        print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
    else:
        _print(result)
    return 0 if result.kept else 1


if __name__ == "__main__":
    raise SystemExit(main())
