import json
import tempfile
import unittest
from pathlib import Path

from bench.compare import compare, render_compare_md


def _bench(evals: dict) -> dict:
    """evals: {(config, eval_name): [usd, ...]} -> minimal benchmark.json structure."""
    runs = []
    for (cfg, name), usds in evals.items():
        for i, u in enumerate(usds, 1):
            runs.append({"eval_id": 0, "eval_name": name, "configuration": cfg, "run_number": i,
                         "result": {"pass_rate": 1.0, "passed": 5, "failed": 0, "total": 5, "time_seconds": 100.0,
                                    "tokens": 1000, "tool_calls": 10, "errors": 0, "usd": u, "usd_5m": u * 0.8,
                                    "cache_write": 100, "cache_read": 1000, "output_tokens": 50, "final_context": 200,
                                    "api_calls": 8, "files_read_kb": {"skill:techdeck-workflow": 10.0}}, "expectations": []})
    return {"runs": runs}


class Compare(unittest.TestCase):
    def test_delta_and_target_per_eval(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "it1", Path(d) / "it2"
            a.mkdir(); b.mkdir()
            (a / "benchmark.json").write_text(json.dumps(_bench({("with_skill", "S0-turn-start"): [7.0, 7.5, 7.3],
                                                                   ("with_skill", "S4-reviewer-slide"): [4.4, 4.3]})), encoding="utf-8")
            (b / "benchmark.json").write_text(json.dumps(_bench({("with_skill", "S0-turn-start"): [4.3, 4.6, 4.5],
                                                                   ("with_skill", "S4-reviewer-slide"): [4.0, 4.2],
                                                                   ("with_skill_opus55", "S4-reviewer-slide"): [1.5]})), encoding="utf-8")
            rows = compare(a, b, targets={"S0-turn-start": -0.30, "S4-reviewer-slide": -0.15})
            s0 = next(r for r in rows if r["eval"] == "S0-turn-start" and r["config"] == "with_skill")
            self.assertAlmostEqual(s0["usd_before"], 7.2667, places=3)
            self.assertAlmostEqual(s0["usd_after"], 4.4667, places=3)
            self.assertAlmostEqual(s0["usd_delta_pct"], -38.53, places=1)
            self.assertEqual(s0["target_pct"], -30.0)
            self.assertTrue(s0["target_met"])
            s4 = next(r for r in rows if r["eval"] == "S4-reviewer-slide" and r["config"] == "with_skill")
            self.assertFalse(s4["target_met"])          # -5.7% vs -15% target
            opus = next(r for r in rows if r["config"] == "with_skill_opus55")
            self.assertIsNone(opus["usd_before"])        # no baseline for that arm in it1
            md = render_compare_md(rows)
            self.assertIn("S0-turn-start", md)
            self.assertIn("✔", md)


if __name__ == "__main__":
    unittest.main()
