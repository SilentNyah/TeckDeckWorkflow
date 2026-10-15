"""Programmatic grading of benchmark runs -> grading.json per run.

The assertions mirror evals.json (same order, same wording) so the viewer and
benchmark show the same text. Every check is a regex / file check on the
response, the transcript, or the run's project copy; nothing is judged by a
model. Subjective quality is left to the human review in the viewer.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from bench.transcript import parse_transcript

# English fragments of the four sources Slide 030 cites. A dispatch that
# contains any of them has transcribed source text (the contract forbids it).
QUOTE_FRAGMENTS = [
    "active only when the UI is visible",
    "as long as the user might return",
    "keeps the upstream producer active",
    "keep the flow active forever",
    "start the producer immediately",
    "Don't make the UI observe the UI state",
    "To convert any flow to a StateFlow",
]
# Not in the list on purpose: the SRC-002 item name "Use lifecycle-aware UI state collection."
# — it appears verbatim in the prior review/build results that a dispatch legitimately pastes
# as PRIOR, and the project's CF-76 requires citing the item name next to its label.
VERDICTS = ("PASS", "PASS_WITH_MINOR_FIXES", "REVISION_REQUIRED", "BLOCKED")
DISPOSITIONS = ("FIXED", "PUSHED_BACK", "PARTIAL", "NEEDS_USER")


def _has(text: str, pattern: str, flags=re.M) -> bool:
    return re.search(pattern, text, flags) is not None


def _keys_present(text: str, keys: list[str]) -> tuple[bool, str]:
    # accepts "MODE:", "`MODE`:", "| MODE |", "**MODE**:" at a line start or after whitespace,
    # and a section-heading rendering of the same key ("### CARRIED")
    missing = [k for k in keys
               if not _has(text, r"(^|[\s|*`])\**`?" + re.escape(k) + r"`?\**\s*[:：|]")
               and not _has(text, r"^#{1,4}\s*`?" + re.escape(k) + r"`?\b")]
    return (not missing), ("missing: " + ", ".join(missing) if missing else "all keys found")


def _quotes_absent(text: str) -> tuple[bool, str]:
    hits = [f for f in QUOTE_FRAGMENTS if f.lower() in text.lower()]
    return (not hits), ("found: " + "; ".join(hits) if hits else "no source fragments found")


def _strip_carried(text: str) -> str:
    """Drop a pasted `## Feedback carried forward` block (it is allowed to be verbatim)."""
    m = re.search(r"^#{1,3} Feedback carried forward.*?(?=^#{1,2} (?!#)|\Z)", text, flags=re.M | re.S)
    return (text[:m.start()] + text[m.end():]) if m else text


def _finding_blocks(text: str) -> dict[str, str]:
    """id -> block text; the heading line is kept because a prior finding's status may sit there
    (`### FINDING-001 ─ \\`RESOLVED\\``), which the reviewer's output cap invites."""
    blocks = {}
    for m in re.finditer(r"^(#{3,4} (FINDING-\d+)[^\n]*)\n(.*?)(?=^#{3,4} |\Z)", text, flags=re.M | re.S):
        blocks[m.group(2)] = m.group(1) + "\n" + m.group(3)
    return blocks


def _has_key(block: str, key: str) -> bool:
    """`* Key:` on its own line, or inline (`Severity: X ／ Category: Y`), or a status in the heading."""
    if _has(block, r"(^|[\s／|/])\**" + key + r"\**\s*[:：]"):
        return True
    if key == "Status":
        head = block.splitlines()[0] if block else ""
        return re.search(r"\b(RESOLVED|OPEN|DEFERRED|REJECTED)\b", head) is not None
    return False


