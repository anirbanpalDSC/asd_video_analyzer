# ASD Video Analyzer — Architecture & Workflow Diagrams

---

## 1. System Architecture

```mermaid
graph TD
    classDef ui        fill:#4f86c6,stroke:#2d5f9e,color:#fff,rx:6
    classDef pipeline  fill:#5aaa8a,stroke:#3a7a64,color:#fff
    classDef analysis  fill:#b06fc4,stroke:#824b92,color:#fff
    classDef models    fill:#e8944a,stroke:#b56b28,color:#fff
    classDef storage   fill:#5c6b8a,stroke:#3a4a6a,color:#fff
    classDef external  fill:#888,stroke:#555,color:#fff

    subgraph UI["  UI Layer  "]
        APP["app.py\nStreamlit single-page app"]:::ui
        UIUTIL["ui_utils.py\nOutput parser & table renderer"]:::ui
    end

    subgraph PROC["  Processing Layer  "]
        PROCESSOR["processor.py\nVideo pipeline orchestrator"]:::pipeline
        ANNOTATOR["annotator.py  ★ NEW\nSpecialized model runner"]:::pipeline
    end

    subgraph ANALYSIS["  Analysis Layer  "]
        ANALYZER["analyzer.py\nVLM prompt builder & caller"]:::analysis
    end

    subgraph CONFIG["  Config  "]
        CFG["config/config.py\nPaths · Prompt · ANNOTATION_FPS"]:::external
    end

    subgraph EXTTOOLS["  External Tools  "]
        FFMPEG["ffmpeg\nAudio + frame extraction"]:::external
        WHISPER["Whisper\nSpeech-to-text + word timestamps"]:::external
        OLLAMA["Ollama API\ngemma3:27b-it-fp16  (VLM)"]:::external
    end

    subgraph SPECMODELS["  Specialized Models (annotator.py)  "]
        L2CS["L2CS-Net\nGaze angle · Signal 1"]:::models
        MP["MediaPipe Pose + Hands\nPosture geometry · Signals 7 8 9"]:::models
        YOLO["YOLOv8m\nObject arrangement · Signal 6"]:::models
        NLP["NLP Pattern Matching\nTranscript alignment · Signals 4 5"]:::models
    end

    subgraph STORAGE["  Filesystem  "]
        UPLOADS["uploads/\nvideo files"]:::storage
        PROCESSED["processed/‹stem›/\n├─ audio.mp3\n├─ transcript.txt\n├─ transcript.words.json  ★\n└─ thumbs/\n   ├─ thumb_00001.jpg …\n   └─ annotations.json  ★"]:::storage
    end

    APP -->|"upload / URL"| PROCESSOR
    APP -->|"selected frames"| ANALYZER
    APP --> UIUTIL

    PROCESSOR -->|"extract audio"| FFMPEG
    PROCESSOR -->|"extract frames"| FFMPEG
    PROCESSOR -->|"transcribe"| WHISPER
    PROCESSOR -->|"annotate frames"| ANNOTATOR
    PROCESSOR --> PROCESSED
    PROCESSOR --> UPLOADS

    ANNOTATOR --> L2CS
    ANNOTATOR --> MP
    ANNOTATOR --> YOLO
    ANNOTATOR --> NLP
    ANNOTATOR -->|"write annotations.json"| PROCESSED

    ANALYZER -->|"load annotations"| PROCESSED
    ANALYZER -->|"multimodal prompt"| OLLAMA
    OLLAMA -->|"FRAME_DETECTIONS\nSIGNALS\nCLINICAL NARRATIVE"| UIUTIL

    CFG -.->|"prompt · fps"| ANNOTATOR
    CFG -.->|"prompt · API_URL"| ANALYZER
```

---

## 2. Processing Pipeline (Video Ingestion)

Runs once per video. Idempotent — skips completed stages if output already exists.

