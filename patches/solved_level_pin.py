"""Solved-level pin: carry what cleared a level through the rest of the game.

Idea credit: the "solved-level memory" experiment in the sirikilohit / LohitSiriki ARC-AGI-3
Milestone-2 write-up (https://github.com/LohitSiriki/arc-agi-3-milestone2-solution). This is an
independent implementation written for the dfranzen (TAAF / Duck harness) base; no code is copied.

Why: the base trims chat history from ~118k down to ~59k tokens roughly every ~100 actions, which
drops the early solved levels. The system prompt is never trimmed, so a short block pinned there
survives.

Design rules (fail-safe):
  * pure, dependency-free functions (testable without the harness),
  * the wrapper NEVER raises: on any error the original prompt is returned unchanged,
  * OFF unless env ARC3X_SOLVED_PIN=1,
  * single process, no threads; only I/O is the optional event log (ARC3X_PIN_LOG).

Cost to measure: editing the system prompt invalidates the prefix cache once per solved level.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

ACTIONS_KEPT = 30
REASONING_CHARS = 900
RULE_CHARS = 600
FULL_LEVELS = 3        # newest N levels keep actions + reasoning; older keep the rule only
ASK_TURNS = 2          # how many prompts we ask the model to state its rule
HEADER = "=== SOLVED LEVELS (this game; kept for the whole game) ==="
FOOTER = "=== END SOLVED LEVELS ==="
ENV_FLAG = "ARC3X_SOLVED_PIN"
LOG_ENV = "ARC3X_PIN_LOG"   # optional path: one JSON line per event (never raises)


def enabled() -> bool:
    return os.environ.get(ENV_FLAG, "0").strip().lower() in {"1", "true", "on", "yes"}


def log_event(event: str, **kw: Any) -> None:
    path = os.environ.get(LOG_ENV, "")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(t=round(time.time(), 1), pid=os.getpid(), event=event, **kw)) + "\n")
    except Exception:
        pass


def message_text(msg: Any) -> str:
    """All visible + reasoning text of one chat message dict."""
    if not isinstance(msg, dict):
        return ""
    parts: list[str] = []
    for key in ("content", "reasoning_content", "reasoning"):
        v = msg.get(key)
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts += [p["text"] for p in v if isinstance(p, dict) and isinstance(p.get("text"), str)]
    return "\n".join(p for p in parts if p)


def level_actions(history_entries: Any, level: int) -> list[str]:
    """Actions taken while on `level`.

    history[i].frame is the frame AFTER history[i].action, so an action belongs to the level of
    the frame BEFORE it. A seeded first entry with an empty action is skipped.
    """
    out: list[str] = []
    prev_level = None
    for e in history_entries or []:
        act = str(getattr(e, "action", "") or "").strip()
        if act and prev_level == level:
            out.append(act)
        lv = getattr(getattr(e, "frame", None), "level", None)
        if isinstance(lv, int):
            prev_level = lv
    return out


def find_rule(text: str, level: int) -> str | None:
    """Extract a line 'Rule for level N: ...' (own line if >=40 chars, else up to 5 lines)."""
    m = re.search(r"Rule for level\s*%d\s*:[ \t]*" % int(level), text or "", re.I)
    if not m:
        return None
    lines = text[m.end():].split("\n")
    first = lines[0].strip()
    if len(first) >= 40:
        rule = first
    else:
        got = [first] if first else []
        for ln in lines[1:6]:
            if not ln.strip():
                if got:
                    break
                continue
            got.append(ln.strip())
        rule = " ".join(got)
    rule = " ".join(rule.split())[:RULE_CHARS]
    return rule if len(rule) >= 20 else None


def render_block(levels: list[dict]) -> str:
    if not levels:
        return ""
    lines = [HEADER]
    full_from = max(0, len(levels) - FULL_LEVELS)
    for i, rec in enumerate(levels):
        lines.append(f"Level {rec['level']} cleared after {rec['n_actions']} actions.")
        lines.append(f"  Your rule: {rec.get('rule') or 'not stated'}")
        if i >= full_from:
            tail = rec.get("actions") or []
            skipped = rec["n_actions"] - len(tail)
            lines.append(
                "  Last actions before it cleared"
                + (f" ({skipped} earlier omitted)" if skipped > 0 else "")
                + ": " + (", ".join(tail) if tail else "none recorded")
            )
            if rec.get("reasoning"):
                lines.append("  Your reasoning in the turn that cleared it: " + rec["reasoning"])
    lines.append("Reuse these where the new level has the same controls; verify with one probe first.")
    lines.append(FOOTER)
    return "\n".join(lines)


def replace_block(system_prompt: str, old_block: str, new_block: str) -> str:
    """Put new_block at the end of the prompt, replacing old_block in place (never duplicates)."""
    sp = system_prompt or ""
    if old_block and old_block in sp:
        out = sp.replace(old_block, new_block)
        return out if new_block else out.rstrip("\n")
    if new_block:
        return sp.rstrip("\n") + "\n\n" + new_block
    return sp


def ask_text(level: int) -> str:
    return (
        f"\n\nLEVEL {level} SOLVED. In your reply this turn, before acting, write one short paragraph "
        f"that starts exactly with 'Rule for level {level}:' -- the goal, what each control did, and the "
        "plan that won (at most 5 lines). It is pinned for every later level."
    )


class Stats:
    def __init__(self) -> None:
        self.levels_recorded = 0
        self.rules_captured = 0
        self.rules_missing = 0
        self.asks = 0
        self.errors = 0
        self.last_error = ""
        self.block_chars_max = 0

    def as_dict(self) -> dict:
        return dict(self.__dict__)


STATS = Stats()


def _last_assistant_tail(history_messages: Any) -> str:
    for m in reversed(history_messages or []):
        if isinstance(m, dict) and m.get("role") == "assistant":
            t = " ".join(message_text(m).split())
            if t:
                return t[-REASONING_CHARS:]
    return ""


def step(agent: Any, prompt: str, kwargs: dict) -> str:
    """One turn of the pin logic. Mutates agent state, returns the (possibly extended) prompt."""
    if not hasattr(agent, "_pin_levels"):
        agent._pin_levels = []
        agent._pin_block = ""
    changed = False

    # 1. capture rules the model wrote since we asked
    pending = [r for r in agent._pin_levels if not r.get("rule") and r["asks"] > r["checks"]]
    if pending:
        texts = [message_text(m) for m in (getattr(agent, "_history_messages", []) or [])
                 if isinstance(m, dict) and m.get("role") == "assistant"]
        for rec in pending:
            rec["checks"] += 1
            for t in reversed(texts):
                rule = find_rule(t, rec["level"])
                if rule:
                    rec["rule"] = rule
                    changed = True
                    STATS.rules_captured += 1
                    log_event("rule_captured", level=rec["level"], chars=len(rule))
                    break
            if not rec.get("rule") and rec["checks"] >= ASK_TURNS:
                STATS.rules_missing += 1
                log_event("rule_missing", level=rec["level"])

    # 2. record a newly solved level
    summary = kwargs.get("previous_step_summary") or {}
    level_now = getattr(kwargs.get("current_frame"), "level", None)
    if summary.get("level_transition") and not summary.get("run_complete") and isinstance(level_now, int):
        solved = level_now - 1
        if solved >= 1 and all(r["level"] != solved for r in agent._pin_levels):
            acts = level_actions(kwargs.get("history_entries"), solved)
            agent._pin_levels.append(dict(
                level=solved, n_actions=len(acts), actions=acts[-ACTIONS_KEPT:],
                reasoning=_last_assistant_tail(getattr(agent, "_history_messages", None)),
                rule=None, asks=0, checks=0))
            changed = True
            STATS.levels_recorded += 1
            log_event("level_recorded", level=solved, n_actions=len(acts))

    # 3. ask for the rule on the newest level
    last = agent._pin_levels[-1] if agent._pin_levels else None
    if last is not None and not last.get("rule") and last["asks"] < ASK_TURNS:
        last["asks"] += 1
        STATS.asks += 1
        prompt = prompt + ask_text(last["level"])

    # 4. refresh the pinned block
    if changed:
        new_block = render_block(agent._pin_levels)
        agent._system_prompt = replace_block(getattr(agent, "_system_prompt", "") or "", agent._pin_block, new_block)
        agent._pin_block = new_block
        STATS.block_chars_max = max(STATS.block_chars_max, len(new_block))
        log_event("block_updated", chars=len(new_block), levels=len(agent._pin_levels))
    return prompt


def install(tool_agent_cls: Any) -> bool:
    """Wrap ToolAgent._build_user_prompt. Returns False (no change) when disabled."""
    if not enabled():
        return False
    inner = tool_agent_cls._build_user_prompt
    if getattr(inner, "_pin_wrapped", False):
        raise RuntimeError("solved_level_pin installed twice")

    def wrapped(self, action_num, *args, **kwargs):
        out = inner(self, action_num, *args, **kwargs)
        try:
            return step(self, out, kwargs)
        except Exception as exc:  # never break a game over a memory aid
            STATS.errors += 1
            STATS.last_error = f"{type(exc).__name__}: {exc}"[:200]
            log_event("error", error=STATS.last_error)
            return out

    wrapped._pin_wrapped = True
    tool_agent_cls._build_user_prompt = wrapped
    return True
