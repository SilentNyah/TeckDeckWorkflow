"""Parse a Claude Code session / subagent transcript (.jsonl) into per-call facts.

What we need from a transcript and why:
  * per API call: usage (cache write / read, input) -> context growth and cost
    composition. `output_tokens` in these records is a partial placeholder
    (thinking is hidden on Fable), so it is reported but never trusted; the
    headless CLI's result.json carries the true output count.
  * tool calls: counts per tool, and which files were read and how large they
    are -> attributes cost to fixed documents (skill, agents, references) vs
    project state files (storyboard, review_state, ...).
  * effort / model actually used by the session.

A transcript stores one assistant message as several records sharing
`message.id` (one per content block); the usage snapshot on the last record
for an id is the one we keep.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter

_PATH_RE = re.compile(r"""(?:[A-Za-z]:[\\/]|/[A-Za-z]/|/)[^\s"'`;|&<>()$]+""")
_READ_CMDS = ("cat", "sed", "head", "tail", "grep", "awk", "less", "more", "type", "Get-Content", "python")


def _iter_records(path: str):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    parts.append(b.get("text", ""))
                elif b.get("type") == "tool_result":
                    parts.append(_text_of(b.get("content")))
        return "".join(parts)
    return ""


def parse_transcript(path: str, resolve_sizes: bool = True) -> dict:
    """Return a dict with calls, tool usage, files read and session facts."""
    calls: dict[str, dict] = {}        # message id -> last usage snapshot
    order: list[str] = []
    tools = Counter()
    reads: Counter = Counter()          # (path) -> times read
    read_chars: Counter = Counter()     # (path) -> chars that actually entered the context
    use_paths: dict[str, list[str]] = {}  # tool_use id -> paths it read
    bash_cmds: list[str] = []
    tool_result_chars = 0
    first_prompt = None
    effort = None
    model = None
    requested_model = None
    agent_text_chars = 0

    for r in _iter_records(path):
        rtype = r.get("type")
        m = r.get("message") or {}
        if rtype == "user":
            if first_prompt is None:
                first_prompt = _text_of(m.get("content"))
            c = m.get("content")
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        n = len(_text_of(b.get("content")))
                        tool_result_chars += n
                        paths = use_paths.get(b.get("tool_use_id") or "", [])
                        for p in paths:  # a multi-file shell command: split evenly
                            read_chars[p] += n // len(paths)
            continue
        if rtype != "assistant":
            continue
        mid = m.get("id") or r.get("requestId") or r.get("uuid")
        if mid not in calls:
            order.append(mid)
        if m.get("usage"):
            calls[mid] = m["usage"]
        elif mid not in calls:
            calls[mid] = {}
        effort = effort or r.get("effort")
        model = model or m.get("model")
        requested_model = requested_model or r.get("requestedModel")
        for b in m.get("content") or []:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "text":
                agent_text_chars += len(b.get("text") or "")
            elif t == "tool_use":
                name = b.get("name") or "?"
                tools[name] += 1
                inp = b.get("input") or {}
                if name == "Read" and inp.get("file_path"):
                    p = os.path.normpath(inp["file_path"])
                    reads[p] += 1
                    use_paths[b.get("id") or ""] = [p]
                elif name in ("Bash", "PowerShell"):
                    cmd = str(inp.get("command") or "")
                    bash_cmds.append(cmd)
                    ps = _paths_read_by_shell(cmd)
                    for p in ps:
                        reads[p] += 1
                    if ps:
                        use_paths[b.get("id") or ""] = ps

    usages = [calls[mid] for mid in order]
    ctx = [int(u.get("input_tokens") or 0) + int(u.get("cache_creation_input_tokens") or 0)
           + int(u.get("cache_read_input_tokens") or 0) for u in usages]
    files = []
    for p, n in reads.most_common():
        size = None
        if resolve_sizes:
            try:
                size = os.path.getsize(p)
            except OSError:
                size = None
        files.append({"path": p, "times": n, "bytes": size, "chars": read_chars.get(p, 0)})
    return {
        "path": path,
        "calls": len(usages),
        "usages": usages,
        "context_per_call": ctx,
        "final_context": ctx[-1] if ctx else 0,
        "peak_context": max(ctx) if ctx else 0,
        "first_context": ctx[0] if ctx else 0,
        "tools": dict(tools),
        "tool_uses": sum(tools.values()),
        "files_read": files,
        "bash_commands": bash_cmds,
        "tool_result_chars": tool_result_chars,
        "agent_text_chars": agent_text_chars,
        "effort": effort,
        "model": model,
        "requested_model": requested_model,
        "first_prompt": first_prompt or "",
    }


