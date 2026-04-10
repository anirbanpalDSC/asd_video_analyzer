# Design: Remove `top_k` to Restore ASD Signal Detection Performance

**Date:** 2026-04-09
**Status:** Approved

---

## Problem

ASD signal detection performance significantly dropped after two changes made on Apr 6–7 2026:

1. **Commit `807df55`** — added `top_k: 1` and `seed: 42` to the LLM payload options
2. **Commit `913e0f6`** — added strict per-signal ASSESSABILITY RULES to the prompt

Signals are now predominantly reported as `No` rather than `Unclear` or `Yes`, indicating the model is not exercising the assessability rules at all — it is defaulting straight to the statistically most probable token, which is `No`.

### Root Cause

`top_k: 1` enforces pure greedy decoding: the model can only ever select the single most probable next token at each generation step. Combined with `temperature: 0`, this is the most conservative generation setting possible. The model converges on `No` for all signals because that is the highest-probability token in a classification output format, especially when paired with an example in the prompt that shows `10=Yes` (Background) for all frames.

The assessability rules (added to reduce false positives) are not the primary cause — they would produce `Unclear`, not `No`. The `top_k: 1` constraint prevents the model from even reaching the conditional reasoning those rules require.

### Why `top_k: 1` Was Added

Solely for output reproducibility. However, `temperature: 0` combined with `seed: 42` already provides strong determinism. `top_k: 1` is redundant for this goal and actively harmful to recall.

---

## Solution

Remove `top_k` from the inference options in both `analyze()` and `analyze_stream()` in [src/analyzer.py](../../../src/analyzer.py).

### Before
```python
"options": {"temperature": 0, "top_k": 1, "seed": 42}
```

### After
```python
"options": {"temperature": 0, "seed": 42}
```

Absent `top_k` defaults to the Ollama model default (typically 40–64), giving the model enough token candidates to reason through the assessability rules and output `Yes` when evidence supports it.

---

## Scope

| File | Change |
|------|--------|
| `src/analyzer.py` | Remove `top_k: 1` from options dict in `analyze()` and `analyze_stream()` |
| All other files | No change |

---

## Trade-offs Considered

| Option | Verdict |
|--------|---------|
| Remove `top_k` entirely | **Selected** — cleanest fix, no loss of reproducibility |
| Raise `top_k` to 20–40 | Viable alternative, negligible practical difference from removing it given `temperature=0` + `seed=42` |
| Fix example frames in prompt | Deferred — revisit only if detection remains low after parameter fix |
| Relax assessability rules | Deferred — keep rules as-is, re-evaluate after parameter fix |

---

## Success Criteria

- Signals previously detected (before Apr 6) are detected again on the same video inputs
- Output remains deterministic across repeated runs on the same frames (`temperature: 0`, `seed: 42`)
- No new false positives relative to pre-Apr-6 baseline
