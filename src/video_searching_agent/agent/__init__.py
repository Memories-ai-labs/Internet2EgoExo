"""Agents.

One general agent answers questions and runs collection searches; three
specialized agents own the corpus work, each with a single job:

* :class:`CleaningAgent` — agentic filtering and agentic clipping.
* :class:`AnnotationAgent` — agentic annotation, task → action → event.
* :class:`CurationAgent` — agentic curation across a whole set.
"""

from video_searching_agent.agent.annotation_agent import AnnotationAgent, AnnotationRun
from video_searching_agent.agent.cleaning_agent import (
    CleaningAgent,
    CleaningVerdict,
    ScreeningVerdict,
    Segment,
)
from video_searching_agent.agent.core import VideoSearchingAgent
from video_searching_agent.agent.curation_agent import (
    CuratedClip,
    CurationAgent,
    CurationReport,
)

__all__ = [
    "AnnotationAgent",
    "AnnotationRun",
    "CleaningAgent",
    "CleaningVerdict",
    "CuratedClip",
    "CurationAgent",
    "CurationReport",
    "ScreeningVerdict",
    "Segment",
    "VideoSearchingAgent",
]
