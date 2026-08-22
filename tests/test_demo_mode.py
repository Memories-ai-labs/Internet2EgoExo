"""Tests for demo mode — the deployed link that needs no keys.

Demo mode exists so a stranger can click through the whole product without a
Google project, a Datalake key or a budget. Two things have to hold for that to
be honest: the payloads must be shaped exactly like the real ones, and the page
must say plainly that they are canned.
"""

import json
import re

import pytest
from fastapi.testclient import TestClient

from video_searching_agent.config import settings as settings_module
from video_searching_agent.web import demo


@pytest.fixture
def demo_client(monkeypatch):
    """A client for an app in demo mode with no credentials at all."""
    for key in ("GOOGLE_API_KEY", "YOUTUBE_API_KEY", "MEMORIES_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    settings_module.get_settings.cache_clear()
    from video_searching_agent.web.app import create_app

    try:
        yield TestClient(create_app())
    finally:
        settings_module.get_settings.cache_clear()


def _events(raw: str) -> list[tuple[str, dict]]:
    parsed = []
    for block in raw.replace("\r\n", "\n").split("\n\n"):
        name = payload = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                payload = line[5:].strip()
        if name and payload:
            parsed.append((name, json.loads(payload)))
    return parsed


class TestBootingWithoutKeys:
    def test_the_app_starts_with_no_credentials(self, demo_client):
        response = demo_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["demo_mode"] is True

    def test_the_ui_is_served(self, demo_client):
        assert demo_client.get("/ui/").status_code == 200

    def test_keys_are_still_required_when_not_in_demo_mode(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("DEMO_MODE", raising=False)
        settings_module.get_settings.cache_clear()
        try:
            # `_env_file=None` so a developer's own .env cannot make this pass.
            with pytest.raises(Exception, match="GOOGLE_API_KEY|validation error"):
                settings_module.Settings(_env_file=None)
        finally:
            settings_module.get_settings.cache_clear()

    def test_an_openrouter_key_also_lifts_the_google_requirement(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
        monkeypatch.delenv("DEMO_MODE", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        settings_module.get_settings.cache_clear()
        try:
            settings = settings_module.Settings(_env_file=None)
            assert settings.resolved_llm_provider == "openrouter"
            assert settings.demo_mode is False
        finally:
            settings_module.get_settings.cache_clear()


class TestDemoStreams:
    def test_the_search_stream_returns_a_manifest(self, demo_client):
        response = demo_client.post(
            "/api/v1/queries/stream", json={"query": "first-person cooking"}
        )
        assert response.status_code == 200
        events = dict(_events(response.text))
        assert "complete" in events
        manifest = events["complete"]["dataset"]
        # The four hour measures, kept apart, exactly as the real one reports.
        assert set(manifest["hours"]) >= {
            "delivered_hours",
            "accepted_hours",
            "accepted_labeled_hours",
            "media_yield",
        }
        assert manifest["clips"][0]["annotations"]

    def test_the_answer_says_it_is_demo_data(self, demo_client):
        response = demo_client.post("/api/v1/queries/stream", json={"query": "x"})
        answer = dict(_events(response.text))["complete"]["answer"].lower()
        assert "demo" in answer

    def test_collection_streams_every_stage_then_the_verdicts(self, demo_client):
        response = demo_client.post(
            "/api/v1/collect/stream",
            json={"urls": ["https://youtube.com/watch?v=a", "https://youtube.com/watch?v=b"]},
        )
        names = [name for name, _ in _events(response.text)]
        assert names.count("clip_stage") >= 7
        assert names[-1] == "complete"

    def test_the_demo_shows_a_clip_dropped_for_having_no_hands(self, demo_client):
        response = demo_client.post(
            "/api/v1/collect/stream",
            json={"urls": ["https://youtube.com/watch?v=a", "https://youtube.com/watch?v=b"]},
        )
        complete = dict(_events(response.text))["complete"]
        assert complete["accepted_count"] == 1
        rejected = complete["rejected"][0]
        assert rejected["rejection_reason"] == "no hands visible in the captions"
        # A clip that failed a blocking gate is not graded.
        assert rejected["quality"] is None

    def test_the_accepted_demo_clip_carries_a_real_tree(self, demo_client):
        response = demo_client.post(
            "/api/v1/collect/stream", json={"urls": ["https://youtube.com/watch?v=a"]}
        )
        clip = dict(_events(response.text))["complete"]["accepted"][0]
        levels = [a["hier_level"] for a in clip["annotation"]["annotations"]]
        # Two actions, one of which has an event inside it.
        assert levels == ["task", "action", "event", "action"]
        assert clip["annotation"]["caveat"]

    def test_curation_reports_the_ledger_and_an_unmeasured_gate(self, demo_client):
        response = demo_client.post("/api/v1/curate/stream", json={"tag": "clean_pass"})
        complete = dict(_events(response.text))["complete"]
        assert complete["batch_grade"] == "B"
        assert complete["hours"]["accepted_labeled_hours"] <= complete["hours"]["delivered_hours"]
        dup = next(c for c in complete["dataset_checks"] if c["id"] == "G3-DUP")
        assert dup["measured"] is False

    def test_validation_still_applies_in_demo_mode(self, demo_client):
        assert demo_client.post("/api/v1/collect/stream", json={"urls": []}).status_code == 422
        assert demo_client.post("/api/v1/curate/stream", json={}).status_code == 422


class TestPayloadFidelity:
    """The demo is only useful if its shapes match the real ones."""

    def test_gate_checks_have_the_real_gate_shape(self):
        for check in demo.CHECKS:
            assert set(check) == {
                "id",
                "name",
                "passed",
                "measured",
                "blocking",
                "value",
                "threshold",
                "detail",
            }

    def test_the_tree_is_well_formed(self):
        by_id = {a["segment_id"]: a for a in demo.TREE}
        for annotation in demo.TREE:
            parent = by_id.get(annotation["parent_segment_id"])
            if not parent:
                continue
            # G2-TREE-1: a child sits inside its parent.
            assert annotation["span_start"] >= parent["span_start"]
            assert annotation["span_end"] <= parent["span_end"]
            # G2-TREE-3: each level says something of its own.
            assert annotation["narration"] != parent["narration"]

    def test_no_annotation_claims_a_cut_file(self):
        assert all("clip_file" not in annotation for annotation in demo.TREE)

    def test_hand_assignment_is_left_null_where_it_is_not_stated(self):
        task = next(a for a in demo.TREE if a["hier_level"] == "task")
        assert task["left_hand"] is None and task["right_hand"] is None

    def test_the_ui_bundle_asks_for_the_health_endpoint(self):
        # The banner depends on it, so a build that dropped the call would ship
        # a demo deployment that never says it is one.
        from pathlib import Path

        static = Path("src/video_searching_agent/web/static/assets")
        bundles = list(static.glob("*.js"))
        assert bundles, "no built UI bundle found"
        assert any("/api/v1/health" in b.read_text() for b in bundles)

    def test_every_demo_payload_is_json_safe(self):
        class _Body:
            urls = ["https://youtube.com/watch?v=a", "https://youtube.com/watch?v=b"]
            query = "cooking"
            tag = "clean_pass"
            video_ids = None
            target_hours = 2

        for events in (
            demo.query_events(_Body()),
            demo.collect_events(_Body()),
            demo.curate_events(_Body()),
        ):
            for name, payload in events:
                assert re.fullmatch(r"[a-z_]+", name)
                json.loads(json.dumps(payload))