def _paths_read_by_shell(cmd: str) -> list[str]:
    """Best-effort: absolute paths that appear in a shell command which reads files.

    Variables like $P/... are expanded when the command assigns them
    (P="..."; cat "$P/x") — common in these transcripts.
    """
    if not any(re.search(r"(^|[\s;|&(])" + re.escape(c) + r"\b", cmd) for c in _READ_CMDS):
        return []
    assigns = dict(re.findall(r"""\b([A-Za-z_][A-Za-z0-9_]*)=["']?([^"'\s;]+)["']?""", cmd))
    expanded = cmd
    for k, v in assigns.items():
        expanded = expanded.replace("${%s}" % k, v).replace("$" + k + "/", v + "/")
    out = []
    for p in _PATH_RE.findall(expanded):
        p = p.rstrip('",;:)')
        if "/" not in p and "\\" not in p:
            continue
        # Git Bash spells C:/x as /c/x (or /C/x); normalise so sizes resolve on Windows
        m = re.match(r"^/([A-Za-z])/(.*)$", p)
        if m:
            p = f"{m.group(1).upper()}:/{m.group(2)}"
        # keep only things that look like files (have an extension) to avoid dirs
        if not re.search(r"\.[A-Za-z0-9]{1,6}$", p):
            continue
        out.append(os.path.normpath(p))
    return out


def classify_path(p: str) -> str:
    """Bucket a read path for the fixed-vs-project cost breakdown.

    Falls back on the basename because shell reads often use a variable assigned
    in an earlier command (`sed -n ... "$RS"`), which leaves only the file name.
    """
    q = p.replace("\\", "/").lower()
    base = q.rsplit("/", 1)[-1]
    if "/tool-results/" in q:
        return "tool-output-files"          # the agent re-reading its own persisted tool output
    if "/.claude/agents/" in q or "/agents/techdeck-slide" in q or base.startswith("techdeck-slide-"):
        return "agent-definition"
    if "/pptx-toolkit/" in q or base in ("deckkit.py", "codehl.py", "pictogram.py", "check_deck.py",
                                         "render_deck.py", "new_deck.py", "inspect_deck.py", "recipes.md",
                                         "ooxml-gotchas.md", "edit-script.py"):
        return "skill:pptx-toolkit"
    if "/techdeck-workflow/" in q or base in ("statekit.py", "renumber.py", "review-rubric.md", "visual-design.md",
                                              "editorial-rules.md", "state-schema.md", "status-vocabulary.md",
                                              "deck-profile.md", "examples-rules.md", "skill.md") \
            or base.startswith("phase") or base in ("storyboard-entry.md", "review-report.md", "finding-entry.md",
                                                     "source-entry.md", "comment-import.md"):
        return "skill:techdeck-workflow"
    if q.endswith((".png", ".jpg", ".jpeg")):
        return "project:png"
    if "/slides/storyboard" in q or base == "storyboard.md":
        return "project:storyboard"
    if "/slides/review_state" in q or base == "review_state.md":
        return "project:review_state"
    if "/sources/" in q or base == "source_index.md":
        return "project:sources"
    if "/slides/reviews/" in q or "review-result" in q or "build-result" in q or base == "deck-final-review.md":
        return "project:reviews"
    if "/notes/" in q or base in ("task.md", "agents.md", "outline.md", "deck-profile.json", "glossary.md",
                                  "decisions.md", "findings.md", "open_questions.md") or "/slides/" in q \
            or "/assets/" in q or "/examples/" in q:
        return "project:other"
    return "other"


def png_dims(path: str) -> tuple[int, int] | None:
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        import struct
        w, h = struct.unpack(">II", head[16:24])
        return w, h
    except OSError:
        return None


def image_tokens(path: str) -> int:
    """Anthropic's rule of thumb: tokens ~= width * height / 750 (capped by downscaling)."""
    d = png_dims(path)
    if not d:
        return 0
    w, h = d
    scale = min(1.0, 1568 / max(w, h))
    return int(w * scale * h * scale / 750)
