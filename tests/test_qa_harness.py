"""The QA sweep's own judgement rules.

The sweep is the thing that tells me whether the deployment still behaves, so
a false positive in it is as expensive as a bug in the product: it either
cries wolf every half hour or, worse, it stops crying when it should. The rule
below took two live runs to get right, which is exactly why it is pinned here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "qa_run_qa", Path(__file__).resolve().parents[1] / "qa" / "run_qa.py"
)
run_qa = importlib.util.module_from_spec(_SPEC)
# Registered before execution because the module defines dataclasses, and
# dataclasses resolves annotations through sys.modules.
sys.modules[_SPEC.name] = run_qa
_SPEC.loader.exec_module(run_qa)


def test_every_declared_expectation_is_one_the_runner_checks() -> None:
    """An expectation the runner ignores reads like a check that passed."""

    for case in run_qa.QUERIES:
        unknown = set(case.get("expect") or {}) - run_qa.KNOWN_EXPECTATIONS
        assert not unknown, f"{case['id']} declares {sorted(unknown)}"


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("Ego4D provides 3,670 hours of egocentric video.", []),
        ("Assembly101 covers 513 hours across 4,321 sequences.", []),
        ("I collected approximately 4.8 hours of cooking footage.", ["4.8 hours"]),
        (
            "The run delivered 12 hours, of which 9.5 hours were accepted.",
            ["12 hours", "9.5 hours"],
        ),
        ("These clips below total 2 hrs.", ["2 hrs"]),
        ("No quantities here at all.", []),
    ],
)
def test_only_a_claim_about_this_run_counts_as_an_invented_hour(
    answer: str, expected: list[str]
) -> None:
    assert run_qa.own_yield_claims(answer) == expected


def test_hour_claims_sees_every_figure_regardless_of_attribution() -> None:
    answer = "Ego4D is 3,670 hours; EPIC-KITCHENS is 100 hours."
    assert run_qa.hour_claims(answer) == ["3,670 hours", "100 hours"]


def test_a_literature_query_is_the_only_one_allowed_to_quote_hours() -> None:
    """Relaxing the rule is a per-query decision, visible in queries.json."""

    relaxed = [
        case["id"]
        for case in run_qa.QUERIES
        if (case.get("expect") or {}).get("quotes_published_hours")
    ]
    assert relaxed == ["datasets"]
