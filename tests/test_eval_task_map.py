"""The rules that turn the task map into eval queries.

Every one of these is a claim about a judgement rather than about a function
signature: which rows a person can be filmed doing, which spellings of a family
are the same family, and what an imperative instruction reads like once it is
phrased as something to search for. A change that breaks one of these changes
the eval set, and the eval set is frozen — so breaking one on purpose means
rebuilding `eval/queries.json` and saying so.
"""

from __future__ import annotations

import pytest

from video_searching_agent.evaluation.task_map import (
    DIFFICULTY_BY_GRANULARITY,
    EXCLUDED_DOMAINS,
    FAMILY_ALIASES,
    MAX_QUERY_WORDS,
    NOT_A_VERB,
    NOUN_HEADS,
    Task,
    as_gerund_phrase,
    canonical_family,
    drop_reason,
    filmable,
    gerund,
    imperative_verbs,
    load_task_map,
    sample,
    usable_as_query,
)


def _task(**overrides) -> Task:
    base = {
        "rdt_id": "RDT-00001",
        "task_name": "Fold Cloth",
        "instruction": "Fold the cloth.",
        "domain": "Household & Daily-Living Robotics",
        "task_family": "Laundry & Clothing Care",
        "granularity": "Atomic Task",
    }
    return Task(**{**base, **overrides})


@pytest.mark.parametrize(
    ("verb", "expected"),
    [
        ("fold", "folding"),
        ("place", "placing"),  # silent e is dropped
        ("see", "seeing"),  # ... but not a doubled one
        ("tie", "tying"),  # irregular
        ("cut", "cutting"),  # one vowel group, single final consonant
        ("stir", "stirring"),
        ("mop", "mopping"),
        ("clean", "cleaning"),  # two vowels: no doubling
        ("open", "opening"),  # two vowel groups: no doubling
        ("fold", "folding"),  # two final consonants: no doubling
        ("fix", "fixing"),  # x never doubles
        ("begin", "beginning"),  # stressed second syllable, listed as irregular
        ("unplug", "unplugging"),
        ("cooking", "cooking"),  # already a gerund
    ],
)
def test_gerund_spelling(verb: str, expected: str) -> None:
    assert gerund(verb) == expected


def test_a_normalised_label_is_lowercased_but_a_sentence_is_not() -> None:
    # "someone adjusting Bottle" reads like a typo.
    assert as_gerund_phrase("Adjust Bottle.") == "adjusting bottle"
    # A real sentence keeps its capitals, so a proper noun in one survives.
    assert as_gerund_phrase("Wash the lettuce in the Belfast sink.") == (
        "washing the lettuce in the Belfast sink"
    )


def test_a_head_that_is_not_a_verb_gets_doing_rather_than_a_made_up_gerund() -> None:
    assert as_gerund_phrase("Pj Sandwich Prep") == "doing pj sandwich prep"
    assert "pjing" not in as_gerund_phrase("Pj Sandwich Prep")


@pytest.mark.parametrize(
    ("instruction", "usable"),
    [
        ("Fold the cloth.", True),
        ("There is a mixed pile of fruit on the counter. Locate all of it.", False),
        ("Put the plate away. Then wipe the counter.", False),
        # Length is `shorten`'s job, not this one's: a long imperative still
        # says what the hands do.
        ("Pick " + " ".join(["word"] * (MAX_QUERY_WORDS + 1)), True),
        ("", False),
    ],
)
def test_only_a_short_single_imperative_is_used_as_the_query(
    instruction: str, usable: bool
) -> None:
    assert usable_as_query(instruction) is usable


def test_an_unusable_instruction_falls_back_to_the_canonical_task_name() -> None:
    task = _task(
        task_name="Defrost By Category",
        instruction="There is a mixed pile on the counter. Defrost the fruit.",
    )
    assert task.query == "someone defrosting by category"


def test_a_multi_step_instruction_is_cut_at_its_first_clause() -> None:
    task = _task(
        instruction=(
            "Pick up the black bowl between the plate and the ramekin "
            "and place it on the plate"
        )
    )
    assert len(task.query.split()) <= MAX_QUERY_WORDS + 1
    assert task.query.startswith("someone picking up the black bowl")


