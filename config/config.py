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

# Frames per second to annotate with specialized models.
# Lower this to reduce processing time for long videos (e.g. 1.0 for 60-min videos).
# Must be <= the thumbnail extraction fps (2.0). Non-annotated thumbnails are still
# displayed and selectable; they simply have no FRAME_ANNOTATIONS entry in the prompt.
ANNOTATION_FPS: float = 2.0

# Path to the L2CS-Net gaze model weights file.
GAZE_WEIGHTS_PATH = ROOT / "models" / "L2CSNet_gaze360.pkl"

# Paths to MediaPipe Tasks model bundles (downloaded on first use).
POSE_MODEL_PATH  = ROOT / "models" / "pose_landmarker_full.task"
HANDS_MODEL_PATH = ROOT / "models" / "hand_landmarker.task"

# Download URLs for MediaPipe Tasks model bundles.
POSE_MODEL_URL  = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
HANDS_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

# =========================================================================
# ASD Behavioral Analysis Configuration
# =========================================================================

DEFAULT_ASD_PROMPT = """You are a behavioral analyst specializing in Autism Spectrum Disorder (ASD) assessment. Analyze this video session for ASD-related behavioral signals. Review the transcript and the provided video frames carefully.

When a FRAME_ANNOTATIONS section appears below, treat it as objective measurements
from specialized vision and language models that ran before this analysis. These
complement — not replace — your visual interpretation of the frames. For quantitative
claims (gaze angle in degrees, object arrangement, posture geometry, transcript
content), weight the annotations more heavily than your own visual estimate. If an
annotation says a condition is unassessable, mark that signal Unclear unless you have
strong contradicting visual evidence.

Signals 2 (Aggressive Behavior) and 3 (Hyper-/Hyporeactivity to Sensory Input) are
assessed from your visual analysis only — no annotation is provided for them.

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
- Do not infer a signal from indirect cues. Only mark Yes when the defining behaviour is directly observable, or — for signals 7, 8, and 9 where motion cannot be captured in a static frame — when posture or body position is directly and unambiguously consistent with the behaviour.
- Required evidence per signal:
  1. Absence or Avoidance of Eye Contact: the subject's face must be fully visible, gaze direction must be assessable from the camera angle, and a social partner or camera-directed interaction must be present or implied in the scene. If any condition is unmet → Unclear.
  2. Aggressive Behavior: at least one other person must be present and physical contact or a directed physical threat must be visible in the frame. If no other person is present → Unclear.
  3. Hyper- or Hyporeactivity to Sensory Input: a sensory stimulus (sound, touch, light, texture) must be identifiable in the frame or transcript, AND a visible behavioural response (e.g. covering ears, flinching, ignoring pain) must be present. If either is absent → Unclear.
  4. Non-Responsiveness to Verbal Interaction: the transcript or audio must show that someone directed speech at the subject in this segment, AND the subject's response (or absence of response) must be observable. If no directed speech is evidenced → Unclear.
  5. Non-Typical Language: spoken output from the subject must be present in the transcript or audio. If the subject produces no speech in this segment → Unclear.
  6. Object Lining-Up: discrete objects must be clearly visible in the frame and their spatial arrangement (lined, sorted, or sequenced) must be directly discernible. If objects are not visible or arrangement cannot be assessed → Unclear.
  7. Self-Hitting or Self-Injurious Behavior: the subject's hands, head, or the body part targeted (e.g., arms for biting, torso for hitting) must be clearly visible and posture, body position, or visible marks (e.g., redness, contact position) consistent with self-directed contact must be present in the frame. If the targeted body parts are not visible → Unclear.
  8. Self-Spinning or Spinning Objects: the subject's full body or the spinning object must be visible and body orientation or posture consistent with rotational movement and not explained by another functional activity (e.g., arms outstretched mid-spin, spinning stance without object interaction) must be present in the frame. If neither is assessable → Unclear.
  9. Upper Limb Stereotypies: both arms or hands must be visible and arm or hand posture consistent with a non-functional motor pattern and not explained by object interaction or purposeful reach (e.g., elevated or extended arms without object contact, rigid finger positions, mid-flap posture) must be present in the frame. If arms/hands are not visible → Unclear.
  10. Background: mark Yes only when ALL signals 1–9 are definitively No. A signal counts as definitively No only if you marked it No (not Unclear) in your per-signal assessment above. If any signal is Unclear, Background must be No. Background=Yes is the rarest outcome; most frames will have at least one signal as Yes or Unclear.

STEP 1: Apply the assessability rules above, then for each frame record Yes, No, or Unclear for every signal.
STEP 2: Provide an aggregate observed status and a brief note for each signal across all frames.
STEP 3: Write a brief clinical narrative.

Respond exactly in this format — no extra text outside the markers:

(Output one line per frame for every frame provided — do not skip any frame.)
FRAME_DETECTIONS:
Frame_1: 1=Yes,2=No,3=Yes,4=Yes,5=No,6=No,7=No,8=No,9=Yes,10=No
Frame_2: 1=Yes,2=No,3=Yes,4=Yes,5=Yes,6=No,7=No,8=Yes,9=Yes,10=No
Frame_3: 1=Yes,2=Yes,3=Yes,4=Yes,5=No,6=No,7=Yes,8=No,9=Yes,10=No
Frame_4: 1=Unclear,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=Yes,10=No
Frame_5: 1=No,2=No,3=Unclear,4=Unclear,5=No,6=No,7=No,8=No,9=No,10=No
Frame_6: 1=No,2=No,3=No,4=No,5=No,6=No,7=No,8=No,9=No,10=Yes

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
    "Background": "Assigned when no ASD-related behavioural signal (1–9) is present; requires that all signals were directly assessable and clearly absent. Frames with any Unclear signal do not qualify.",
}


def ensure_dirs() -> None:
    """Make sure the uploads/ and processed/ directories exist."""
    for d in (UPLOADS_DIR, PROCESSED_DIR):
        d.mkdir(parents=True, exist_ok=True)
