"""Tests for the OpenRouter client and the provider factory."""

import json
from typing import Any

import pytest

from video_searching_agent.api.openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
)


def _response(
    content: str | None = "hello",
    tool_calls: list[dict[str, Any]] | None = None,
    usage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"choices": [{"message": message}], "usage": usage or {}}


def _client() -> OpenRouterClient:
    return OpenRouterClient(api_key="sk-or-test", model="test/model")


class TestResponseReading:
    def test_text_is_extracted(self):
        assert _client().get_text_response(_response("an answer")) == "an answer"

    def test_content_parts_are_joined(self):
        payload = _response(None)
        payload["choices"][0]["message"]["content"] = [
            {"type": "text", "text": "one"},
            {"type": "text", "text": "two"},
        ]
        assert _client().get_text_response(payload) == "one\ntwo"

    def test_an_empty_answer_is_none_not_an_empty_string(self):
        assert _client().get_text_response(_response("   ")) is None
        assert _client().get_text_response({}) is None

    def test_done_means_no_tool_calls(self):
        client = _client()
        assert client.is_done(_response("answer")) is True
        calls = [{"id": "c1", "function": {"name": "video_search", "arguments": "{}"}}]
        assert client.is_done(_response(None, calls)) is False

    def test_tool_arguments_are_parsed(self):
        calls = [
            {
                "id": "c1",
                "function": {"name": "video_search", "arguments": '{"query": "ego cooking"}'},
            }
        ]
        parsed = _client().get_tool_calls(_response(None, calls))
        assert parsed == [{"name": "video_search", "input": {"query": "ego cooking"}}]

    def test_unparseable_arguments_do_not_raise(self):
        calls = [{"id": "c1", "function": {"name": "t", "arguments": "{not json"}}]
        assert _client().get_tool_calls(_response(None, calls)) == [
            {"name": "t", "input": {}}
        ]

    def test_usage_is_reported_in_the_shared_shape(self):
        usage = {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}
        assert _client().get_usage_metadata(_response(usage=usage)) == {
            "input_tokens": 12,
            "output_tokens": 3,
            "total_tokens": 15,
        }

    def test_cost_comes_from_the_provider_not_a_local_table(self):
        client = _client()
        assert client.get_cost_usd(_response(usage={"cost": 0.00042})) == pytest.approx(0.00042)
        assert client.get_cost_usd(_response()) is None


class TestConversationBuilding:
    def test_a_conversation_starts_with_a_user_turn(self):
        assert _client().new_conversation("find ego cooking") == [
            {"role": "user", "content": "find ego cooking"}
        ]

    def test_tool_results_answer_the_call_that_asked(self):
        client = _client()
        messages = client.new_conversation("go")
        calls = [
            {"id": "call_abc", "function": {"name": "video_search", "arguments": "{}"}}
        ]
        client.append_model_response(messages, _response(None, calls))
        client.append_tool_results(messages, [("video_search", "7 videos")])

        assert messages[-1] == {
            "role": "tool",
            "tool_call_id": "call_abc",
            "name": "video_search",
            "content": "7 videos",
        }

    def test_a_result_with_no_matching_call_still_has_an_id(self):
        client = _client()
        messages = client.new_conversation("go")
        client.append_tool_results(messages, [("video_search", "7 videos")])
        assert messages[-1]["tool_call_id"] == "call_video_search"

    def test_claude_shaped_messages_convert_to_openai_shape(self):
        client = _client()
        converted = client.convert_messages_to_gemini(
            [
                {"role": "user", "content": "find ego cooking"},
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "searching"},
                        {"type": "tool_use", "name": "video_search", "input": {"q": "ego"}},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "name": "video_search", "content": "7 videos"}
                    ],
                },
            ]
        )
        assert converted[0] == {"role": "user", "content": "find ego cooking"}
        assistant = converted[1]
        assert assistant["role"] == "assistant"
        assert json.loads(assistant["tool_calls"][0]["function"]["arguments"]) == {"q": "ego"}
        # The result is matched to the id of the call it answers.
        assert converted[2]["tool_call_id"] == assistant["tool_calls"][0]["id"]

    def test_tool_definitions_convert_to_function_tools(self):
        tools = _client().convert_tool_definitions(
            [
                {
                    "name": "video_search",
                    "description": "search",
                    "input_schema": {"type": "object", "properties": {}},
                }
            ]
        )
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "video_search"

    def test_a_tool_definition_without_a_schema_still_has_parameters(self):
        tools = _client().convert_tool_definitions([{"name": "t"}])
        assert tools[0]["function"]["parameters"] == {"type": "object", "properties": {}}

    def test_error_results_are_marked_as_errors(self):
        formatted = _client().format_tool_result("t", "quota exceeded", is_error=True)
        assert formatted == {
            "type": "tool_result",
            "name": "t",
            "content": "Error: quota exceeded",
        }


class TestErrors:
    class _Response:
        def __init__(self, status_code: int, payload: Any = None, text: str = ""):
            self.status_code = status_code
            self._payload = payload
            self.text = text or json.dumps(payload)

        def json(self) -> Any:
            if self._payload is None:
                raise ValueError("not json")
            return self._payload

    def test_an_http_error_says_what_came_back(self):
        with pytest.raises(OpenRouterError, match="401"):
            OpenRouterClient._parse(self._Response(401, {"error": "no"}))

    def test_a_provider_error_inside_a_200_is_still_an_error(self):
        with pytest.raises(OpenRouterError, match="model is overloaded"):
            OpenRouterClient._parse(
                self._Response(200, {"error": {"message": "model is overloaded"}})
            )

    def test_a_non_json_body_is_an_error(self):
        with pytest.raises(OpenRouterError, match="non-JSON"):
            OpenRouterClient._parse(self._Response(200, None, text="<html>"))


class TestProviderChoice:
    def test_openrouter_is_chosen_when_its_key_is_set(self, monkeypatch):
        from video_searching_agent.config import settings as settings_module

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        settings_module.get_settings.cache_clear()
        try:
            from video_searching_agent.api.llm import get_llm_client, llm_label

            assert isinstance(get_llm_client(), OpenRouterClient)
            assert "openrouter" in llm_label()
        finally:
            settings_module.get_settings.cache_clear()

    def test_the_provider_can_be_forced_to_gemini(self, monkeypatch):
        from video_searching_agent.config import settings as settings_module

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        settings_module.get_settings.cache_clear()
        try:
            from video_searching_agent.api.gemini_client import GeminiClient
            from video_searching_agent.api.llm import get_llm_client

            assert isinstance(get_llm_client(), GeminiClient)
        finally:
            settings_module.get_settings.cache_clear()

    def test_a_google_key_is_not_handed_to_openrouter(self, monkeypatch):
        from video_searching_agent.config import settings as settings_module

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        settings_module.get_settings.cache_clear()
        try:
            from video_searching_agent.api.llm import get_llm_client

            client = get_llm_client(google_api_key="google-key")
            assert client.api_key == "sk-or-test"
        finally:
            settings_module.get_settings.cache_clear()
