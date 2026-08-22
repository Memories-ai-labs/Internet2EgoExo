"""Per-request credentials — bring your own key.

The hosted deployment runs on its owner's keys and is therefore rate limited:
one shared budget cannot absorb everyone's indexing bills. Anyone who would
rather not queue can send their own keys with the request and be served without
touching the shared quota.

Three rules make this safe to offer:

* **Per request, never global.** A supplied key builds a client for that one
  request. Nothing is written into the process-wide settings, so one caller's
  key can never leak into another caller's run.
* **Never logged, never stored.** The keys live in the request headers and in
  the caller's own browser, and nowhere else.
* **Absence is not an error.** With no headers the request runs on the server's
  own configuration, exactly as before.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Headers a caller can bring. Names are explicit rather than clever so that
# anyone reading a network tab knows what they are sending.
OPENROUTER_HEADER = "x-openrouter-key"
MEMORIES_HEADER = "x-memories-key"
COLLECTION_HEADER = "x-memories-collection"
GOOGLE_HEADER = "x-google-key"


def _clean(value: str | None) -> str | None:
    """A trimmed header value, or None when it is absent or blank."""
    if not value:
        return None
    trimmed = value.strip()
    return trimmed or None


@dataclass(frozen=True)
class RequestCredentials:
    """Keys supplied by the caller for this one request."""

    openrouter_key: str | None = None
    google_key: str | None = None
    memories_key: str | None = None
    memories_collection_id: str | None = None

    @property
    def supplied(self) -> bool:
        """True when the caller brought at least one key of their own."""
        return bool(self.openrouter_key or self.google_key or self.memories_key)

    @classmethod
    def from_headers(cls, headers: Any) -> RequestCredentials:
        """Read credentials from request headers (case-insensitive)."""
        get = headers.get
        return cls(
            openrouter_key=_clean(get(OPENROUTER_HEADER)),
            google_key=_clean(get(GOOGLE_HEADER)),
            memories_key=_clean(get(MEMORIES_HEADER)),
            memories_collection_id=_clean(get(COLLECTION_HEADER)),
        )

    def llm_client(self) -> Any | None:
        """A model client for this request, or None to use the server's."""
        if not (self.openrouter_key or self.google_key):
            return None

        if self.openrouter_key:
            from video_searching_agent.api.openrouter_client import OpenRouterClient

            return OpenRouterClient(api_key=self.openrouter_key)

        from video_searching_agent.api.gemini_client import GeminiClient

        return GeminiClient(api_key=self.google_key)

    def datalake_client(self) -> Any | None:
        """A Datalake client for this request, or None to use the server's."""
        if not self.memories_key:
            return None

        from video_searching_agent.api.memories_datalake_client import (
            MemoriesDatalakeClient,
        )

        return MemoriesDatalakeClient(
            api_key=self.memories_key,
            collection_id=self.memories_collection_id,
        )

    def describe(self) -> list[str]:
        """Which credentials the caller brought, for the stream's own record.

        Names only — never the values.
        """
        brought = []
        if self.openrouter_key:
            brought.append("openrouter")
        if self.google_key:
            brought.append("google")
        if self.memories_key:
            brought.append("datalake")
        return brought
