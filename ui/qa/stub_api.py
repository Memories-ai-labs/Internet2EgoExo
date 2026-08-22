"""Serve the real app in demo mode, for browser QA that spends nothing.

There is no separate stub any more: `DEMO_MODE=1` makes the real endpoints
serve the canned payloads in `video_searching_agent/web/demo.py`, so QA drives
the same code paths a deployment does — routing, validation, SSE framing and
all — and a UI that passes here cannot fail on shape in production.

    uv run python ui/qa/stub_api.py 8821
    cd ui && npm run qa
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

os.environ["DEMO_MODE"] = "1"
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

if __name__ == "__main__":
    import uvicorn

    from video_searching_agent.web.app import create_app

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8821
    uvicorn.run(create_app(), host="127.0.0.1", port=port)