```mermaid
flowchart TD
    A([User uploads video\nor pastes URL]) --> B{URL or file?}
    B -->|URL| C[yt-dlp\ndownload_video_from_url]
    B -->|file| D[Save to uploads/]
    C --> D

    D --> E{Already processed?}
    E -->|Yes, force=False| Z([Done — load cached artifacts])
    E -->|No / force=True| F

    F["ffmpeg\nExtract audio → audio.mp3"] --> G
    G["Whisper\nTranscribe → transcript.txt\n+ transcript.words.json\nword_timestamps=True"] --> H
    H["ffmpeg\nExtract frames → thumb_00001.jpg …\n@ 2.0 fps"] --> I

    I["annotator.py\nFor each thumbnail at ANNOTATION_FPS:"] --> J

    subgraph ANNLOOP["  Per-frame annotation  "]
        J["L2CS-Net → gaze string\n(signal 1)"]
        K["MediaPipe Pose+Hands → posture string\n(signals 7 · 8 · 9)"]
        L["YOLOv8m → object arrangement string\n(signal 6)"]
        M["NLP window ±3s → language string\n(signals 4 · 5)"]
        J --> K --> L --> M
    end

    M --> N["Write annotations.json\n{thumb_00001.jpg: {gaze, pose, objects, language}, …}"]
    N --> Z
```

---

## 3. Analysis Workflow (Single Run)

Triggered when the user selects frames and clicks **Run Analysis**.

```mermaid
sequenceDiagram
    actor User
    participant app as app.py
    participant az as analyzer.py
    participant fs as annotations.json
    participant ollama as Ollama API<br/>(gemma3:27b-it-fp16)
    participant ui as ui_utils.py

    User->>app: Select frames + click Run Analysis
    app->>az: analyze(selected_thumb_paths, transcript)

    az->>fs: Load annotations for selected frames
    fs-->>az: {frame → {gaze, pose, objects, language}}

    az->>az: Build prompt
    note over az: DEFAULT_ASD_PROMPT<br/>+ FRAME_ANNOTATIONS block<br/>  (selected frames only)<br/>+ base64 JPEG images

    az->>ollama: POST /api/chat<br/>{model, messages, stream:false,<br/>temperature:0, seed:42}
    ollama-->>az: Raw text response

    az-->>app: analysis_text

    app->>ui: parse_and_display_analysis(analysis_text)
    ui->>ui: Parse FRAME_DETECTIONS → confidence scores
    ui->>ui: Render signals table + badges
    ui-->>User: Signals table · CSV download · Clinical narrative
```

---

## 4. Annotation → Prompt Mapping

How specialized model outputs become VLM input for a single frame.

```mermaid
flowchart LR
    subgraph MODELS["Specialized Models"]
        A["L2CS-Net\n→ yaw=-32°, pitch=8°"]
        B["MediaPipe\n→ wrist_left above shoulder_left\n   arms extended, no object contact"]
        C["YOLOv8m\n→ 4× cup, collinear"]
        D["NLP\n→ 'go go go go' ×4 at t=12s"]
    end

    subgraph ANNOTATION["annotations.json entry"]
        E["gaze: Gaze directed 32° left of camera,\n      8° downward. No social target."]
        F["pose: Both wrists elevated above shoulders,\n      arms extended without object contact."]
        G["objects: 4 objects of class 'cup' in a\n         linear arrangement."]
        H["language: t=12s — 'go go go go'\n           (4 repetitions). Possible echolalia."]
    end

    subgraph PROMPT["FRAME_ANNOTATIONS in prompt"]
        I["Frame_3:\n  gaze:     Gaze directed 32° left …\n  pose:     Both wrists elevated …\n  objects:  4 objects of class 'cup' …\n  language: t=12s — 'go go go go' …"]
    end

    subgraph VLM["Gemma3 VLM output"]
        J["FRAME_DETECTIONS:\nFrame_3: 1=Yes,5=Yes,6=Yes,9=Yes,10=No\n\nSIGNALS:\nEye Contact | Yes | Gaze 32° left, no social target …\nObject Lining-Up | Yes | 4 cups in linear arrangement …"]
    end

    A --> E --> I
    B --> F --> I
    C --> G --> I
    D --> H --> I
    I -->|"+ base64 JPEG"| J
```