def grade_S0(resp: str, t: dict, project: Path) -> list[tuple[bool, str]]:
    r = []
    r.append((_has(resp, r"phase3-slide-review"), "route string search"))
    ok, ev = _keys_present(resp, ["PROJECT_ROOT", "MODE", "SLIDE", "STORYBOARD", "SOURCES", "CARRIED"])
    r.append((ok, ev))
    agent_tools = {k: v for k, v in (t.get("tools") or {}).items() if k in ("Agent", "Task")}
    r.append((not agent_tools, f"agent tool uses: {agent_tools or 'none'}"))
    r.append((not (project / "slides" / "deck.pptx").exists(), "slides/deck.pptx exists" if (project / "slides" / "deck.pptx").exists() else "no deck created"))
    r.append(_quotes_absent(_strip_carried(resp)))
    return r


def grade_S1(resp: str, t: dict, project: Path) -> list[tuple[bool, str]]:
    r = []
    ok, ev = _keys_present(resp, ["MODE", "PROJECT_ROOT", "SLIDE", "PNG", "STORYBOARD", "SOURCES",
                                  "RUBRIC", "VISUAL", "CARRIED", "PRIOR", "ITERATION"])
    r.append((ok, ev))
    r.append(_quotes_absent(_strip_carried(resp)))
    both = _has(resp, r"review-rubric\.md") and _has(resp, r"visual-design\.md")
    r.append((both, "rubric path %s, visual path %s" % ("found" if _has(resp, r"review-rubric\.md") else "missing",
                                                      "found" if _has(resp, r"visual-design\.md") else "missing")))
    bad = _has(resp, r"APPROVED\s*にし|approve the slide|set .*APPROVED", re.I | re.M)
    r.append((not bad, "approval instruction found" if bad else "no approval instruction"))
    return r


def grade_S3(resp: str, t: dict, project: Path) -> list[tuple[bool, str]]:
    r = []
    r.append((_has(resp.lstrip(), r"\A(?:```\w*\n)?## BUILD RESULT"), "first non-blank line: " + resp.strip().splitlines()[0][:60] if resp.strip() else "empty"))
    rows = {}
    for fid in ("FINDING-001", "FINDING-002", "FINDING-003"):
        m = re.search(r"^\|\s*`?" + fid + r"`?\s*\|\s*`?(" + "|".join(DISPOSITIONS) + r")`?", resp, flags=re.M)
        rows[fid] = m.group(1) if m else None
    r.append((all(rows.values()), f"dispositions: {rows}"))
    r.append((rows.get("FINDING-001") not in (None, "PUSHED_BACK"), f"FINDING-001 -> {rows.get('FINDING-001')}"))
    cc = _has(resp, r"^### Character count") and _has(resp, r"Not counted", re.I)
    r.append((cc, "Character count + Not counted present" if cc else "section or 'Not counted' missing"))
    r.append((_has(resp, r"^### Deviations from spec"), "section search"))
    r.append((_has(resp, r"^### Progress file"), "section search"))
    appr = _has(resp, r"\bAPPROVED\b")
    r.append((not appr, "'APPROVED' appears" if appr else "no APPROVED"))
    return r


