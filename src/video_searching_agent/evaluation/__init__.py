"""Performance metrics for the collection pipeline.

Three questions, none of which the QA sweep answers:

1. Of the footage this pipeline finds, how much of it is usable — and at which
   step of the funnel is the rest lost?
2. Split by the quality standard's A/B/C/D bands, how much of each does a run
   actually produce?
3. What did a clip of each band cost?

A fourth question follows from the first three, and is the reason the recurring
report exists: is any of this getting better? That needs an interval around
every rate, a rolling window to read it in, and a record of what was deployed
when — `report.py`.

`eval/` holds the frozen query set and the two entry points (`run_eval.py` for a
one-off, `publish.py` for the eight-hourly job); this package holds the parts
worth testing: the controlled vocabulary the queries are drawn from, the runner
that drives the deployment, the metrics, the scorecard, and the report.
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
from video_searching_agent.evaluation.report import (
    Snapshot,
    append_history,
    load_history,
    render_readme_block,
    render_report,
    snapshot_of,
    update_readme,
    wilson,
)
from video_searching_agent.evaluation.runner import health, run_query
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
    "Snapshot",
    "Task",
    "YieldChain",
    "append_history",
    "filmable",
    "health",
    "load_history",
    "load_task_map",
    "render",
    "render_readme_block",
    "render_report",
    "run_query",
    "sample",
    "score_run",
    "snapshot_of",
    "update_readme",
    "wilson",
]
