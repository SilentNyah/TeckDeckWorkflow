"""Aggregate benchmark runs into metrics.json (per run), benchmark.json and benchmark.md.

benchmark.json follows the skill-creator viewer schema (runs[].result.{pass_rate,
time_seconds, tokens, ...}, run_summary.<config>) and adds cost fields:
  result.usd            estimated USD at list price (actual cache TTL)
  result.usd_5m         same run re-priced with 5-minute-TTL cache writes
  result.cache_write / cache_read / output_tokens / final_context
  result.files_read_kb  bytes read, bucketed (skill / agent / project state / png)

`--iteration0 <subagents dir>` adds the 2026-10-13 pressure-test transcripts as
configuration "iteration0_transcripts" (no cost: output tokens unknown there).
"""
from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from bench.cost import cost_usd, sum_usage
from bench.transcript import classify_path, image_tokens, parse_transcript


def _stats(vals: list[float]) -> dict:
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0, "n": 0}
    return {"mean": round(statistics.mean(vals), 3),
            "stddev": round(statistics.pstdev(vals), 3) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 3), "max": round(max(vals), 3), "n": len(vals)}


def _buckets(t: dict) -> dict:
    """KB of text that actually entered the context per bucket (tool-result size, not file size).

    Images are excluded here (see _images): a PNG costs tokens by its pixels, not its bytes.
    """
    b: dict[str, int] = {}
    for f in t.get("files_read", []):
        k = classify_path(f["path"])
        if k == "project:png":
            continue
        n = f.get("chars") or 0
        if not n:  # no tool_result attribution (old transcripts): fall back to file size x times
            n = (f.get("bytes") or 0) * f.get("times", 1)
        b[k] = b.get(k, 0) + n
    return {k: round(v / 1024, 1) for k, v in sorted(b.items())}


def _images(t: dict) -> dict:
    views = 0
    toks = 0
    for f in t.get("files_read", []):
        if classify_path(f["path"]) == "project:png":
            views += f.get("times", 1)
            toks += image_tokens(f["path"]) * f.get("times", 1)
    return {"views": views, "est_tokens": toks}


def _main_model(res: dict) -> tuple[str | None, dict, float]:
    """Pick the model that did the work; return (model, usage without helper-model tokens, helper USD).

    Claude Code adds small helper calls (e.g. claude-haiku-5-5) to modelUsage; pricing the
    whole usage at the first key's rate was wrong by 100x in either direction.
    """
    mu = res.get("modelUsage") or {}
    usage = dict(res.get("usage") or {})
    if not mu:
        return None, usage, 0.0
    main = max(mu, key=lambda k: mu[k].get("costUSD", 0))
    helper_usd = 0.0
    cc = dict(usage.get("cache_creation") or {})
    for k, v in mu.items():
        if k == main:
            continue
        helper_usd += float(v.get("costUSD") or 0)
        usage["input_tokens"] = max(0, int(usage.get("input_tokens") or 0) - int(v.get("inputTokens") or 0))
        usage["output_tokens"] = max(0, int(usage.get("output_tokens") or 0) - int(v.get("outputTokens") or 0))
        usage["cache_read_input_tokens"] = max(0, int(usage.get("cache_read_input_tokens") or 0) - int(v.get("cacheReadInputTokens") or 0))
        w = int(v.get("cacheCreationInputTokens") or 0)
        usage["cache_creation_input_tokens"] = max(0, int(usage.get("cache_creation_input_tokens") or 0) - w)
        for ttl in ("ephemeral_1h_input_tokens", "ephemeral_5m_input_tokens"):  # take from the larger bucket first
            take = min(w, int(cc.get(ttl) or 0))
            cc[ttl] = int(cc.get(ttl) or 0) - take
            w -= take
    usage["cache_creation"] = cc
    return main, usage, helper_usd


