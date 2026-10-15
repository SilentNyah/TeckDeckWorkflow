"""Cost model for Claude Code runs (list prices, USD per million tokens).

Why a separate module: the benchmark's primary metric is estimated USD, and the
weights differ by model and by cache TTL. Keeping the table here, with tests,
means every analysis uses the same numbers and the numbers are reviewable.

Prices taken from the claude-api skill reference on 2026-10-14:
  input / output per MTok; cache read multiplier; cache write 1.25x (5-minute
  TTL) or 2x (1-hour TTL) of the input price.
"""
from __future__ import annotations

PRICES: dict[str, dict[str, float]] = {
    # family key -> USD per MTok
    # Fable 5.1 introduced the 0.025x cache-read price; Fable 5 keeps the standard 0.1x.
    # Claude Code's own total_cost_usd for a claude-fable-5 run matches the 0.1x figure.
    "claude-fable-5-1": {"input": 10.0, "output": 50.0, "cache_read": 0.25},
    "claude-fable-5": {"input": 10.0, "output": 50.0, "cache_read": 1.00},
    "claude-opus-5-5": {"input": 4.0, "output": 20.0, "cache_read": 0.20},
    "claude-opus-5": {"input": 5.0, "output": 25.0, "cache_read": 0.50},
    "claude-sonnet-5-5": {"input": 2.0, "output": 10.0, "cache_read": 0.20},
    "claude-sonnet-5": {"input": 2.0, "output": 10.0, "cache_read": 0.20},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_read": 0.01},
}
CACHE_WRITE_MULT = {"5m": 1.25, "1h": 2.0}
DEFAULT_MODEL = "claude-fable-5-1"


def resolve_model(name: str | None) -> str:
    """Map a model id / alias / canonical name to a pricing key."""
    if not name:
        return DEFAULT_MODEL
    n = name.lower()
    if n in PRICES:
        return n
    for key in sorted(PRICES, key=len, reverse=True):
        if n.startswith(key):
            return key
    if n in ("fable", "mythos"):
        return "claude-fable-5-1"
    if n == "opus":
        return "claude-opus-5-5"
    if n == "sonnet":
        return "claude-sonnet-5-5"
    if n == "haiku":
        return "claude-haiku-5-5"
    raise KeyError(f"no price for model {name!r}")


def split_cache_write(usage: dict) -> tuple[int, int]:
    """Return (tokens written at 5m TTL, tokens written at 1h TTL).

    Falls back to treating `cache_creation_input_tokens` as 5m when the TTL
    breakdown is absent (older records).
    """
    cc = usage.get("cache_creation") or {}
    w5 = int(cc.get("ephemeral_5m_input_tokens") or 0)
    w1 = int(cc.get("ephemeral_1h_input_tokens") or 0)
    if w5 == 0 and w1 == 0:
        w5 = int(usage.get("cache_creation_input_tokens") or 0)
    return w5, w1


def cost_usd(usage: dict, model: str | None = None, ttl: str = "actual") -> dict:
    """Cost of one usage record.

    ttl="actual" prices cache writes by their recorded TTL; "5m" or "1h"
    re-prices every write at that TTL (for comparing runs made under
    different harness settings).
    """
    key = resolve_model(model)
    p = PRICES[key]
    inp = int(usage.get("input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    rd = int(usage.get("cache_read_input_tokens") or 0)
    w5, w1 = split_cache_write(usage)
    if ttl == "5m":
        w5, w1 = w5 + w1, 0
    elif ttl == "1h":
        w5, w1 = 0, w5 + w1
    elif ttl != "actual":
        raise ValueError(ttl)
    c_in = inp * p["input"] / 1e6
    c_w5 = w5 * p["input"] * CACHE_WRITE_MULT["5m"] / 1e6
    c_w1 = w1 * p["input"] * CACHE_WRITE_MULT["1h"] / 1e6
    c_rd = rd * p["cache_read"] / 1e6
    c_out = out * p["output"] / 1e6
    return {
        "model": key,
        "ttl": ttl,
        "input_tokens": inp,
        "cache_write_5m_tokens": w5,
        "cache_write_1h_tokens": w1,
        "cache_read_tokens": rd,
        "output_tokens": out,
        "usd_input": c_in,
        "usd_cache_write": c_w5 + c_w1,
        "usd_cache_read": c_rd,
        "usd_output": c_out,
        "usd_total": c_in + c_w5 + c_w1 + c_rd + c_out,
    }


def sum_usage(records: list[dict]) -> dict:
    """Add usage records (per-call) into one usage dict, keeping the TTL split."""
    tot = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
           "cache_creation_input_tokens": 0,
           "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0}}
    for u in records:
        tot["input_tokens"] += int(u.get("input_tokens") or 0)
        tot["output_tokens"] += int(u.get("output_tokens") or 0)
        tot["cache_read_input_tokens"] += int(u.get("cache_read_input_tokens") or 0)
        w5, w1 = split_cache_write(u)
        tot["cache_creation"]["ephemeral_5m_input_tokens"] += w5
        tot["cache_creation"]["ephemeral_1h_input_tokens"] += w1
        tot["cache_creation_input_tokens"] += w5 + w1
    return tot
