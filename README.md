# Video Searching Agent

AI-powered video searching agent that searches, analyzes, and sources videos from across the internet to answer user queries with video references.

## Features

- **Multi-Platform Search**: Search videos across YouTube, TikTok, Instagram, and Twitter/X
- **AI-Powered Analysis**: Uses Google Gemini to understand queries and orchestrate searches
- **Neural Web Search**: Discover videos across the web using Exa.ai neural search
- **Social Media Scraping**: Professional-grade scraping via Apify with anti-bot handling
- **Creator Analysis**: Get detailed insights about content creators
- **Trend Discovery**: Find trending videos in any niche or topic
- **Video Analysis**: Deep analysis using Memories.ai v2 for metadata, transcripts, MAI, and VLM
- **Comparison**: Compare brands, creators, or products side-by-side
- **Interactive Web UI**: Bundled zero-build UI with per-source selection and live streaming progress

## How It Works

The Video Searching Agent follows an **agentic loop pattern** where Google Gemini orchestrates which tools to call based on user queries. Here's the core flow:

### 1. Query Parsing (LLM-First Slot Extraction)

When you send a query, it first goes through the `QueryParser` which uses Gemini to extract structured **slots**:

```python
# Input: "Find the top 5 most liked TikTok videos about coffee from last week"
# Extracted slots:
ParsedQuery(
    platforms=["tiktok"],
    topics=["coffee"],
    metric=MetricType.MOST_LIKED,
    time_frame=TimeFrame.PAST_WEEK,
    quantity=5
)
```

### 2. The Agentic Loop

The agent runs an iterative loop (max 10 steps by default) where Gemini decides which tools to call:

```
┌─────────────────────────────────────────────────────────────┐
│  User Query + Extracted Slots                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Gemini: "I need to search TikTok for coffee videos"        │
│  → Returns function call: tiktok_search(query="coffee")     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ToolRegistry executes tiktok_search with RetryExecutor     │
│  → Results filtered by time_frame BEFORE returning          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Results fed back to Gemini                                 │
│  → Gemini decides: more tools needed? or final answer?      │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    (loop continues or...)
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Final Answer: Natural language response with video refs    │
└─────────────────────────────────────────────────────────────┘
```

### 3. Time Frame Filtering

A critical feature: tool results are filtered by `time_frame` **inside the loop** before Gemini sees them. This ensures accurate answers even when tools return older content.

### 4. Response Generation

The final `AgentResponse` includes:
- Natural language answer
- Video references with metadata and relevance notes
- Usage metrics (token counts, API costs)
- The parsed query with all extracted slots

## Installation

```bash
# Clone the repository
git clone https://github.com/Memories-ai-labs/video-searching-agent.git
cd video-searching-agent

# Install dependencies
pip install -e .

# Or with uv
uv pip install -e .
```

## Configuration

Create a `.env` file with your API keys:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key
YOUTUBE_API_KEY=your_youtube_data_api_key
MEMORIES_API_KEY=your_memories_ai_api_key
MEMORIES_BASE_URL=https://mavi-backend.memories.ai/serve/api/v2

# Optional
MEMORIES_DEFAULT_CHANNEL=memories.ai
MEMORIES_VLM_MODEL=gemini:gemini-3-flash-preview
EXA_API_KEY=your_exa_api_key
APIFY_API_TOKEN=your_apify_api_token
```

### Getting API Keys

1. **Google API Key** (required): Get your Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey)
2. **YouTube Data API Key** (required):
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a project and enable YouTube Data API v3
   - Create an API key
3. **Memories.ai API Key** (required): Sign up at [memories.ai](https://memories.ai)
4. **Exa.ai API Key** (optional): Sign up at [exa.ai](https://exa.ai) for neural web search
5. **Apify API Token** (optional): Sign up at [apify.com](https://apify.com) for TikTok/Instagram/Twitter scraping

## Quick Start

```python
import asyncio
from video_searching_agent import VideoSearchingAgent

async def main():
    # Initialize the agent
    agent = VideoSearchingAgent()

    # Simple query
    response = await agent.query(
        "What are the trending UGC videos for SaaS products?"
    )
    print(response.answer)

    # Show video references
    for ref in response.video_references:
        print(f"- {ref.title}: {ref.url}")

