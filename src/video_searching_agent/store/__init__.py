"""Where the annotation trees live, keyed on the Datalake's video ids.

The Datalake holds the footage. This holds what we concluded about it, in a
shape that can be queried — which is the difference between an annotation you
can round-trip and one you can search.
"""

from video_searching_agent.store.annotations import (
    AnnotationStore,
    Clip,
    Segment,
    open_store,
)

__all__ = ["AnnotationStore", "Clip", "Segment", "open_store"]
