"""Tests for bring-your-own-key.

The hosted deployment runs on its owner's keys and is rate limited. A caller who
brings their own is spending their own money, so they skip the shared quota and
their run uses their key. Three properties have to hold, and the third is the
one that would be a security bug if it broke:

1. Supplied keys are used for that request.
2. Supplied keys bypass the shared rate limit.
3. Supplied keys never end up anywhere global — not in settings, not in the
   cached agent, not in the next caller's request.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from video_searching_agent.api.openrouter_client import OpenRouterClient
from video_searching_agent.config import settings as settings_module
from video_searching_agent.web.credentials import RequestCredentials
from video_searching_agent.web.middleware.rate_limit import RateLimitMiddleware


class TestReadingHeaders:
    def test_headers_become_credentials(self):
        creds = RequestCredentials.from_headers(
            {
                "x-openrouter-key": "sk-or-mine",
                "x-memories-key": "sk-mai-mine",
                "x-memories-collection": "col_mine",
            }
        )
        assert creds.openrouter_key == "sk-or-mine"
        assert creds.memories_key == "sk-mai-mine"
        assert creds.memories_collection_id == "col_mine"
        assert creds.supplied is True

    def test_no_headers_means_nothing_supplied(self):
        creds = RequestCredentials.from_headers({})
        assert creds.supplied is False
        assert creds.llm_client() is None
        assert creds.datalake_client() is None

    def test_blank_headers_are_not_credentials(self):
        creds = RequestCredentials.from_headers({"x-openrouter-key": "   "})
        assert creds.openrouter_key is None
        assert creds.supplied is False

    def test_a_collection_alone_is_not_a_credential(self):
        # Without a key of their own there is nothing to bill to the caller, so
        # a bare collection id must not buy a quota bypass.
        creds = RequestCredentials.from_headers({"x-memories-collection": "col_x"})
        assert creds.supplied is False

    def test_the_openrouter_key_builds_an_openrouter_client(self):
        creds = RequestCredentials.from_headers({"x-openrouter-key": "sk-or-mine"})
        client = creds.llm_client()
        assert isinstance(client, OpenRouterClient)
        assert client.api_key == "sk-or-mine"

    def test_a_google_key_builds_a_gemini_client(self):
        from video_searching_agent.api.gemini_client import GeminiClient

        creds = RequestCredentials.from_headers({"x-google-key": "google-mine"})
        client = creds.llm_client()
        assert isinstance(client, GeminiClient)
        assert client.api_key == "google-mine"

    def test_openrouter_wins_when_both_are_sent(self):
        creds = RequestCredentials.from_headers(
            {"x-openrouter-key": "sk-or-mine", "x-google-key": "google-mine"}
        )
        assert isinstance(creds.llm_client(), OpenRouterClient)

    def test_the_datalake_client_uses_the_callers_collection(self):
        creds = RequestCredentials.from_headers(
            {"x-memories-key": "sk-mai-mine", "x-memories-collection": "col_mine"}
        )
        client = creds.datalake_client()
        assert client.api_key == "sk-mai-mine"
        assert client._collection_id == "col_mine"

    def test_describe_names_the_keys_and_never_their_values(self):
        creds = RequestCredentials.from_headers(
            {"x-openrouter-key": "sk-or-secret", "x-memories-key": "sk-mai-secret"}
        )
        described = creds.describe()
        assert described == ["openrouter", "datalake"]
        assert not any("secret" in entry for entry in described)


class TestNothingLeaksGlobally:
    """The property that would be a security bug if it broke."""

    def test_settings_are_untouched(self):
        before = settings_module.get_settings().openrouter_api_key
        creds = RequestCredentials.from_headers({"x-openrouter-key": "sk-or-mine"})
        creds.llm_client()
        assert settings_module.get_settings().openrouter_api_key == before

    def test_the_shared_agent_never_gets_the_callers_key(self):
        from video_searching_agent.web.routers.queries import _agent_for

        shared = _agent_for(RequestCredentials.from_headers({}))
        private = _agent_for(RequestCredentials.from_headers({"x-openrouter-key": "sk-or-mine"}))

        assert private is not shared
        assert private.llm.api_key == "sk-or-mine"
        assert getattr(shared.llm, "api_key", None) != "sk-or-mine"

        # And the shared one is still the shared one afterwards.
        assert _agent_for(RequestCredentials.from_headers({})) is shared

    def test_two_callers_get_their_own_clients(self):
        from video_searching_agent.web.routers.queries import _agent_for

        first = _agent_for(RequestCredentials.from_headers({"x-openrouter-key": "sk-or-a"}))
        second = _agent_for(RequestCredentials.from_headers({"x-openrouter-key": "sk-or-b"}))
        assert first.llm.api_key == "sk-or-a"
        assert second.llm.api_key == "sk-or-b"

    def test_the_pipeline_is_wired_to_the_callers_keys(self):
        from video_searching_agent.web.routers.pipeline import _pipeline_for

        creds = RequestCredentials.from_headers(
            {"x-openrouter-key": "sk-or-mine", "x-memories-key": "sk-mai-mine"}
        )
        pipeline = _pipeline_for(creds)
        assert pipeline.client.api_key == "sk-mai-mine"
        assert pipeline.cleaning.client.api_key == "sk-mai-mine"
        assert pipeline.annotation.gemini.api_key == "sk-or-mine"

    def test_the_curation_agent_is_wired_to_the_callers_keys(self):
        from video_searching_agent.web.routers.pipeline import _curation_agent_for

        creds = RequestCredentials.from_headers(
            {"x-openrouter-key": "sk-or-mine", "x-memories-key": "sk-mai-mine"}
        )
        agent = _curation_agent_for(creds)
        assert agent.client.api_key == "sk-mai-mine"
        assert agent.annotation.gemini.api_key == "sk-or-mine"

    def test_a_model_key_alone_leaves_the_datalake_on_the_server_config(self):
        from video_searching_agent.web.routers.pipeline import _pipeline_for

        creds = RequestCredentials.from_headers({"x-openrouter-key": "sk-or-mine"})
        pipeline = _pipeline_for(creds)
        assert pipeline.annotation.gemini.api_key == "sk-or-mine"
        # Resolved from settings, not from the caller.
        assert pipeline.client.api_key != "sk-or-mine"


class TestRateLimitBypass:
    @staticmethod
    def _app(rpm: int = 1):
        from fastapi import FastAPI

        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, rpm=rpm)

        @app.post("/api/v1/queries/stream")
        async def _stream() -> dict[str, bool]:
            return {"ok": True}

        return TestClient(app)

    def _settings(self, rpm: int):
        mock = MagicMock()
        mock.rate_limit_rpm = rpm
        mock.rate_limit_enabled = True
        return mock

    def test_the_shared_quota_still_applies_without_keys(self):
        with patch(
            "video_searching_agent.web.middleware.rate_limit.get_settings",
            return_value=self._settings(1),
        ):
            client = self._app(rpm=1)
            assert client.post("/api/v1/queries/stream").status_code == 200
            assert client.post("/api/v1/queries/stream").status_code == 429

    def test_bringing_a_key_skips_the_quota(self):
        with patch(
            "video_searching_agent.web.middleware.rate_limit.get_settings",
            return_value=self._settings(1),
        ):
            client = self._app(rpm=1)
            headers = {"X-OpenRouter-Key": "sk-or-mine"}
            for _ in range(5):
                assert client.post("/api/v1/queries/stream", headers=headers).status_code == 200

    def test_one_visitor_cannot_starve_another(self):
        # Anonymous callers are bucketed per address, so a heavy user does not
        # take the whole deployment down with them.
        with patch(
            "video_searching_agent.web.middleware.rate_limit.get_settings",
            return_value=self._settings(1),
        ):
            client = self._app(rpm=1)
            noisy = {"X-Forwarded-For": "203.0.113.1"}
            quiet = {"X-Forwarded-For": "203.0.113.2"}
            assert client.post("/api/v1/queries/stream", headers=noisy).status_code == 200
            assert client.post("/api/v1/queries/stream", headers=noisy).status_code == 429
            assert client.post("/api/v1/queries/stream", headers=quiet).status_code == 200


class TestDemoModeIsUnaffected:
    def test_demo_mode_ignores_supplied_keys(self, monkeypatch):
        """Demo mode is canned data; a key must not silently make it spend."""
        monkeypatch.setenv("DEMO_MODE", "1")
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
        settings_module.get_settings.cache_clear()
        try:
            from video_searching_agent.web.app import create_app

            client = TestClient(create_app())
            response = client.post(
                "/api/v1/curate/stream",
                json={"tag": "clean_pass"},
                headers={"X-Memories-Key": "sk-mai-mine"},
            )
            assert response.status_code == 200
            assert "demo data" in response.text
        finally:
            settings_module.get_settings.cache_clear()


@pytest.mark.parametrize(
    "header",
    ["X-OpenRouter-Key", "x-openrouter-key", "X-OPENROUTER-KEY"],
)
def test_header_names_are_case_insensitive(header):
    from starlette.datastructures import Headers

    creds = RequestCredentials.from_headers(Headers({header: "sk-or-mine"}))
    assert creds.openrouter_key == "sk-or-mine"
