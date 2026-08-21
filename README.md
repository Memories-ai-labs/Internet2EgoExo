# Internet Video Search

An agent that finds, filters and documents video footage for model training —
**egocentric** (first-person, head or body mounted) and **exocentric**
(third-person, fixed camera, multi-view) — and reports what an hour of it costs.

Popularity is not a signal here. A 200-view head-mounted recording of someone
assembling a bicycle is worth more than a 10M-view edit of the same task, so
candidates are ranked by viewpoint match, clip length and licence — never by
views, likes or engagement.

## Features

- **Viewpoint-aware search**: Every candidate is classified egocentric /
  exocentric / unknown with the cues behind the verdict, and footage from the
  wrong perspective is dropped rather than ranked low
- **Usability ranking**: Viewpoint match, then duration, then licence — with the
  popularity sorts kept only for reporting
- **Licence filtering**: Restrict to Creative-Commons material that is safe to
  reuse, straight through the YouTube API
- **Volume goals**: Ask for hours, not clip counts; the run reports progress
  against the target and what the binding constraint was
- **Dataset manifest**: Every run emits clips with viewpoint, confidence,
  duration, licence and usability score, exportable as JSONL or CSV
- **Cost per hour**: Discovery, download, indexing and annotation costed from
  published rates, per hour collected and per hour delivered
- **Video Datalake**: Index footage once into Memories.ai, then read captions,
  transcription and summary, or search moments across the indexed corpus
- **Moment-level annotation tree**: Open a clip to see its viewpoint evidence,
  provenance and per-span hand/object annotations with the tags written back
- **Multi-source**: YouTube, TikTok, Instagram, Twitter/X and the open web
  (dataset pages, lab sites, archives) via Exa neural search and Apify scraping
- **Interactive Web UI**: Bundled zero-build UI for the whole loop

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
git clone https://github.com/Memories-ai-labs/Internet-Video-Search.git
cd Internet-Video-Search

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
MEMORIES_API_KEY=sk-mai-your_datalake_api_key
MEMORIES_BASE_URL=https://api.memories.ai/serve/datalake/v1

# Optional
MEMORIES_COLLECTION_ID=            # index into an existing collection
MEMORIES_COLLECTION_NAME=video-searching-agent
MEMORIES_INDEX_FPS=1.0
MEMORIES_INDEX_WAIT_SECONDS=120    # how long one call waits for indexing
EXA_API_KEY=your_exa_api_key
APIFY_API_TOKEN=your_apify_api_token
```

### Getting API Keys

1. **Google API Key** (required): Get your Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey)
2. **YouTube Data API Key** (required):
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a project and enable YouTube Data API v3
   - Create an API key
3. **Memories.ai API Key** (required): Create a Video Datalake key (`sk-mai-...`) in the [Console](https://console.memories.ai) → API keys. Indexing is billed per minute of video — see [pricing](https://docs.memories.ai/datalake/pricing)
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

## Training-data collection

### Requirements you can set

| Field | API | What it does |
|-------|-----|--------------|
| Viewpoint | `viewpoint` | `egocentric` or `exocentric`; footage classified as the other perspective is excluded, unknown is kept but ranked below matches |
| Minimum length | `min_duration_seconds` | Drops clips too short to train on |
| Licence | `license_filter` | `reusable` keeps only licence-clear footage (Creative Commons via the YouTube API) |
| Volume goal | `target_hours` | The run reports hours collected against this target |

```bash
curl -N http://localhost:8000/api/v1/queries/stream \
  -H "Content-Type: application/json" \
  -d '{
        "query": "egocentric kitchen prep footage, long continuous takes",
        "viewpoint": "egocentric",
        "min_duration_seconds": 300,
        "license_filter": "reusable",
        "target_hours": 2
      }'
```

### How a candidate is judged

Classification is deterministic keyword/pattern evidence over the title,
description, tags and — once indexed — the Datalake captions, which describe
what the frame actually shows. No LLM call per candidate, and the evidence is
returned so a verdict can be checked.

Confidence is deliberately conservative about `POV`: a large amount of
short-form content titled "POV: ..." is scripted skit work shot in third
person, so POV only reaches high confidence alongside a capture cue
(head/chest mount, GoPro, wearable, visible hands) or a real activity.

Ranking weights viewpoint match at 0.6, duration at 0.3 (saturating at 10
minutes) and licence at 0.1.

### The manifest

Every run returns a `dataset` manifest: clips with viewpoint, confidence,
evidence, duration, licence and usability score, plus totals — hours collected,
viewpoint mix, source mix, reusable-licence count, and every exclusion with its
reason. The UI exports it as JSONL (one clip per line, for an ingest pipeline)
or CSV.

### Cost per hour

Costed from the [published Datalake rates](https://docs.memories.ai/datalake/pricing):

| Term | Rate | Per hour of footage |
|------|------|---------------------|
| Indexing | $0.05 / video-minute at fps 1.0 | **$3.00** |
| Moment search | $0.008 / call | per annotation pass |
| Moment read | $0.008 / call | per annotation pass |
| Derived read (caption/transcript/title/summary) | $0.001 / call | a few cents |
| Storage | $0.02 / GB-month | ~$0.04 for 1080p |
| Discovery | measured per run (Gemini + Exa + Apify) | cents |
| Download | your egress; $0/h on owned infrastructure | configurable |

Indexing dominates, so a collected hour lands near **$3.05/h** with discovery
included. The run also reports cost per *delivered* hour: the vendor-facing
figure that 44% of an agent's shortlist survives a frame-level check makes that
roughly **$6.90/h**. Terms the run could not measure are reported as zero and
called out, never filled with a guess.

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
- **Video content** — when the agent reads a video through the Datalake, its AI title,
  summary, visual captions and timestamped speech turns are shown inline; while indexing
  is still running you get an `indexing` notice with the `video_id` to ask again with.
- **Moments** — hits from `video_moment_search` render as cards with their time range,
  match target, score, snippet and thumbnail.
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

Ask about a video's own content and the agent indexes it into the Video Datalake,
then reads back the captions, transcription and summary:

```python
response = await agent.query(
    "What does this video actually show and say? https://example.com/clip.mp4"
)
```

Indexing takes time. If it is still running when the call's wait budget expires,
the tool reports `status: "processing"` with a `video_id`, and the next call reads
the results instead of re-indexing.

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
    │   ├── Video Datalake: VideoIndexTool, VideoAnalysisTool, VideoMomentSearchTool
    │   └── Unified: VideoSearchTool
    └── AgentSession (tracks query lifecycle)
```

## Tools Reference

The agent has access to 16 specialized tools organized by category:

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

### Memories.ai Video Datalake Tools (3)

The Datalake is the agent's long-term video memory: a video indexed once stays
searchable, so later questions read the lake instead of re-processing the video.

| Tool | Description |
|------|-------------|
| `video_analysis` | Index a video URL (or read an indexed `video_id`) and return its AI title, summary, visual captions and speech transcription — whole video or a `start`/`end` window |
| `video_index` | Add a video to the Datalake without waiting for indexing to finish |
| `video_moment_search` | Search already-indexed videos for the moments matching a description, with timestamps and thumbnails |

Cost control: indexing is billed per minute of video, so the tool policy blocks
these tools unless the query actually names a video or asks what is inside one —
a broad discovery query can never trigger paid indexing.

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
