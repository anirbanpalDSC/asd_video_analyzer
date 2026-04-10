# Design: Fix Background Bias and Restore True Signal Detection

**Date:** 2026-04-10
**Status:** Approved

---

## Problem

After removing `top_k=1` (commit `047bd0d`), signal detection partially improved but Background (`signal 10`) remains highly biased — appearing as `Yes` in virtually every frame. True ASD signals (1–9) are still not surfacing even in videos where they are clearly present (e.g., a child visibly flapping arms).

### Root Causes

Three compounding problems in `config/config.py` → `DEFAULT_ASD_PROMPT`:

**1. Example frames anchor the model on "all No + Background=Yes"**
Both example rows in the `FRAME_DETECTIONS` block show `1=No,...,9=No,10=Yes`. The model treats these as the target output pattern and replicates them regardless of frame content. With `temperature=0`, this anchoring is extremely strong.

**2. Background rule cascades from Unclear signals**
Signal 10 rule: "mark Yes only when no other signal (1–9) can be assessed as Yes."
This condition is satisfied by both `No` AND `Unclear`. The strict assessability rules push many signals to `Unclear` (evidence absent), which still triggers `Background=Yes`. The result: ambiguity always collapses into Background.

**3. Static-frame assessability rules block Yes for motor signals**
Rules for signals 7, 8, 9 require motion to be "directly observable" — which is physically impossible in a static JPEG frame. A child caught mid-flap is penalized because rotational/repetitive motion cannot be seen in a single image. Signal 1 (eye contact) requires a social partner present, which is often not captured in the frame even when gaze avoidance is clearly visible.

---

## Solution

Three targeted changes to `DEFAULT_ASD_PROMPT` in `config/config.py`. No other files change.

---

### Change 1: Replace example frames with realistic mixed-signal output

The example `FRAME_DETECTIONS` block must demonstrate that:
- Multiple signals can be `Yes` simultaneously (co-occurrence is normal in ASD)
- High-density frames (5+ signals Yes) are valid and expected
- `Unclear` is appropriate for partial evidence
- Background (`10=Yes`) is the rarest outcome, not the default

**New example block:**
```
FRAME_DETECTIONS:
Frame_1: 1=Yes,2=No,3=Yes,4=Yes,5=No,6=No,7=No,8=No,9=Yes,10=No
Frame_2: 1=Yes,2=No,3=Yes,4=Yes,5=Yes,6=No,7=No,8=Yes,9=Yes,10=No
Frame_3: 1=Yes,2=Yes,3=Yes,4=Yes,5=No,6=No,7=Yes,8=No,9=Yes,10=No
Frame_4: 1=Unclear,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=Yes,10=No
Frame_5: 1=No,2=No,3=Unclear,4=Unclear,5=No,6=No,7=No,8=No,9=No,10=No
Frame_6: 1=No,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=Yes
...continue one line per frame for all frames...
```

---

### Change 2: Fix the Background rule

**Current:**
> mark Yes only when no other signal (1–9) can be assessed as Yes, and the frame contains no behavioural evidence relevant to ASD signals.

**Replacement:**
> mark `Yes` only when ALL signals 1–9 are definitively `No` — meaning evidence was present and the behaviour was clearly absent. If any signal is `Unclear`, Background must be `No`. Background=Yes is the rarest outcome; most frames will have at least one signal as `Yes` or `Unclear`.

**Why:** `Unclear` anywhere now forces Background=No, breaking the cascade where ambiguity collapsed into Background=Yes.

---

### Change 3: Relax static-frame assessability rules for motion-dependent signals

**Signal 1 (Absence or Avoidance of Eye Contact):**
- Remove social partner requirement — gaze direction alone is sufficient
- Before: face visible AND social partner present AND camera angle suitable
- After: face visible AND gaze direction assessable from camera angle

**Signal 7 (Self-Hitting or Self-Injurious Behavior):**
- Replace "strike directly observable" with posture/position evidence
- Before: self-directed strike, bite, or impact must be directly observable in the frame
- After: posture, body position, or visible marks consistent with self-directed contact must be present

**Signal 8 (Self-Spinning or Spinning Objects):**
- Replace "rotational motion directly observable" with body orientation evidence
- Before: rotational motion must be directly observable; a static frame where posture is ambiguous is not sufficient
- After: body orientation or posture consistent with rotational movement (e.g., arms outstretched, spinning stance) must be visible

**Signal 9 (Upper Limb Stereotypies):**
- Replace "repetitive pattern directly observable" with arm/hand posture evidence
- Before: repetitive non-functional motor pattern must be directly observable
- After: arm or hand posture consistent with a non-functional motor pattern (e.g., elevated/extended arms, rigid finger positions, mid-flap posture) must be visible

Signals 2–6 are not motion-dependent — their rules are unchanged.

---

## Scope

| File | Change |
|------|--------|
| `config/config.py` | Update `DEFAULT_ASD_PROMPT`: example frames, Background rule, signals 1/7/8/9 assessability rules |
| All other files | No change |

---

## Trade-offs

| Option | Verdict |
|--------|---------|
| Fix example frames + Background rule only | Not selected — static-frame rules would still suppress Yes for motor signals |
| Fix examples + Background + relax static-frame rules | **Selected** — addresses all three root causes |
| Full prompt simplification (drop all strict rules) | Not selected — risks undoing false-positive reduction from prior work |

---

## Success Criteria

- Videos with clearly visible ASD behaviors (e.g., arm flapping, eye gaze avoidance) produce at least one `Yes` signal in FRAME_DETECTIONS
- Background (`10=Yes`) appears only on frames with genuinely no behavioral evidence
- `Unclear` is used for frames where evidence is partial, not as a fallback that triggers Background
- No increase in false positives relative to pre-regression baseline
