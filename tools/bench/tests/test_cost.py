import unittest

from bench.cost import cost_usd, resolve_model, split_cache_write, sum_usage


class ResolveModel(unittest.TestCase):
    def test_exact_and_prefix(self):
        self.assertEqual(resolve_model("claude-fable-5-1"), "claude-fable-5-1")
        self.assertEqual(resolve_model("claude-fable-5"), "claude-fable-5")
        self.assertEqual(resolve_model("claude-opus-5-5-20260401"), "claude-opus-5-5")

    def test_aliases_and_default(self):
        self.assertEqual(resolve_model("fable"), "claude-fable-5-1")
        self.assertEqual(resolve_model(None), "claude-fable-5-1")

    def test_unknown_raises(self):
        with self.assertRaises(KeyError):
            resolve_model("gpt-9")


class CacheWriteSplit(unittest.TestCase):
    def test_breakdown_present(self):
        u = {"cache_creation_input_tokens": 100,
             "cache_creation": {"ephemeral_5m_input_tokens": 40, "ephemeral_1h_input_tokens": 60}}
        self.assertEqual(split_cache_write(u), (40, 60))

    def test_fallback_to_total_as_5m(self):
        self.assertEqual(split_cache_write({"cache_creation_input_tokens": 100}), (100, 0))


class CostUsd(unittest.TestCase):
    def test_fable_components(self):
        u = {"input_tokens": 1_000_000, "output_tokens": 1_000_000,
             "cache_read_input_tokens": 1_000_000,
             "cache_creation": {"ephemeral_5m_input_tokens": 1_000_000,
                                "ephemeral_1h_input_tokens": 1_000_000}}
        c = cost_usd(u, "claude-fable-5-1")
        self.assertAlmostEqual(c["usd_input"], 10.0)
        self.assertAlmostEqual(c["usd_output"], 50.0)
        self.assertAlmostEqual(c["usd_cache_read"], 0.25)
        self.assertAlmostEqual(c["usd_cache_write"], 12.5 + 20.0)
        self.assertAlmostEqual(c["usd_total"], 10 + 50 + 0.25 + 32.5)

    def test_matches_smoke_run(self):
        # observed: 40,429 tokens written at 1h TTL + 108 output -> $0.814 reported by claude -p
        u = {"input_tokens": 2, "output_tokens": 108, "cache_read_input_tokens": 0,
             "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 40429}}
        c = cost_usd(u, "claude-fable-5")
        self.assertAlmostEqual(c["usd_total"], 0.814, places=2)

    def test_matches_pilot_run_fable5(self):
        # claude -p reported $3.740365 for this usage on canonical model claude-fable-5
        u = {"input_tokens": 15, "output_tokens": 24564, "cache_read_input_tokens": 608095,
             "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 95196}}
        self.assertAlmostEqual(cost_usd(u, "claude-fable-5")["usd_total"], 3.7404, places=3)
        # the same run on Fable 5.1 would be cheaper only through cache reads
        self.assertAlmostEqual(cost_usd(u, "claude-fable-5-1")["usd_total"], 3.7404 - 608095 * 0.75 / 1e6, places=3)

    def test_ttl_normalisation(self):
        u = {"cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 1_000_000}}
        self.assertAlmostEqual(cost_usd(u, "claude-fable-5-1", ttl="5m")["usd_cache_write"], 12.5)
        self.assertAlmostEqual(cost_usd(u, "claude-fable-5-1", ttl="1h")["usd_cache_write"], 20.0)
        with self.assertRaises(ValueError):
            cost_usd(u, "claude-fable-5-1", ttl="2h")


class SumUsage(unittest.TestCase):
    def test_sums_keep_ttl_split(self):
        a = {"input_tokens": 1, "output_tokens": 2, "cache_read_input_tokens": 3,
             "cache_creation": {"ephemeral_5m_input_tokens": 4, "ephemeral_1h_input_tokens": 0}}
        b = {"input_tokens": 10, "output_tokens": 20, "cache_read_input_tokens": 30,
             "cache_creation_input_tokens": 40}
        t = sum_usage([a, b])
        self.assertEqual(t["input_tokens"], 11)
        self.assertEqual(t["output_tokens"], 22)
        self.assertEqual(t["cache_read_input_tokens"], 33)
        self.assertEqual(t["cache_creation"]["ephemeral_5m_input_tokens"], 44)
        self.assertEqual(t["cache_creation_input_tokens"], 44)


if __name__ == "__main__":
    unittest.main()
