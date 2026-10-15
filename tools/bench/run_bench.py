"""Run the techdeck-workflow credit benchmark: one `claude -p` session per (eval, rep).

Layout written (matches skill-creator's viewer and aggregator):
  <workspace>/iteration-<N>/eval-<id>-<name>/eval_metadata.json
  <workspace>/iteration-<N>/eval-<id>-<name>/<config>/run-<k>/
      project/            fresh copy of the fixture (the session's cwd)
      prompt.md           the rendered prompt that was sent
      result.json         `claude -p --output-format json` output (true usage + cost)
      stderr.txt
      outputs/response.md the agent's final text (what the viewer shows)
      timing.json         total_tokens / total_duration_seconds / total_cost_usd / usage
      transcript.jsonl    the session transcript copied from ~/.claude/projects

Why `claude -p` and not the Agent tool: the task notification of a subagent reports
its final context size, and transcripts hide thinking tokens; the headless CLI
reports true usage and `total_cost_usd` (see memory note techdeck-token-measurement-facts).

Runs are serial on purpose (529 overload retries, and comparability with the
real workflow where build and render are serial).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~").expanduser()
DEFAULTS = {
    "SKILL_DIR": str(HOME / ".claude" / "skills" / "techdeck-workflow").replace("\\", "/"),
    "AGENTS_DIR": str(HOME / ".claude" / "agents").replace("\\", "/"),
    "TOOLKIT": str(HOME / ".claude" / "skills" / "pptx-toolkit" / "scripts").replace("\\", "/"),
}
_SECTION_RE = r"^## {name}\s*$.*?(?=^## |\Z)"


def extract_section(text: str, heading: str) -> str:
    """Return the `## <heading>` section (heading line included) or '' if absent."""
    m = re.search(_SECTION_RE.format(name=re.escape(heading)), text, flags=re.M | re.S)
    return m.group(0).rstrip() + "\n" if m else ""


def render_prompt(template: str, ctx: dict, project_dir: Path) -> str:
    """Fill {{KEY}}, {{CARRIED}} and {{FILE:name}} placeholders."""
    out = template
    if "{{CARRIED}}" in out:
        rs = (project_dir / "slides" / "review_state.md").read_text(encoding="utf-8", errors="replace")
        cf = extract_section(rs, "Feedback carried forward")
        if not cf:
            raise RuntimeError("review_state.md has no '## Feedback carried forward' section")
        out = out.replace("{{CARRIED}}", cf)
    for m in re.finditer(r"\{\{FILE:([^}]+)\}\}", template):
        p = project_dir / m.group(1)
        out = out.replace(m.group(0), p.read_text(encoding="utf-8", errors="replace"))
    for m in re.finditer(r"\{\{CARRIED_CF:(\d+)\}\}", template):
        # the revised contract: CARRIED = `statekit.py show-cf --for-slide N` (one line per rule)
        kit = Path(ctx["SKILL_DIR"]) / "scripts" / "statekit.py"
        res = subprocess.run([sys.executable, "-X", "utf8", str(kit), "show-cf",
                              str(project_dir / "slides" / "review_state.md"), "--for-slide", m.group(1),
                              "--storyboard", str(project_dir / "slides" / "storyboard.md")],
                             capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            raise RuntimeError(f"show-cf failed: {res.stderr}")
        out = out.replace(m.group(0), res.stdout.rstrip("\n"))
    for k, v in ctx.items():
        out = out.replace("{{%s}}" % k, v)
    left = re.findall(r"\{\{[A-Z_]+(?::[^}]*)?\}\}", out)
    if left:
        raise RuntimeError(f"unfilled placeholders: {sorted(set(left))}")
    return out


def parse_extra(s: str | None) -> list[str]:
    """`--extra "--effort high"`: one quoted string, split like a shell would.

    argparse cannot take `--extra --effort high` (the inner `--effort` looks like an option),
    which is how the effort arm of iteration-2 failed to launch.
    """
    import shlex
    return shlex.split(s) if s else []


def _completed(run_dir: Path) -> bool:
    """A run counts as done only if its result.json is a non-error result."""
    rj = run_dir / "result.json"
    if not rj.exists():
        return False
    try:
        return not json.loads(rj.read_text(encoding="utf-8")).get("is_error")
    except (json.JSONDecodeError, OSError):
        return False


def find_transcript(session_id: str) -> Path | None:
    hits = glob.glob(str(HOME / ".claude" / "projects" / "*" / f"{session_id}.jsonl"))
    return Path(hits[0]) if hits else None


def usage_total(usage: dict) -> int:
    return sum(int(usage.get(k) or 0) for k in
               ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))


CLAUDE_BIN = os.environ.get("BENCH_CLAUDE_BIN", "claude")


def build_cmd(prompt_len: int, session_id: str, agent: str | None, max_turns: int,
              model: str | None, extra: list[str]) -> list[str]:
    cmd = [CLAUDE_BIN, "-p", "--output-format", "json", "--strict-mcp-config",
           "--max-turns", str(max_turns), "--session-id", session_id,
           "--dangerously-skip-permissions"]
    if agent:
        cmd += ["--agent", agent]
    if model:
        cmd += ["--model", model]
    cmd += extra
    return cmd


def run_one(run_dir: Path, fixture: Path, prompt_template: str, ctx: dict, agent: str | None,
            max_turns: int, model: str | None, extra: list[str], log, timeout_s: int = 3600,
            retries: int = 2) -> dict:
    project = run_dir / "project"
    if project.exists():
        shutil.rmtree(project)
    shutil.copytree(fixture, project)
    pctx = dict(ctx, PROJECT_ROOT=str(project.resolve()).replace("\\", "/"))
    prompt = render_prompt(prompt_template, pctx, project)
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    attempt = 0
    while True:
        attempt += 1
        sid = str(uuid.uuid4())
        cmd = build_cmd(len(prompt), sid, agent, max_turns, model, extra)
        log(f"  attempt {attempt}: {' '.join(cmd[:6])} ... agent={agent} prompt_chars={len(prompt)}")
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, input=prompt, cwd=str(project), env=env, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=timeout_s,
                                  shell=(os.name == "nt"))
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            rc, out, err = -1, (e.stdout or ""), f"TIMEOUT after {timeout_s}s\n" + (e.stderr or "")
        wall = time.time() - t0
        (run_dir / "stderr.txt").write_text(err or "", encoding="utf-8")
        result = None
        try:
            result = json.loads(out) if out.strip() else None
        except json.JSONDecodeError:
            # stream may contain extra lines; keep the last JSON object
            for line in reversed(out.splitlines()):
                try:
                    result = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
        ok = result is not None and not result.get("is_error") and rc == 0
        # retry only on capacity errors; a usage error (bad flag, unknown model) must fail fast
        overloaded = bool(re.search(r"\b529\b|overloaded|rate.?limit|ECONNRESET|ETIMEDOUT", (err or "") + (out or ""), flags=re.I))
        if result is not None:
            result["_session_id"] = sid
            result["_wall_seconds"] = wall
            result["_attempt"] = attempt
            (run_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        if ok or attempt > retries or not overloaded:
            break
        log(f"  attempt {attempt} failed (rc={rc}, overloaded={overloaded}); sleeping 300s before retry")
        time.sleep(300)
    # persist outputs
    outputs = run_dir / "outputs"
    outputs.mkdir(exist_ok=True)
    text = (result or {}).get("result") or ""
    if not text and result is None:
        text = f"(no JSON result; rc={rc})\n\nSTDERR:\n{err}\n\nSTDOUT:\n{out[:5000]}"
    (outputs / "response.md").write_text(text, encoding="utf-8")
    usage = (result or {}).get("usage") or {}
    timing = {
        "total_tokens": usage_total(usage),
        "duration_ms": (result or {}).get("duration_ms"),
        "total_duration_seconds": round(((result or {}).get("duration_ms") or wall * 1000) / 1000, 1),
        "wall_seconds": round(wall, 1),
        "total_cost_usd": (result or {}).get("total_cost_usd"),
        "num_turns": (result or {}).get("num_turns"),
        "usage": usage,
        "model_usage": (result or {}).get("modelUsage"),
        "is_error": (result or {}).get("is_error", result is None),
        "returncode": rc,
        "session_id": sid,
    }
    (run_dir / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding="utf-8")
    tp = find_transcript(sid)
    if tp:
        shutil.copy2(tp, run_dir / "transcript.jsonl")
        sub = tp.with_suffix("") / "subagents"
        if sub.is_dir():
            shutil.copytree(sub, run_dir / "subagents", dirs_exist_ok=True)
    else:
        log("  transcript not found for session " + sid)
    log(f"  done: rc={rc} tokens={timing['total_tokens']:,} usd={timing['total_cost_usd']} "
        f"turns={timing['num_turns']} {timing['total_duration_seconds']}s")
    return timing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--evals", required=True, help="path to evals.json")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--fixture", required=True, help="fixture directory (built by make_fixture)")
    ap.add_argument("--iteration", type=int, default=1)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--only", nargs="*", default=None, help="eval ids or names to run")
    ap.add_argument("--config", default="with_skill", help="configuration label (viewer groups by it)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-turns", type=int, default=None, help="override evals' max_turns")
    ap.add_argument("--skill-dir", default=DEFAULTS["SKILL_DIR"])
    ap.add_argument("--agents-dir", default=DEFAULTS["AGENTS_DIR"])
    ap.add_argument("--toolkit", default=DEFAULTS["TOOLKIT"])
    ap.add_argument("--extra", default=None, help='extra args passed to claude, as ONE quoted string, e.g. --extra "--effort high"')
    ap.add_argument("--dry-run", action="store_true", help="render prompts only, no claude calls")
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args(argv)

    evals_path = Path(a.evals)
    spec = json.loads(evals_path.read_text(encoding="utf-8"))
    ws = Path(a.workspace)
    it_dir = ws / f"iteration-{a.iteration}"
    it_dir.mkdir(parents=True, exist_ok=True)
    logf = open(it_dir / "progress.log", "a", encoding="utf-8")

    def log(msg):
        line = f"{datetime.now().strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n"); logf.flush()

    ctx = {"SKILL_DIR": a.skill_dir, "AGENTS_DIR": a.agents_dir, "TOOLKIT": a.toolkit}
    selected = []
    for e in spec["evals"]:
        if a.only and str(e["id"]) not in a.only and e["name"] not in a.only:
            continue
        selected.append(e)
    log(f"benchmark start: iteration={a.iteration} evals={[e['name'] for e in selected]} reps={a.reps} config={a.config}")
    for e in selected:
        eval_dir = it_dir / f"eval-{e['id']}-{e['name']}"
        cfg_dir = eval_dir / a.config
        cfg_dir.mkdir(parents=True, exist_ok=True)
        template = (evals_path.parent / e["prompt_file"]).read_text(encoding="utf-8")
        meta = {"eval_id": e["id"], "eval_name": e["name"], "prompt": e["prompt"],
                "prompt_file": e["prompt_file"], "agent": e.get("agent"),
                "expected_output": e.get("expected_output"), "assertions": e.get("assertions", [])}
        for d in (eval_dir, cfg_dir):
            (d / "eval_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        for k in range(1, a.reps + 1):
            run_dir = cfg_dir / f"run-{k}"
            if _completed(run_dir):
                log(f"skip {e['name']} run-{k}: completed result.json exists")
                continue
            run_dir.mkdir(parents=True, exist_ok=True)
            log(f"run {e['name']} run-{k}")
            if a.dry_run:
                project = run_dir / "project"
                if not project.exists():
                    shutil.copytree(Path(a.fixture), project)
                p = render_prompt(template, dict(ctx, PROJECT_ROOT=str(project.resolve()).replace("\\", "/")), project)
                (run_dir / "prompt.md").write_text(p, encoding="utf-8")
                log(f"  dry-run: prompt {len(p):,} chars written")
                continue
            run_one(run_dir, Path(a.fixture), template, ctx, e.get("agent"),
                    a.max_turns or e.get("max_turns", 60), a.model, parse_extra(a.extra), log, timeout_s=a.timeout)
    log("benchmark end")
    logf.close()


if __name__ == "__main__":
    main()
