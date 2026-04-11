# Fix Background Bias and Restore Signal Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three prompt defects in `DEFAULT_ASD_PROMPT` that cause Background to dominate output and suppress true ASD signal detection.

**Architecture:** All changes are confined to the `DEFAULT_ASD_PROMPT` string in `config/config.py`. Three targeted edits: (1) replace example frames with realistic multi-signal output, (2) fix the Background assessability rule, (3) relax four static-frame assessability rules (signals 1, 7, 8, 9).

**Tech Stack:** Python, string editing in `config/config.py`

---

### Task 1: Replace example FRAME_DETECTIONS block

**Files:**
- Modify: `config/config.py:58-61`

> **Note:** This project has no automated test suite. Verification is manual via the Streamlit UI.

- [ ] **Step 1: Confirm current example block**

Open `config/config.py` lines 58–61 and verify it reads exactly:
```
FRAME_DETECTIONS:
Frame_1: 1=No,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=Yes
Frame_2: 1=No,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=Yes
...continue one line per frame for all frames...
```

- [ ] **Step 2: Replace example block**

In `config/config.py`, replace:
```
FRAME_DETECTIONS:
Frame_1: 1=No,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=Yes
Frame_2: 1=No,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=Yes
...continue one line per frame for all frames...
```
with:
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

- [ ] **Step 3: Verify the change**

Run:
```bash
grep -n "Frame_1\|Frame_2\|Frame_3" config/config.py
```
Expected output:
```
59:Frame_1: 1=Yes,2=No,3=Yes,4=Yes,5=No,6=No,7=No,8=No,9=Yes,10=No
60:Frame_2: 1=Yes,2=No,3=Yes,4=Yes,5=Yes,6=No,7=No,8=Yes,9=Yes,10=No
61:Frame_3: 1=Yes,2=Yes,3=Yes,4=Yes,5=No,6=No,7=Yes,8=No,9=Yes,10=No
```

- [ ] **Step 4: Commit**

```bash
git add config/config.py
git commit -m "fix: replace example frames to remove Background=Yes anchor bias

Both example rows showed all-No + 10=Yes, anchoring the model to output
Background for every frame. New examples show realistic multi-signal
detection including frames with 5+ Yes signals."
```

---

### Task 2: Fix the Background (signal 10) assessability rule

**Files:**
- Modify: `config/config.py:50`

- [ ] **Step 1: Confirm current Background rule**

Open `config/config.py` line 50 and verify it reads:
```
  10. Background: mark Yes only when no other signal (1–9) can be assessed as Yes, and the frame contains no behavioural evidence relevant to ASD signals.
```

- [ ] **Step 2: Replace Background rule**

In `config/config.py`, replace:
```
  10. Background: mark Yes only when no other signal (1–9) can be assessed as Yes, and the frame contains no behavioural evidence relevant to ASD signals.
```
with:
```
  10. Background: mark Yes only when ALL signals 1–9 are definitively No — meaning evidence was present and the behaviour was clearly absent. If any signal is Unclear, Background must be No. Background=Yes is the rarest outcome; most frames will have at least one signal as Yes or Unclear.
```

- [ ] **Step 3: Verify the change**

Run:
```bash
grep -n "Background:" config/config.py
```
Expected output includes:
```
  10. Background: mark Yes only when ALL signals 1–9 are definitively No — meaning evidence was present and the behaviour was clearly absent. If any signal is Unclear, Background must be No. Background=Yes is the rarest outcome; most frames will have at least one signal as Yes or Unclear.
```

- [ ] **Step 4: Commit**

```bash
git add config/config.py
git commit -m "fix: Background rule now requires all signals definitively No

Previously fired Yes when signals were Unclear, cascading ambiguity into
Background=Yes. Now Unclear anywhere forces Background=No."
```

---

### Task 3: Relax static-frame assessability rules for signals 1, 7, 8, 9

**Files:**
- Modify: `config/config.py:41,47,48,49`

- [ ] **Step 1: Fix Signal 1 (Eye Contact) — remove social partner requirement**

In `config/config.py`, replace:
```
  1. Absence or Avoidance of Eye Contact: the subject's face must be fully visible, a social partner must be present in the scene, and the camera angle must allow gaze direction to be reliably determined. If any condition is unmet → Unclear.
```
with:
```
  1. Absence or Avoidance of Eye Contact: the subject's face must be fully visible and gaze direction must be assessable from the camera angle. If either condition is unmet → Unclear.
```

- [ ] **Step 2: Fix Signal 7 (Self-Hitting) — replace "directly observable strike" with posture evidence**

