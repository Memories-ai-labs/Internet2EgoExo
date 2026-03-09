"""LLM-first slot extraction for user queries per PRD requirements."""

import json
import re
from typing import Any

from video_searching_agent.api.gemini_client import GeminiClient
from video_searching_agent.models.query import (
    MetricType,
    ParsedQuery,
    QueryType,
    SortOrder,
    TimeFrame,
)

# LLM prompt for slot extraction
SLOT_EXTRACTION_PROMPT = """You are a slot extraction system for a video search agent.
Extract structured information from the user's query and return a JSON object.

## Slots to Extract

- **query_type**: One of: industry_topic, brand_analysis, product_search,
  creator_profile, creator_discovery, comparison, channel_analysis,
  video_analysis, creative_inspiration, general
- **video_category**: Industry/brand/product category
  (e.g., "Technology", "Beauty", "Food", "AI Art")
- **topics**: List of specific keywords or topic phrases
- **hashtags**: List of hashtags (with or without #)
- **creators**: List of creator handles/usernames (with or without @)
- **brands**: List of brand names mentioned
- **products**: List of product names mentioned
- **platforms**: List of target platforms (youtube, tiktok, instagram,
  twitter, web). Use "web" for queries about blogs, Vimeo, news sites,
  podcasts, or general web search.
- **metric**: Sorting metric - one of: most_popular, fastest_growth_views,
  highest_engagement, most_liked, most_commented, most_shared, most_recent
- **time_frame**: Time range - one of: past_24_hours, past_48_hours,
  past_week, past_month, past_year, all_time
- **quantity**: Number of results requested (integer, default 10)
- **language**: Content language (ISO code, e.g., "en", "zh-CN")
- **sort_order**: "desc" or "asc" (default "desc")
- **is_comparison**: Boolean - is this a comparison query?
- **comparison_entities**: List of entities being compared
- **needs_video_analysis**: Boolean - does this need deep video content analysis?
- **confidence**: A confidence score from 0-1 for the overall extraction

## Rules

1. If a slot is not mentioned or unclear, omit it from the response
2. For platforms, only include if explicitly mentioned or strongly implied
3. For metric, infer from context:
   - "trending", "viral", "popular" → most_popular
   - "fastest growing", "blowing up" → fastest_growth_views
   - "best engagement", "most engaging" → highest_engagement
4. For time_frame, ALWAYS infer based on context (do not leave empty):
   - "today", "24 hours", "just happened", "breaking" → past_24_hours
   - "48 hours", "2 days" → past_48_hours
   - "this week", "trending", "viral", "what's hot", "buzzing" → past_week
   - "this month", "recent", "latest", "new" → past_month
   - "this year" → past_year
   - "best", "top", "all time", "ever" → all_time
   - If no time signals present, default to past_year
5. Extract exact numbers for quantity (e.g., "top 20" → 20, "give me 15" → 15)
6. For creators, remove @ prefix in the response
7. For hashtags, remove # prefix in the response

## Response Format

Return ONLY a valid JSON object, no explanation or markdown.

Example response:
{
  "query_type": "industry_topic",
  "video_category": "Beauty",
  "topics": ["ASMR", "makeup tutorial"],
  "hashtags": ["ASMRbeauty", "MakeupASMR"],
  "platforms": ["tiktok", "instagram"],
  "metric": "most_popular",
  "time_frame": "past_week",
  "quantity": 10,
  "confidence": 0.9
}

## User Query

"""


