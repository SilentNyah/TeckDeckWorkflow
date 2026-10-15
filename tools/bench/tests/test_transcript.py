import json
import os
import tempfile
import unittest

from bench.transcript import _paths_read_by_shell, classify_path, parse_transcript


def _rec(rtype, **kw):
    return json.dumps({"type": rtype, **kw}, ensure_ascii=False)


class ParseTranscript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.doc = os.path.join(self.tmp.name, "storyboard.md")
        with open(self.doc, "w", encoding="utf-8") as fh:
            fh.write("x" * 1234)
        lines = [
            _rec("user", message={"role": "user", "content": "あなたはオーケストレータです。"}),
            # message A split over two records; second record carries the final usage
            _rec("assistant", effort="xhigh", message={"id": "A", "model": "claude-fable-5-1",
                 "usage": {"input_tokens": 2, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 0,
                           "output_tokens": 8, "cache_creation": {"ephemeral_5m_input_tokens": 100, "ephemeral_1h_input_tokens": 0}},
                 "content": [{"type": "thinking", "thinking": ""}]}),
            _rec("assistant", message={"id": "A", "model": "claude-fable-5-1",
                 "usage": {"input_tokens": 2, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 0,
                           "output_tokens": 50},
                 "content": [{"type": "tool_use", "id": "tu1", "name": "Read", "input": {"file_path": self.doc, "offset": 10, "limit": 5}}]}),
            _rec("user", message={"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu1", "content": "y" * 500}]}),
            _rec("assistant", message={"id": "B", "model": "claude-fable-5-1",
                 "usage": {"input_tokens": 2, "cache_creation_input_tokens": 700, "cache_read_input_tokens": 100,
                           "output_tokens": 9},
                 "content": [{"type": "tool_use", "id": "tu2", "name": "Bash",
                              "input": {"command": f'P="{self.tmp.name}"; cat "$P/storyboard.md"'}},
                             {"type": "text", "text": "done"}]}),
            _rec("user", message={"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu2", "content": "z" * 1234}]}),
        ]
        self.path = os.path.join(self.tmp.name, "t.jsonl")
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_calls_and_context(self):
        t = parse_transcript(self.path)
        self.assertEqual(t["calls"], 2)
        self.assertEqual(t["context_per_call"], [102, 802])
        self.assertEqual(t["final_context"], 802)
        self.assertEqual(t["usages"][0]["output_tokens"], 50)  # last snapshot wins

    def test_tools_and_reads(self):
        t = parse_transcript(self.path)
        self.assertEqual(t["tools"], {"Read": 1, "Bash": 1})
        self.assertEqual(len(t["files_read"]), 1)
        self.assertEqual(t["files_read"][0]["times"], 2)
        self.assertEqual(t["files_read"][0]["bytes"], 1234)
        self.assertEqual(t["files_read"][0]["chars"], 500 + 1234)  # what actually entered the context
        self.assertEqual(t["tool_result_chars"], 500 + 1234)
        self.assertEqual(t["first_context"], 102)
        self.assertEqual(t["effort"], "xhigh")
        self.assertEqual(t["agent_text_chars"], 4)
        self.assertTrue(t["first_prompt"].startswith("あなたは"))


class ShellPaths(unittest.TestCase):
    def test_cat_with_variable(self):
        cmd = 'P="C:/proj"; cat "$P/slides/review_state.md" | head -50'
        self.assertEqual(_paths_read_by_shell(cmd), [os.path.normpath("C:/proj/slides/review_state.md")])

    def test_non_reading_command_ignored(self):
        self.assertEqual(_paths_read_by_shell('ls "C:/proj/slides"'), [])

    def test_sed_range(self):
        cmd = "sed -n '10,40p' /c/Users/me/.claude/skills/techdeck-workflow/SKILL.md"
        self.assertEqual(len(_paths_read_by_shell(cmd)), 1)


class Classify(unittest.TestCase):
    def test_buckets(self):
        self.assertEqual(classify_path(r"C:\Users\me\.claude\agents\techdeck-slide-builder.md"), "agent-definition")
        self.assertEqual(classify_path("C:/Users/me/.claude/skills/techdeck-workflow/reference/review-rubric.md"), "skill:techdeck-workflow")
        self.assertEqual(classify_path("C:/Users/me/.claude/skills/pptx-toolkit/SKILL.md"), "skill:pptx-toolkit")
        self.assertEqual(classify_path("D:/w/project/slides/storyboard.md"), "project:storyboard")
        self.assertEqual(classify_path("D:/w/project/slides/review_state.md"), "project:review_state")
        self.assertEqual(classify_path("D:/w/project/output/png/slide-30.png"), "project:png")
        self.assertEqual(classify_path("D:/w/project/sources/source_index.md"), "project:sources")
        self.assertEqual(classify_path("D:/w/project/notes/glossary.md"), "project:other")

    def test_basename_fallback_and_tool_output(self):
        self.assertEqual(classify_path("\\review_state.md"), "project:review_state")
        self.assertEqual(classify_path("\\storyboard.md"), "project:storyboard")
        self.assertEqual(classify_path("\\statekit.py"), "skill:techdeck-workflow")
        self.assertEqual(classify_path("\\phase3-batch-build.md"), "skill:techdeck-workflow")
        self.assertEqual(classify_path("C:/x/sess/tool-results/abc.txt"), "tool-output-files")


class ImageTokens(unittest.TestCase):
    def test_png_dims_and_tokens(self):
        import struct, zlib
        from bench.transcript import image_tokens, png_dims
        w, h = 1600, 900
        ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
        chunk = b"IHDR" + ihdr
        png = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xffffffff)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.png")
            with open(p, "wb") as fh:
                fh.write(png)
            self.assertEqual(png_dims(p), (1600, 900))
            self.assertEqual(image_tokens(p), int(1600 * (1568 / 1600) * 900 * (1568 / 1600) / 750))


if __name__ == "__main__":
    unittest.main()
