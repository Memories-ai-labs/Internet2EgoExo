"""Google Gemini API client with tool use support."""

import asyncio
from typing import Any

from google import genai
from google.genai import types

from video_searching_agent.config.settings import get_settings


class GeminiClient:
    """Client for interacting with Gemini API with tool use."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """Initialize the Gemini client.

        Args:
            api_key: Google API key. Defaults to settings.
            model: Model to use. Defaults to settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.google_api_key
        self.model = model or settings.gemini_model
        self._client: genai.Client | None = None  # Lazy-loaded

    @property
    def client(self) -> genai.Client:
        """Lazy-load the Gemini client."""
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _build_config(
        self,
        system: str | None = None,
        tools: list[types.Tool] | None = None,
        max_tokens: int = 4096,
    ) -> types.GenerateContentConfig:
        """Build Gemini request config."""
        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            system_instruction=system,
        )
        if tools:
            config.tools = tools  # type: ignore[assignment]
            # Disable automatic function calling - we want to handle it manually
            config.automatic_function_calling = types.AutomaticFunctionCallingConfig(disable=True)
        return config

    def create_message(
        self,
        messages: list[types.Content],
        system: str | None = None,
        tools: list[types.Tool] | None = None,
        max_tokens: int = 4096,
    ) -> types.GenerateContentResponse:
        """Create a message with Gemini.

        Args:
            messages: Conversation messages as Content objects.
            system: System prompt.
            tools: Tool definitions for function calling.
            max_tokens: Maximum tokens in response.

        Returns:
            Gemini's response.
        """
        config = self._build_config(system=system, tools=tools, max_tokens=max_tokens)

        return self.client.models.generate_content(
            model=self.model,
            contents=messages,  # type: ignore[arg-type]
            config=config,
        )

    async def create_message_async(
        self,
        messages: list[types.Content],
        system: str | None = None,
        tools: list[types.Tool] | None = None,
        max_tokens: int = 4096,
    ) -> types.GenerateContentResponse:
        """Create a Gemini message without blocking the event loop."""
        config = self._build_config(system=system, tools=tools, max_tokens=max_tokens)
        return await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=messages,  # type: ignore[arg-type]
            config=config,
        )

    # ------------------------------------------------ conversation building
    #
    # These four keep the agent loops free of provider types, so the same loop
    # runs on Gemini or on OpenRouter.

    def new_conversation(self, text: str) -> list[types.Content]:
        """Start a conversation with one user turn."""
        return [types.Content(role="user", parts=[types.Part(text=text)])]

    def new_visual_conversation(
        self, text: str, images: list[bytes], mime_type: str = "image/jpeg"
    ) -> list[types.Content]:
        """Start a conversation that shows the model some frames."""
        parts = [types.Part(text=text)]
        parts.extend(types.Part.from_bytes(data=raw, mime_type=mime_type) for raw in images)
        return [types.Content(role="user", parts=parts)]

    def new_video_conversation(self, text: str, video_url: str) -> list[types.Content]:
        """Start a conversation that shows the model an actual video.

        Gemini takes a YouTube URL as a file part and watches it. It is billed
        per video token, so this is an escalation rather than a default — see
        :mod:`video_searching_agent.curation.frame_viewpoint`.
        """
        return [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=text),
                    types.Part(file_data=types.FileData(file_uri=video_url, mime_type="video/*")),
                ],
            )
        ]

    def append_user_text(self, messages: list[types.Content], text: str) -> None:
        """Add a user turn."""
        messages.append(types.Content(role="user", parts=[types.Part(text=text)]))

    def append_model_response(
        self,
        messages: list[types.Content],
        response: types.GenerateContentResponse,
    ) -> None:
        """Add the model turn, preserving thought signatures."""
        content = self.get_response_content(response)
        if content is not None:
            messages.append(content)

    def append_tool_results(
        self,
        messages: list[types.Content],
        results: list[tuple[str, str]],
    ) -> None:
        """Add one user turn carrying every function response."""
        if not results:
            return
        parts = [
            types.Part.from_function_response(name=name, response={"result": content})
            for name, content in results
        ]
        messages.append(types.Content(role="user", parts=parts))

    def get_cost_usd(self, response: types.GenerateContentResponse) -> float | None:
        """Gemini does not report cost; the local price table computes it."""
        return None

    def convert_messages_to_gemini(
        self,
        messages: list[dict[str, Any]],
    ) -> list[types.Content]:
        """Convert Claude-style messages to Gemini Content objects.

        Args:
            messages: Messages in Claude format (role: user/assistant, content: ...).

        Returns:
            List of Gemini Content objects.
        """
        gemini_messages: list[types.Content] = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # Convert role: assistant -> model
            gemini_role = "model" if role == "assistant" else "user"

            parts: list[types.Part] = []

            if isinstance(content, str):
                parts.append(types.Part(text=content))
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        item_type = item.get("type")
                        if item_type == "text":
                            parts.append(types.Part(text=item["text"]))
                        elif item_type == "tool_use":
                            # Model made a function call
                            parts.append(
                                types.Part(
                                    function_call=types.FunctionCall(
                                        name=item["name"],
                                        args=item["input"],
                                    )
                                )
                            )
                        elif item_type == "tool_result":
                            # User returning function result
                            parts.append(
                                types.Part.from_function_response(
                                    name=item["name"],
                                    response={"result": item["content"]},
                                )
                            )
                    elif isinstance(item, types.Part):
                        parts.append(item)

            gemini_messages.append(types.Content(role=gemini_role, parts=parts))

        return gemini_messages

    def convert_tool_definitions(
        self,
        tools: list[dict[str, Any]],
    ) -> list[types.Tool]:
        """Convert Claude-style tool definitions to Gemini format.

        Args:
            tools: Tool definitions in Claude format.

        Returns:
            List of Gemini Tool objects.
        """
        declarations = []
        for tool in tools:
            declarations.append(
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool.get("input_schema", {}),
                )
            )

        return [types.Tool(function_declarations=declarations)]

    def format_tool_result(
        self,
        function_name: str,
        result: Any,
        is_error: bool = False,
    ) -> dict[str, Any]:
        """Format a tool result for sending back to Gemini.

        Args:
            function_name: Name of the function that was called.
            result: Result from tool execution.
            is_error: Whether the result is an error.

        Returns:
            Formatted tool result dict with name and content.
        """
        content = str(result) if not isinstance(result, str) else result
        if is_error:
            content = f"Error: {content}"

        return {
            "type": "tool_result",
            "name": function_name,
            "content": content,
        }

    def is_done(self, response: types.GenerateContentResponse) -> bool:
        """Check if Gemini is done (no more function calls).

        Args:
            response: Gemini's response.

        Returns:
            True if response contains only text (no function calls).
        """
        if not response.candidates or not response.candidates[0].content:
            return True

        parts = response.candidates[0].content.parts
        if parts:
            for part in parts:
                if part.function_call:
                    return False
        return True

    def get_text_response(self, response: types.GenerateContentResponse) -> str | None:
        """Extract text from Gemini's response.

        Args:
            response: Gemini's response.

        Returns:
            Text content or None if no text.
        """
        if not response.candidates or not response.candidates[0].content:
            return None

        text_parts = []
        parts = response.candidates[0].content.parts
        if parts:
            for part in parts:
                if part.text:
                    text_parts.append(part.text)

        return "\n".join(text_parts) if text_parts else None

    def get_tool_calls(self, response: types.GenerateContentResponse) -> list[dict[str, Any]]:
        """Extract function calls from Gemini's response.

        Args:
            response: Gemini's response.

        Returns:
            List of tool call dicts with 'name' and 'input'.
        """
        tool_calls: list[dict[str, Any]] = []

        if not response.candidates or not response.candidates[0].content:
            return tool_calls

        parts = response.candidates[0].content.parts
        if parts:
            for part in parts:
                if part.function_call:
                    tool_calls.append(
                        {
                            "name": part.function_call.name,
                            "input": dict(part.function_call.args)
                            if part.function_call.args
                            else {},
                        }
                    )

        return tool_calls

    def get_response_content(self, response: types.GenerateContentResponse) -> types.Content | None:
        """Get the full content from response (preserves thought signatures).

        Args:
            response: Gemini's response.

        Returns:
            The Content object from the response, or None.
        """
        if not response.candidates or not response.candidates[0].content:
            return None
        return response.candidates[0].content

    def get_usage_metadata(self, response: types.GenerateContentResponse) -> dict[str, int]:
        """Extract token usage from Gemini response.

        Args:
            response: Gemini's response.

        Returns:
            Dict with input_tokens, output_tokens, and total_tokens.
        """
        usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            metadata = response.usage_metadata
            usage["input_tokens"] = getattr(metadata, "prompt_token_count", 0) or 0
            usage["output_tokens"] = getattr(metadata, "candidates_token_count", 0) or 0
            usage["total_tokens"] = getattr(metadata, "total_token_count", 0) or 0
        return usage