asyncio.run(main())
```

## Web UI

The package ships a zero-build web UI (plain HTML/CSS/JS, no npm, no bundler) served by
the API itself:

```bash
# Start the server (reads .env)
uvicorn video_searching_agent.web.main:app --port 8000
# or: python -m video_searching_agent.web.main
```

Open <http://localhost:8000> — `/` redirects to the UI at `/ui/`.

What it gives you:

- **Source selection** — pin the search to any combination of YouTube, TikTok, Instagram,
  X and the open web, or leave **Auto** on and let the agent infer sources from your query.
- **Live agent activity** — every step, tool call and tool failure streams in over SSE
  while the run is still going, so a long query is never a blank screen.
- **Video results** — thumbnail cards with platform, creator, duration, views, likes,
  comments, engagement rate and the agent's relevance note for each video.
- **Run stats** — steps, tools used, videos analysed, wall-clock time and the run's
  Gemini + tool cost in USD.
- **Clarification flow** — when the agent needs one more detail it asks inline; answer
  with a suggested option or in your own words and the query re-runs.
- **API key field** — only needed when the server sets `API_KEYS`. The key is kept in the
  browser's `localStorage` and sent as the `X-API-Key` header.

The UI is public (so it can load and ask for a key); `/api/v1/queries/*` stays behind
API-key auth and rate limiting.

The design language follows the memories.ai framework: Manrope, square corners, hairline
borders on a black canvas, with the violet accent ramp and one muted signal colour per
source.

## Streaming API

`POST /api/v1/queries/stream` runs a query and streams Server-Sent Events
(`started`, `progress`, `tool_call`, `tool_result`, `clarification_needed`,
`complete`, `error`):

```bash
curl -N http://localhost:8000/api/v1/queries/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
        "query": "Top latte art videos from the past week",
        "sources": ["youtube", "tiktok"]
      }'
```

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Natural language query (1-2000 chars) |
| `sources` | string[] | Pin the search to `youtube`, `tiktok`, `instagram`, `twitter`, `web`. Omit, send `[]`, or send `["auto"]` to let the agent choose. Aliases: `yt`, `x`, `ig`, `reels`, `exa` |
| `clarification` | string | Answer to a previous `clarification_needed` event |
| `max_steps` | int | Override the agent step budget (1-20) |
| `enable_clarification` | bool | Set `false` to never ask for clarification |

Pinned sources replace whatever platforms the query parser inferred, and the agent is told
to search only those.

## Usage Examples

### Find Trending Videos

```python
response = await agent.find_trending(
    topic="fitness",
    platform="youtube"
)
```

### Analyze a Creator

```python
response = await agent.analyze_creator(
    username="mkbhd",
    platform="youtube"
)
```

### Compare Brands

```python
response = await agent.compare(
    entities=["Nike", "Adidas"],
    platform="youtube"
)
```

### Analyze a Specific Video

```python
response = await agent.analyze_video(
    "https://www.youtube.com/watch?v=VIDEO_ID"
)
```

### Complex Query

```python
response = await agent.query("""
    Analyze the most viral food content on YouTube in 2025.
    What common patterns in hooks, opening techniques, and
    storytelling methods make food videos go viral?
""")
```

## Response Structure

```python
AgentResponse:
    session_id: str           # Unique session identifier
    query: str                # Original query
    answer: str               # Natural language answer
    video_references: list    # List of VideoReference objects
    platforms_searched: list  # Platforms that were searched
    total_videos_analyzed: int
    steps_taken: int          # Agent loop iterations
    tools_used: list          # Tools that were called
    execution_time_seconds: float

    # Extended fields
    usage_metrics: UsageMetrics   # Detailed cost tracking
    parsed_query: ParsedQuery     # Extracted slots from query
    tool_execution_details: list  # Success/failure for each tool call
    confidence_score: float       # Answer confidence (0-1)
    needs_clarification: bool     # Whether clarification is needed
    clarification_question: str   # Question to ask user if needed
```

### UsageMetrics Structure

```python
UsageMetrics:
    gemini: GeminiCost            # Gemini API costs
        token_usage: TokenUsage   # input_tokens, output_tokens, total_tokens
        input_cost_usd: float
        output_cost_usd: float
        total_cost_usd: float
    tool_costs: list[ToolUsageCost]  # Per-tool cost breakdown
    total_cost_usd: float         # Combined Gemini + tools cost
    gemini_calls: int             # Number of Gemini API calls
    tool_calls: int               # Total tool invocations
```

## Supported Query Types

| Type | Example |
|------|---------|
| Industry/Topic | "Trending UGC for SaaS" |
| Brand Analysis | "Analyze Sephora's video content" |
| Product Search | "Viral videos featuring mugs" |
| Creator Profile | "What type of blogger is @mkbhd?" |
| Creator Discovery | "Top 10 pet bloggers on YouTube" |
| Comparison | "Coca-Cola vs Pepsi on YouTube" |
| Channel Analysis | "What are @mkbhd's main views on tech trends?" |
| Video Analysis | "Analyze this video: [URL]" |
| Creative Inspiration | "Generate video title ideas for..." |

## Architecture

```
VideoSearchingAgent
    ├── GeminiClient (Google Gemini API)
    ├── QueryParser (LLM-first slot extraction)
    ├── ClarificationManager (handles missing context)
    ├── RetryExecutor (retry with exponential backoff + fallbacks)
    ├── ToolRegistry
    │   ├── YouTube: YouTubeSearchTool, YouTubeChannelTool
    │   ├── Exa: ExaSearchTool, ExaSimilarTool, ExaContentTool, ExaResearchTool
    │   ├── TikTok (Apify): TikTokSearchTool, TikTokCreatorTool
    │   ├── Instagram (Apify): InstagramSearchTool, InstagramCreatorTool
    │   ├── Twitter (Apify): TwitterSearchTool, TwitterProfileTool
    │   ├── Memories.ai v2: MetadataTool, TranscriptTool, MAITranscriptTool, VLMAnalysisTool
    │   └── Unified: VideoSearchTool
    └── AgentSession (tracks query lifecycle)
```

## Tools Reference

The agent has access to 17 specialized tools organized by category:

### YouTube Tools (2)

| Tool | Description |
|------|-------------|
| `youtube_search` | Search YouTube videos with filters (relevance, date, view count, rating) |
| `youtube_channel_info` | Get detailed channel information and recent videos |

### Exa.ai Tools (4)

| Tool | Description |
|------|-------------|
| `exa_search` | Neural web search to discover video content across the web |
| `exa_find_similar` | Find videos similar to a given URL |
| `exa_get_content` | Extract full content/text from web pages |
| `exa_research` | Deep research mode with multiple searches and synthesis |

### Apify Social Media Tools (6)

| Tool | Description |
|------|-------------|
| `tiktok_search` | Search TikTok videos by keyword, hashtag, or music |
| `tiktok_creator_info` | Get TikTok creator profile and recent videos |
| `instagram_search` | Search Instagram Reels and videos |
| `instagram_creator_info` | Get Instagram creator profile and content |
| `twitter_search` | Search Twitter/X for video tweets |
| `twitter_profile_info` | Get Twitter profile and video tweets |

### Memories.ai v2 Tools (4)

| Tool | Description |
|------|-------------|
| `social_media_metadata` | Extract metadata from any social media video URL |
| `social_media_transcript` | Get transcripts from video URLs |
| `social_media_mai_transcript` | Get AI-generated visual + audio transcript for social video URLs |
| `vlm_video_analysis` | Deep video analysis using Vision-Language Models |

### Unified Tools (1)

| Tool | Description |
|------|-------------|
| `video_search` | Unified search combining Exa discovery + Apify scraping |

## Query Slots

The agent extracts structured **slots** from natural language queries using LLM-first parsing. These slots control search behavior:

### Platform Slots

| Slot | Values | Description |
|------|--------|-------------|
| `platforms` | `youtube`, `tiktok`, `instagram`, `twitter` | Target platforms for search |

### Entity Slots

| Slot | Example | Description |
|------|---------|-------------|
| `topics` | `["coffee", "latte art"]` | Subject matter keywords |
| `brands` | `["Nike", "Adidas"]` | Brand names to search |
| `creators` | `["@mkbhd", "@charlidamelio"]` | Specific creators to find |
| `hashtags` | `["#fitness", "#workout"]` | Hashtags to search |
| `products` | `["iPhone 15", "AirPods"]` | Product names |

### Metric Slots

| Slot | Values | Description |
|------|--------|-------------|
| `metric` | `most_popular` (default) | Highest current views |
| | `fastest_growth_views` | View velocity / viral potential |
| | `highest_engagement` | Best engagement rate |
| | `most_liked` | Highest like count |
| | `most_commented` | Highest comment count |
| | `most_shared` | Highest share count |
| | `most_recent` | Most recently published |

### Time Frame Slots

| Slot | Values | Description |
|------|--------|-------------|
| `time_frame` | `past_24_hours` | Videos from last 24 hours |
| | `past_48_hours` | Videos from last 48 hours |
| | `past_week` (default) | Videos from last 7 days |
| | `past_month` | Videos from last 30 days |
| | `past_year` | Videos from last 365 days |
| | `all_time` | No time restriction |

### Quantity Slots

| Slot | Range | Description |
|------|-------|-------------|
| `quantity` | 1-100 (default: 10) | Number of videos to return |

## Data Models

### Core Entities

```python
Video:
    platform: Platform        # youtube, tiktok, instagram, twitter
    platform_id: str          # ID on source platform
    url: HttpUrl              # Direct video URL
    title: str | None
    creator: Creator | None
    metrics: VideoMetrics | None
    published_at: datetime | None
    hashtags: list[str]

Creator:
    username: str
    platform: Platform
    followers: int | None
    verified: bool
    total_videos: int | None

VideoMetrics:
    views: int | None
    likes: int | None
    comments: int | None
    shares: int | None
    engagement_rate: float | None  # Platform-specific calculation
```

### Query Models

```python
ParsedQuery:
    original_query: str
    query_type: QueryType     # industry_topic, brand_analysis, creator_profile, etc.
    platforms: list[str]
    topics: list[str]
    creators: list[str]
    metric: MetricType        # most_popular, highest_engagement, etc.
    time_frame: TimeFrame     # past_week, past_month, etc.
    quantity: int             # 1-100
    needs_clarification: bool

AgentSession:
    session_id: str
    user_query: str
    parsed_query: ParsedQuery | None
    current_step: int         # Current iteration in agentic loop
    max_steps: int            # Default: 10
    status: str               # initialized → running → completed/failed
    messages: list[dict]      # Conversation history for Gemini
```

## Retry & Fallback

The agent implements robust reliability features to achieve high success rates:

### Exponential Backoff

Tool failures are retried with exponential backoff:

```
Attempt 1 → fail → wait 1s
Attempt 2 → fail → wait 2s
Attempt 3 → fail → wait 4s
Attempt 4 → fail → wait 8s (capped at 30s max)
```

Configuration:
- `max_retries`: 3 (4 total attempts)
- `base_delay`: 1.0 seconds
- `max_delay`: 30.0 seconds
- `backoff_factor`: 2.0

### Retryable Errors

The system automatically retries on transient errors:
- Timeouts and connection errors
- Rate limits (429, "too many requests")
- Server errors (502, 503, 504)
- "Temporarily unavailable" responses

### Tool Fallback Chains

When a primary tool fails, the system tries fallback alternatives:

| Primary Tool | Fallback Tools |
|--------------|----------------|
| `twitter_search` | `exa_search` |
| `exa_find_similar` | `exa_search` |
| `exa_research` | `exa_search` |

TikTok and Instagram tools handle fallbacks internally (switching between API and scraping backends).

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/

# Type checking
mypy src/
```

## Project Structure

```
video-searching-agent/
├── src/video_searching_agent/
│   ├── agent/          # Core agent logic
│   ├── api/            # External API clients
│   ├── config/         # Configuration
│   ├── models/         # Pydantic data models
│   ├── router/         # Query classification
│   ├── tools/          # Gemini function calling tools
│   └── web/            # FastAPI app, SSE streaming, middleware
│       └── static/     # Zero-build web UI (index.html / styles.css / app.js)
├── examples/           # Usage examples
├── tests/              # Test suite
└── pyproject.toml      # Project configuration
```
