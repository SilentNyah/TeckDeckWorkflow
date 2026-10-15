"""Build the read-only benchmark fixture from a real deck project.

Why a curated copy instead of the live project:
  * runs must not touch the real project (the orchestrator scenario legitimately
    edits review_state.md);
  * the builder scenario is measured "without deck or PowerPoint" (as in the
    2026-10-13 pressure test) so deck.pptx and its backups are left out;
  * only the files an agent can legitimately read are copied, so the
    files-read breakdown is attributable.

Usage:
  python -m bench.make_fixture --source "D:/documents/android/architecture" \
      --dest "<workspace>/fixture" --slides 29 30 31 --png-dir output/png-final \
      --extra <evals/files dir>
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
from pathlib import Path

# relative paths (files or directories) to copy from the source project
COPY = [
    "TASK.md",
    "AGENTS.md",
    "README.md",
    ".gitignore",
    "slides/storyboard.md",
    "slides/review_state.md",
    "slides/outline.md",
    "slides/deck-profile.json",
    "slides/AGENTS.md",
    "slides/reviews",
    "sources/source_index.md",
    "notes",
    "examples",
]
# inside copied directories, skip these patterns
SKIP = ["*.pptx", "*.bak-*", "__pycache__", "*.pyc", "*.pdf", "*.png", "*.jpg"]
# diagram sources: only editable .py files, not generated pptx
DIAGRAM_GLOB = "assets/diagrams/*.py"


def _ignored(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in SKIP)


def _copy_tree(src: Path, dst: Path) -> list[str]:
    copied = []
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not _ignored(d)]
        for f in files:
            if _ignored(f):
                continue
            s = Path(root) / f
            rel = s.relative_to(src)
            d = dst / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            copied.append(str(rel))
    return copied


def build_fixture(source: Path, dest: Path, slides: list[int], png_dir: str,
                  extra: Path | None) -> dict:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    manifest = {"source": str(source), "copied": [], "pngs": [], "extra": [], "omitted": []}
    for rel in COPY:
        s = source / rel
        if not s.exists():
            manifest["omitted"].append(rel + " (missing in source)")
            continue
        if s.is_dir():
            for c in _copy_tree(s, dest / rel):
                manifest["copied"].append(f"{rel}/{c}")
        else:
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, dest / rel)
            manifest["copied"].append(rel)
    for p in sorted((source).glob(DIAGRAM_GLOB)):
        d = dest / p.relative_to(source)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, d)
        manifest["copied"].append(str(p.relative_to(source)))
    # rendered PNGs for the target slide and its neighbours -> output/png/slide-NN.png
    out_png = dest / "output" / "png"
    out_png.mkdir(parents=True, exist_ok=True)
    for n in slides:
        s = source / png_dir / f"slide-{n}.png"
        if s.exists():
            shutil.copy2(s, out_png / f"slide-{n}.png")
            manifest["pngs"].append(f"output/png/slide-{n}.png")
        else:
            manifest["omitted"].append(f"{png_dir}/slide-{n}.png (missing)")
    # scenario files (prior review / build results) go to the project root
    if extra and extra.exists():
        for p in sorted(extra.iterdir()):
            if p.is_file():
                shutil.copy2(p, dest / p.name)
                manifest["extra"].append(p.name)
    for d in ("slides/review-input", "slides/review-output", "output/bench"):
        (dest / d).mkdir(parents=True, exist_ok=True)
    manifest["omitted"].append("slides/deck.pptx and slides/*.bak-*.pptx (benchmark runs without a deck)")
    (dest / "FIXTURE.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--slides", type=int, nargs="+", default=[29, 30, 31])
    ap.add_argument("--png-dir", default="output/png-final")
    ap.add_argument("--extra", default=None, help="directory whose files are copied to the fixture root")
    a = ap.parse_args(argv)
    m = build_fixture(Path(a.source), Path(a.dest), a.slides, a.png_dir, Path(a.extra) if a.extra else None)
    print(f"fixture at {a.dest}: {len(m['copied'])} files, pngs={m['pngs']}, extra={m['extra']}")
    for o in m["omitted"]:
        print("  omitted:", o)


if __name__ == "__main__":
    main()
