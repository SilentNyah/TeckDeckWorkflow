import json
import os
import tempfile
import unittest
from pathlib import Path

from bench.analyze import _main_model
from bench.grade import grade_S1, grade_S3, grade_S4, _strip_carried
from bench.make_fixture import build_fixture
from bench.run_bench import build_cmd, extract_section, render_prompt


class MainModel(unittest.TestCase):
    def test_helper_model_is_subtracted(self):
        res = {"usage": {"input_tokens": 100, "output_tokens": 1000, "cache_read_input_tokens": 50_000,
                         "cache_creation_input_tokens": 20_000,
                         "cache_creation": {"ephemeral_1h_input_tokens": 20_000, "ephemeral_5m_input_tokens": 0}},
               "modelUsage": {"claude-haiku-5-5": {"inputTokens": 90, "outputTokens": 10, "cacheReadInputTokens": 0,
                                                   "cacheCreationInputTokens": 5_000, "costUSD": 0.005},
                              "claude-fable-5-1": {"inputTokens": 10, "outputTokens": 990, "cacheReadInputTokens": 50_000,
                                                   "cacheCreationInputTokens": 15_000, "costUSD": 1.0}}}
        model, usage, helper = _main_model(res)
        self.assertEqual(model, "claude-fable-5-1")
        self.assertAlmostEqual(helper, 0.005)
        self.assertEqual(usage["input_tokens"], 10)
        self.assertEqual(usage["output_tokens"], 990)
        self.assertEqual(usage["cache_creation_input_tokens"], 15_000)
        self.assertEqual(usage["cache_creation"]["ephemeral_1h_input_tokens"], 15_000)

    def test_no_model_usage(self):
        model, usage, helper = _main_model({"usage": {"input_tokens": 1}})
        self.assertIsNone(model)
        self.assertEqual(usage["input_tokens"], 1)


class ExtractSection(unittest.TestCase):
    def test_section_until_next_h2(self):
        txt = "## Rules\nr1\n\n## Feedback carried forward\n\n### batch\n* CF-1\n\n## Progress\n|a|\n"
        s = extract_section(txt, "Feedback carried forward")
        self.assertTrue(s.startswith("## Feedback carried forward"))
        self.assertIn("CF-1", s)
        self.assertNotIn("Progress", s)

    def test_missing(self):
        self.assertEqual(extract_section("## A\nx\n", "B"), "")


class RenderPrompt(unittest.TestCase):
    def test_fills_everything(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "slides").mkdir()
            (p / "slides" / "review_state.md").write_text("## Rules\n\n## Feedback carried forward\n* CF-9 rule\n\n## Progress\n", encoding="utf-8")
            (p / "prior.md").write_text("PRIOR TEXT", encoding="utf-8")
            tpl = "root={{PROJECT_ROOT}} skill={{SKILL_DIR}}\n{{CARRIED}}\n{{FILE:prior.md}}\n"
            out = render_prompt(tpl, {"PROJECT_ROOT": "X:/proj", "SKILL_DIR": "S"}, p)
            self.assertIn("root=X:/proj skill=S", out)
            self.assertIn("CF-9 rule", out)
            self.assertIn("PRIOR TEXT", out)
            self.assertNotIn("{{", out)

    def test_unfilled_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                render_prompt("{{NOPE}}", {}, Path(d))

    def test_carried_cf_placeholder_uses_statekit_show_cf(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "slides").mkdir()
            (p / "slides" / "review_state.md").write_text(
                "## Rules\n\n## Feedback carried forward\n\n* 【b1 / Slide 1 / R3 / 対象: 図】凡例を置く。\n"
                "* 【b1 / Slide 2 / R1 / 対象: 用語】用語は統一。\n\n## Progress\n", encoding="utf-8")
            (p / "slides" / "storyboard.md").write_text(
                "## Slide 030: x\n\n### Diagram\n\nなし。\n\n### Code\n\n```kotlin\nval a = 1\n```\n", encoding="utf-8")
            skill = Path(__file__).resolve().parents[3] / "skills" / "techdeck-workflow"
            out = render_prompt("CARRIED:\n{{CARRIED_CF:30}}\n", {"SKILL_DIR": str(skill)}, p)
            self.assertIn("1 of 2 rules", out)        # 図 rule dropped: the slide has no diagram
            self.assertIn("用語は統一", out)
            self.assertNotIn("凡例を置く", out)


