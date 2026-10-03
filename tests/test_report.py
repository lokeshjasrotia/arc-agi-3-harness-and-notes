import json

import pytest

from arcbench.report import BEGIN, END, load_results, render_table, splice_into
from arcbench.schema import aggregate


def _write(tmp_path, doc, name):
    doc["aggregate"] = aggregate(doc["games"], None)
    (tmp_path / name).write_text(json.dumps(doc), encoding="utf-8")


def test_untraceable_results_are_rejected_not_tabulated(tmp_path, good):
    _write(tmp_path, good, "ok.json")
    bad = json.loads(json.dumps(good))
    bad["git"]["sha"] = "unknown"
    _write(tmp_path, bad, "bad.json")
    docs, problems = load_results(tmp_path)
    assert [d["_file"] for d in docs] == ["ok.json"]
    assert len(problems) == 1 and problems[0].startswith("bad.json")


def test_table_marks_dirty_and_sorts_newest_first(tmp_path, good):
    old = json.loads(json.dumps(good))
    old["created_utc"] = "2026-09-01T00:00:00+00:00"
    old["git"]["dirty"] = True
    _write(tmp_path, old, "old.json")
    _write(tmp_path, good, "new.json")
    docs, _ = load_results(tmp_path)
    table = render_table(docs)
    assert table.index("new.json") < table.index("old.json")
    assert "`aaaaaaa`*" in table  # dirty row marked
    assert "n/a" in table  # no scorecard score


def test_empty_table():
    assert "No committed result files" in render_table([])


def test_splice_roundtrip():
    text = f"intro\n{BEGIN}\nold\n{END}\noutro\n"
    out = splice_into(text, "NEW")
    assert "NEW" in out and "old" not in out and out.startswith("intro") and out.endswith("outro\n")
    with pytest.raises(ValueError):
        splice_into("no markers", "x")
