"""Tests for topics.py — slug generation, the daily guard, and area de-weighting."""

import topics


# --- slugify --------------------------------------------------------------

def test_slugify_basic():
    assert topics.slugify("The Hidden Clock") == "the-hidden-clock"


def test_slugify_strips_accents_and_punctuation():
    assert topics.slugify("Café: München & Co.!") == "cafe-munchen-co"


def test_slugify_truncates_to_60_chars():
    slug = topics.slugify("word " * 40)
    assert len(slug) <= 60


def test_slugify_empty_falls_back_to_topic():
    assert topics.slugify("!!!") == "topic"
    assert topics.slugify("") == "topic"


# --- already_done_today ---------------------------------------------------

def test_already_done_today_true_when_date_present():
    seen = [{"date": "2026-07-01", "topic": "A"}, {"date": "2026-07-02", "topic": "B"}]
    assert topics.already_done_today(seen, "2026-07-02") is True


def test_already_done_today_false_when_absent():
    seen = [{"date": "2026-07-01", "topic": "A"}]
    assert topics.already_done_today(seen, "2026-07-02") is False


def test_already_done_today_empty_state():
    assert topics.already_done_today([], "2026-07-02") is False


# --- pick_area (recent-area de-weighting) ---------------------------------

def test_pick_area_avoids_recent_areas():
    areas = ["econ", "physics", "history"]
    # Recent window will include the last areas; "history" is the only fresh one.
    seen = [{"area": "econ"}, {"area": "physics"}]
    picked = {topics.pick_area(areas, seen) for _ in range(50)}
    assert picked == {"history"}


def test_pick_area_falls_back_when_all_recent():
    areas = ["only-one"]
    seen = [{"area": "only-one"}]
    # With a single area there is nothing fresh; it must still return that area.
    assert topics.pick_area(areas, seen) == "only-one"