class QueryParser:
    """LLM-first slot extraction for video search queries."""

    def __init__(self, gemini_client: GeminiClient | None = None):
        """Initialize the query parser.

        Args:
            gemini_client: Gemini client for LLM extraction. Creates new if None.
        """
        self.gemini = gemini_client or GeminiClient()

    async def parse(self, query: str) -> ParsedQuery:
        """Parse a user query and extract all PRD-defined slots.

        Uses LLM-first approach for maximum accuracy.

        Args:
            query: User's natural language query.

        Returns:
            ParsedQuery with extracted slots and confidence scores.
        """
        try:
            # Use Gemini for slot extraction
            prompt = SLOT_EXTRACTION_PROMPT + query
            messages = self.gemini.convert_messages_to_gemini(
                [{"role": "user", "content": prompt}]
            )
            response = await self.gemini.create_message_async(
                messages=messages,
                max_tokens=1024,
            )

            text = self.gemini.get_text_response(response)
            if text:
                parsed = self._parse_extraction_response(text, query)
                # Add local regex extraction as fallback/enhancement
                parsed = self._enhance_with_local_extraction(parsed, query)
                parsed = self._apply_video_analysis_guard(parsed, query)
                return parsed

        except Exception:
            # Fall back to local-only extraction on error
            pass

        # Fallback to local extraction
        return self._apply_video_analysis_guard(self._local_extraction(query), query)

    def _parse_extraction_response(self, text: str, original_query: str) -> ParsedQuery:
        """Parse Gemini's slot extraction response.

        Args:
            text: Gemini's response text (should be JSON).
            original_query: Original user query.

        Returns:
            ParsedQuery from extraction.
        """
        # Extract JSON from response
        json_match = re.search(r"\{[\s\S]*\}", text)
        if not json_match:
            return ParsedQuery(original_query=original_query)

        try:
            data = json.loads(json_match.group())
            return self._build_parsed_query(data, original_query)
        except json.JSONDecodeError:
            return ParsedQuery(original_query=original_query)

    def _build_parsed_query(self, data: dict[str, Any], original_query: str) -> ParsedQuery:
        """Build ParsedQuery from extracted JSON data.

        Args:
            data: Extracted slot data.
            original_query: Original user query.

        Returns:
            ParsedQuery object.
        """
        # Map query_type string to enum
        query_type = self._map_query_type(data.get("query_type", "general"))

        # Map metric string to enum
        metric = self._map_metric(data.get("metric", "most_popular"))

        # Map time_frame string to enum
        time_frame = self._map_time_frame(data.get("time_frame", "past_year"))

        # Map sort_order string to enum
        sort_order = self._map_sort_order(data.get("sort_order", "desc"))

        # Build confidence dict
        confidence = data.get("confidence", 0.8)
        extraction_confidence = {
            "overall": confidence,
            "query_type": confidence,
            "slots": confidence,
        }

        # Check if clarification is needed
        needs_clarification = False
        clarification_reason = None

        # Trigger clarification for very ambiguous queries (only if no strong signals)
        topics = data.get("topics", [])
        creators = data.get("creators", [])
        hashtags = data.get("hashtags", [])
        brands = data.get("brands", [])
        has_strong_signals = topics or creators or hashtags or brands

        if query_type == QueryType.GENERAL and confidence < 0.6 and not has_strong_signals:
            needs_clarification = True
            clarification_reason = (
                "Query is ambiguous. What type of video content are "
                "you looking for?"
            )

        # Trigger clarification if no platform and query seems platform-specific
        platforms = data.get("platforms", [])
        if not platforms and data.get("query_type") in ["industry_topic", "creator_discovery"]:
            # Don't force clarification, but note low confidence
            extraction_confidence["platforms"] = 0.3

        return ParsedQuery(
            original_query=original_query,
            query_type=query_type,
            video_category=data.get("video_category"),
            topics=topics,
            hashtags=hashtags,
            creators=creators,
            brands=brands,
            products=data.get("products", []),
            platforms=platforms,
            metric=metric,
            time_frame=time_frame,
            time_range=data.get("time_frame"),  # Keep string version too
            quantity=data.get("quantity", 10),
            language=data.get("language"),
            sort_order=sort_order,
            is_comparison=data.get("is_comparison", False),
            comparison_entities=data.get("comparison_entities", []),
            needs_video_analysis=data.get("needs_video_analysis", False),
            extraction_confidence=extraction_confidence,
            needs_clarification=needs_clarification,
            clarification_reason=clarification_reason,
        )

    def _map_query_type(self, value: str) -> QueryType:
        """Map string to QueryType enum."""
        try:
            return QueryType(value)
        except ValueError:
            return QueryType.GENERAL

    def _map_metric(self, value: str) -> MetricType:
        """Map string to MetricType enum."""
        try:
            return MetricType(value)
        except ValueError:
            return MetricType.MOST_POPULAR

    def _map_time_frame(self, value: str) -> TimeFrame:
        """Map string to TimeFrame enum."""
        try:
            return TimeFrame(value)
        except ValueError:
            return TimeFrame.PAST_YEAR

    def _map_sort_order(self, value: str) -> SortOrder:
        """Map string to SortOrder enum."""
        try:
            return SortOrder(value)
        except ValueError:
            return SortOrder.DESC

    def _local_extraction(self, query: str) -> ParsedQuery:
        """Fallback local extraction without LLM.

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
        platforms = self._detect_platforms(query_lower)

        # Detect query type
        query_type = self._detect_query_type(query_lower, creators)

        # Detect metric
        metric = self._detect_metric(query_lower)

        # Detect time frame
        time_frame = self._detect_time_frame(query_lower)

        # Detect quantity
        quantity = self._detect_quantity(query_lower)

        # Detect comparison
        is_comparison, comparison_entities = self._detect_comparison(query_lower)

        # Extract topics
        topics = self._extract_topics(query)

        return ParsedQuery(
            original_query=query,
            query_type=query_type,
            topics=topics,
            creators=creators,
            hashtags=hashtags,
            platforms=platforms,
            metric=metric,
            time_frame=time_frame,
            quantity=quantity,
            is_comparison=is_comparison,
            comparison_entities=comparison_entities,
            extraction_confidence={"overall": 0.5},  # Lower confidence for local
        )

    def _enhance_with_local_extraction(self, parsed: ParsedQuery, query: str) -> ParsedQuery:
        """Enhance LLM extraction with local regex patterns.

        Args:
            parsed: LLM-extracted ParsedQuery.
            query: Original query.

        Returns:
            Enhanced ParsedQuery.
        """
        # Extract any missed creators
        creators = set(parsed.creators)
        creators.update(re.findall(r"@(\w+)", query))
        parsed.creators = list(creators)

        # Extract any missed hashtags
        hashtags = set(parsed.hashtags)
        hashtags.update(re.findall(r"#(\w+)", query))
        parsed.hashtags = list(hashtags)

        # Extract any missed topics
        local_topics = self._extract_topics(query)
        topics = set(parsed.topics)
        topics.update(local_topics)
        parsed.topics = list(topics)

        # Validate quantity bounds
        parsed.quantity = max(1, min(parsed.quantity, 100))

        return parsed

    def _apply_video_analysis_guard(self, parsed: ParsedQuery, query: str) -> ParsedQuery:
        """Deterministically gate deep analysis to explicit video-analysis requests.

        This prevents broad discovery prompts from intermittently toggling
        `needs_video_analysis=True` due to LLM extraction variance.
        """
        query_lower = query.lower()

        extracted_urls = self._extract_urls(query)
        supported_video_urls = [
            url for url in extracted_urls if self._is_supported_video_url(url)
        ]
        parsed.video_urls = supported_video_urls

        has_any_url = bool(extracted_urls)
        has_supported_video_url = bool(supported_video_urls)
        llm_intent = (
            parsed.needs_video_analysis or parsed.query_type == QueryType.VIDEO_ANALYSIS
        )
        local_intent = any(
            phrase in query_lower
            for phrase in [
                "analyze",
                "analyse",
                "analysis",
                "transcript",
                "transcribe",
                "transcription",
                "summarize",
                "summarise",
                "summary",
                "key points",
                "highlights",
                "message",
                "messaging",
                "break down",
                "breakdown",
                "describe",
                "what happens",
                "what is shown",
                "what's in",
                "whats in",
                "what does this video say",
            ]
        )
        has_specific_video_reference = any(
            token in query_lower
            for token in [
                "this video",
                "that video",
                "this clip",
                "that clip",
                "this reel",
                "this short",
            ]
        )
        explicit_video_reference = has_specific_video_reference or has_supported_video_url
        unsupported_url_present = has_any_url and not has_supported_video_url
        has_discovery_link_intent = any(
            phrase in query_lower
            for phrase in [
                "find similar",
                "similar videos",
                "videos like",
                "find videos like",
                "related videos",
                "more videos like",
                "recommend videos",
            ]
        )

        if unsupported_url_present:
            # Prevent deep analysis for non-video links (e.g., blog/article URLs).
            parsed.needs_video_analysis = False
            if parsed.query_type == QueryType.VIDEO_ANALYSIS:
                parsed.query_type = QueryType.GENERAL
            return parsed

        if explicit_video_reference and (
            local_intent or (llm_intent and not has_discovery_link_intent)
        ):
            parsed.needs_video_analysis = True
            return parsed

        # Default discovery-safe behavior: do not enable deep analysis.
        parsed.needs_video_analysis = False
        if parsed.query_type == QueryType.VIDEO_ANALYSIS:
            parsed.query_type = QueryType.GENERAL

        return parsed

    def _extract_urls(self, query: str) -> list[str]:
        """Extract URLs from a query and normalize trailing punctuation.

        Supports both fully-qualified URLs (http/https) and common bare links
        like `youtube.com/watch?v=...`.
        """
        raw_urls = re.findall(
            r"(?:https?://)?(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s<>\"]*)?",
            query,
            flags=re.IGNORECASE,
        )
        seen: set[str] = set()
        normalized: list[str] = []
        for url in raw_urls:
            cleaned = url.rstrip(".,!?;:)]}'\"")
            if not cleaned:
                continue
            if not re.match(r"^https?://", cleaned, flags=re.IGNORECASE):
                cleaned = f"https://{cleaned}"
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                normalized.append(cleaned)
        return normalized

    def _is_supported_video_url(self, url: str) -> bool:
        """Check whether a URL is a supported social/video link.

        Supports:
        - Social video pages (YouTube/TikTok/Instagram/X)
        - Direct video files (.mp4, .webm, .mov, .avi, .mkv)
        """
        url_lower = url.lower()
        video_patterns = [
            r"(?:youtube\.com/watch\?v=|youtube\.com/shorts/|youtu\.be/)",
            r"(?:tiktok\.com/(?:.+/video/|t/)|(?:vm|vt)\.tiktok\.com/)",
            r"instagram\.com/(?:reel|reels)/",
            r"(?:twitter\.com|x\.com)/[^/]+/status/",
            r"\.(?:mp4|webm|mov|avi|mkv)(?:$|[?#])",
        ]
        return any(re.search(pattern, url_lower) for pattern in video_patterns)

    def _detect_platforms(self, query_lower: str) -> list[str]:
        """Detect platforms from query text."""
        platforms = []
        platform_keywords = {
            "youtube": ["youtube", "yt"],
            "tiktok": ["tiktok", "tik tok"],
            "instagram": ["instagram", "ig", "reels"],
            "twitter": ["twitter", "x.com", "tweet"],
            "web": [
                "vimeo", "dailymotion", "blog", "blogger", "medium.com",
                "podcast", "news site", "web search", "search the web",
                "article", "website",
            ],
        }
        for platform, keywords in platform_keywords.items():
            if any(kw in query_lower for kw in keywords):
                platforms.append(platform)
        return platforms

    def _detect_query_type(self, query_lower: str, creators: list[str]) -> QueryType:
        """Detect query type from query text."""
        if creators and any(
            phrase in query_lower for phrase in ["who is", "about @", "profile"]
        ):
            return QueryType.CREATOR_PROFILE

        if any(word in query_lower for word in ["vs", "versus", "compare"]):
            return QueryType.COMPARISON

        if any(word in query_lower for word in ["trending", "viral", "popular"]):
            return QueryType.INDUSTRY_TOPIC

        if any(phrase in query_lower for phrase in ["brand", "company"]):
            return QueryType.BRAND_ANALYSIS

        if any(word in query_lower for word in [
            "analyze", "breakdown", "break down", "transcribe", "transcription",
            "summary", "summarize", "highlights", "what's in", "whats in",
            "explain this video", "what does this video"
        ]):
            return QueryType.VIDEO_ANALYSIS

        return QueryType.GENERAL

    def _detect_metric(self, query_lower: str) -> MetricType:
        """Detect metric from query text."""
        if any(
            phrase in query_lower
            for phrase in ["fastest growing", "fastest-growing", "blowing up", "growth"]
        ):
            return MetricType.FASTEST_GROWTH_VIEWS

        if any(
            phrase in query_lower
            for phrase in ["most engaging", "highest engagement", "engagement"]
        ):
            return MetricType.HIGHEST_ENGAGEMENT

        if any(phrase in query_lower for phrase in ["most liked", "most likes"]):
            return MetricType.MOST_LIKED

        if any(phrase in query_lower for phrase in ["most recent", "newest", "latest"]):
            return MetricType.MOST_RECENT

        return MetricType.MOST_POPULAR

    def _detect_time_frame(self, query_lower: str) -> TimeFrame:
        """Detect time frame from query text."""
        if any(phrase in query_lower for phrase in [
            "24 hours", "today", "past day", "just happened", "breaking"
        ]):
            return TimeFrame.PAST_24_HOURS

        if any(phrase in query_lower for phrase in ["48 hours", "2 days"]):
            return TimeFrame.PAST_48_HOURS

        if any(phrase in query_lower for phrase in [
            "this week", "past week", "trending", "viral", "what's hot", "buzzing"
        ]):
            return TimeFrame.PAST_WEEK

        if any(phrase in query_lower for phrase in [
            "this month", "past month", "30 days", "recent", "latest", "new"
        ]):
            return TimeFrame.PAST_MONTH

        if any(phrase in query_lower for phrase in ["past year", "this year"]):
            return TimeFrame.PAST_YEAR

        if any(phrase in query_lower for phrase in ["best", "all time", "ever"]):
            return TimeFrame.ALL_TIME

        return TimeFrame.PAST_YEAR

    def _detect_quantity(self, query_lower: str) -> int:
        """Detect requested quantity from query text."""
        # Look for patterns like "top 20", "give me 15", "20 videos"
        patterns = [
            r"top\s+(\d+)",
            r"(\d+)\s+videos?",
            r"(\d+)\s+results?",
            r"give\s+me\s+(\d+)",
            r"find\s+(\d+)",
            r"show\s+(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return min(int(match.group(1)), 100)
        return 10

    def _detect_comparison(self, query_lower: str) -> tuple[bool, list[str]]:
        """Detect comparison and extract entities."""
        is_comparison = any(
            word in query_lower for word in ["vs", "versus", "compare", "vs."]
        )
        comparison_entities = []
        if is_comparison:
            vs_match = re.search(
                r"(\w+(?:\s+\w+)?)\s+(?:vs\.?|versus)\s+(\w+(?:\s+\w+)?)", query_lower
            )
            if vs_match:
                comparison_entities = [
                    vs_match.group(1).strip(),
                    vs_match.group(2).strip(),
                ]
        return is_comparison, comparison_entities

    def _extract_topics(self, query: str) -> list[str]:
        """Extract topic keywords from query text.

        Args:
            query: User's query.

        Returns:
            List of extracted topic keywords.
        """
        query_lower = query.lower()
        topics = []

        # Common stop words to filter out
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into", "through",
            "during", "before", "after", "above", "below", "between",
            "under", "again", "further", "then", "once", "here", "there",
            "when", "where", "why", "how", "all", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only",
            "own", "same", "so", "than", "too", "very", "just", "also",
            "now", "give", "me", "list", "find", "show", "get", "want",
            "looking", "search", "about", "especially", "particularly",
            "current", "currently", "famous", "best", "top", "new",
        }

        # Extract quoted phrases first
        quoted = re.findall(r'"([^"]+)"', query)
        topics.extend(quoted)

        # Extract acronyms (UGC, SaaS, B2B, etc.)
        acronyms = re.findall(r"\b([A-Z]{2,})\b", query)
        topics.extend([a.lower() for a in acronyms])

        # Common topic indicator patterns
        patterns = [
            r"(?:about|for|on|regarding)\s+([a-z]+(?:\s+[a-z]+)?)",
            r"([a-z]+)\s+(?:trends?|videos?|content|creators?)",
            r"(?:trends?|videos?|content)\s+(?:about|for|on|in)\s+([a-z]+(?:\s+[a-z]+)?)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                if match and match not in stop_words:
                    topics.append(match.strip())

        # Extract capitalized terms that might be proper nouns/topics
        capitalized = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", query)
        for term in capitalized:
            if term.lower() not in stop_words:
                topics.append(term.lower())

        # Look for compound terms like "saas products", "ugc trends"
        compound_patterns = [
            r"\b([a-z]+\s+products?)\b",
            r"\b([a-z]+\s+trends?)\b",
            r"\b([a-z]+\s+videos?)\b",
            r"\b([a-z]+\s+content)\b",
            r"\b([a-z]+\s+marketing)\b",
        ]
        for pattern in compound_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                if match and match.split()[0] not in stop_words:
                    topics.append(match.strip())

        # Deduplicate while preserving order
        seen = set()
        unique_topics = []
        for t in topics:
            t_clean = t.strip().lower()
            if t_clean and t_clean not in seen and t_clean not in stop_words:
                seen.add(t_clean)
                unique_topics.append(t_clean)

        return unique_topics
