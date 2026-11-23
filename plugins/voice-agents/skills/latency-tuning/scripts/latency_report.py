#!/usr/bin/env python3
"""Per-stage latency report for voice agents: where do the milliseconds go?

Part of claude-voice-agent-skills by Viprasol Tech Private Limited.

Input, either:
  * JSON Lines events: {"call": "c1", "turn": 3, "event": "stt_final", "t": 12.345}
    (t in seconds by default; --unit ms for milliseconds)
  * a CSV with one row per turn and one column per stage timestamp.

Stages, in pipeline order (any subset is fine; deltas use consecutive stages present):
  user_speech_end -> stt_final -> llm_first_token -> tts_first_audio -> agent_audio_start

Voice-to-voice latency = user_speech_end -> agent_audio_start (or the last stage
present). Prints p50/p90/p95 per stage and lists the slowest turns.
Standard library only. Run ``python latency_report.py --self-test`` to check it.

  python latency_report.py events.jsonl
  python latency_report.py turns.csv --unit ms --slow 1200
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict

STAGES = ["user_speech_end", "stt_final", "llm_first_token", "tts_first_audio", "agent_audio_start"]
LABELS = {
    ("user_speech_end", "stt_final"): "endpointing + STT final",
    ("stt_final", "llm_first_token"): "LLM time to first token",
    ("llm_first_token", "tts_first_audio"): "TTS time to first audio",
    ("tts_first_audio", "agent_audio_start"): "transport / playout",
}


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile."""
    if not values:
        return math.nan
    ordered = sorted(values)
    k = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[k - 1]


def load(path: str, unit: str) -> dict[tuple[str, str], dict[str, float]]:
    scale = 1000.0 if unit == "s" else 1.0
    turns: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    with open(path, encoding="utf-8-sig") as fh:
        first = ""
        for line in fh:
            if line.strip():
                first = line.lstrip()
                break
        fh.seek(0)
        if first.startswith("{"):
            for n, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                    if not isinstance(ev, dict):
                        raise ValueError("not a JSON object")
                    key = (str(ev.get("call", "")), str(ev["turn"]))
                    name = ev["event"]
                    t = float(ev["t"]) * scale
                    if not math.isfinite(t):
                        raise ValueError("t is not a finite number")
                except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    raise ValueError(f"{path}:{n}: bad event ({exc})") from None
                if name in STAGES:
                    turns[key].setdefault(name, t)  # first occurrence wins
        else:
            reader = csv.DictReader(fh)
            if not reader.fieldnames or not any(s in reader.fieldnames for s in STAGES):
                raise ValueError(f"{path}: CSV needs stage columns such as {', '.join(STAGES)}")
            for n, row in enumerate(reader, 2):
                key = (row.get("call") or "", row.get("turn") or f"row{n}")
                for s in STAGES:
                    cell = (row.get(s) or "").strip()
                    if cell:
                        try:
                            turns[key][s] = float(cell) * scale
                            if not math.isfinite(turns[key][s]):
                                raise ValueError
                        except ValueError:
                            raise ValueError(f"{path}:{n}: {s} is not a number: {cell!r}") from None
    return turns


def analyse(turns: dict[tuple[str, str], dict[str, float]], slow_ms: float = 1500) -> dict:
    deltas: dict[str, list[float]] = defaultdict(list)
    v2v: list[tuple[float, tuple[str, str]]] = []
    problems = []
    partial = 0
    for key, st in turns.items():
        present = [s for s in STAGES if s in st]
        for a, b in zip(present, present[1:]):
            d = st[b] - st[a]
            if d < 0:
                problems.append(f"call {key[0]} turn {key[1]}: {b} is before {a} (clock skew or wrong event)")
                continue
            deltas[LABELS.get((a, b), f"{a} -> {b}")].append(d)
        if "user_speech_end" in st and "agent_audio_start" in st:
            total_ms = st["agent_audio_start"] - st["user_speech_end"]
            if total_ms >= 0:  # negative = clock skew, already reported above
                v2v.append((total_ms, key))
        elif "user_speech_end" in st:
            partial += 1  # e.g. barge-in or dropped turn: no agent audio to measure
    total = [x for x, _ in v2v]
    return {
        "turns": len(turns),
        "stages": {k: {"n": len(v), "p50": percentile(v, 50), "p90": percentile(v, 90), "p95": percentile(v, 95)}
                   for k, v in deltas.items()},
        "voice_to_voice": {"n": len(total), "p50": percentile(total, 50), "p90": percentile(total, 90),
                           "p95": percentile(total, 95)},
        "partial_turns": partial,
        "slow_turns": [{"call": k[0], "turn": k[1], "ms": round(x)} for x, k in sorted(v2v, reverse=True) if x > slow_ms][:10],
        "problems": problems,
    }


