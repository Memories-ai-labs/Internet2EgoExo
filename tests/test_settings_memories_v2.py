"""Tests for Memories.ai v2 settings behavior."""

import os
from unittest.mock import patch

from video_searching_agent.config.settings import Settings


def _base_env() -> dict[str, str]:
    return {
        "GOOGLE_API_KEY": "google-test",
        "YOUTUBE_API_KEY": "youtube-test",
    }


def test_memories_key_used_when_present() -> None:
    env = {
        **_base_env(),
        "MEMORIES_API_KEY": "memories-primary",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings(_env_file=None)

    assert settings.memories_api_key == "memories-primary"


def test_memories_api_key_whitespace_is_treated_as_empty() -> None:
    env = {
        **_base_env(),
        "MEMORIES_API_KEY": "   ",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings(_env_file=None)

    assert settings.memories_api_key == ""


def test_whitespace_optional_memories_settings_fall_back_to_defaults() -> None:
    env = {
        **_base_env(),
        "MEMORIES_API_KEY": "memories-primary",
        "MEMORIES_BASE_URL": "   ",
        "MEMORIES_DEFAULT_CHANNEL": "   ",
        "MEMORIES_VLM_MODEL": "   ",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings(_env_file=None)

    assert settings.memories_base_url == "https://mavi-backend.memories.ai/serve/api/v2"
    assert settings.memories_default_channel == "memories.ai"
    assert settings.memories_vlm_model == "gemini:gemini-3-flash-preview"


def test_memories_defaults_used_when_optional_envs_missing() -> None:
    env = {
        **_base_env(),
        "MEMORIES_API_KEY": "memories-primary",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings(_env_file=None)

    assert settings.memories_base_url == "https://mavi-backend.memories.ai/serve/api/v2"
    assert settings.memories_default_channel == "memories.ai"
    assert settings.memories_vlm_model == "gemini:gemini-3-flash-preview"
    assert settings.tool_execution_concurrency == 4
    assert settings.openclaw_progress_gate_seconds == 5


def test_unknown_legacy_env_vars_are_ignored() -> None:
    env = {
        **_base_env(),
        "LEGACY_API_KEY": "legacy-key",
        "LEGACY_BASE_URL": "https://legacy.example.com/v2",
        "LEGACY_DEFAULT_CHANNEL": "rapid",
        "LEGACY_VLM_MODEL": "gemini:gemini-2.5-flash",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings(_env_file=None)

    # Unknown env vars should not override canonical settings.
    assert settings.memories_api_key == ""
    assert settings.memories_base_url == "https://mavi-backend.memories.ai/serve/api/v2"
    assert settings.memories_default_channel == "memories.ai"
    assert settings.memories_vlm_model == "gemini:gemini-3-flash-preview"


def test_memories_env_vars_take_effect() -> None:
    env = {
        **_base_env(),
        "MEMORIES_API_KEY": "memories-primary",
        "MEMORIES_BASE_URL": "https://custom.example.com/v2",
        "MEMORIES_DEFAULT_CHANNEL": "rapid",
        "MEMORIES_VLM_MODEL": "gemini:gemini-2.5-flash",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings(_env_file=None)

    assert settings.memories_api_key == "memories-primary"
    assert settings.memories_base_url == "https://custom.example.com/v2"
    assert settings.memories_default_channel == "rapid"
    assert settings.memories_vlm_model == "gemini:gemini-2.5-flash"
