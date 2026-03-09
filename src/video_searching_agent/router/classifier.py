"""Query classification using Claude."""

import json
import re

from video_searching_agent.agent.prompts import CLASSIFICATION_PROMPT
from video_searching_agent.api.gemini_client import GeminiClient
from video_searching_agent.models.query import ParsedQuery, QueryType


class QueryClassifier:
    """Classifies user queries and extracts structured information."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        """Initialize classifier.

        Args:
            gemini_client: Gemini client for classification. Creates new if None.
        """
        self.gemini = gemini_client or GeminiClient()

    async def classify(self, query: str) -> ParsedQuery:
        """Classify a user query and extract entities.

        Args:
            query: User's natural language query.

        Returns:
            ParsedQuery with classification and extracted entities.
        """
        # First, do quick local extraction
        local_result = self._local_extraction(query)

        # For simple cases, we might not need Claude
        if self._is_simple_query(local_result):
            return local_result

        # Use Gemini for complex classification
        try:
            prompt = CLASSIFICATION_PROMPT.format(query=query)
            messages = self.gemini.convert_messages_to_gemini(
                [{"role": "user", "content": prompt}]
            )
            response = await self.gemini.create_message_async(
                messages=messages,
                max_tokens=1024,
            )

            text = self.gemini.get_text_response(response)
            if text:
                parsed = self._parse_classification_response(text, query)
                # Merge with local extraction
                return self._merge_results(local_result, parsed)

        except Exception:
            # Fall back to local extraction
            pass

        return local_result

    def _local_extraction(self, query: str) -> ParsedQuery:
        """Perform local extraction without LLM.

        Args:
            query: User's query.

        Returns:
            ParsedQuery with locally extracted information.
        """
        query_lower = query.lower()

        # Extract creators (@username)
        creators = re.findall(r"@(\w+)", query)

        # Extract hashtags (#hashtag)
        hashtags = re.findall(r"#(\w+)", query)

        # Detect platforms
        platforms = []
        platform_keywords = {
            "youtube": ["youtube", "yt"],
            "tiktok": ["tiktok", "tik tok"],
            "instagram": ["instagram", "ig", "reels"],
            "twitter": ["twitter", "x.com", "tweet"],
            "facebook": ["facebook", "fb"],
        }
        for platform, keywords in platform_keywords.items():
            if any(kw in query_lower for kw in keywords):
                platforms.append(platform)

        # Detect query type
        query_type = self._detect_query_type(query_lower, creators)

        # Detect comparison
        is_comparison = any(
            word in query_lower for word in ["vs", "versus", "compare", "comparison", "vs."]
        )
        comparison_entities = []
        if is_comparison:
            # Simple extraction of entities around "vs"
            vs_match = re.search(
                r"(\w+(?:\s+\w+)?)\s+(?:vs\.?|versus)\s+(\w+(?:\s+\w+)?)",
                query_lower,
            )
            if vs_match:
                comparison_entities = [vs_match.group(1).strip(), vs_match.group(2).strip()]

        # Detect time range
        time_range = self._detect_time_range(query_lower)

        # Detect if video analysis is needed
        needs_video_analysis = any(
            phrase in query_lower
            for phrase in [
                "analyze this video",
                "watch this",
                "what happens in",
                "summarize this video",
                "transcribe",
            ]
        )

        return ParsedQuery(
            original_query=query,
            query_type=query_type,
            creators=creators,
            hashtags=hashtags,
            platforms=platforms,
            is_comparison=is_comparison,
            comparison_entities=comparison_entities,
            time_range=time_range,
            needs_video_analysis=needs_video_analysis,
        )

    def _detect_query_type(self, query_lower: str, creators: list[str]) -> QueryType:
        """Detect query type from query text.

        Args:
            query_lower: Lowercase query.
            creators: Extracted creator usernames.

        Returns:
            QueryType enum value.
        """
        # Creator profile
        if creators and any(
            phrase in query_lower
            for phrase in ["what type", "who is", "about @", "analyze @", "profile"]
        ):
            return QueryType.CREATOR_PROFILE

        # Creator discovery
        if any(
            phrase in query_lower
            for phrase in [
                "find creators",
                "popular bloggers",
                "top creators",
                "give me",
                "list of",
            ]
        ) and any(word in query_lower for word in ["blogger", "creator", "influencer", "channel"]):
            return QueryType.CREATOR_DISCOVERY

        # Brand analysis
        if any(
            phrase in query_lower
            for phrase in ["brand", "company", "analyze", "content from"]
        ):
            return QueryType.BRAND_ANALYSIS

        # Comparison
        if any(word in query_lower for word in ["vs", "versus", "compare"]):
            return QueryType.COMPARISON

        # Channel analysis
        if any(phrase in query_lower for phrase in ["channel", "@"]) and any(
            word in query_lower for word in ["analyze", "views", "content", "strategy"]
        ):
            return QueryType.CHANNEL_ANALYSIS

        # Video analysis
        if any(
            phrase in query_lower
            for phrase in [
                "this video",
                "analyze video",
                "watch",
                "summarize",
                "transcribe",
            ]
        ):
            return QueryType.VIDEO_ANALYSIS

        # Creative inspiration
        if any(
            phrase in query_lower
            for phrase in [
                "title",
                "script",
                "idea",
                "generate",
                "create content",
                "inspiration",
            ]
        ):
            return QueryType.CREATIVE_INSPIRATION

        # Product search
        if any(phrase in query_lower for phrase in ["product", "featuring", "about"]):
            return QueryType.PRODUCT_SEARCH

        # Industry/topic (default for trend queries)
        if any(
            word in query_lower
            for word in ["trending", "trend", "viral", "popular", "ugc", "niche"]
        ):
            return QueryType.INDUSTRY_TOPIC

        return QueryType.GENERAL

    def _detect_time_range(self, query_lower: str) -> str | None:
        """Detect time range from query.

        Args:
            query_lower: Lowercase query.

        Returns:
            Time range string or None.
        """
        time_patterns = {
            "past week": ["past week", "last week", "this week", "7 days"],
            "past month": ["past month", "last month", "this month", "30 days"],
            "past day": ["today", "past day", "last 24 hours", "yesterday"],
            "past year": ["past year", "last year", "this year", "2024", "2025"],
        }

        for time_range, patterns in time_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return time_range

        return None

    def _is_simple_query(self, parsed: ParsedQuery) -> bool:
        """Check if query is simple enough to skip LLM classification.

        Args:
            parsed: Locally parsed query.

        Returns:
            True if query is simple.
        """
        # If we extracted clear signals, we might not need LLM
        has_clear_type = parsed.query_type != QueryType.GENERAL
        has_platforms = len(parsed.platforms) > 0
        has_entities = (
            len(parsed.creators) > 0 or parsed.is_comparison or parsed.needs_video_analysis
        )

        return has_clear_type and (has_platforms or has_entities)

    def _parse_classification_response(self, text: str, original_query: str) -> ParsedQuery:
        """Parse Claude's classification response.

        Args:
            text: Claude's response text.
            original_query: Original user query.

        Returns:
            ParsedQuery from Claude's classification.
        """
        # Try to extract JSON from response
        json_match = re.search(r"\{[\s\S]*\}", text)
        if not json_match:
            return ParsedQuery(original_query=original_query)

        try:
            data = json.loads(json_match.group())

            # Map query type string to enum
            query_type_str = data.get("query_type", "general")
            try:
                query_type = QueryType(query_type_str)
            except ValueError:
                query_type = QueryType.GENERAL

            return ParsedQuery(
                original_query=original_query,
                query_type=query_type,
                platforms=data.get("platforms", []),
                brands=data.get("brands", []),
                creators=data.get("creators", []),
                products=data.get("products", []),
                topics=data.get("topics", []),
                hashtags=data.get("hashtags", []),
                time_range=data.get("time_range"),
                needs_video_analysis=data.get("needs_video_analysis", False),
                is_comparison=data.get("is_comparison", False),
                comparison_entities=data.get("comparison_entities", []),
            )

        except json.JSONDecodeError:
            return ParsedQuery(original_query=original_query)

    def _merge_results(self, local: ParsedQuery, llm: ParsedQuery) -> ParsedQuery:
        """Merge local extraction with LLM classification.

        Args:
            local: Locally extracted result.
            llm: LLM classification result.

        Returns:
            Merged ParsedQuery.
        """
        # Prefer LLM classification but keep local extractions
        return ParsedQuery(
            original_query=local.original_query,
            query_type=llm.query_type if llm.query_type != QueryType.GENERAL else local.query_type,
            platforms=list(set(local.platforms + llm.platforms)),
            brands=list(set(local.brands + llm.brands)),
            creators=list(set(local.creators + llm.creators)),
            products=list(set(local.products + llm.products)),
            topics=list(set(local.topics + llm.topics)),
            hashtags=list(set(local.hashtags + llm.hashtags)),
            time_range=llm.time_range or local.time_range,
            needs_video_analysis=llm.needs_video_analysis or local.needs_video_analysis,
            is_comparison=llm.is_comparison or local.is_comparison,
            comparison_entities=llm.comparison_entities or local.comparison_entities,
        )
