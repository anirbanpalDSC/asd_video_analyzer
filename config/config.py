from pathlib import Path

# Root of the Python project (one level up from this file)
ROOT = Path(__file__).parent.parent

# Directories matching the PHP layout
UPLOADS_DIR = ROOT / "uploads"
PROCESSED_DIR = ROOT / "processed"

# Maximum allowed upload size (bytes)
MAX_FILE_SIZE = 512 * 1024 * 1024  # 512 MB

# Allowed video extensions (lowercase, without dot)
ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}

# External LLM API (same as the PHP project)
API_URL = "https://gs1.cht77.com/api/chat"

# =========================================================================
# ASD Behavioral Analysis Configuration
# =========================================================================

DEFAULT_ASD_PROMPT = """You are a behavioral analyst specializing in Autism Spectrum Disorder (ASD) assessment. Analyze this video session for ASD-related behavioral signals. Review the transcript and the provided video frames carefully.

Signal Numbers (used below):
1. Absence or Avoidance of Eye Contact
2. Aggressive Behavior
3. Hyper- or Hyporeactivity to Sensory Input
4. Non-Responsiveness to Verbal Interaction
5. Non-Typical Language
6. Object Lining-Up
7. Self-Hitting or Self-Injurious Behavior
8. Self-Spinning or Spinning Objects
9. Upper Limb Stereotypies
10. Background (not-applicable / no ASD signal present)

ASSESSABILITY RULES — apply before marking any signal:
- Mark Unclear (never Yes or No) when the required evidence for that signal is absent from the frame and transcript.
- Do not infer a signal from indirect cues. Only mark Yes when the defining behaviour is directly observable.
- Required evidence per signal:
  1. Absence or Avoidance of Eye Contact: the subject's face must be fully visible, a social partner must be present in the scene, and the camera angle must allow gaze direction to be reliably determined. If any condition is unmet → Unclear.
  2. Aggressive Behavior: at least one other person must be present and physical contact or a directed physical threat must be visible in the frame. If no other person is present → Unclear.
  3. Hyper- or Hyporeactivity to Sensory Input: a sensory stimulus (sound, touch, light, texture) must be identifiable in the frame or transcript, AND a visible behavioural response (e.g. covering ears, flinching, ignoring pain) must be present. If either is absent → Unclear.
  4. Non-Responsiveness to Verbal Interaction: the transcript or audio must show that someone directed speech at the subject in this segment, AND the subject's response (or absence of response) must be observable. If no directed speech is evidenced → Unclear.
  5. Non-Typical Language: spoken output from the subject must be present in the transcript or audio. If the subject produces no speech in this segment → Unclear.
  6. Object Lining-Up: discrete objects must be clearly visible in the frame and their spatial arrangement (lined, sorted, or sequenced) must be directly discernible. If objects are not visible or arrangement cannot be assessed → Unclear.
  7. Self-Hitting or Self-Injurious Behavior: the subject's hands, head, or relevant body part must be clearly visible and a self-directed strike, bite, or impact must be directly observable in the frame. If the relevant body parts are not visible → Unclear.
  8. Self-Spinning or Spinning Objects: the subject's full body or the spinning object must be visible and rotational motion must be directly observable. A single static frame where posture is ambiguous is not sufficient → Unclear.
  9. Upper Limb Stereotypies: both arms or hands must be visible and a repetitive non-functional motor pattern (flapping, waving, finger-flicking) must be directly observable. If arms/hands are not visible → Unclear.
  10. Background: mark Yes only when no other signal (1–9) can be assessed as Yes, and the frame contains no behavioural evidence relevant to ASD signals.

STEP 1: Apply the assessability rules above, then for each frame record Yes, No, or Unclear for every signal.
STEP 2: Provide an aggregate observed status and a brief note for each signal across all frames.
STEP 3: Write a brief clinical narrative.

Respond exactly in this format — no extra text outside the markers:

FRAME_DETECTIONS:
Frame_1: 1=Yes,2=No,3=Yes,4=Yes,5=No,6=No,7=No,8=No,9=Yes,10=No
Frame_2: 1=Yes,2=No,3=Yes,4=Yes,5=Yes,6=No,7=No,8=Yes,9=Yes,10=No
Frame_3: 1=Yes,2=Yes,3=Yes,4=Yes,5=No,6=No,7=Yes,8=No,9=Yes,10=No
Frame_4: 1=Unclear,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=Yes,10=No
Frame_5: 1=No,2=No,3=Unclear,4=Unclear,5=No,6=No,7=No,8=No,9=No,10=No
Frame_6: 1=No,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=Yes
...continue one line per frame for all frames...

SIGNALS:
Absence or Avoidance of Eye Contact | Yes/No/Unclear | Your one-sentence observation here.
Aggressive Behavior | Yes/No/Unclear | Your one-sentence observation here.
Hyper- or Hyporeactivity to Sensory Input | Yes/No/Unclear | Your one-sentence observation here.
Non-Responsiveness to Verbal Interaction | Yes/No/Unclear | Your one-sentence observation here.
Non-Typical Language | Yes/No/Unclear | Your one-sentence observation here.
Object Lining-Up | Yes/No/Unclear | Your one-sentence observation here.
Self-Hitting or Self-Injurious Behavior | Yes/No/Unclear | Your one-sentence observation here.
Self-Spinning or Spinning Objects | Yes/No/Unclear | Your one-sentence observation here.
Upper Limb Stereotypies | Yes/No/Unclear | Your one-sentence observation here.
Background | Yes/No/Unclear | Your one-sentence observation here.

CLINICAL NARRATIVE:
Write your 3-5 sentence summary here."""

