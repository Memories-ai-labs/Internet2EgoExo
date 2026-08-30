"""Make the suite independent of whatever is in a developer's `.env`.

Settings are loaded with `env_file=".env"`, so a local file changes what the
tests do. That bit: adding `LOOK_AT_FRAMES=1` to a working `.env` turned four
offline unit tests into real API calls and took the suite from 15 seconds to
147. A test that behaves differently on two machines is not a test.

So the paid, network-touching capabilities are forced off here, for every test,
and a test that wants one opts in explicitly with the `looking` fixture.
"""

from __future__ import annotations

import pytest

# Everything that costs money or reaches the network when switched on.
_OFF_FOR_TESTS = {
    "LOOK_AT_FRAMES": "0",
    "VIEWPOINT_CHECK": "off",
}


@pytest.fixture(autouse=True)
def _deterministic_settings(monkeypatch: pytest.MonkeyPatch):
    """Pin the spending switches off, whatever the local `.env` says."""

    from video_searching_agent.config import settings as settings_module

    for name, value in _OFF_FOR_TESTS.items():
        monkeypatch.setenv(name, value)
    settings_module.get_settings.cache_clear()
    yield
    settings_module.get_settings.cache_clear()


@pytest.fixture
def looking(monkeypatch: pytest.MonkeyPatch):
    """Opt one test into the frame-examining paths."""

    from video_searching_agent.config import settings as settings_module

    monkeypatch.setenv("LOOK_AT_FRAMES", "1")
    settings_module.get_settings.cache_clear()
    yield
    settings_module.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _annotation_store_is_never_the_real_one(tmp_path, monkeypatch):
    """Point the annotation store at a temp file for every test.

    `refine_anchors` records what it uploaded, and `record_refined` resolves the
    store through `open_store()` — so without this the suite wrote its fake
    `vid_clean1` and `vid_clean2` straight into `data/annotations.sqlite3` and
    they showed up in the browse UI as real clips.
    """
    from video_searching_agent.store import annotations as store_module

    monkeypatch.setenv("ANNOTATION_STORE_PATH", str(tmp_path / "annotations.sqlite3"))
    # The module caches an open handle per path; clear it so a test never
    # inherits another test's rows.
    monkeypatch.setattr(store_module, "_OPEN", {})
    yield
