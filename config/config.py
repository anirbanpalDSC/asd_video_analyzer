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

For each signal category below, provide:
- Observed: Yes/No/Unclear
- Confidence: High/Medium/Low
- A brief note (one sentence)

Signal Categories:
1. Absence or Avoidance of Eye Contact - (Social domain)
2. Aggressive Behavior - (Social domain)
3. Hyper- or Hyporeactivity to Sensory Input - RRB (Restricted and Repetitive Behaviors)
4. Non-Responsiveness to Verbal Interaction - (Social domain)
5. Non-Typical Language - (Social domain)
6. Object Lining-Up - RRB (Restricted and Repetitive Behaviors)
7. Self-Hitting or Self-Injurious Behavior - RRB (Restricted and Repetitive Behaviors)
8. Self-Spinning or Spinning Objects - RRB (Restricted and Repetitive Behaviors)
9. Upper Limb Stereotypies - RRB (Restricted and Repetitive Behaviors)
10. Background (i.e., not-applicable)

After the signal table, write a brief clinical observation narrative (3-5 sentences) summarizing the activities and key findings.
Respond exactly in this format - no extra text outside the markers:

SIGNALS:
Absence or Avoidance of Eye Contact | <Observed> | <Confidence> | <Note>
Aggressive Behavior | <Observed> | <Confidence> | <Note>
Hyper- or Hyporeactivity to Sensory Input | <Observed> | <Confidence> | <Note>
Non-Responsiveness to Verbal Interaction | <Observed> | <Confidence> | <Note>
Non-Typical Language | <Observed> | <Confidence> | <Note>
Object Lining-Up | <Observed> | <Confidence> | <Note>
Self-Hitting or Self-Injurious Behavior | <Observed> | <Confidence> | <Note>
Self-Spinning or Spinning Objects | <Observed> | <Confidence> | <Note>
Upper Limb Stereotypies | <Observed> | <Confidence> | <Note>
Background | <Observed> | <Confidence> | <Note>

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