# ASD signal categories (for sidebar reference card)
ASD_SIGNAL_REFERENCE = {
    "Absence or Avoidance of Eye Contact": "A consistent lack of direct gaze or active aversion to maintaining eye contact during social interactions, often limiting nonverbal engagement.",
    "Aggressive Behavior": "Physical acts of hostility directed outward toward other people or property, often triggered by communication frustration, disrupted routines, or sensory overwhelm.",
    "Hyper- or Hyporeactivity to Sensory Input": "An atypical sensory response characterized by either exaggerated sensitivity (e.g., covering ears, distress to textures or sounds) or diminished responsiveness (e.g., high pain tolerance, apparent indifference to sensory stimuli).",
    "Non-Responsiveness to Verbal Interaction": "Failure to respond appropriately to spoken language, including not reacting to one's name, delayed responses, or absence of contingent verbal or behavioral acknowledgment.",
    "Non-Typical Language": "Atypical patterns of speech production or usage, including echolalia, scripted speech, unusual prosody, repetitive phrasing, or language that lacks typical conversational reciprocity.",
    "Object Lining-Up": "The repetitive arrangement of objects in ordered, symmetrical, or sequential patterns, often performed with focused attention and resistance to disruption.",
    "Self-Hitting or Self-Injurious Behavior": "Repetitive physical actions directed toward oneself that may cause harm or discomfort, such as hitting, biting, head-banging, or scratching, often associated with emotional dysregulation or sensory modulation difficulties.",
    "Self-Spinning or Spinning Objects": "Repetitive rotational movements of the body or objects, performed persistently or with unusual intensity, typically reflecting sensory-seeking or self-stimulatory behavior.",
    "Upper Limb Stereotypies": "Repetitive, non-functional motor movements involving the arms or hands, such as flapping, waving, or finger flicking, often occurring during heightened emotional or sensory states.",
    "Background": "Contextual environmental and situational information present during observation, when no other signals can be detected.",
}


def ensure_dirs() -> None:
    """Make sure the uploads/ and processed/ directories exist."""
    for d in (UPLOADS_DIR, PROCESSED_DIR):
        d.mkdir(parents=True, exist_ok=True)
