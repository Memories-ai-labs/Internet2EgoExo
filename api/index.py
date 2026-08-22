"""Vercel entrypoint.

Vercel's Python runtime serves the ASGI app it finds in `app`. The package uses
a src layout and is not pip-installed on the function, so `src/` is put on the
path here rather than depending on an editable install.

What works on serverless, and what does not:

* The UI, the search stream and the curation stream are fine — they are HTTP and
  they stream.
* Collection (download → index) is bounded by the function timeout, which is 60s
  on Hobby and up to 300s on Pro. Indexing a long video takes minutes, so the
  stream ends with `indexing still running` and the `video_id` to come back
  with. That is the pipeline's own designed behaviour, not a failure — but for
  bulk collection run the app on a host without a request timeout.
* `DEMO_MODE=1` needs no keys at all: every stream serves canned payloads, so a
  deployed link is clickable by anyone.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from video_searching_agent.web.app import create_app  # noqa: E402

app = create_app()