In `config/config.py`, replace:
```
  7. Self-Hitting or Self-Injurious Behavior: the subject's hands, head, or relevant body part must be clearly visible and a self-directed strike, bite, or impact must be directly observable in the frame. If the relevant body parts are not visible → Unclear.
```
with:
```
  7. Self-Hitting or Self-Injurious Behavior: the subject's hands, head, or relevant body part must be clearly visible and posture, body position, or visible marks consistent with self-directed contact must be present in the frame. If the relevant body parts are not visible → Unclear.
```

- [ ] **Step 3: Fix Signal 8 (Self-Spinning) — replace "rotational motion directly observable" with body orientation evidence**

In `config/config.py`, replace:
```
  8. Self-Spinning or Spinning Objects: the subject's full body or the spinning object must be visible and rotational motion must be directly observable. A single static frame where posture is ambiguous is not sufficient → Unclear.
```
with:
```
  8. Self-Spinning or Spinning Objects: the subject's full body or the spinning object must be visible and body orientation or posture consistent with rotational movement (e.g., arms outstretched, spinning stance) must be present in the frame. If neither is assessable → Unclear.
```

- [ ] **Step 4: Fix Signal 9 (Upper Limb Stereotypies) — replace "repetitive pattern directly observable" with arm/hand posture evidence**

In `config/config.py`, replace:
```
  9. Upper Limb Stereotypies: both arms or hands must be visible and a repetitive non-functional motor pattern (flapping, waving, finger-flicking) must be directly observable. If arms/hands are not visible → Unclear.
```
with:
```
  9. Upper Limb Stereotypies: both arms or hands must be visible and arm or hand posture consistent with a non-functional motor pattern (e.g., elevated or extended arms, rigid finger positions, mid-flap posture) must be present in the frame. If arms/hands are not visible → Unclear.
```

- [ ] **Step 5: Verify all four rules changed**

Run:
```bash
grep -n "1\. Absence\|7\. Self-Hitting\|8\. Self-Spinning\|9\. Upper" config/config.py
```
Expected output:
```
41:  1. Absence or Avoidance of Eye Contact: the subject's face must be fully visible and gaze direction must be assessable from the camera angle. If either condition is unmet → Unclear.
47:  7. Self-Hitting or Self-Injurious Behavior: the subject's hands, head, or relevant body part must be clearly visible and posture, body position, or visible marks consistent with self-directed contact must be present in the frame. If the relevant body parts are not visible → Unclear.
48:  8. Self-Spinning or Spinning Objects: the subject's full body or the spinning object must be visible and body orientation or posture consistent with rotational movement (e.g., arms outstretched, spinning stance) must be present in the frame. If neither is assessable → Unclear.
49:  9. Upper Limb Stereotypies: both arms or hands must be visible and arm or hand posture consistent with a non-functional motor pattern (e.g., elevated or extended arms, rigid finger positions, mid-flap posture) must be present in the frame. If arms/hands are not visible → Unclear.
```

- [ ] **Step 6: Confirm signals 2–6 are unchanged**

Run:
```bash
grep -n "2\. Aggressive\|3\. Hyper\|4\. Non-Responsiveness\|5\. Non-Typical\|6\. Object" config/config.py
```
Expected: original text for all five rules (no changes).

- [ ] **Step 7: Commit**

```bash
git add config/config.py
git commit -m "fix: relax static-frame assessability rules for signals 1, 7, 8, 9

Motion-dependent rules required directly observable motion which is
impossible in static JPEG frames. Replaced with posture/body-position
evidence. Eye contact rule drops social partner requirement — gaze
direction alone is sufficient."
```

---

### Task 4: Manual verification

- [ ] **Step 1: Start the app**

```bash
source venv/bin/activate && streamlit run app.py
```

- [ ] **Step 2: Test with a known-signal video**

Upload or select a video where ASD behaviors are clearly visible (e.g., arm flapping, eye gaze avoidance). Select 5–8 frames that include the behavior.

- [ ] **Step 3: Verify signal detection restored**

Click **Run Analysis**. Confirm:
- At least one signal (1–9) reports `Yes` in FRAME_DETECTIONS for frames showing the behavior
- `Background (10=Yes)` appears only on frames with no behavioral evidence — not on every frame
- `Unclear` appears on frames where body parts are partially visible or evidence is ambiguous

- [ ] **Step 4: Verify Background is rare**

Count the `10=Yes` entries across all frame rows. In a video with visible ASD behaviors, Background=Yes should be the minority (ideally fewer than 20% of frames).

- [ ] **Step 5: Verify reproducibility**

Run analysis a second time on the same frames. Confirm output is identical.
