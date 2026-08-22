"""Driving the deployment, one eval query at a time.

The pipeline is reached over HTTP rather than imported, on purpose: what is
being measured is a deployment — its settings, its keys, its rate limits — and
importing the code would measure this checkout instead. Three streams per
query, in the order the product uses them:

    /queries/stream   search: candidates, and the run's own discovery spend
    /collect/stream   download, upload, index, clean, annotate — one URL per call
    /curate/stream    clean, annotate and grade the worklist

One request per URL in the collect step, because a serverless function has 300
seconds and a long video spends most of that being downloaded and indexed; two
in one request means the stream is cut before the summary arrives.

Everything a clip cost is recorded in **billable units** — video-minutes, moment
calls, derived reads — rather than dollars, so the rates stay in one place
(`curation.cost`) and a run recorded today can be re-costed when the Datalake's
price list changes.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from video_searching_agent.evaluation.metrics import ClipOutcome, QueryOutcome, was_blocked

# The cleaning agent reads a clip's caption, transcription and summary back out
# of the Datalake before it grades anything. Three derived reads, every clip,
# every time — a fixed property of the code path rather than an estimate, which
# is why it is counted rather than left unmeasured.
DERIVED_READS_PER_CLIP = 3

NETWORK_ERRORS = (urllib.error.URLError, TimeoutError, OSError)



def sse(
    url: str, body: dict[str, Any], timeout: float = 600.0
) -> list[tuple[str, dict[str, Any]]]:
    """Read a whole SSE stream into (event, payload) pairs."""
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    events: list[tuple[str, dict[str, Any]]] = []
    event: str | None = None
    with urllib.request.urlopen(request, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                try:
                    events.append((event or "", json.loads(line[5:].strip())))
                except json.JSONDecodeError:
                    continue
    return events


def final(
    events: list[tuple[str, dict[str, Any]]], name: str = "complete"
) -> dict[str, Any]:
    """The last payload of a named event, or an empty dict."""
    return next((payload for event, payload in reversed(events) if event == name), {})


def health(deployment: str, timeout: float = 30.0) -> dict[str, Any]:
    """What the deployment says about itself.

    Recorded with every snapshot because the two settings that most change
    yield and cost — the model, and how hard it looks before downloading — can
    change without a commit. A step in the trend with no commit behind it is
    otherwise unattributable.
    """
    try:
        with urllib.request.urlopen(f"{deployment}/api/v1/health", timeout=timeout) as response:
            payload = json.load(response)
    except (*NETWORK_ERRORS, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        key: payload.get(key)
        for key in ("version", "model", "viewpoint_check", "demo_mode", "max_collect_urls")
        if payload.get(key) is not None
    }


def clip_outcome(query_id: str, clip: dict[str, Any]) -> ClipOutcome:
    """Read one curated clip into the record, in billable units."""
    cleaning = clip.get("cleaning") or {}
    annotation = clip.get("annotation") or {}
    anchors = cleaning.get("segments") or []
    labels = annotation.get("annotations") or []
    duration = int(clip.get("duration_seconds") or 0)
    spans_read = int(annotation.get("spans_considered") or 0)

    return ClipOutcome(
        query_id=query_id,
        video_id=str(clip.get("video_id") or ""),
        grade=str(clip.get("grade") or "D"),
        score=int(clip.get("score") or 0),
        accepted=bool(clip.get("accepted")),
        annotation_level=str(clip.get("annotation_level") or "L0"),
        duration_seconds=duration,
        usable_seconds=int(clip.get("usable_seconds") or 0),
        idle_seconds=int(clip.get("idle_seconds") or 0),
        action_anchors=sum(1 for a in anchors if a.get("hier_level") == "action"),
        total_anchors=len(anchors),
        annotations=len(labels),
        blocking_failures=list(clip.get("blocking_failures") or []),
        indexed_minutes=duration / 60,
        # One moment search per video, then one read per span it shortlisted.
        moment_search_calls=1 if annotation else 0,
        moment_read_calls=spans_read,
        derived_reads=DERIVED_READS_PER_CLIP,
        look_usd=float(annotation.get("look_cost_usd") or 0.0),
    )


def _nothing_to_collect(outcome: QueryOutcome) -> str:
    """Why a query produced no URLs, told apart from why it might have.

    "Found nothing" and "found eighteen videos and screened every one of them"
    are opposite findings — the first is about the search, the second is about
    the web — and both used to arrive as `0 candidates`.
    """
    if not outcome.screened_out:
        return "search found nothing"
    top = ", ".join(
        f"{reason} ×{count}"
        for reason, count in sorted(outcome.screen_reasons.items(), key=lambda kv: -kv[1])[:2]
    )
    return f"{outcome.found} found, all screened out ({top})"


def run_query(
    case: dict[str, Any],
    *,
    deployment: str,
    per_query: int = 2,
    dry_run: bool = False,
    viewpoint: str | None = "egocentric",
) -> QueryOutcome:
    """Search, collect and curate one eval query."""
    outcome = QueryOutcome(
        query_id=str(case["id"]),
        query=str(case["query"]),
        rdt_id=str(case.get("rdt_id") or ""),
        task_family=str(case.get("task_family") or ""),
        difficulty=str(case.get("difficulty") or ""),
    )
    started = time.time()

    # ---- 1. search ------------------------------------------------------
    try:
        events = sse(
            f"{deployment}/api/v1/queries/stream",
            {"query": case["query"], "viewpoint": viewpoint},
            timeout=300,
        )
    except NETWORK_ERRORS as exc:
        outcome.error = f"search failed: {exc}"
        outcome.seconds = time.time() - started
        return outcome

    manifest = final(events).get("dataset") or {}
    clips = manifest.get("clips") or []
    outcome.candidates = len(clips)
    # What the search found before the pre-download screen, and why the screen
    # dropped what it dropped. Reported because "0 candidates" was being used to
    # mean two opposite things: the search could not answer the query, and the
    # search answered it with eighteen tripod-shot videos.
    outcome.screened_out = int(manifest.get("excluded_clips") or 0)
    outcome.screen_reasons = dict(manifest.get("exclusion_reasons") or {})
    outcome.found = outcome.candidates + outcome.screened_out
    # The search reports its own spend — model tokens plus per-call search fees.
    outcome.discovery_usd = float((manifest.get("cost") or {}).get("discovery_usd") or 0.0)

    urls = [clip["url"] for clip in clips if clip.get("url")][:per_query]
    # A dry run attempted nothing, and saying otherwise would report a 0% index
    # rate against candidates that were never collected.
    outcome.dry_run = dry_run
    outcome.attempted = 0 if dry_run else len(urls)
    if dry_run or not urls:
        if not urls:
            outcome.error = _nothing_to_collect(outcome)
        outcome.seconds = time.time() - started
        return outcome

    # ---- 2. collect, one URL per request --------------------------------
    indexed: list[str] = []
    failures: list[str] = []
    for url in urls:
        try:
            events = sse(
                f"{deployment}/api/v1/collect/stream",
                {
                    "urls": [url],
                    "viewpoint": viewpoint,
                    "require_hands": True,
                    "annotate": True,
                    # The search already looked at these frames.
                    "viewpoint_verified_urls": [url],
                },
                timeout=900,
            )
        except NETWORK_ERRORS as exc:
            failures.append(f"collect cut off: {exc}")
            continue
        last: dict[str, Any] = {}
        for event, payload in events:
            if event in ("clip_stage", "clip_done"):
                last = payload.get("clip") or {}
        if last.get("video_id"):
            indexed.append(str(last["video_id"]))
        else:
            failures.append(
                str(
                    last.get("rejection_reason")
                    or last.get("error")
                    or f"stopped at {last.get('stage') or 'nothing streamed'}"
                )[:90]
            )
    outcome.indexed = len(indexed)
    outcome.blocked = any(was_blocked(failure) for failure in failures)
    if not indexed:
        reason = "the platform refused us" if outcome.blocked else "nothing reached the Datalake"
        outcome.error = f"{reason}: {sorted(set(failures)) or ['no events']}"
        outcome.seconds = time.time() - started
        return outcome

    # ---- 3. curate: clean, annotate, grade ------------------------------
    try:
        events = sse(
            f"{deployment}/api/v1/curate/stream",
            {"video_ids": indexed, "query": case["query"], "viewpoint": viewpoint},
            timeout=900,
        )
    except NETWORK_ERRORS as exc:
        outcome.error = f"curation failed: {exc}"
        outcome.seconds = time.time() - started
        return outcome

    for clip in final(events).get("clips") or []:
        outcome.clips.append(clip_outcome(outcome.query_id, clip))
    if not outcome.clips:
        outcome.error = "curation returned no graded clips"
    outcome.seconds = time.time() - started
    return outcome
