"""Pick the model provider once, so nothing downstream has to care.

Two providers are supported and they present the same interface:

* **Gemini** (`GOOGLE_API_KEY`) — the original path, using the google-genai SDK.
* **OpenRouter** (`OPENROUTER_API_KEY`) — one key in front of hundreds of
  models, including multimodal ones, and no Google project required.

`LLM_PROVIDER` forces a choice; the default (`auto`) prefers OpenRouter when its
key is present, because a deployment that has been given an OpenRouter key
meant to use it.
"""

from __future__ import annotations

from typing import Any

from video_searching_agent.config.settings import get_settings


def get_llm_client(
    api_key: str | None = None,
    model: str | None = None,
    google_api_key: str | None = None,
) -> Any:
    """Build the configured model client.

    Args:
        api_key: Override the chosen provider's key.
        model: Override the model.
        google_api_key: A Google key from a caller that predates OpenRouter
            support. Used only when Gemini is the provider — passing it to
            OpenRouter would authenticate nothing.

    Returns:
        A client exposing the shared interface: `create_message_async`,
        `convert_messages_to_gemini`, `convert_tool_definitions`,
        `format_tool_result`, `is_done`, `get_text_response`, `get_tool_calls`,
        `get_response_content`, `get_usage_metadata`, plus the conversation
        helpers (`new_conversation`, `append_user_text`, `append_model_response`,
        `append_tool_results`).
    """
    settings = get_settings()

    if settings.resolved_llm_provider == "openrouter":
        from video_searching_agent.api.openrouter_client import OpenRouterClient

        return OpenRouterClient(api_key=api_key, model=model)

    from video_searching_agent.api.gemini_client import GeminiClient

    return GeminiClient(api_key=api_key or google_api_key, model=model)


def llm_label() -> str:
    """Human-readable "provider · model", for logs and the health endpoint."""
    settings = get_settings()
    if settings.resolved_llm_provider == "openrouter":
        return f"openrouter · {settings.openrouter_model}"
    return f"gemini · {settings.gemini_model}"


def get_video_client() -> Any | None:
    """A client that can be *asked how much of a video to look at*.

    Sampling controls are the difference between a $0.005 look and a $0.37 one.
    Measured on the same 89-minute video:

    | request | video tokens |
    |---|---|
    | default sampling | 488,504 |
    | `fps=1/60` (one frame a minute) | 140,222 |
    | a two-minute window | 10,920 |

    Gemini honours all of that. OpenRouter drops it — the three requests above
    came back with the *identical* 488,504 tokens through that gateway, which is
    how you know nothing arrived. So a whole-video look prefers Gemini whenever
    a Google key exists, whatever the configured provider is for everything
    else, and returns None when there is none: the caller then bounds the look
    by duration instead of quietly paying for the whole thing.
    """
    settings = get_settings()
    if not settings.google_api_key:
        return None
    from video_searching_agent.api.gemini_client import GeminiClient

    return GeminiClient(api_key=settings.google_api_key)
