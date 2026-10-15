"""Compare two iterations' benchmark.json per (configuration, eval) and score the PRD targets.

    python -m bench.compare <iteration-1 dir> <iteration-2 dir> \
        --target S0-turn-start=-30 --target S3-builder-fix=-15 --target S4-reviewer-slide=-15

Why a separate step: benchmark.json summarises one iteration; the question the PRD asks is
"did the change move each scenario by at least X%", which needs both iterations side by side,
per configuration (the model / effort arms have no baseline in iteration-1 and are shown as such).
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def _load(it_dir: Path) -> dict:
    return json.loads((it_dir / "benchmark.json").read_text(encoding="utf-8"))


def _group(bench: dict) -> dict:
    g: dict[tuple[str, str], list[dict]] = {}
    for r in bench.get("runs", []):
        if r.get("configuration") == "iteration0_transcripts":
            continue
        g.setdefault((r["configuration"], r["eval_name"]), []).append(r["result"])
    return g


def _mean(rs: list[dict], key: str):
    vals = [r.get(key) for r in rs if r.get(key) is not None]
    return statistics.mean(vals) if vals else None


def _sd(rs: list[dict], key: str):
    vals = [r.get(key) for r in rs if r.get(key) is not None]
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


def _kb(rs: list[dict]) -> float:
    tot = [sum((r.get("files_read_kb") or {}).values()) for r in rs]
    return statistics.mean(tot) if tot else 0.0


def compare(before_dir: Path, after_dir: Path, targets: dict[str, float] | None = None) -> list[dict]:
    """targets: eval_name -> required USD change as a fraction (e.g. -0.30)."""
    targets = targets or {}
    gb, ga = _group(_load(before_dir)), _group(_load(after_dir))
    rows = []
    for key in sorted(set(gb) | set(ga)):
        cfg, name = key
        b, a = gb.get(key, []), ga.get(key, [])
        ub, ua = _mean(b, "usd"), _mean(a, "usd")
        delta = ((ua - ub) / ub * 100) if (ub and ua is not None) else None
        tgt = targets.get(name)
        rows.append({
            "config": cfg, "eval": name, "n_before": len(b), "n_after": len(a),
            "usd_before": ub, "usd_after": ua, "sd_before": _sd(b, "usd"), "sd_after": _sd(a, "usd"),
            "usd_delta_pct": round(delta, 2) if delta is not None else None,
            "usd5m_before": _mean(b, "usd_5m"), "usd5m_after": _mean(a, "usd_5m"),
            "calls_before": _mean(b, "api_calls"), "calls_after": _mean(a, "api_calls"),
            "tools_before": _mean(b, "tool_calls"), "tools_after": _mean(a, "tool_calls"),
            "out_before": _mean(b, "output_tokens"), "out_after": _mean(a, "output_tokens"),
            "write_before": _mean(b, "cache_write"), "write_after": _mean(a, "cache_write"),
            "ctx_before": _mean(b, "final_context"), "ctx_after": _mean(a, "final_context"),
            "time_before": _mean(b, "time_seconds"), "time_after": _mean(a, "time_seconds"),
            "kb_before": _kb(b), "kb_after": _kb(a),
            "pass_before": _mean(b, "pass_rate"), "pass_after": _mean(a, "pass_rate"),
            "target_pct": (tgt * 100) if tgt is not None else None,
            "target_met": (delta is not None and tgt is not None and delta <= tgt * 100),
        })
    return rows


def _f(v, fmt="{:.2f}"):
    return "—" if v is None else fmt.format(v)


def render_compare_md(rows: list[dict]) -> str:
    L = ["| config | eval | n | USD before → after | Δ% | target | 5m-TTL before → after | API calls | tool uses | output tok | cache write | final ctx | text read KB | time s | pass |",
         "| --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        tgt = "" if r["target_pct"] is None else ("%s %.0f%%" % ("✔" if r["target_met"] else "✘", r["target_pct"]))
        L.append("| %s | %s | %d→%d | %s±%s → %s±%s | %s | %s | %s → %s | %s → %s | %s → %s | %s → %s | %s → %s | %s → %s | %s → %s | %s → %s | %s → %s |" % (
            r["config"], r["eval"], r["n_before"], r["n_after"],
            _f(r["usd_before"]), _f(r["sd_before"]), _f(r["usd_after"]), _f(r["sd_after"]),
            _f(r["usd_delta_pct"], "{:+.0f}%"), tgt,
            _f(r["usd5m_before"]), _f(r["usd5m_after"]),
            _f(r["calls_before"], "{:.1f}"), _f(r["calls_after"], "{:.1f}"),
            _f(r["tools_before"], "{:.0f}"), _f(r["tools_after"], "{:.0f}"),
            _f(r["out_before"], "{:,.0f}"), _f(r["out_after"], "{:,.0f}"),
            _f(r["write_before"], "{:,.0f}"), _f(r["write_after"], "{:,.0f}"),
            _f(r["ctx_before"], "{:,.0f}"), _f(r["ctx_after"], "{:,.0f}"),
            _f(r["kb_before"], "{:.0f}"), _f(r["kb_after"], "{:.0f}"),
            _f(r["time_before"], "{:.0f}"), _f(r["time_after"], "{:.0f}"),
            _f(r["pass_before"]), _f(r["pass_after"])))
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before"); ap.add_argument("after")
    ap.add_argument("--target", action="append", default=[], metavar="EVAL=PCT", help="e.g. S0-turn-start=-30")
    ap.add_argument("--out", default=None, help="write the markdown table here as well")
    a = ap.parse_args(argv)
    targets = {}
    for t in a.target:
        k, v = t.split("=", 1)
        targets[k] = float(v) / 100.0
    rows = compare(Path(a.before), Path(a.after), targets)
    md = render_compare_md(rows)
    print(md)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
        (Path(a.out).with_suffix(".json")).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