@pytest.mark.parametrize(
    ("field", "value", "reason_starts"),
    [
        ("domain", "Locomotion & Whole-Body Control", "domain"),
        ("task_family", "Visual reasoning", "family"),
        ("granularity", "Evaluation Protocol", "granularity"),
    ],
)
def test_rows_that_are_not_human_work_are_dropped(
    field: str, value: str, reason_starts: str
) -> None:
    reason = drop_reason(_task(**{field: value}))
    assert reason and reason.startswith(reason_starts)


@pytest.mark.parametrize(
    "instruction",
    [
        "Command the robot arm to fold the cloth.",
        "Push the puck to the goal.",
        "Rotate valve level4.",
        "Put the [*vegetables*] in the pan.",
        "{Increase/Decrease} the oven temperature.",
        "Grasp the target .",
        "Fold",
    ],
)
def test_instructions_written_for_a_simulator_are_dropped(instruction: str) -> None:
    assert drop_reason(_task(instruction=instruction)) is not None


def test_kicking_a_ball_into_a_goal_is_not_a_simulator_goal() -> None:
    assert drop_reason(_task(instruction="Kick the soccer ball into the goal.")) is None


def test_family_aliases_resolve_in_one_step() -> None:
    """An alias pointing at another alias would silently not resolve."""
    for source, target in FAMILY_ALIASES.items():
        assert target not in FAMILY_ALIASES, f"{source} -> {target} -> {FAMILY_ALIASES[target]}"


def test_family_spellings_collapse() -> None:
    assert canonical_family("Cleaning") == canonical_family("Cleaning & Hygiene")
    assert canonical_family("Pick and place") == canonical_family("Pick–Place & Transport")
    assert canonical_family("") == "Other"


def test_every_granularity_in_the_map_has_a_difficulty() -> None:
    """An unmapped granularity would silently default to medium."""
    unmapped = {
        task.granularity
        for task in filmable(load_task_map())[0]
        if task.granularity.lower() not in DIFFICULTY_BY_GRANULARITY
    }
    assert not unmapped


def test_the_map_loads_and_most_of_it_is_filmable() -> None:
    every = load_task_map()
    assert len(every) > 1900
    usable, dropped = filmable(every)
    assert len(usable) + sum(dropped.values()) == len(every)
    # If a rule ever starts dropping most of the vocabulary, that is a bug in
    # the rule and not a fact about the vocabulary.
    assert len(usable) > 0.8 * len(every)


def test_sampling_is_deterministic_and_hits_its_quotas() -> None:
    usable, _ = filmable(load_task_map())
    first = sample(usable, 200)
    second = sample(usable, 200)

    assert [t.rdt_id for t in first.tasks] == [t.rdt_id for t in second.tasks]
    assert len(first.tasks) == 200
    assert len({t.rdt_id for t in first.tasks}) == 200
    assert first.per_difficulty == {"easy": 40, "medium": 100, "hard": 60}
    assert not first.shortfall
    # Coverage-first sampling: a proportional draw would spend a fifth of the
    # set on the largest family.
    assert len(first.per_family) >= 20
    assert max(first.per_family.values()) <= 25


def test_a_small_sample_still_spreads_across_families() -> None:
    usable, _ = filmable(load_task_map())
    selection = sample(usable, 30)
    assert len(selection.tasks) == 30
    assert len(selection.per_family) >= 10


def test_the_verb_lexicon_comes_from_the_map_and_is_not_empty() -> None:
    verbs = imperative_verbs(load_task_map())
    assert {"fold", "clean", "pick", "pour"} <= verbs
    assert len(verbs) > 100
    # The overlap with NOUN_HEADS is the whole reason that override exists: the
    # map really does open some instructions with a noun.
    assert verbs & NOT_A_VERB <= NOUN_HEADS | {"there"}


def test_no_excluded_domain_survives_the_filter() -> None:
    usable, _ = filmable(load_task_map())
    assert not {task.domain for task in usable} & EXCLUDED_DOMAINS
