import pytest

from arcbench.schema import ALLOWED_SPLITS, ResultError, aggregate, validate_result


def test_good_result_passes(good):
    validate_result(good)


@pytest.mark.parametrize("sha", ["", "unknown", "abc123", "A" * 40, "g" * 40])
def test_missing_or_bad_sha_is_rejected(good, sha):
    good["git"]["sha"] = sha
    with pytest.raises(ResultError, match="SHA"):
        validate_result(good)


def test_dirty_flag_required(good):
    del good["git"]["dirty"]
    with pytest.raises(ResultError, match="dirty"):
        validate_result(good)


def test_unknown_split_rejected(good):
    good["split"] = "my-own-split"
    with pytest.raises(ResultError, match="split"):
        validate_result(good)
    assert "public-local" in ALLOWED_SPLITS


@pytest.mark.parametrize("cmd", ["", "   ", None])
def test_command_required(good, cmd):
    good["command"] = cmd
    with pytest.raises(ResultError, match="command"):
        validate_result(good)


def test_empty_games_rejected(good):
    good["games"] = []
    with pytest.raises(ResultError, match="games"):
        validate_result(good)


def test_game_row_missing_key(good):
    del good["games"][0]["actions"]
    with pytest.raises(ResultError, match="missing keys"):
        validate_result(good)


def test_aggregate(good):
    good["games"][0]["error"] = "boom"
    agg = aggregate(good["games"], 12.5)
    assert agg["runs"] == 2
    assert agg["total_levels_completed"] == 4
    assert agg["mean_levels_completed"] == 2.0
    assert agg["wins"] == 1
    assert agg["errors"] == 1
    assert agg["total_actions"] == 120
    assert agg["scorecard_score"] == 12.5