def _no_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: _no_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_no_nan(v) for v in obj]
    return obj


def _fmt(x: float) -> str:
    return "   -  " if math.isnan(x) else f"{x:6.0f}"


def _self_test() -> None:
    assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 50) == 5 and percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95) == 10
    assert math.isnan(percentile([], 50))
    turns = {
        ("c1", "1"): {"user_speech_end": 1000, "stt_final": 1300, "llm_first_token": 1700, "tts_first_audio": 1850, "agent_audio_start": 1900},
        ("c1", "2"): {"user_speech_end": 5000, "stt_final": 5250, "llm_first_token": 6400, "tts_first_audio": 6600, "agent_audio_start": 6700},
        ("c2", "1"): {"user_speech_end": 100, "llm_first_token": 600, "agent_audio_start": 900},
        ("c2", "2"): {"user_speech_end": 100, "stt_final": 50},
    }
    r = analyse(turns, slow_ms=1500)
    assert r["turns"] == 4
    assert r["stages"]["endpointing + STT final"]["n"] == 2
    assert r["voice_to_voice"]["n"] == 3  # the skewed turn has no agent audio
    assert r["partial_turns"] == 1
    assert r["voice_to_voice"]["p50"] == 900 and r["stages"]["LLM time to first token"]["p95"] == 1150
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        j = os.path.join(d, "e.jsonl")
        with open(j, "w", encoding="utf-8") as fh:
            fh.write('\n  \n{"call":"a","turn":1,"event":"user_speech_end","t":1}\n'
                     '{"call":"a","turn":1,"event":"agent_audio_start","t":1.8}\n')
        assert analyse(load(j, "s"))["voice_to_voice"]["p50"] == 800   # leading blank lines ok
        with open(j, "w", encoding="utf-8") as fh:
            fh.write('{"call":"a","turn":1,"event":"stt_final","t":1}\n[1,2]\n')
        try:
            load(j, "s")
        except ValueError:
            pass
        else:
            raise AssertionError("non-object JSON line accepted")
        c = os.path.join(d, "t.csv")
        with open(c, "w", encoding="utf-8") as fh:
            fh.write("call,turn,user_speech_end,agent_audio_start\nx,,0,900\nx,,0,1000\n")
        assert analyse(load(c, "ms"))["turns"] == 2                      # blank turn cells not merged
        assert json.dumps(_no_nan({"a": math.nan}), allow_nan=False) == '{"a": null}'
    assert r["slow_turns"][0] == {"call": "c1", "turn": "2", "ms": 1700}
    assert any("before" in p for p in r["problems"])
    print("latency_report self-test passed")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Per-stage latency report for voice agents")
    ap.add_argument("file", nargs="?", help="JSONL events or CSV of turns")
    ap.add_argument("--unit", choices=["s", "ms"], default="s", help="Timestamp unit in the input")
    ap.add_argument("--slow", type=float, default=1500, help="Flag turns slower than this many ms")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        _self_test()
        return 0
    if not a.file:
        ap.error("file is required (or use --self-test)")
    try:
        report = analyse(load(a.file, a.unit), a.slow)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(_no_nan(report), indent=2))
        return 0
    print(f"{report['turns']} turns\n")
    print(f"{'stage':<28}{'n':>5}{'p50':>8}{'p90':>8}{'p95':>8}   (ms)")
    for name, s in report["stages"].items():
        print(f"{name:<28}{s['n']:>5}  {_fmt(s['p50'])}  {_fmt(s['p90'])}  {_fmt(s['p95'])}")
    v = report["voice_to_voice"]
    print(f"{'VOICE-TO-VOICE':<28}{v['n']:>5}  {_fmt(v['p50'])}  {_fmt(v['p90'])}  {_fmt(v['p95'])}")
    if report["partial_turns"]:
        print(f"({report['partial_turns']} turns without agent_audio_start excluded from voice-to-voice)")
    if report["slow_turns"]:
        print(f"\nslowest turns over {a.slow:.0f} ms:")
        for t in report["slow_turns"]:
            print(f"  call {t['call']} turn {t['turn']}: {t['ms']} ms")
    for p in report["problems"]:
        print(f"warning: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
