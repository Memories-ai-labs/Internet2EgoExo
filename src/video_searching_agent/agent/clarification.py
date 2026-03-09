"""Clarification flow management for ambiguous queries per PRD."""

from typing import Any

from video_searching_agent.models.query import ParsedQuery, QueryType, TimeFrame


class ClarificationManager:
    """Manages clarification flow when queries are ambiguous.

    Per PRD, clarification is triggered when:
    - Intent is ambiguous (e.g., "what's trending?")
    - Missing required platform for platform-specific queries
    - Conflicting slot values
    - Low confidence extraction
    """

    # Threshold for triggering clarification
    CONFIDENCE_THRESHOLD = 0.5

    # Query types that typically need platform specification
    PLATFORM_SENSITIVE_TYPES = {
        QueryType.INDUSTRY_TOPIC,
        QueryType.CREATOR_DISCOVERY,
        QueryType.BRAND_ANALYSIS,
    }

    def needs_clarification(self, parsed_query: ParsedQuery) -> bool:
        """Determine if the query needs user clarification.

        Args:
            parsed_query: Parsed query with extraction results.

        Returns:
            True if clarification is needed.
        """
        # Check if already flagged by parser
        if parsed_query.needs_clarification:
            return True

        # Check overall confidence
        overall_confidence = parsed_query.extraction_confidence.get("overall", 1.0)
        if overall_confidence < self.CONFIDENCE_THRESHOLD:
            return True

        # Check for ambiguous query type
        if parsed_query.query_type == QueryType.GENERAL:
            # General type with no clear entities is ambiguous
            if not (
                parsed_query.creators
                or parsed_query.brands
                or parsed_query.hashtags
                or parsed_query.topics
                or parsed_query.video_category
            ):
                return True

        # Check for platform-sensitive query without platform
        if (
            parsed_query.query_type in self.PLATFORM_SENSITIVE_TYPES
            and not parsed_query.platforms
        ):
            # Only clarify if no other strong signals
            if not (
                parsed_query.creators
                or parsed_query.hashtags
                or parsed_query.topics
                or parsed_query.video_category
            ):
                return True

        return False

    def generate_clarification_question(self, parsed_query: ParsedQuery) -> str:
        """Generate a clarification question based on what's missing/ambiguous.

        Args:
            parsed_query: Parsed query needing clarification.

        Returns:
            Clarification question string.
        """
        # If parser already has a reason, use it
        if parsed_query.clarification_reason:
            return parsed_query.clarification_reason

        # Generate based on what's missing
        questions = []

        # Check query type ambiguity
        if parsed_query.query_type == QueryType.GENERAL:
            questions.append(
                "What type of video content are you looking for? "
                "(trending topics, specific creator analysis, brand comparison, etc.)"
            )

        # Check platform specification
        if (
            parsed_query.query_type in self.PLATFORM_SENSITIVE_TYPES
            and not parsed_query.platforms
        ):
            questions.append(
                "Which platform(s) should I search? "
                "(YouTube, TikTok, Instagram, Twitter, or all)"
            )

        # Check if very short/vague query
        if len(parsed_query.original_query.split()) < 3:
            if not questions:
                questions.append(
                    "Could you provide more details about what you're looking for?"
                )

        if questions:
            return " ".join(questions)

        # Default clarification
        return (
            "I want to make sure I understand your request correctly. "
            "Could you provide more details about what video content you're looking for?"
        )

    def generate_clarification_options(
        self, parsed_query: ParsedQuery
    ) -> dict[str, Any] | None:
        """Generate structured options for clarification.

        Args:
            parsed_query: Parsed query needing clarification.

        Returns:
            Dict with options for different clarification needs, or None.
        """
        options = {}

        # Query type options
        if parsed_query.query_type == QueryType.GENERAL:
            options["query_type"] = {
                "question": "What type of search are you looking for?",
                "choices": [
                    {"value": "trending", "label": "Trending/viral videos"},
                    {"value": "creator", "label": "Creator/influencer analysis"},
                    {"value": "brand", "label": "Brand content analysis"},
                    {"value": "comparison", "label": "Compare brands/creators"},
                ],
            }

        # Platform options
        if (
            parsed_query.query_type in self.PLATFORM_SENSITIVE_TYPES
            and not parsed_query.platforms
        ):
            options["platform"] = {
                "question": "Which platform(s) should I search?",
                "choices": [
                    {"value": "all", "label": "All platforms"},
                    {"value": "youtube", "label": "YouTube"},
                    {"value": "tiktok", "label": "TikTok"},
                    {"value": "instagram", "label": "Instagram"},
                    {"value": "twitter", "label": "Twitter/X"},
                    {"value": "web", "label": "Web (blogs, Vimeo, news)"},
                ],
                "multi_select": True,  # type: ignore[dict-item]
            }

        # Time frame options if not specified
        if parsed_query.time_frame == TimeFrame.PAST_WEEK:
            # Default was used, might want to clarify
            options["time_frame"] = {
                "question": "What time period?",
                "choices": [
                    {"value": "past_24_hours", "label": "Past 24 hours"},
                    {"value": "past_48_hours", "label": "Past 48 hours"},
                    {"value": "past_week", "label": "Past week"},
                    {"value": "past_month", "label": "Past month"},
                ],
            }

        return options if options else None

    def apply_clarification(
        self,
        parsed_query: ParsedQuery,
        clarification_response: str,
    ) -> ParsedQuery:
        """Apply user's clarification to update the parsed query.

        This method parses the user's clarification response and updates
        the ParsedQuery accordingly.

        Args:
            parsed_query: Original parsed query.
            clarification_response: User's response to clarification question.

        Returns:
            Updated ParsedQuery with clarification applied.
        """
        response_lower = clarification_response.lower()

        # Update platforms if mentioned
        platform_keywords = {
            "youtube": ["youtube", "yt"],
            "tiktok": ["tiktok", "tik tok"],
            "instagram": ["instagram", "ig", "reels"],
            "twitter": ["twitter", "x.com", "tweet"],
            "web": ["web", "vimeo", "blog", "news", "article", "podcast"],
        }

        new_platforms = list(parsed_query.platforms)
        if "all" in response_lower:
            new_platforms = ["youtube", "tiktok", "instagram", "twitter"]
        else:
            for platform, keywords in platform_keywords.items():
                if any(kw in response_lower for kw in keywords):
                    if platform not in new_platforms:
                        new_platforms.append(platform)

        # Update query type if mentioned
        query_type = parsed_query.query_type
        if "trend" in response_lower or "viral" in response_lower:
            query_type = QueryType.INDUSTRY_TOPIC
        elif "creator" in response_lower or "influencer" in response_lower:
            query_type = QueryType.CREATOR_DISCOVERY
        elif "brand" in response_lower:
            query_type = QueryType.BRAND_ANALYSIS
        elif "compar" in response_lower:
            query_type = QueryType.COMPARISON

        # Update time frame if mentioned
        time_frame = parsed_query.time_frame
        if "24 hour" in response_lower or "today" in response_lower:
            time_frame = TimeFrame.PAST_24_HOURS
        elif "48 hour" in response_lower:
            time_frame = TimeFrame.PAST_48_HOURS
        elif "week" in response_lower:
            time_frame = TimeFrame.PAST_WEEK
        elif "month" in response_lower:
            time_frame = TimeFrame.PAST_MONTH

        # Create updated query
        updated = ParsedQuery(
            original_query=parsed_query.original_query,
            query_type=query_type,
            video_category=parsed_query.video_category,
            topics=parsed_query.topics,
            hashtags=parsed_query.hashtags,
            creators=parsed_query.creators,
            brands=parsed_query.brands,
            products=parsed_query.products,
            platforms=new_platforms,
            metric=parsed_query.metric,
            time_frame=time_frame,
            time_range=parsed_query.time_range,
            quantity=parsed_query.quantity,
            language=parsed_query.language,
            sort_order=parsed_query.sort_order,
            is_comparison=parsed_query.is_comparison,
            comparison_entities=parsed_query.comparison_entities,
            needs_video_analysis=parsed_query.needs_video_analysis,
            extraction_confidence={"overall": 0.8},  # Improved confidence after clarification
            needs_clarification=False,
            clarification_reason=None,
        )

        return updated

    def build_clarification_response(
        self,
        parsed_query: ParsedQuery,
        include_options: bool = True,
    ) -> dict[str, Any]:
        """Build a structured clarification response.

        Args:
            parsed_query: Parsed query needing clarification.
            include_options: Whether to include structured options.

        Returns:
            Dict with clarification question and optional choices.
        """
        response = {
            "needs_clarification": True,
            "question": self.generate_clarification_question(parsed_query),
            "understood_so_far": {
                "query_type": parsed_query.query_type.value,
                "platforms": parsed_query.platforms,
                "topics": parsed_query.topics,
                "hashtags": parsed_query.hashtags,
                "creators": parsed_query.creators,
            },
        }

        if include_options:
            options = self.generate_clarification_options(parsed_query)
            if options:
                response["options"] = options

        return response
