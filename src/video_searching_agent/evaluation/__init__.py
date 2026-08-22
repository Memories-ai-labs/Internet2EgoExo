"""Performance metrics for the collection pipeline.

Three questions, none of which the QA sweep answers:

1. Of the footage this pipeline finds, how much of it is usable — and at which
   step of the funnel is the rest lost?
2. Split by the quality standard's A/B/C/D bands, how much of each does a run
   actually produce?
3. What did a clip of each band cost?

`eval/` holds the frozen query set and the runner; this package holds the parts
worth testing: the controlled vocabulary the queries are drawn from, the
metrics, and the scorecard they are rendered into.
"""

from video_searching_agent.evaluation.metrics import (
    DISPOSITION,
    GRADES,
    ClipOutcome,
    CostLedger,
    GradeBand,
    QueryOutcome,
    Scorecard,
    YieldChain,
    score_run,
)
from video_searching_agent.evaluation.scorecard import render
from video_searching_agent.evaluation.task_map import (
    DIFFICULTY_MIX,
    Selection,
    Task,
    filmable,
    load_task_map,
    sample,
)

__all__ = [
    "DIFFICULTY_MIX",
    "DISPOSITION",
    "GRADES",
    "ClipOutcome",
    "CostLedger",
    "GradeBand",
    "QueryOutcome",
    "Scorecard",
    "Selection",
    "Task",
    "YieldChain",
    "filmable",
    "load_task_map",
    "render",
    "sample",
    "score_run",
]