def grade_S4(resp: str, t: dict, project: Path) -> list[tuple[bool, str]]:
    r = []
    r.append((_has(resp.lstrip(), r"\A(?:```\w*\n)?## REVIEW RESULT"), "first non-blank line: " + resp.strip().splitlines()[0][:60] if resp.strip() else "empty"))
    heads = ["Slide", "Iteration", "Overall result", "Counts", "Rubric items failed", "3-second takeaway",
             "Cold-read summary", "Body chars"]
    missing = [h for h in heads if not _has(resp, r"^\*\s*" + re.escape(h))]
    r.append((not missing, "missing header lines: " + ", ".join(missing) if missing else "all header lines present"))
    m = re.search(r"^\*\s*Overall result:\s*`?([A-Z_]+)`?", resp, flags=re.M)
    verdict = m.group(1) if m else None
    r.append((verdict in VERDICTS, f"verdict={verdict}"))
    blocks = _finding_blocks(resp)
    prior = {}
    for fid in ("FINDING-001", "FINDING-002", "FINDING-003"):
        b = blocks.get(fid, "")
        sm = re.search(r"Status\**\s*[:：]\s*`?([A-Z_]+)`?", b)
        if not sm:  # also accept a heading/table/line form "FINDING-001 ─ `RESOLVED`"
            sm = re.search(fid + r"[^\n]*?\b(RESOLVED|OPEN|DEFERRED|REJECTED)\b", resp)
        prior[fid] = sm.group(1) if sm else None
    r.append((all(prior.values()), f"prior statuses: {prior}"))
    # Prior findings (001–003) may be cited by id + Status only (the reviewer's output cap says so);
    # a NEW finding must carry Severity, Category, Rubric and Status.
    bad = []
    for fid, b in blocks.items():
        keys = ("Status",) if fid in ("FINDING-001", "FINDING-002", "FINDING-003") else ("Severity", "Category", "Rubric", "Status")
        for key in keys:
            if not _has_key(b, key):
                bad.append(f"{fid}:{key}")
    r.append((not bad and bool(blocks), "all finding blocks complete" if blocks and not bad else f"incomplete: {bad or 'no finding blocks'}"))
    r.append((_has(resp, r"^### R6 notes"), "section search"))
    ok = verdict not in (None, "BLOCKED") and not _has(resp, r"Overall result:\s*`?APPROVED")
    r.append((ok, f"verdict={verdict}"))
    return r


GRADERS = {"S0-turn-start": grade_S0, "S1-reviewer-dispatch": grade_S1,
           "S3-builder-fix": grade_S3, "S4-reviewer-slide": grade_S4}


def grade_run(run_dir: Path, meta: dict) -> dict:
    resp_p = run_dir / "outputs" / "response.md"
    resp = resp_p.read_text(encoding="utf-8", errors="replace") if resp_p.exists() else ""
    tp = run_dir / "transcript.jsonl"
    t = parse_transcript(str(tp), resolve_sizes=False) if tp.exists() else {"tools": {}, "tool_uses": 0}
    grader = GRADERS[meta["eval_name"]]
    results = grader(resp, t, run_dir / "project")
    texts = meta.get("assertions", [])
    if len(texts) != len(results):
        raise RuntimeError(f"{meta['eval_name']}: {len(texts)} assertions in evals.json vs {len(results)} checks in grader")
    expectations = [{"text": txt, "passed": bool(ok), "evidence": ev} for txt, (ok, ev) in zip(texts, results)]
    passed = sum(1 for e in expectations if e["passed"])
    timing = {}
    tj = run_dir / "timing.json"
    if tj.exists():
        timing = json.loads(tj.read_text(encoding="utf-8"))
    return {
        "expectations": expectations,
        "summary": {"passed": passed, "failed": len(expectations) - passed, "total": len(expectations),
                    "pass_rate": round(passed / len(expectations), 3) if expectations else 0.0},
        "execution_metrics": {"tool_calls": t.get("tools", {}), "total_tool_calls": t.get("tool_uses", 0),
                              "total_steps": t.get("calls", 0), "errors_encountered": 1 if timing.get("is_error") else 0,
                              "output_chars": len(resp), "transcript_chars": t.get("agent_text_chars", 0)},
        "timing": {"executor_duration_seconds": timing.get("total_duration_seconds", 0.0),
                   "grader_duration_seconds": 0.0,
                   "total_duration_seconds": timing.get("total_duration_seconds", 0.0)},
    }


def grade_iteration(it_dir: Path) -> int:
    n = 0
    for meta_p in sorted(it_dir.glob("eval-*/eval_metadata.json")):
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        for run_dir in sorted(meta_p.parent.glob("*/run-*")):
            if not (run_dir / "outputs").is_dir():
                continue
            g = grade_run(run_dir, meta)
            (run_dir / "grading.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
            n += 1
            print(f"{run_dir.relative_to(it_dir)}: {g['summary']['passed']}/{g['summary']['total']}")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("iteration_dir")
    a = ap.parse_args(argv)
    print("graded runs:", grade_iteration(Path(a.iteration_dir)))


if __name__ == "__main__":
    main()
