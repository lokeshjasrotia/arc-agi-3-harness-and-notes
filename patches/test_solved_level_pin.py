"""Unit tests with fake harness classes. Single process, no GPU, no network. Runs in < 1 s."""
from dataclasses import dataclass

import pytest
import solved_level_pin as P


@dataclass
class Fr:
    level: int

@dataclass
class En:
    action: str
    frame: Fr


class FakeAgent:
    def __init__(self):
        self._system_prompt = "SYSTEM"
        self._history_messages = []
    def _build_user_prompt(self, action_num, *, valid_actions=None, current_frame=None,
                           history_entries=None, previous_step_summary=None):
        return f"turn {action_num}"


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    P.STATS.__init__()
    monkeypatch.setenv(P.ENV_FLAG, "1")


def hist(levels_actions):
    """[(level_before, action)] -> HistoryEntry list with frame level AFTER the action."""
    out = [En("", Fr(1))]
    lv = 1
    for nxt, act in levels_actions:
        lv = nxt
        out.append(En(act, Fr(lv)))
    return out


def test_level_actions_belongs_to_level_before():
    h = hist([(1, "A1"), (1, "A2"), (2, "A3"), (2, "A4")])
    assert P.level_actions(h, 1) == ["A1", "A2", "A3"]   # A3 cleared level 1
    assert P.level_actions(h, 2) == ["A4"]


def test_find_rule_variants():
    assert P.find_rule("Rule for level 2: move the red block onto the blue square then press A5 twice.", 2)
    assert P.find_rule("Rule for level 2:\n- goal: x y z\n- ACTION1 moves up\n\nother", 2) == "- goal: x y z - ACTION1 moves up"
    assert P.find_rule("Rule for level 3: short", 3) is None
    assert P.find_rule("Rule for level 2: " + "x" * 40, 3) is None
    assert len(P.find_rule("Rule for level 1: " + "y" * 2000, 1)) == P.RULE_CHARS


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv(P.ENV_FLAG, raising=False)
    assert P.install(FakeAgent) is False
    assert not getattr(FakeAgent._build_user_prompt, "_pin_wrapped", False)


def make_installed():
    class A(FakeAgent):
        pass
    assert P.install(A) is True
    return A()


def test_full_flow_pin_replace_and_no_duplicates():
    a = make_installed()
    summ = dict(level_transition=True, run_complete=False)
    a._history_messages = [{"role": "assistant", "content": "I moved the box and cleared it"}]
    out = a._build_user_prompt(5, current_frame=Fr(2), history_entries=hist([(1, "A1"), (2, "A2")]),
                               previous_step_summary=summ)
    assert "LEVEL 1 SOLVED" in out and "Rule for level 1:" in out
    assert P.HEADER in a._system_prompt and "Level 1 cleared after 2 actions" in a._system_prompt
    # model answers with the rule
    a._history_messages.append({"role": "assistant", "content":
        "Rule for level 1: push the box right until it touches the wall, then ACTION2."})
    out2 = a._build_user_prompt(6, current_frame=Fr(2), history_entries=hist([(1, "A1"), (2, "A2")]),
                                previous_step_summary=dict(level_transition=False))
    assert "SOLVED" not in out2
    assert a._system_prompt.count(P.HEADER) == 1
    assert "push the box right" in a._system_prompt
    assert P.STATS.rules_captured == 1 and P.STATS.errors == 0
    # second level solved -> still one block, both levels present
    a._build_user_prompt(9, current_frame=Fr(3), history_entries=hist([(1, "A1"), (2, "A2"), (3, "A3")]),
                         previous_step_summary=summ)
    assert a._system_prompt.count(P.HEADER) == 1 and "Level 2 cleared" in a._system_prompt
    assert a._system_prompt.startswith("SYSTEM")


def test_ask_limited_to_ask_turns():
    a = make_installed()
    summ = dict(level_transition=True)
    a._build_user_prompt(1, current_frame=Fr(2), history_entries=hist([(2, "A1")]), previous_step_summary=summ)
    n = 0
    for i in range(6):
        o = a._build_user_prompt(2 + i, current_frame=Fr(2), history_entries=hist([(2, "A1")]),
                                 previous_step_summary=dict(level_transition=False))
        n += "LEVEL 1 SOLVED" in o
    assert n + 1 == P.ASK_TURNS
    assert P.STATS.rules_missing == 1
    assert "not stated" in a._system_prompt


def test_run_complete_and_level1_ignored():
    a = make_installed()
    a._build_user_prompt(1, current_frame=Fr(9), history_entries=[],
                         previous_step_summary=dict(level_transition=True, run_complete=True))
    a._build_user_prompt(2, current_frame=Fr(1), history_entries=[],
                         previous_step_summary=dict(level_transition=True))
    assert a._system_prompt == "SYSTEM" and P.STATS.levels_recorded == 0


def test_never_breaks_prompt_on_error():
    a = make_installed()
    a._history_messages = 5  # garbage state -> exception inside step
    out = a._build_user_prompt(3, current_frame=Fr(2), history_entries=hist([(1, "A1"), (2, "A2")]),
                               previous_step_summary=dict(level_transition=True))
    assert out == "turn 3" and P.STATS.errors == 1


def test_double_install_refused():
    class A(FakeAgent):
        pass
    P.install(A)
    with pytest.raises(RuntimeError):
        P.install(A)


def test_block_size_bounded():
    levels = [dict(level=i, n_actions=500, actions=["ACTION%d" % (j % 7) for j in range(30)],
                   reasoning="r" * 900, rule="x" * 600) for i in range(1, 40)]
    full = P.render_block(levels)
    assert len(full) < 40 * 800 + 3 * 1800   # older levels are rule-only
    assert full.count("Your reasoning in the turn") == P.FULL_LEVELS


def test_event_log_written_and_safe(tmp_path, monkeypatch):
    log = tmp_path / "pin.jsonl"
    monkeypatch.setenv(P.LOG_ENV, str(log))
    a = make_installed()
    a._build_user_prompt(1, current_frame=Fr(2), history_entries=hist([(1, "A1"), (2, "A2")]),
                         previous_step_summary=dict(level_transition=True))
    import json
    ev = [json.loads(x)["event"] for x in log.read_text().splitlines()]
    assert "level_recorded" in ev and "block_updated" in ev
    monkeypatch.setenv(P.LOG_ENV, str(tmp_path / "nodir" / "x.jsonl"))  # unwritable path must not raise
    P.log_event("x")


def test_source_has_no_triple_single_quotes():
    # the notebook embeds this file inside r'''...'''
    assert "'''" not in open(P.__file__, encoding="utf-8").read()