def run_metrics(run_dir: Path) -> dict | None:
    rj = run_dir / "result.json"
    if not rj.exists():
        return None
    res = json.loads(rj.read_text(encoding="utf-8"))
    model, usage, helper_usd = _main_model(res)
    c_actual = cost_usd(usage, model, "actual")
    c_5m = cost_usd(usage, model, "5m")
    c_actual["usd_total"] += helper_usd
    c_5m["usd_total"] += helper_usd
    tp = run_dir / "transcript.jsonl"
    t = parse_transcript(str(tp)) if tp.exists() else {}
    g = {}
    gj = run_dir / "grading.json"
    if gj.exists():
        g = json.loads(gj.read_text(encoding="utf-8"))
    m = {
        "run": str(run_dir),
        "model": model,
        "helper_models_usd": round(helper_usd, 4),
        "reported_cost_usd": res.get("total_cost_usd"),
        "usd": round(c_actual["usd_total"], 4),
        "usd_5m": round(c_5m["usd_total"], 4),
        "usd_components": {k: round(v, 4) for k, v in c_actual.items() if k.startswith("usd_")},
        "images": _images(t) if t else {"views": 0, "est_tokens": 0},
        "input_tokens": c_actual["input_tokens"],
        "cache_write": c_actual["cache_write_5m_tokens"] + c_actual["cache_write_1h_tokens"],
        "cache_write_ttl": "1h" if c_actual["cache_write_1h_tokens"] else "5m",
        "cache_read": c_actual["cache_read_tokens"],
        "output_tokens": c_actual["output_tokens"],
        "thinking_tokens": (usage.get("output_tokens_details") or {}).get("thinking_tokens"),
        "total_tokens": c_actual["input_tokens"] + c_actual["cache_write_5m_tokens"] + c_actual["cache_write_1h_tokens"]
                        + c_actual["cache_read_tokens"] + c_actual["output_tokens"],
        "num_turns": res.get("num_turns"),
        "duration_s": round((res.get("duration_ms") or 0) / 1000, 1),
        "api_calls": t.get("calls"),
        "tool_uses": t.get("tool_uses"),
        "tools": t.get("tools"),
        "final_context": t.get("final_context"),
        "peak_context": t.get("peak_context"),
        "session_overhead_tokens": t.get("first_context"),  # system prompt + CLAUDE.md + tools, before any work
        "effort": t.get("effort"),
        "files_read_kb": _buckets(t) if t else {},
        "files_read": [{"path": f["path"], "file_kb": round((f.get("bytes") or 0) / 1024, 1),
                        "read_kb": round((f.get("chars") or 0) / 1024, 1), "times": f["times"]}
                       for f in t.get("files_read", [])],
        "pass_rate": (g.get("summary") or {}).get("pass_rate"),
        "passed": (g.get("summary") or {}).get("passed"),
        "failed": (g.get("summary") or {}).get("failed"),
        "total": (g.get("summary") or {}).get("total"),
        "expectations": g.get("expectations", []),
        "is_error": bool(res.get("is_error")),
        "stop_reason": res.get("stop_reason"),
        "subtype": res.get("subtype"),
    }
    (run_dir / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return m


def transcript_only_metrics(path: Path, label: str) -> dict:
    t = parse_transcript(str(path))
    u = sum_usage(t["usages"])
    c = cost_usd(u, t.get("model"), "actual")
    return {"run": str(path), "label": label, "model": t.get("model"), "usd": None, "usd_5m": None,
            "cache_write": c["cache_write_5m_tokens"] + c["cache_write_1h_tokens"], "cache_read": c["cache_read_tokens"],
            "output_tokens": None, "api_calls": t["calls"], "tool_uses": t["tool_uses"],
            "final_context": t["final_context"], "peak_context": t["peak_context"], "effort": t.get("effort"),
            "files_read_kb": _buckets(t), "pass_rate": None, "duration_s": None}


def analyze_iteration(it_dir: Path, skill_name: str, skill_path: str, iteration0: Path | None) -> dict:
    runs = []
    for meta_p in sorted(it_dir.glob("eval-*/eval_metadata.json")):
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        for cfg_dir in sorted(p for p in meta_p.parent.iterdir() if p.is_dir()):
            for run_dir in sorted(cfg_dir.glob("run-*")):
                m = run_metrics(run_dir)
                if not m:
                    continue
                runs.append({
                    "eval_id": meta["eval_id"], "eval_name": meta["eval_name"], "configuration": cfg_dir.name,
                    "run_number": int(run_dir.name.split("-")[1]),
                    "result": {"pass_rate": m["pass_rate"] or 0.0, "passed": m["passed"] or 0, "failed": m["failed"] or 0,
                               "total": m["total"] or 0, "time_seconds": m["duration_s"], "tokens": m["total_tokens"],
                               "tool_calls": m["tool_uses"] or 0, "errors": 1 if m["is_error"] else 0,
                               "usd": m["usd"], "usd_5m": m["usd_5m"], "cache_write": m["cache_write"],
                               "cache_read": m["cache_read"], "output_tokens": m["output_tokens"],
                               "final_context": m["final_context"], "api_calls": m["api_calls"],
                               "files_read_kb": m["files_read_kb"], "images": m["images"],
                               "session_overhead_tokens": m["session_overhead_tokens"],
                               "model": m["model"], "effort": m["effort"]},
                    "expectations": m["expectations"], "notes": [],
                })
    if iteration0 and iteration0.is_dir():
        for p in sorted(iteration0.glob("*.jsonl")):
            meta_f = p.with_suffix(".meta.json")
            label = json.loads(meta_f.read_text(encoding="utf-8")).get("description", p.stem) if meta_f.exists() else p.stem
            m = transcript_only_metrics(p, label)
            runs.append({"eval_id": -1, "eval_name": label, "configuration": "iteration0_transcripts", "run_number": 0,
                         "result": {"pass_rate": 0.0, "passed": 0, "failed": 0, "total": 0, "time_seconds": 0.0,
                                    "tokens": (m["cache_write"] or 0) + (m["cache_read"] or 0), "tool_calls": m["tool_uses"],
                                    "errors": 0, "usd": None, "usd_5m": None, "cache_write": m["cache_write"],
                                    "cache_read": m["cache_read"], "output_tokens": None, "final_context": m["final_context"],
                                    "api_calls": m["api_calls"], "files_read_kb": m["files_read_kb"], "model": m["model"],
                                    "images": {"views": 0, "est_tokens": 0}, "session_overhead_tokens": None,
                                    "effort": m["effort"]}, "expectations": [], "notes": ["transcript-only: output tokens unknown"]})
    configs = sorted({r["configuration"] for r in runs})
    summary = {}
    for c in configs:
        rs = [r["result"] for r in runs if r["configuration"] == c]
        summary[c] = {"pass_rate": _stats([r["pass_rate"] for r in rs]),
                      "time_seconds": _stats([r["time_seconds"] for r in rs]),
                      "tokens": _stats([r["tokens"] for r in rs]),
                      "usd": _stats([r["usd"] for r in rs]),
                      "usd_5m": _stats([r["usd_5m"] for r in rs]),
                      "cache_write": _stats([r["cache_write"] for r in rs]),
                      "cache_read": _stats([r["cache_read"] for r in rs]),
                      "output_tokens": _stats([r["output_tokens"] for r in rs]),
                      "final_context": _stats([r["final_context"] for r in rs])}
    # per-eval summaries (what the user actually wants to read)
    per_eval = {}
    for c in configs:
        for name in sorted({r["eval_name"] for r in runs if r["configuration"] == c}):
            rs = [r["result"] for r in runs if r["configuration"] == c and r["eval_name"] == name]
            per_eval.setdefault(c, {})[name] = {
                "n": len(rs), "usd": _stats([r["usd"] for r in rs]), "usd_5m": _stats([r["usd_5m"] for r in rs]),
                "cache_write": _stats([r["cache_write"] for r in rs]), "cache_read": _stats([r["cache_read"] for r in rs]),
                "output_tokens": _stats([r["output_tokens"] for r in rs]), "final_context": _stats([r["final_context"] for r in rs]),
                "time_seconds": _stats([r["time_seconds"] for r in rs]), "tool_calls": _stats([r["tool_calls"] for r in rs]),
                "api_calls": _stats([r["api_calls"] for r in rs]), "pass_rate": _stats([r["pass_rate"] for r in rs]),
                "files_read_kb": _merge_buckets([r["files_read_kb"] for r in rs]),
                "image_views": _stats([(r.get("images") or {}).get("views") for r in rs]),
                "image_tokens": _stats([(r.get("images") or {}).get("est_tokens") for r in rs]),
                "session_overhead_tokens": _stats([r.get("session_overhead_tokens") for r in rs])}
    delta = {}
    if "with_skill" in summary and "without_skill" in summary:
        for k in ("pass_rate", "time_seconds", "tokens", "usd"):
            delta[k] = f"{summary['with_skill'][k]['mean'] - summary['without_skill'][k]['mean']:+.3f}"
    notes = _analyst_notes(runs, per_eval)
    bench = {"metadata": {"skill_name": skill_name, "skill_path": skill_path,
                          "executor_model": next((r["result"]["model"] for r in runs
                                                  if r["configuration"] != "iteration0_transcripts" and r["result"].get("model")), None),
                          "timestamp": datetime.now(timezone.utc).isoformat(), "evals_run": sorted({r["eval_name"] for r in runs if r["eval_id"] >= 0}),
                          "runs_per_configuration": max([sum(1 for r in runs if r["configuration"] == c and r["eval_name"] == n)
                                                         for c in configs for n in {r["eval_name"] for r in runs}] or [0])},
             "runs": runs, "run_summary": {**summary, "delta": delta}, "eval_summary": per_eval, "notes": notes}
    (it_dir / "benchmark.json").write_text(json.dumps(bench, ensure_ascii=False, indent=1), encoding="utf-8")
    (it_dir / "benchmark.md").write_text(render_md(bench), encoding="utf-8")
    return bench


def _merge_buckets(bs: list[dict]) -> dict:
    out: dict[str, list] = {}
    for b in bs:
        for k, v in (b or {}).items():
            out.setdefault(k, []).append(v)
    return {k: round(statistics.mean(v), 1) for k, v in sorted(out.items())}


def _analyst_notes(runs, per_eval) -> list[str]:
    notes = []
    for c, evs in per_eval.items():
        for name, s in evs.items():
            if s["usd"]["n"] and s["usd"]["mean"]:
                cv = s["usd"]["stddev"] / s["usd"]["mean"]
                if cv > 0.25:
                    notes.append(f"{c}/{name}: cost varies a lot between runs (cv={cv:.2f}); treat the mean with care")
            fr = s["files_read_kb"]
            if fr:
                top = max(fr.items(), key=lambda kv: kv[1])
                notes.append(f"{c}/{name}: largest read bucket is {top[0]} ({top[1]} KB per run on average)")
    exp_pass = {}
    for r in runs:
        for e in r.get("expectations", []):
            exp_pass.setdefault(e["text"], []).append(e["passed"])
    for text, vals in exp_pass.items():
        if len(vals) >= 3 and all(vals):
            notes.append(f"assertion always passes: '{text[:70]}'")
        if len(vals) >= 3 and not any(vals):
            notes.append(f"assertion always fails: '{text[:70]}' (check the grader or the skill)")
    return notes


def render_md(b: dict) -> str:
    L = [f"# Benchmark: {b['metadata']['skill_name']}", "",
         f"model: {b['metadata']['executor_model']}  timestamp: {b['metadata']['timestamp']}", ""]
    for c, evs in b["eval_summary"].items():
        L += [f"## configuration: {c}", "",
              "| eval | n | USD (actual TTL) | USD (5m TTL) | cache write | cache read | output | final ctx | turns/API calls | tool uses | time s | pass |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for name, s in evs.items():
            f = lambda st, fmt="{:.2f}": (fmt.format(st["mean"]) + ("±" + fmt.format(st["stddev"]) if st["n"] > 1 else "")) if st["n"] else "—"
            L.append(f"| {name} | {s['n']} | {f(s['usd'])} | {f(s['usd_5m'])} | {f(s['cache_write'], '{:,.0f}')} | {f(s['cache_read'], '{:,.0f}')} | "
                     f"{f(s['output_tokens'], '{:,.0f}')} | {f(s['final_context'], '{:,.0f}')} | {f(s['api_calls'], '{:.1f}')} | {f(s['tool_calls'], '{:.1f}')} | "
                     f"{f(s['time_seconds'], '{:.0f}')} | {f(s['pass_rate'], '{:.2f}')} |")
        L.append("")
        L += ["| eval | session overhead (tokens) | image views / est. tokens | text read per run (KB, mean) |",
              "| --- | ---: | ---: | --- |"]
        for name, s in evs.items():
            L.append(f"| {name} | {s['session_overhead_tokens']['mean']:,.0f} | "
                     f"{s['image_views']['mean']:.1f} / {s['image_tokens']['mean']:,.0f} | "
                     + ", ".join(f"{k} {v}" for k, v in s["files_read_kb"].items()) + " |")
        L.append("")
    if b["notes"]:
        L += ["## notes", ""] + [f"* {n}" for n in b["notes"]] + [""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iteration_dir")
    ap.add_argument("--skill-name", default="techdeck-workflow")
    ap.add_argument("--skill-path", default="")
    ap.add_argument("--iteration0", default=None, help="directory of 2026-10-13 subagent transcripts to include")
    a = ap.parse_args(argv)
    b = analyze_iteration(Path(a.iteration_dir), a.skill_name, a.skill_path, Path(a.iteration0) if a.iteration0 else None)
    print(render_md(b))


if __name__ == "__main__":
    main()
