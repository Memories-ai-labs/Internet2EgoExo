"""OpenRouter client, drop-in compatible with the Gemini one.

One key instead of three. OpenRouter speaks the OpenAI chat-completions
protocol in front of hundreds of models, so a single `OPENROUTER_API_KEY` gets
the agent loop, the annotation agent and (through a vision-capable model) frame
reading — without a Google project, and with the model choice left to whoever
deploys it.

The public surface mirrors :class:`GeminiClient` exactly, including the
`convert_messages_to_gemini` name, so the agent loop does not care which
provider it is talking to. What differs is hidden here:

* messages are OpenAI-shaped (`role`/`content`, `tool_calls`, `role: "tool"`),
  not `types.Content`;
* tool results have to carry the `tool_call_id` of the call they answer, which
  is matched back by function name against the assistant turn that asked;
* cost comes from the provider rather than a local price table — OpenRouter
  returns what the call actually cost, so nothing is guessed.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from video_searching_agent.config.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
# Cheap, fast, and multimodal (text/image/video), so the same key can later read
# frames rather than only caption text.
DEFAULT_MODEL = "google/gemini-3.7-flash"


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter refuses a request."""


class OpenRouterClient:
    """Chat completions over OpenRouter, with tool use."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            api_key: OpenRouter key (`sk-or-...`). Defaults to settings.
            model: Model slug, e.g. `google/gemini-3.7-flash`. Defaults to settings.
            base_url: API root. Defaults to settings.
            timeout_seconds: Request timeout. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.openrouter_model or DEFAULT_MODEL
        self.base_url = (base_url or settings.openrouter_base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout_seconds = float(
            timeout_seconds
            if timeout_seconds is not None
            else max(settings.api_timeout_seconds, 120)
        )

    # ----------------------------------------------------------- requests

    def _payload(
        self,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]] | None,
        max_tokens: int,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": ([{"role": "system", "content": system}] if system else []) + messages,
            "max_tokens": max_tokens,
            # Ask for the real cost of the call rather than inferring it.
            "usage": {"include": True},
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        return body

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter uses these for attribution on its dashboards.
            "HTTP-Referer": "https://github.com/Memories-ai-labs/Internet-Video-Search",
            "X-Title": "Internet Video Search",
        }

    def create_message(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send one completion request and return the parsed response."""
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=self._payload(messages, system, tools, max_tokens),
            )
        return self._parse(response)

    async def create_message_async(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send one completion request without blocking the event loop."""
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=self._payload(messages, system, tools, max_tokens),
            )
        return self._parse(response)

    @staticmethod
    def _parse(response: httpx.Response) -> dict[str, Any]:
        """Turn an HTTP response into a payload, or raise with the reason."""
        if response.status_code >= 400:
            detail = response.text[:400]
            raise OpenRouterError(f"OpenRouter returned {response.status_code}: {detail}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise OpenRouterError("OpenRouter returned a non-JSON body") from exc

        # A 200 can still carry a provider-level error.
        if isinstance(payload.get("error"), dict):
            message = payload["error"].get("message") or "unknown error"
            raise OpenRouterError(f"OpenRouter error: {message}")
        return payload

    # ------------------------------------------------ conversation building

    def new_conversation(self, text: str) -> list[dict[str, Any]]:
        """Start a conversation with one user turn."""
        return [{"role": "user", "content": text}]

    def append_user_text(self, messages: list[dict[str, Any]], text: str) -> None:
        """Add a user turn."""
        messages.append({"role": "user", "content": text})

    def append_model_response(
        self, messages: list[dict[str, Any]], response: dict[str, Any]
    ) -> None:
        """Add the assistant turn, keeping its tool-call ids intact."""
        message = self.get_response_content(response)
        if message is not None:
            messages.append(message)

    def append_tool_results(
        self,
        messages: list[dict[str, Any]],
        results: list[tuple[str, str]],
    ) -> None:
        """Add one `role: "tool"` turn per result.

        OpenAI-shaped tool results must name the call they answer, so each
        result is matched by function name against the tool calls in the
        assistant turn that asked for them.
        """
        pending = self._pending_tool_calls(messages)
        for name, content in results:
            call_id = pending.pop(name, None) or f"call_{name}"
            messages.append(
                {"role": "tool", "tool_call_id": call_id, "name": name, "content": content}
            )

    @staticmethod
    def _pending_tool_calls(messages: list[dict[str, Any]]) -> dict[str, str]:
        """`{function name: tool_call_id}` from the most recent assistant turn."""
        for message in reversed(messages):
            if message.get("role") != "assistant":
                continue
            calls = message.get("tool_calls") or []
            return {
                str(call.get("function", {}).get("name")): str(call.get("id"))
                for call in calls
                if isinstance(call, dict) and call.get("id")
            }
        return {}

    def convert_messages_to_gemini(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert Claude-style messages to OpenAI-shaped ones.

        The name is the Gemini client's, kept so either client can be dropped
        into the same call site.
        """
        converted: list[dict[str, Any]] = []
        call_ids: dict[str, str] = {}

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content")

            if isinstance(content, str):
                converted.append({"role": role, "content": content})
                continue
            if not isinstance(content, list):
                converted.append({"role": role, "content": ""})
                continue

            texts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            tool_results: list[dict[str, Any]] = []

            for item in content:
                if not isinstance(item, dict):
                    continue
                kind = item.get("type")
                if kind == "text":
                    texts.append(str(item.get("text", "")))
                elif kind == "tool_use":
                    name = str(item.get("name"))
                    call_id = str(item.get("id") or f"call_{len(call_ids) + 1}_{name}")
                    call_ids[name] = call_id
                    tool_calls.append(
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps(item.get("input") or {}),
                            },
                        }
                    )
                elif kind == "tool_result":
                    name = str(item.get("name"))
                    tool_results.append(
                        {
                            "role": "tool",
                            "tool_call_id": call_ids.get(name, f"call_{name}"),
                            "name": name,
                            "content": str(item.get("content", "")),
                        }
                    )

            if tool_calls or texts:
                assistant_role = "assistant" if role == "assistant" or tool_calls else role
                entry: dict[str, Any] = {
                    "role": assistant_role,
                    "content": "\n".join(texts) if texts else None,
                }
                if tool_calls:
                    entry["tool_calls"] = tool_calls
                converted.append(entry)
            converted.extend(tool_results)

        return converted

    def convert_tool_definitions(
        self,
        tools: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert Claude-style tool definitions to OpenAI function tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema") or {"type": "object", "properties": {}},
                },
            }
            for tool in tools
        ]

    def format_tool_result(
        self,
        function_name: str,
        result: Any,
        is_error: bool = False,
    ) -> dict[str, Any]:
        """Format a tool result the same way the Gemini client does."""
        content = result if isinstance(result, str) else str(result)
        if is_error:
            content = f"Error: {content}"
        return {"type": "tool_result", "name": function_name, "content": content}

    # ------------------------------------------------------ response reading

    @staticmethod
    def _message(response: dict[str, Any]) -> dict[str, Any]:
        choices = response.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            return {}
        message = choices[0].get("message")
        return message if isinstance(message, dict) else {}

    def is_done(self, response: dict[str, Any]) -> bool:
        """True when the model asked for no tools."""
        return not self._message(response).get("tool_calls")

    def get_text_response(self, response: dict[str, Any]) -> str | None:
        """The assistant's text, or None."""
        content = self._message(response).get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            # Some providers return content parts rather than a string.
            text = "\n".join(
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict) and part.get("type") in (None, "text")
            ).strip()
            return text or None
        return None

    def get_tool_calls(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Tool calls as `{"name", "input"}`, with arguments already parsed."""
        calls: list[dict[str, Any]] = []
        for call in self._message(response).get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            function = call.get("function") or {}
            raw = function.get("arguments")
            try:
                arguments = json.loads(raw) if isinstance(raw, str) and raw.strip() else (raw or {})
            except json.JSONDecodeError:
                logger.info("unparseable tool arguments for %s: %r", function.get("name"), raw)
                arguments = {}
            calls.append(
                {
                    "name": function.get("name"),
                    "input": arguments if isinstance(arguments, dict) else {},
                }
            )
        return calls

    def get_response_content(self, response: dict[str, Any]) -> dict[str, Any] | None:
        """The assistant message, ready to append to the conversation."""
        message = self._message(response)
        return dict(message) if message else None

    def get_usage_metadata(self, response: dict[str, Any]) -> dict[str, int]:
        """Token usage in the same shape the Gemini client reports."""
        usage = response.get("usage") or {}
        return {
            "input_tokens": int(usage.get("prompt_tokens") or 0),
            "output_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }

    def get_cost_usd(self, response: dict[str, Any]) -> float | None:
        """What the call actually cost, as reported by OpenRouter.

        Returned rather than computed: the price depends on which provider
        served the request, so a local table would be a guess.
        """
        usage = response.get("usage") or {}
        cost = usage.get("cost")
        try:
            return float(cost) if cost is not None else None
        except (TypeError, ValueError):
            return None
