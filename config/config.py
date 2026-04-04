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

STEP 1: For each frame individually, record whether each signal is present (Yes) or absent (No).
STEP 2: Provide an aggregate observed status and a brief note for each signal.
STEP 3: Write a brief clinical narrative.

Respond exactly in this format — no extra text outside the markers:

FRAME_DETECTIONS:
Frame_1: 1=Yes,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=No
Frame_2: 1=Yes,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=No
...continue one line per frame for all frames...

SIGNALS:
Absence or Avoidance of Eye Contact | <Observed: Yes/No/Unclear> | <Note: one sentence>
Aggressive Behavior | <Observed: Yes/No/Unclear> | <Note: one sentence>
Hyper- or Hyporeactivity to Sensory Input | <Observed: Yes/No/Unclear> | <Note: one sentence>
Non-Responsiveness to Verbal Interaction | <Observed: Yes/No/Unclear> | <Note: one sentence>
Non-Typical Language | <Observed: Yes/No/Unclear> | <Note: one sentence>
Object Lining-Up | <Observed: Yes/No/Unclear> | <Note: one sentence>
Self-Hitting or Self-Injurious Behavior | <Observed: Yes/No/Unclear> | <Note: one sentence>
Self-Spinning or Spinning Objects | <Observed: Yes/No/Unclear> | <Note: one sentence>
Upper Limb Stereotypies | <Observed: Yes/No/Unclear> | <Note: one sentence>
Background | <Observed: Yes/No/Unclear> | <Note: one sentence>

CLINICAL NARRATIVE:
<Your 3-5 sentence summary here>"""

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
