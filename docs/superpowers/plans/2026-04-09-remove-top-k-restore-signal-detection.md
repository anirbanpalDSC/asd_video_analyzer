# Remove top_k to Restore ASD Signal Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `top_k: 1` from the LLM inference options in `src/analyzer.py` to restore ASD signal detection recall without sacrificing output reproducibility.

**Architecture:** Single-file change — delete `top_k: 1` from the `options` dict in both the `analyze()` and `analyze_stream()` functions. `temperature: 0` + `seed: 42` remain and are sufficient for determinism.

**Tech Stack:** Python, requests, Ollama-compatible chat API (`gemma3:27b-it-fp16`)

---

### Task 1: Remove `top_k` from `analyze()` and `analyze_stream()`

**Files:**
- Modify: `src/analyzer.py:83` (analyze) and `src/analyzer.py:141` (analyze_stream)

> **Note:** This project has no automated test suite. Verification is manual via the Streamlit UI.

- [ ] **Step 1: Confirm current state of both payload blocks**

Open `src/analyzer.py` and verify both payload dicts contain:
```python
"options": {"temperature": 0, "top_k": 1, "seed": 42}
```
There should be exactly two occurrences — one in `analyze()` (~line 83) and one in `analyze_stream()` (~line 141).

- [ ] **Step 2: Remove `top_k: 1` from `analyze()`**

In `src/analyzer.py`, change the payload options in `analyze()` from:
```python
        "options": {"temperature": 0, "top_k": 1, "seed": 42},
```
to:
```python
        "options": {"temperature": 0, "seed": 42},
```

- [ ] **Step 3: Remove `top_k: 1` from `analyze_stream()`**

In `src/analyzer.py`, change the payload options in `analyze_stream()` from:
```python
        "options": {"temperature": 0, "top_k": 1, "seed": 42},
```
to:
```python
        "options": {"temperature": 0, "seed": 42},
```

- [ ] **Step 4: Verify no remaining `top_k` references in analyzer.py**

Run:
```bash
grep -n "top_k" src/analyzer.py
```
Expected output: (no output — zero matches)

- [ ] **Step 5: Commit**

```bash
git add src/analyzer.py
git commit -m "fix: remove top_k=1 to restore ASD signal detection recall

top_k=1 enforces greedy decoding and causes the model to default to No
for all signals regardless of frame content. temperature=0 + seed=42 is
sufficient for reproducibility without the recall penalty."
```

- [ ] **Step 6: Manual verification**

Start the app:
```bash
source venv/bin/activate && streamlit run app.py
```

1. Upload or select a video that previously showed ASD signals before Apr 6
2. Select 3–5 representative frames
3. Click **Run Analysis**
4. Confirm that at least one signal reports `Yes` in the FRAME_DETECTIONS output (previously all were `No`)
5. Run analysis a second time on the same frames — confirm the output is identical (reproducibility check)
