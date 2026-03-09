"""Apify API client for running actors and fetching results."""

import asyncio
import logging
import re
from typing import Any, cast

import httpx

from video_searching_agent.config.settings import get_settings

logger = logging.getLogger(__name__)


class ApifyClient:
    """Wrapper for Apify API to run actors and fetch results.

    Apify provides maintained actors for scraping social media platforms
    with anti-bot/proxy handling built-in.
    """

    # Actor IDs for each platform
    ACTORS = {
        "tiktok": "clockworks/tiktok-scraper",
        "instagram": "apify/instagram-scraper",
        "twitter": "apidojo/tweet-scraper",
    }

    def __init__(self, api_token: str | None = None):
        """Initialize Apify client.

        Args:
            api_token: Apify API token. Defaults to settings.
        """
        settings = get_settings()
        self.api_token = api_token or settings.apify_api_token
        self.base_url = "https://api.apify.com/v2"
        self.timeout = settings.api_timeout_seconds
        self._clients: dict[float, tuple[httpx.AsyncClient, Any]] = {}
        self._client_lock = asyncio.Lock()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def _get_client(self, timeout: float) -> Any:
        """Get or create a shared AsyncClient for the given timeout."""
        key = float(timeout)
        existing = self._clients.get(key)
        if existing is not None:
            return existing[1]

        async with self._client_lock:
            existing = self._clients.get(key)
            if existing is not None:
                return existing[1]

            raw_client = httpx.AsyncClient(timeout=timeout)
            enter = getattr(raw_client, "__aenter__", None)
            if callable(enter):
                entered = enter()
                active_client = await entered if asyncio.iscoroutine(entered) else entered
            else:
                active_client = raw_client
            self._clients[key] = (raw_client, active_client)
            return active_client

    async def aclose(self) -> None:
        """Close all shared clients."""
        async with self._client_lock:
            clients = list(self._clients.values())
            self._clients.clear()

        for raw_client, _ in clients:
            if hasattr(raw_client, "aclose"):
                await raw_client.aclose()

    async def run_actor(
        self,
        actor_id: str,
        input_data: dict[str, Any],
        timeout_secs: int = 120,
        memory_mbytes: int = 1024,
    ) -> list[dict[str, Any]]:
        """Run an Apify actor and wait for results.

        Args:
            actor_id: Actor ID (e.g., "clockworks/tiktok-scraper").
            input_data: Input parameters for the actor.
            timeout_secs: Maximum run time in seconds.
            memory_mbytes: Memory allocation for the actor.

        Returns:
            Dataset items from the actor run.

        Raises:
            ValueError: If API token is not configured.
            httpx.HTTPError: If API request fails.
        """
        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN is required for Apify actors")

        # Convert actor_id format from "username/actor" to "username~actor" for API URL
        api_actor_id = actor_id.replace("/", "~")
        url = f"{self.base_url}/acts/{api_actor_id}/run-sync-get-dataset-items"
        params = {
            "timeout": timeout_secs,
            "memory": memory_mbytes,
        }

        client = await self._get_client(timeout_secs + 30)
        response = await client.post(
            url,
            headers=self._get_headers(),
            params=params,
            json=input_data,
        )
        if not response.is_success:
            error_detail = response.text
            logger.error(f"Apify API error {response.status_code}: {error_detail}")
            logger.error(f"Request input_data: {input_data}")
        response.raise_for_status()
        return cast(list[dict[str, Any]], response.json())

    async def run_actor_async(
        self,
        actor_id: str,
        input_data: dict[str, Any],
        memory_mbytes: int = 1024,
    ) -> str:
        """Start an Apify actor run without waiting for completion.

        Args:
            actor_id: Actor ID.
            input_data: Input parameters for the actor.
            memory_mbytes: Memory allocation for the actor.

        Returns:
            Run ID for polling status.

        Raises:
            ValueError: If API token is not configured.
            httpx.HTTPError: If API request fails.
        """
        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN is required for Apify actors")

        # Convert actor_id format from "username/actor" to "username~actor" for API URL
        api_actor_id = actor_id.replace("/", "~")
        url = f"{self.base_url}/acts/{api_actor_id}/runs"
        params = {"memory": memory_mbytes}

        client = await self._get_client(float(self.timeout))
        response = await client.post(
            url,
            headers=self._get_headers(),
            params=params,
            json=input_data,
        )
        response.raise_for_status()
        return cast(str, response.json()["data"]["id"])

    async def get_run_status(self, run_id: str) -> dict[str, Any]:
        """Get the status of an actor run.

        Args:
            run_id: The run ID to check.

        Returns:
            Run status information.
        """
        url = f"{self.base_url}/actor-runs/{run_id}"

        client = await self._get_client(float(self.timeout))
        response = await client.get(url, headers=self._get_headers())
        response.raise_for_status()
        return cast(dict[str, Any], response.json()["data"])

    async def get_dataset_items(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Fetch items from an Apify dataset.

        Args:
            dataset_id: Dataset ID from an actor run.
            limit: Maximum items to fetch.
            offset: Starting offset for pagination.

        Returns:
            List of dataset items.
        """
        url = f"{self.base_url}/datasets/{dataset_id}/items"
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
            "format": "json",
        }

        client = await self._get_client(float(self.timeout))
        response = await client.get(
            url,
            headers=self._get_headers(),
            params=params,
        )
        response.raise_for_status()
        return cast(list[dict[str, Any]], response.json())

    async def scrape_tiktok(
        self,
        query: str | None = None,
        hashtag: str | None = None,
        username: str | None = None,
        urls: list[str] | None = None,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """Scrape TikTok using the Apify actor.

        Args:
            query: Search query for keyword search.
            hashtag: Hashtag to scrape (without #).
            username: Creator username to scrape (without @).
            urls: Specific TikTok URLs to scrape.
            max_results: Maximum results to return.

        Returns:
            List of TikTok video data.
        """
        input_data: dict[str, Any] = {
            "resultsPerPage": max_results,
        }

        # Determine search type and build input
        if urls:
            input_data["postURLs"] = urls
        elif username:
            input_data["profiles"] = [username.lstrip("@")]
            input_data["resultsPerPage"] = max_results
        elif hashtag:
            input_data["hashtags"] = [hashtag.lstrip("#")]
        elif query:
            input_data["searchQueries"] = [query]
        else:
            raise ValueError("Must provide query, hashtag, username, or urls")

        return await self.run_actor(
            self.ACTORS["tiktok"],
            input_data,
            timeout_secs=120,
        )

    async def scrape_instagram(
        self,
        query: str | None = None,
        hashtag: str | None = None,
        username: str | None = None,
        urls: list[str] | None = None,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """Scrape Instagram using the Apify actor.

        Args:
            query: Search query for keyword search.
            hashtag: Hashtag to scrape (without #).
            username: Creator username to scrape (without @).
            urls: Specific Instagram URLs to scrape.
            max_results: Maximum results to return.

        Returns:
            List of Instagram post/reel data.
        """
        input_data: dict[str, Any] = {
            "resultsLimit": max_results,
        }

        # Determine search type and build input using directUrls
        # The apify/instagram-scraper actor requires directUrls with full
        # Instagram URLs rather than separate hashtags/usernames fields.
        if urls:
            input_data["directUrls"] = urls
        elif username:
            clean = self._sanitize_username(username)
            if not clean:
                raise ValueError("Instagram username is invalid")
            input_data["directUrls"] = [f"https://www.instagram.com/{clean}/"]
            input_data["resultsType"] = "posts"
        elif hashtag:
            clean = self._sanitize_hashtag(hashtag)
            if not clean:
                raise ValueError("Instagram hashtag is invalid")
            input_data["directUrls"] = [f"https://www.instagram.com/explore/tags/{clean}/"]
            input_data["resultsType"] = "posts"
        elif query:
            # Instagram doesn't have keyword search, use hashtag explore page
            clean = self._sanitize_hashtag(query)
            if not clean:
                raise ValueError("Instagram query does not contain a valid hashtag token")
            input_data["directUrls"] = [f"https://www.instagram.com/explore/tags/{clean}/"]
            input_data["resultsType"] = "posts"
        else:
            raise ValueError("Must provide query, hashtag, username, or urls")

        return await self.run_actor(
            self.ACTORS["instagram"],
            input_data,
            timeout_secs=120,
        )

    @staticmethod
    def _sanitize_hashtag(value: str) -> str:
        cleaned = value.lstrip("#").strip()
        return re.sub(r"[^\w]", "", cleaned, flags=re.UNICODE)

    @staticmethod
    def _sanitize_username(value: str) -> str:
        cleaned = value.lstrip("@").strip()
        return re.sub(r"[^\w.]", "", cleaned, flags=re.UNICODE)

    async def scrape_twitter(
        self,
        query: str | None = None,
        hashtag: str | None = None,
        username: str | None = None,
        urls: list[str] | None = None,
        max_results: int = 20,
        sort: str = "Top",
    ) -> list[dict[str, Any]]:
        """Scrape Twitter/X using the Apify actor.

        Args:
            query: Search query for keyword search.
            hashtag: Hashtag to scrape (without #).
            username: Creator username to scrape (without @).
            urls: Specific Twitter URLs to scrape.
            max_results: Maximum results to return.
            sort: Sort order for search results - "Top" (default) or "Latest".

        Returns:
            List of Twitter post data.
        """
        input_data: dict[str, Any] = {
            "maxItems": max_results,
            "includeSearchTerms": False,
        }

        # Determine search type and build input
        if urls:
            input_data["startUrls"] = [{"url": url} for url in urls]
        elif username:
            input_data["startUrls"] = [
                {"url": f"https://twitter.com/{username.lstrip('@')}"}
            ]
            input_data["tweetsDesired"] = max_results
        elif hashtag:
            search_term = f"#{hashtag.lstrip('#')}"
            input_data["searchTerms"] = [search_term]
            input_data["sort"] = sort
        elif query:
            # For video content, add filter:videos
            input_data["searchTerms"] = [f"{query} filter:videos"]
            input_data["sort"] = sort
        else:
            raise ValueError("Must provide query, hashtag, username, or urls")

        return await self.run_actor(
            self.ACTORS["twitter"],
            input_data,
            timeout_secs=120,
        )

    async def scrape_urls(
        self,
        urls: list[str],
        platform: str,
    ) -> list[dict[str, Any]]:
        """Scrape specific URLs from a platform.

        Args:
            urls: List of URLs to scrape.
            platform: Platform name (tiktok, instagram, twitter).

        Returns:
            List of scraped content data.
        """
        platform = platform.lower()

        if platform == "tiktok":
            return await self.scrape_tiktok(urls=urls)
        elif platform == "instagram":
            return await self.scrape_instagram(urls=urls)
        elif platform == "twitter":
            return await self.scrape_twitter(urls=urls)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