class ExtraArgs(unittest.TestCase):
    def test_extra_is_one_shell_string_split_into_argv(self):
        from bench.run_bench import parse_extra
        self.assertEqual(parse_extra("--effort high"), ["--effort", "high"])
        self.assertEqual(parse_extra('--permission-mode "accept edits"'), ["--permission-mode", "accept edits"])
        self.assertEqual(parse_extra(None), [])


class BuildCmd(unittest.TestCase):
    def test_agent_and_flags(self):
        cmd = build_cmd(10, "sid", "techdeck-slide-builder", 60, None, [])
        self.assertEqual(cmd[:3], ["claude", "-p", "--output-format"])
        self.assertIn("--strict-mcp-config", cmd)
        self.assertIn("--agent", cmd)
        self.assertNotIn("--model", cmd)
        self.assertNotIn("--no-session-persistence", cmd)  # we need the transcript


class Fixture(unittest.TestCase):
    def test_copies_selected_files_only(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src"; dst = Path(d) / "dst"; extra = Path(d) / "extra"
            for rel in ["TASK.md", "slides/storyboard.md", "slides/review_state.md", "slides/deck.pptx",
                        "slides/deck.bak-1.pptx", "sources/source_index.md", "notes/glossary.md",
                        "assets/diagrams/x.py", "assets/diagrams/x.pptx", "output/png-final/slide-30.png",
                        "slides/reviews/deck-final-review.md"]:
                f = src / rel; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(b"x")
            extra.mkdir(); (extra / "prior.md").write_text("p", encoding="utf-8")
            m = build_fixture(src, dst, [30], "output/png-final", extra)
            self.assertTrue((dst / "slides" / "storyboard.md").exists())
            self.assertFalse((dst / "slides" / "deck.pptx").exists())
            self.assertFalse((dst / "slides" / "deck.bak-1.pptx").exists())
            self.assertTrue((dst / "assets" / "diagrams" / "x.py").exists())
            self.assertFalse((dst / "assets" / "diagrams" / "x.pptx").exists())
            self.assertTrue((dst / "output" / "png" / "slide-30.png").exists())
            self.assertTrue((dst / "prior.md").exists())
            self.assertTrue((dst / "FIXTURE.json").exists())
            self.assertIn("output/png/slide-30.png", m["pngs"])


class Graders(unittest.TestCase):
    def test_s1_pass(self):
        resp = ("- MODE: slide\n- PROJECT_ROOT: X\n- SLIDE: 030\n- PNG: a.png\n- STORYBOARD: s.md\n- SOURCES: i.md\n"
                "- RUBRIC: /r/review-rubric.md\n- VISUAL: /r/visual-design.md\n- CARRIED: ...\n- PRIOR: ...\n- ITERATION: 2\n")
        r = grade_S1(resp, {"tools": {}}, Path("."))
        self.assertTrue(all(ok for ok, _ in r), r)

    def test_s1_backticked_keys(self):
        resp = ("* `MODE`: `slide`\n* `PROJECT_ROOT`: X\n* `SLIDE`: 030\n* `PNG`:\n  * a.png\n* `STORYBOARD`: s.md\n"
                "* `SOURCES`: i.md\n* `RUBRIC`: review-rubric.md\n* `VISUAL`: visual-design.md\n* **CARRIED**:\n"
                "* `PRIOR`: ...\n* `ITERATION`: 2\n")
        self.assertTrue(grade_S1(resp, {"tools": {}}, Path("."))[0][0])

    def test_s1_detects_transcription(self):
        resp = "- MODE: slide\n原文: Use SharingStarted.WhileSubscribed if the pipeline needs to be active only when the UI is visible\n"
        r = grade_S1(resp, {"tools": {}}, Path("."))
        self.assertFalse(r[1][0])

    def test_strip_carried_keeps_rest(self):
        txt = "- MODE: x\n## Feedback carried forward\n* active only when the UI is visible\n## Next\nok\n"
        self.assertNotIn("active only", _strip_carried(txt))
        self.assertIn("ok", _strip_carried(txt))

    def test_s3(self):
        resp = ("## BUILD RESULT\n* Slide: 030\n### Finding dispositions\n| Finding | Disposition | 内容 |\n| --- | --- | --- |\n"
                "| FINDING-001 | `FIXED` | a |\n| FINDING-002 | `PARTIAL` | b |\n| FINDING-003 | `NEEDS_USER` | c |\n"
                "### Character count\n* Counted: 1\n* Not counted: t\n### Deviations from spec\n* none\n### Progress file\n* x\n")
        r = grade_S3(resp, {"tools": {}}, Path("."))
        self.assertTrue(all(ok for ok, _ in r), r)
        bad = resp.replace("| FINDING-001 | `FIXED`", "| FINDING-001 | `PUSHED_BACK`")
        self.assertFalse(grade_S3(bad, {"tools": {}}, Path("."))[2][0])

    def test_s4(self):
        resp = ("## REVIEW RESULT\n* Slide: 030\n* Batch: p4\n* Iteration: 2\n* Overall result: `PASS_WITH_MINOR_FIXES`\n"
                "* Counts: CRITICAL=0 HIGH=0 MEDIUM=1 LOW=0\n* Rubric items failed: R5-4\n* 3-second takeaway: 「x」\n"
                "* Cold-read summary: y\n* Body chars (§5 count): 1\n\n"
                "### FINDING-001\n* Severity: `HIGH`\n* Category: `[TECH]`\n* Status: `RESOLVED`\n* Rubric: R1-B-2\n\n"
                "### FINDING-002\n* Severity: `MEDIUM`\n* Category: `[CONSISTENCY]`\n* Status: `RESOLVED`\n* Rubric: R6-1\n\n"
                "### FINDING-003\n* Severity: `MEDIUM`\n* Category: `[VISUAL]`\n* Status: `RESOLVED`\n* Rubric: R5-4\n\n"
                "### R6 notes\n* none\n")
        r = grade_S4(resp, {"tools": {}}, Path("."))
        self.assertTrue(all(ok for ok, _ in r), r)

    def test_s4_accepts_compact_forms_the_output_cap_invites(self):
        resp = ("## REVIEW RESULT\n* Slide: 030\n* Batch: p4\n* Iteration: 2\n* Overall result: `REVISION_REQUIRED`\n"
                "* Counts: CRITICAL=0 HIGH=1 MEDIUM=0 LOW=0\n* Rubric items failed: R1-A-2\n* 3-second takeaway: 「x」\n"
                "* Cold-read summary: y\n* Body chars (§5 count): 1\n\n"
                "### FINDING-001 ─ `RESOLVED`\n* 新しい PNG で確認した。\n\n"
                "### FINDING-002\n* Status: `RESOLVED` ─ 脚注を確認。\n\n"
                "### FINDING-003 ─ `RESOLVED`\n* 等幅で描かれている。\n\n"
                "### FINDING-004\n* Severity: `HIGH` ／ Category: `[SOURCE]` ／ Status: `OPEN` ／ Rubric: R1-A-2\n* Locus: x\n\n"
                "### R6 notes\n* none\n")
        r = grade_S4(resp, {"tools": {}}, Path("."))
        self.assertTrue(all(ok for ok, _ in r), r)


if __name__ == "__main__":
    unittest.main()
