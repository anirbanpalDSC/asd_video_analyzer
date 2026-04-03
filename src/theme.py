"""Apple Glass theme CSS injection for Streamlit.

Adapted from apple_glass_theme.md (light) and apple_glass_dark_theme.md (dark).
Inject via st.markdown(..., unsafe_allow_html=True) at the top of main().
"""

_FONT_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');"

_LIGHT_CSS = """
<style>
{font}

/* ── Page & app background ── */
.stApp {{
  background: #eef2f8 !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
[data-testid="stAppViewContainer"] > .main {{
  background: transparent !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
  background: rgba(255,255,255,0.72) !important;
  backdrop-filter: blur(28px) saturate(1.6) !important;
  border-right: 1px solid rgba(255,255,255,0.88) !important;
  box-shadow: 4px 0 24px rgba(0,0,0,0.07) !important;
}}
[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
  color: #17191f !important;
}}

/* ── Buttons ── */
.stButton > button {{
  background: rgba(26,108,245,0.08) !important;
  color: #1a6cf5 !important;
  border: 1.5px solid rgba(26,108,245,0.22) !important;
  border-radius: 100px !important;
  font-weight: 600 !important;
  font-family: 'Inter', sans-serif !important;
  transition: background 0.2s, box-shadow 0.2s !important;
}}
.stButton > button:hover {{
  background: rgba(26,108,245,0.16) !important;
  box-shadow: 0 4px 20px rgba(26,108,245,0.18) !important;
}}
.stButton > button[kind="primary"] {{
  background: #1a6cf5 !important;
  color: #fff !important;
  border-color: #1a6cf5 !important;
}}
.stButton > button[kind="primary"]:hover {{
  background: #1558d4 !important;
  box-shadow: 0 4px 20px rgba(26,108,245,0.35) !important;
}}

/* ── Expanders ── */
[data-testid="stExpander"] {{
  background: rgba(255,255,255,0.58) !important;
  backdrop-filter: blur(20px) saturate(1.5) !important;
  border: 1px solid rgba(255,255,255,0.88) !important;
  border-radius: 14px !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06) !important;
}}

/* ── Text inputs / select boxes / textareas ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextArea"] textarea {{
  background: rgba(255,255,255,0.72) !important;
  border: 1px solid rgba(50,55,80,0.18) !important;
  border-radius: 10px !important;
  color: #17191f !important;
}}

/* ── DataFrames / tables ── */
[data-testid="stDataFrame"] {{
  background: rgba(255,255,255,0.65) !important;
  border: 1px solid rgba(255,255,255,0.88) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
  background: rgba(255,255,255,0.72) !important;
  backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(255,255,255,0.88) !important;
  border-radius: 14px !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.07) !important;
  padding: 1rem 1.2rem !important;
}}

/* ── Alerts / info boxes ── */
[data-testid="stAlert"] {{
  border-radius: 12px !important;
  border: none !important;
}}

/* ── Divider ── */
hr {{ border-color: rgba(50,55,80,0.09) !important; }}

/* ── Typography ── */
.stApp, .stApp p, .stApp span, .stApp label {{ color: #17191f !important; }}
h1, h2, h3, h4, h5, h6 {{ color: #17191f !important; font-family: 'Inter', sans-serif !important; }}

/* ── Transcript / text areas ── */
[data-testid="stTextArea"] textarea {{ color: #17191f !important; }}
</style>
""".format(font=_FONT_IMPORT)

_DARK_CSS = """
<style>
{font}

/* ── Page & app background ── */
.stApp {{
  background: #111318 !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
[data-testid="stAppViewContainer"] > .main {{
  background: transparent !important;
}}

/* ── Top header banner ── */
[data-testid="stHeader"] {{
  background: #111318 !important;
  border-bottom: 1px solid rgba(255,255,255,0.08) !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
  background: rgba(17,19,24,0.92) !important;
  backdrop-filter: blur(28px) saturate(1.4) !important;
  border-right: 1px solid rgba(255,255,255,0.08) !important;
  box-shadow: 4px 0 24px rgba(0,0,0,0.4) !important;
}}
[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
  color: #eef0f8 !important;
}}

/* ── Buttons ── */
.stButton > button {{
  background: rgba(77,142,247,0.15) !important;
  color: #4d8ef7 !important;
  border: 1.5px solid rgba(77,142,247,0.30) !important;
  border-radius: 100px !important;
  font-weight: 600 !important;
  font-family: 'Inter', sans-serif !important;
  transition: background 0.2s, box-shadow 0.2s !important;
}}
.stButton > button:hover {{
  background: rgba(77,142,247,0.28) !important;
  box-shadow: 0 4px 20px rgba(77,142,247,0.25) !important;
}}
.stButton > button[kind="primary"] {{
  background: #4d8ef7 !important;
  color: #fff !important;
  border-color: #4d8ef7 !important;
}}
.stButton > button[kind="primary"]:hover {{
  background: #3a7de6 !important;
  box-shadow: 0 4px 20px rgba(77,142,247,0.35) !important;
}}

/* ── Expanders ── */
[data-testid="stExpander"] {{
  background: rgba(255,255,255,0.055) !important;
  backdrop-filter: blur(28px) saturate(1.4) !important;
  border: 1px solid rgba(255,255,255,0.11) !important;
  border-radius: 14px !important;
  box-shadow: 0 8px 40px rgba(0,0,8,0.55) !important;
}}

/* ── Text inputs / select boxes / textareas ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextArea"] textarea {{
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.13) !important;
  border-radius: 10px !important;
  color: #eef0f8 !important;
}}

/* ── DataFrames / tables ── */
[data-testid="stDataFrame"] {{
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.11) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.11) !important;
  border-radius: 14px !important;
  padding: 1rem 1.2rem !important;
}}

/* ── Alerts / info boxes ── */
[data-testid="stAlert"] {{
  border-radius: 12px !important;
  border: none !important;
}}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
  background: transparent !important;
}}
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploadDropzone"] {{
  background: rgba(255,255,255,0.055) !important;
  border: 1.5px dashed rgba(255,255,255,0.18) !important;
  border-radius: 14px !important;
  color: #eef0f8 !important;
}}
[data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploadDropzone"] * {{
  color: #eef0f8 !important;
  background: transparent !important;
}}
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploadDropzone"] button {{
  background: rgba(77,142,247,0.15) !important;
  color: #4d8ef7 !important;
  border: 1.5px solid rgba(77,142,247,0.30) !important;
  border-radius: 100px !important;
}}

/* ── Divider ── */
hr {{ border-color: rgba(200,210,240,0.08) !important; }}

/* ── Typography ── */
.stApp, .stApp p, .stApp span, .stApp label {{ color: #eef0f8 !important; }}
h1, h2, h3, h4, h5, h6 {{ color: #eef0f8 !important; font-family: 'Inter', sans-serif !important; }}

/* ── Transcript / text areas ── */
[data-testid="stTextArea"] textarea {{ color: #17191f !important; }}

/* ── URL / text inputs (white background in dark mode) ── */
[data-testid="stTextInput"] input {{ color: #17191f !important; }}

/* ── Expander content text ── */
[data-testid="stExpander"] * {{ color: #17191f !important; }}
[data-testid="stExpander"] label {{ color: #17191f !important; }}
</style>
""".format(font=_FONT_IMPORT)


def get_theme_css(theme: str) -> str:
    """Return the Apple Glass CSS for the given theme ('light' or 'dark')."""
    return _LIGHT_CSS if theme == "light" else _DARK_CSS
