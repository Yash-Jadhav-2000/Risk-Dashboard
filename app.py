import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io
from datetime import datetime

st.set_page_config(page_title="Risk Analytics Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Hide Streamlit's top deploy/toolbar navigation bar completely
st.markdown("""
<style>
    .stAppToolbar {display: none !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    header[data-testid="stHeader"] {display: none !important;}
    #MainMenu {display: none !important;}
    footer {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ── Brand colours ─────────────────────────────────────────────────────────────
PRIMARY    = "#6FACDE"
PRIMARY_DK = "#4F8DC0"
DARK_BLUE  = "#00263E"
LIGHT_BG   = "#F5F8FC"
WHITE      = "#FFFFFF"
BORDER     = "#E4EBF3"
BORDER_DK  = "#CCD7E5"
MUTED      = "#566576"   # darkened from #6B7A8D for WCAG AA contrast on light bg
TEXT       = "#1A2A3A"

# ── Professional design tokens (clean UI refresh) ───────────────────────────────
PAGE_BG    = "#f1f5f9"   # app background
CARD_BG    = "#ffffff"   # content cards
LINE       = "#e2e8f0"   # hairline borders
LABEL_GRAY = "#6b7280"   # form / metric labels
SUBTLE     = "#94a3b8"   # subtitles / secondary
NAVY       = "#1e3a5f"   # primary accent (section borders, active pill)
TEXT_DK    = "#1e293b"   # chart titles / primary text
GRID       = "#f1f5f9"   # chart gridlines
CARD_SHADOW = "0 1px 4px rgba(0,0,0,0.08)"
# Consistent 5-colour categorical palette used across all charts
PALETTE    = ["#2563eb", "#0d9488", "#f59e0b", "#f43f5e", "#8b5cf6"]
# Per-KPI accent (top border + icon tint)
KPI_ACCENTS = {"tiv": "#2563eb", "aal": "#0d9488", "loc": "#8b5cf6",
               "ratio": "#f43f5e", "avg": "#f59e0b"}

# Per-model themes (with futuristic gradients)
MODEL_THEMES = {
    "RMS": {
        "accent":     "#6FACDE",
        "accent_dk":  "#00263E",
        "accent_lt":  "#EBF4FB",
        "gradient":   "linear-gradient(135deg, #6FACDE 0%, #00263E 100%)",
        "soft_glow":  "rgba(111,172,222,0.25)",
        "bar_seq":    [[0,"#D5E7F5"],[1,"#6FACDE"]],
    },
    "AIR": {
        "accent":     "#4E8B6F",
        "accent_dk":  "#1B4332",
        "accent_lt":  "#E8F5EE",
        "gradient":   "linear-gradient(135deg, #6FB89A 0%, #1B4332 100%)",
        "soft_glow":  "rgba(78,139,111,0.25)",
        "bar_seq":    [[0,"#CDE5D8"],[1,"#4E8B6F"]],
    },
}
COMPARE_GRADIENT = "linear-gradient(135deg, #6FACDE 0%, #4E8B6F 100%)"

PERIL_NAMES  = {"WS":"Windstorm","FL":"Flood","FR":"Fire/EQ","SCS":"Conv. Storm","WT":"Winter Storm","EQ":"Earthquake"}
# Consistent 5-colour palette (repeated for >5 categories)
PERIL_COLORS = ["#2563eb","#0d9488","#f59e0b","#f43f5e","#8b5cf6","#2563eb"]
DONUT_COLORS = ["#2563eb","#0d9488","#f59e0b","#f43f5e","#8b5cf6","#2563eb","#0d9488"]

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css(mt):
    a  = mt["accent"]
    ad = mt["accent_dk"]
    al = mt["accent_lt"]
    gradient = mt["gradient"]
    glow = mt["soft_glow"]
    st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

  *, html, body, [class*="css"] {{
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    box-sizing: border-box;
  }}

  /* Keep Streamlit's Material icon glyphs intact — the global Inter override above
     would otherwise turn icon ligatures into literal text (e.g. "upload"). */
  span[data-testid="stIconMaterial"],
  [data-testid="stIconMaterial"],
  .material-icons, .material-icons-outlined, .material-icons-rounded,
  .material-symbols-rounded, .material-symbols-outlined, .material-symbols-sharp,
  [class*="material-symbols"], [class*="material-icons"] {{
    font-family: 'Material Symbols Rounded','Material Symbols Outlined',
                 'Material Icons Outlined','Material Icons' !important;
  }}

  .stApp {{
    background: {PAGE_BG} !important;
  }}

  /* ── Entrance animations ───────────────────────────────────────────────── */
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(14px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  @keyframes shimmer {{
    0%   {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
  }}
  .kpi-card, div[data-testid="stPlotlyChart"], .active-bar, .compare-banner {{
    animation: fadeUp 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
  }}

  /* Streamlit container — clean 24px content gutter */
  .block-container {{
    padding: 0 24px !important;
    max-width: 100% !important;
  }}
  @media (max-width: 900px) {{
    .block-container {{ padding: 0 24px !important; }}
  }}

  #MainMenu, footer, .stDeployButton {{ visibility: hidden; display: none; }}
  /* Sidebar fully removed — Restart now lives inline in the main view */
  section[data-testid="stSidebar"],
  [data-testid="stSidebarContent"],
  [data-testid="stSidebarCollapsedControl"],
  [data-testid="collapsedControl"] {{ display: none !important; }}

  /* ═══════════════════════════════════════════════════════════════════════════
     TITLE BAR — Sticky, premium feel
     ═══════════════════════════════════════════════════════════════════════════ */
  .titlebar {{
    background: {WHITE};
    border-bottom: 1px solid {BORDER};
    padding: 0 40px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 12px rgba(0,38,62,0.05);
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    background: rgba(255,255,255,0.85);
  }}
  .titlebar-left {{
    display: flex;
    align-items: center;
    gap: 14px;
  }}
  .titlebar-logo {{
    width: 36px;
    height: 36px;
    background: {gradient};
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px {glow};
    transition: all 0.25s ease;
  }}
  .titlebar-logo:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 16px {glow};
  }}
  .titlebar-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: {TEXT};
    letter-spacing: -0.4px;
    line-height: 1;
  }}
  .titlebar-sub {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    font-weight: 400;
    color: {MUTED};
    letter-spacing: -0.4px;
    margin-left: 6px;
    line-height: 1;
  }}
  .titlebar-tag {{
    font-size: 0.65rem;
    font-weight: 700;
    color: {a};
    background: {al};
    border: 1px solid {a}44;
    padding: 3px 9px;
    border-radius: 4px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-left: 10px;
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     PAGE PADDING — Generous outer breathing room
     ═══════════════════════════════════════════════════════════════════════════ */
  .page-wrap {{
    padding: 28px 40px 32px 40px;
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     MODEL SWITCHER ROW
     ═══════════════════════════════════════════════════════════════════════════ */
  .model-row-label {{
    font-size: 0.65rem;
    font-weight: 700;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .model-row-label::before {{
    content: '';
    width: 14px;
    height: 1.5px;
    background: {a};
    display: inline-block;
  }}

  /* Model-switcher button theming is injected dynamically in main()
     (see inject_model_switch_css) so it can reflect the selected model. */

  /* Restart button — top right of titlebar */
  div[data-restart-btn] + div .stButton > button,
  .restart-row .stButton > button {{
    background: transparent !important;
    color: {MUTED} !important;
    border: 1px solid {BORDER_DK} !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    height: 36px !important;
    padding: 0 18px !important;
    box-shadow: none !important;
  }}
  div[data-restart-btn] + div .stButton > button:hover,
  .restart-row .stButton > button:hover {{
    border-color: #E76F51 !important;
    color: #E76F51 !important;
    background: #FEF3F0 !important;
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     BUTTONS — Equal height, no wrap
     ═══════════════════════════════════════════════════════════════════════════ */
  .stButton > button {{
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 0 18px !important;
    height: 40px !important;
    min-height: 40px !important;
    line-height: 1 !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    letter-spacing: 0.3px !important;
  }}
  .stButton > button p {{ margin: 0 !important; line-height: 1 !important; }}
  .stButton > button:hover {{ transform: translateY(-1px); }}
  .stButton > button:active {{ transform: translateY(0); }}

  /* Download buttons — themed to the active accent */
  [data-testid="stDownloadButton"] > button {{
    background: {al} !important;
    color: {ad} !important;
    border: 1.5px solid {a}66 !important;
    border-radius: 8px !important;
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    height: 40px !important;
    width: 100% !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s cubic-bezier(0.4,0,0.2,1) !important;
  }}
  [data-testid="stDownloadButton"] > button:hover {{
    background: {gradient} !important;
    color: {WHITE} !important;
    border-color: transparent !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px {glow} !important;
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     ACTIVE INDICATOR BAR
     ═══════════════════════════════════════════════════════════════════════════ */
  .active-bar {{
    margin: 18px 0 22px 0;
    padding: 10px 16px;
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 1px 4px rgba(0,38,62,0.04);
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     KPI CARDS
     ═══════════════════════════════════════════════════════════════════════════ */
  .kpi-card {{
    background: linear-gradient(160deg, {WHITE} 0%, {al}55 100%);
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,38,62,0.05);
    transition: transform 0.28s cubic-bezier(0.22,1,0.36,1), box-shadow 0.28s ease, border-color 0.28s ease;
    height: 100%;
  }}
  .kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    height: 3px;
    width: 100%;
    background: {gradient};
  }}
  .kpi-card::after {{
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 110px; height: 110px;
    background: radial-gradient(circle, {glow} 0%, transparent 70%);
    opacity: 0.6;
    pointer-events: none;
    transition: opacity 0.28s ease;
  }}
  .kpi-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 28px rgba(0,38,62,0.12);
    border-color: {a}66;
  }}
  .kpi-card:hover::after {{ opacity: 1; }}
  .kpi-head {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }}
  .kpi-icon {{
    width: 30px; height: 30px;
    border-radius: 9px;
    background: {al};
    border: 1px solid {a}33;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    box-shadow: inset 0 1px 2px rgba(255,255,255,0.6);
  }}
  .kpi-label {{
    font-size: 0.66rem;
    font-weight: 700;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 1.2px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .kpi-value {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: {TEXT};
    line-height: 1.1;
    letter-spacing: -0.6px;
  }}
  .kpi-sub {{
    font-size: 0.7rem;
    color: {MUTED};
    margin-top: 6px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .kpi-sub::before {{
    content: '';
    width: 5px; height: 5px;
    border-radius: 50%;
    background: {a};
    display: inline-block;
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     CHART CARDS — Generous padding, soft shadows
     ═══════════════════════════════════════════════════════════════════════════ */
  div[data-testid="stPlotlyChart"] {{
    background: {WHITE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 0 !important;
    padding: 14px 14px 10px 14px !important;
    box-shadow: 0 2px 10px rgba(0,38,62,0.05) !important;
    transition: box-shadow 0.25s ease;
  }}
  div[data-testid="stPlotlyChart"]:hover {{
    box-shadow: 0 6px 20px rgba(0,38,62,0.08) !important;
  }}
  .js-plotly-plot, .js-plotly-plot .plot-container, .js-plotly-plot .svg-container {{ border-radius: 0 !important; }}

  /* ═══════════════════════════════════════════════════════════════════════════
     SECTION LABEL
     ═══════════════════════════════════════════════════════════════════════════ */
  .sec-lbl {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.92rem;
    font-weight: 600;
    color: {TEXT};
    letter-spacing: -0.2px;
    margin: 30px 0 16px 0;
    padding: 6px 0 6px 14px;
    position: relative;
    display: flex;
    align-items: center;
    gap: 10px;
    animation: fadeUp 0.5s cubic-bezier(0.22,1,0.36,1) both;
  }}
  .sec-lbl::before {{
    content: '';
    position: absolute;
    left: 0; top: 50%;
    transform: translateY(-50%);
    width: 3px; height: 70%;
    border-radius: 3px;
    background: {gradient};
    box-shadow: 0 0 8px {glow};
  }}
  .sec-lbl-sub {{
    font-size: 0.7rem;
    color: {MUTED};
    font-weight: 400;
    font-family: 'Inter', sans-serif;
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     SELECTBOXES — Visible text, proper height
     ═══════════════════════════════════════════════════════════════════════════ */
  .stSelectbox > div > div,
  .stMultiSelect > div > div {{
    background: {WHITE} !important;
    border: 1px solid {BORDER_DK} !important;
    color: {TEXT} !important;
    border-radius: 8px !important;
    font-size: 0.84rem !important;
    box-shadow: 0 1px 3px rgba(0,38,62,0.05) !important;
    min-height: 40px !important;
    transition: all 0.15s !important;
  }}
  .stSelectbox > div > div:hover,
  .stMultiSelect > div > div:hover {{
    border-color: {a} !important;
    box-shadow: 0 2px 8px {glow} !important;
  }}
  .stSelectbox label, .stMultiSelect label {{
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    color: {MUTED} !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px !important;
  }}
  div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
  div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
  div[data-testid="stSelectbox"] div[role="combobox"] {{
    color: {TEXT} !important;
    font-weight: 500 !important;
  }}
  div[data-baseweb="popover"] li,
  div[data-baseweb="popover"] div {{
    background: {WHITE} !important;
    color: {TEXT} !important;
  }}
  div[data-baseweb="popover"] li:hover {{
    background: {al} !important;
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     FILE UPLOADER
     ═══════════════════════════════════════════════════════════════════════════ */
  [data-testid="stFileUploader"] {{
    background: {WHITE} !important;
    border: 2px dashed {a} !important;
    border-radius: 12px !important;
    padding: 12px !important;
    box-shadow: 0 4px 20px {glow} !important;
  }}
  [data-testid="stFileUploader"]:hover {{
    border-color: {ad} !important;
    background: {al}80 !important;
  }}
  [data-testid="stFileUploader"] label {{ display: none !important; }}
  [data-testid="stFileUploaderDropzone"] {{
    background: transparent !important;
    padding: 24px !important;
  }}
  [data-testid="stFileUploaderDropzone"] * {{ color: {TEXT} !important; }}
  [data-testid="stFileUploaderDropzone"] small,
  [data-testid="stFileUploaderDropzone"] span:not(button span) {{
    color: {MUTED} !important;
    font-size: 0.8rem !important;
  }}
  [data-testid="stFileUploaderDropzone"] button {{
    background: {gradient} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    box-shadow: 0 2px 8px {glow} !important;
  }}
  [data-testid="stFileUploaderDropzone"] button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 14px {glow} !important;
  }}
  [data-testid="stFileUploaderFile"] {{
    background: {al} !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
  }}
  [data-testid="stFileUploaderFile"] * {{ color: {TEXT} !important; }}

  /* ═══════════════════════════════════════════════════════════════════════════
     COMPARE BANNER
     ═══════════════════════════════════════════════════════════════════════════ */
  .compare-banner {{
    background: linear-gradient(to right, #EBF4FB, #E8F5EE);
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 14px 20px;
    font-size: 0.85rem;
    font-weight: 600;
    color: {TEXT};
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 2px 10px rgba(0,38,62,0.06);
  }}

  /* Column spacing */
  [data-testid="column"] {{ padding: 0 8px !important; }}
  [data-testid="stHorizontalBlock"] {{ gap: 0 !important; }}

  /* Plot container — no overlap */
  div[data-testid="stPlotlyChart"] > div {{ overflow: visible !important; }}
  .plotly .legend {{ overflow: visible !important; }}

  /* ═══════════════════════════════════════════════════════════════════════════
     RESPONSIVE — let fixed column rows reflow on narrow screens
     ═══════════════════════════════════════════════════════════════════════════ */
  /* Tablet & below: rows wrap, columns take half width (2-up) */
  @media (max-width: 1024px) {{
    [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
      flex: 1 1 48% !important;
      min-width: 48% !important;
      margin-bottom: 12px;
    }}
  }}
  /* Phone: everything stacks 1-up */
  @media (max-width: 640px) {{
    .block-container {{ padding: 0 16px !important; }}
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
      flex: 1 1 100% !important;
      min-width: 100% !important;
    }}
    .kpi-value {{ font-size: 1.5rem; }}
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     PROFESSIONAL UI REFRESH — overrides (clean, flat, consistent)
     ═══════════════════════════════════════════════════════════════════════════ */
  /* Type scale */
  h1, h2, h3 {{ font-size: 17px !important; font-weight: 600 !important; color: {TEXT_DK} !important; }}

  /* Sticky top header bar */
  .pro-header {{
    position: sticky; top: 0; z-index: 999;
    height: 64px;
    background: {CARD_BG};
    border-bottom: 1px solid {LINE};
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px;
    margin: 0 -24px 12px -24px;
  }}
  .pro-header .ph-left {{ display: flex; align-items: center; gap: 10px; }}
  .pro-header .ph-title {{ font-size: 17px; font-weight: 700; color: {TEXT_DK}; line-height: 1.1; }}
  .pro-header .ph-sub {{ font-size: 11px; color: {SUBTLE}; line-height: 1.1; margin-top: 2px; }}
  .pro-header .ph-right {{ display: flex; align-items: center; gap: 14px; }}
  .pro-header .ph-time {{ font-size: 12px; color: {LABEL_GRAY}; }}
  .pro-header .ph-gear {{ font-size: 16px; color: {SUBTLE}; cursor: pointer; }}

  /* Model selector — segmented pill (st.radio horizontal) */
  div[data-testid="stRadio"] > div[role="radiogroup"] {{
    background: {LINE};
    border-radius: 999px;
    padding: 4px;
    gap: 4px;
    display: inline-flex;
    flex-direction: row;
    flex-wrap: nowrap;
  }}
  div[data-testid="stRadio"] label {{
    background: transparent;
    border-radius: 999px;
    padding: 6px 20px;
    margin: 0 !important;
    color: {TEXT_DK};            /* all tabs share the same readable colour */
    font-weight: 600;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  div[data-testid="stRadio"] label p {{ color: {TEXT_DK}; font-weight: 600; }}
  div[data-testid="stRadio"] label > div:first-child {{ display: none !important; }}
  div[data-testid="stRadio"] label:hover {{ color: {NAVY}; }}
  div[data-testid="stRadio"] label:has(input:checked) {{
    background: {NAVY};
    color: #ffffff !important;
  }}
  div[data-testid="stRadio"] label:has(input:checked) p {{ color: #ffffff !important; }}

  /* Form labels — 11–12px uppercase grey */
  .stSelectbox label, .stMultiSelect label, .stNumberInput label {{
    font-size: 11px !important;
    font-weight: 400 !important;
    color: {LABEL_GRAY} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    margin-bottom: 6px !important;
  }}
  /* Top N number input — match the other (light) filter controls */
  .stNumberInput > div > div {{
    background: {CARD_BG} !important;
    border: 1px solid {BORDER_DK} !important;
    border-radius: 8px !important;
  }}
  .stNumberInput div[data-baseweb="input"],
  .stNumberInput div[data-baseweb="base-input"] {{
    background: {CARD_BG} !important;
  }}
  .stNumberInput input {{
    background: {CARD_BG} !important;
    color: {TEXT_DK} !important;
    -webkit-text-fill-color: {TEXT_DK} !important;
  }}
  /* +/- stepper buttons */
  .stNumberInput button,
  [data-testid="stNumberInputStepUp"],
  [data-testid="stNumberInputStepDown"] {{
    background: {CARD_BG} !important;
    color: {TEXT_DK} !important;
    border-left: 1px solid {LINE} !important;
  }}
  .stNumberInput button:hover,
  [data-testid="stNumberInputStepUp"]:hover,
  [data-testid="stNumberInputStepDown"]:hover {{
    background: {LIGHT_BG} !important;
    color: {NAVY} !important;
  }}

  /* Filter control-panel zone — carded, full width, matches KPI card styling */
  .st-key-filterpanel {{
    background: #F8F9FB !important;
    border: 1px solid #E2E6EA !important;
    border-radius: 8px !important;
    box-shadow: {CARD_SHADOW} !important;
    padding: 12px 16px !important;
    margin-bottom: 8px !important;
  }}
  .panel-file {{
    display: flex; align-items: center; gap: 6px;
    color: {MUTED}; font-size: 0.74rem; font-weight: 500;
    margin-bottom: 6px;
  }}

  /* KPI cards — flat, soft shadow, accent top border set inline */
  .kpi-card {{
    background: {CARD_BG} !important;
    border: 1px solid {LINE} !important;
    border-radius: 12px !important;
    box-shadow: {CARD_SHADOW} !important;
  }}
  .kpi-card::before, .kpi-card::after {{ display: none !important; }}
  .kpi-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.10) !important;
  }}
  .kpi-icon {{ width: 36px !important; height: 36px !important; background: transparent !important;
               border: none !important; box-shadow: none !important; }}
  .kpi-label {{ font-size: 12px !important; font-weight: 400 !important; color: {LABEL_GRAY} !important;
                text-transform: uppercase; letter-spacing: 0.6px; }}
  .kpi-value {{ color: {TEXT_DK} !important; }}
  .kpi-sub {{ color: {SUBTLE} !important; }}
  .kpi-sub::before {{ background: {SUBTLE} !important; }}

  /* Section headers — 3px navy left border, bold title, 12px subtitle inline */
  .sec-lbl {{
    border-left: 3px solid {NAVY} !important;
    padding-left: 12px !important;
    margin: 36px 0 12px 0 !important;
    font-size: 17px !important;
    font-weight: 600 !important;
    color: {TEXT_DK} !important;
  }}
  .sec-lbl::before {{ display: none !important; }}
  .sec-lbl-sub {{ font-size: 12px !important; color: {SUBTLE} !important; font-weight: 400 !important; }}

  /* Chart cards — flat, no rounded corners, no scrollbars */
  div[data-testid="stPlotlyChart"] {{
    border: 1px solid {LINE} !important;
    border-radius: 0 !important;
    box-shadow: {CARD_SHADOW} !important;
    margin-bottom: 16px !important;
    overflow: hidden !important;
  }}
  div[data-testid="stPlotlyChart"] > div,
  div[data-testid="stPlotlyChart"] iframe {{
    overflow: hidden !important;
  }}
  div[data-testid="stPlotlyChart"]:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.10) !important; }}

  /* Inline Restart button (outlined, subtle) */
  .st-key-btn_restart button {{
    background: {CARD_BG} !important;
    color: #dc2626 !important;
    border: 1px solid {LINE} !important;
    font-weight: 600 !important;
    height: 38px !important;
  }}
  .st-key-btn_restart button:hover {{
    background: #fef2f2 !important;
    border-color: #fca5a5 !important;
  }}

  /* ═══════════════════════════════════════════════════════════════════════════
     SINGLE-VIEWPORT COMPACT MODE — fit everything on one 1080p screen
     ═══════════════════════════════════════════════════════════════════════════ */
  /* Kill wasted top/bottom page padding */
  .block-container {{ padding-top: 6px !important; padding-bottom: 6px !important; }}
  .stApp [data-testid="stMainBlockContainer"] {{ padding-top: 6px !important; padding-bottom: 6px !important; }}

  /* Tighten Streamlit's default vertical gap between stacked elements */
  [data-testid="stVerticalBlock"] {{ gap: 0.6rem !important; }}
  [data-testid="stVerticalBlockBorderWrapper"] {{ gap: 0.6rem !important; }}

  /* Header — slimmer + flush */
  .pro-header {{ height: 52px !important; margin: 0 -24px 6px -24px !important; }}

  /* Model selector + filename strip — compact */
  .model-row-label {{ margin: 4px 0 4px 0 !important; }}
  .active-bar {{ margin: 6px 0 8px 0 !important; padding: 6px 12px !important; }}
  div[data-testid="stRadio"] label {{ padding: 4px 16px !important; }}

  /* Filter row — flush, minimal vertical padding */
  .stSelectbox > div > div, .stMultiSelect > div > div,
  .stNumberInput > div > div {{ min-height: 34px !important; }}
  .stSelectbox label, .stMultiSelect label, .stNumberInput label {{ margin-bottom: 2px !important; }}

  /* KPI cards — compact padding + type */
  .kpi-card {{ padding: 10px 14px !important; }}
  .kpi-head {{ margin-bottom: 4px !important; }}
  .kpi-icon {{ width: 26px !important; height: 26px !important; }}
  .kpi-icon svg {{ width: 20px !important; height: 20px !important; }}
  .kpi-value {{ font-size: 1.35rem !important; }}
  .kpi-label {{ font-size: 11px !important; }}
  .kpi-sub {{ font-size: 10px !important; margin-top: 2px !important; }}

  /* Chart cards — comfortable padding + gap (no edge clipping) */
  div[data-testid="stPlotlyChart"] {{ padding: 10px 12px 8px 12px !important; margin-bottom: 16px !important; }}

  /* Tile group label — slim band above each chart row (Power BI grouping) */
  .tile-group {{
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: {NAVY};
    border-left: 3px solid {NAVY};
    padding-left: 8px;
    margin: 30px 0 8px 0;   /* extra breathing room between rows */
  }}

  /* Tab bar — compact, flush under filters */
  [data-testid="stTabs"] {{ margin-top: 2px !important; }}
  [data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap: 4px !important; }}
  [data-testid="stTabs"] [data-baseweb="tab"] {{
    padding: 4px 14px !important;
    height: 34px !important;
  }}
  [data-testid="stTabs"] [data-baseweb="tab-panel"] {{ padding-top: 6px !important; }}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_num(df, col):
    if col and col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(0)
    return pd.Series([0]*len(df), index=df.index)

def format_currency(n):
    """Single consistent currency formatter used by every KPI card and chart label.
    Rules: Billions → 2 dp, Millions → 2 dp, Thousands → 1 dp, below 1K → whole dollars."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "$0"
    if abs(n) >= 1_000_000_000: return f"${n/1e9:.2f}B"
    if abs(n) >= 1_000_000:     return f"${n/1e6:.2f}M"
    if abs(n) >= 1_000:         return f"${n/1e3:.1f}K"
    return f"${n:,.0f}"

# Backwards-compatible alias — all existing call sites use fmt()
fmt = format_currency

def clean_labels(series):
    """Coerce a category column to readable string labels; blanks/NaN → 'Unknown'."""
    s = series.astype("object").where(series.notna(), "Unknown")
    s = s.astype(str).str.strip()
    return s.replace({"": "Unknown", "nan": "Unknown", "None": "Unknown"})

def detect_cols(df):
    c = {k.upper().strip(): k for k in df.columns}
    def find(*ps):
        for p in ps:
            for k,v in c.items():
                if p.upper() in k: return v
        return None
    def find_name(*ps):
        """Like find(), but for human-readable name columns: prefer a text/object
        column and skip obvious numeric ID/code columns so legends/axes show names."""
        matches = [v for p in ps for k,v in c.items() if p.upper() in k]
        # de-dup, preserve order
        seen, ordered = set(), []
        for v in matches:
            if v not in seen:
                seen.add(v); ordered.append(v)
        # 1) text column that isn't an ID/code/number field
        for v in ordered:
            up = v.upper()
            is_idish = any(t in up for t in ("ID", "CODE", "NUM", "NO", "KEY"))
            if not is_idish and df[v].dtype == object:
                return v
        # 2) any text column
        for v in ordered:
            if df[v].dtype == object:
                return v
        # 3) fall back to first match
        return ordered[0] if ordered else None
    return {
        "city":      find_name("CITYNAME","CITY","TOWN"),
        "state":     find_name("PROVINCE NAME","STATE NAME","PROVINCE","STATE","REGION","LOCNAME","LOC_NAME"),
        "account":   find("ACCNTNUM","ACCOUNT","ACCT","POLICY"),
        "date":      find("INCEPTDATE","INCEPTION","INCP","DATE"),
        "ws_aal":    find("WS AAL","WSAAL"),
        "fl_aal":    find("FL AAL","FLAAL"),
        "fr_aal":    find("FR AAL","FRAAL"),
        "scs_aal":   find("SCS AAL","SCSAAL"),
        "wt_aal":    find("WT AAL","WTAAL"),
        "eq_aal":    find("EQ AAL","EQAAL"),
        "total_aal": find("TOTAL AAL","TOTALAAL"),
        "ws_trv":    find("WS TRV","WSTRV","WS TIV","WSTIV"),
        "fl_trv":    find("FL TRV","FLTRV","FL TIV","FLTIV"),
        "fr_trv":    find("FR TRV","FRTRV"),
    }

def prepare(df, cols):
    peril_map = {"WS":cols["ws_aal"],"FL":cols["fl_aal"],"FR":cols["fr_aal"],
                 "SCS":cols["scs_aal"],"WT":cols["wt_aal"],"EQ":cols["eq_aal"]}
    avail = {k:v for k,v in peril_map.items() if v}
    for k,v in avail.items():
        df[f"_p_{k}"] = safe_num(df, v)
    if cols["total_aal"]:
        df["_TotalAAL"] = safe_num(df, cols["total_aal"])
    elif avail:
        df["_TotalAAL"] = sum(df[f"_p_{k}"] for k in avail)
    else:
        df["_TotalAAL"] = 0
    tiv_col = cols["ws_trv"] or cols["fl_trv"] or cols["fr_trv"]
    df["_TIV"] = safe_num(df, tiv_col)
    if cols["date"]:
        df["_date"] = pd.to_datetime(df[cols["date"]], errors="coerce")
        df["_quarter"] = df["_date"].dt.to_period("Q").astype(str)
    else:
        df["_date"] = pd.NaT
        df["_quarter"] = "Unknown"
    return df, avail

# ── Chart theming ─────────────────────────────────────────────────────────────
def tf(fig, mt, title="", height=300):
    """Apply base chart theming — clean, consistent, professional."""
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color=TEXT_DK, family="Inter, sans-serif", size=11),
        title=dict(
            text=f"<span style='font-weight:500'>{title}</span>" if title else "",
            font=dict(size=14, color=TEXT_DK, family="Inter, sans-serif"),
            x=0.01, xanchor="left", y=0.97
        ),
        margin=dict(l=14, r=28, t=48, b=52),
        height=height,
        legend=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=LINE,
            borderwidth=1,
            font=dict(size=10, color=TEXT_DK),
            orientation="h",
            yanchor="bottom",
            y=-0.30,
            xanchor="center",
            x=0.5,
        ),
        xaxis=dict(gridcolor=GRID, gridwidth=1, showgrid=True, zeroline=False, automargin=True,
                   tickfont=dict(size=10, color=LABEL_GRAY), linecolor=LINE, tickcolor=LINE),
        yaxis=dict(gridcolor=GRID, gridwidth=1, showgrid=False, zeroline=False, automargin=True,
                   tickfont=dict(size=10, color=LABEL_GRAY), linecolor=LINE),
        hoverlabel=dict(bgcolor="#ffffff", font_size=12, font_family="Inter, sans-serif",
                        bordercolor=LINE, font_color=TEXT_DK),
        coloraxis_colorbar=dict(tickfont=dict(size=9), title_font=dict(size=10)),
    )
    return fig

def h_bar(df_in, y_col, x_col, mt, title="", top_n=10, height=300):
    # Sort ascending so the largest bar ends up at the TOP of a horizontal chart
    df_p = df_in.nlargest(top_n, x_col).sort_values(x_col, ascending=True).copy()
    labels = clean_labels(df_p[y_col]).tolist()
    xvals = pd.to_numeric(df_p[x_col], errors="coerce").fillna(0).tolist()
    xmax = max(xvals) if xvals else 0
    fig = go.Figure(go.Bar(
        y=labels, x=xvals, orientation="h",
        marker=dict(color=xvals, colorscale=mt["bar_seq"], line=dict(width=0)),
        text=[fmt(v) for v in xvals],
        textposition="outside", textfont=dict(size=10, color=MUTED),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f}<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        # Force a categorical Y axis (prevents numeric-looking labels rendering as a
        # 0→1000 numeric scale) and keep rank order from the data (largest on top).
        yaxis=dict(type="category", categoryorder="array",
                   categoryarray=labels, autorange=True),
        # Value axis always starts at 0; pad ~22% so outside labels don't clip.
        xaxis=dict(showticklabels=False, range=[0, xmax * 1.22 if xmax else 1]),
    )
    fig = tf(fig, mt, title, height)
    fig.update_layout(margin=dict(l=14, r=24, t=48, b=40))
    return fig

def v_bar(df_in, x_col, y_col, mt, title="", top_n=10, height=300):
    df_p = df_in.nlargest(top_n, y_col).copy()
    labels = clean_labels(df_p[x_col]).tolist()
    yvals = pd.to_numeric(df_p[y_col], errors="coerce").fillna(0).tolist()
    ymax = max(yvals) if yvals else 0
    fig = go.Figure(go.Bar(
        x=labels, y=yvals,
        marker=dict(color=yvals, colorscale=mt["bar_seq"], line=dict(width=0)),
        text=[fmt(v) for v in yvals],
        textposition="outside", textfont=dict(size=10, color=MUTED),
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(type="category", categoryorder="array", categoryarray=labels),
        yaxis=dict(range=[0, ymax * 1.18 if ymax else 1]),  # headroom for labels
    )
    return tf(fig, mt, title, height)

def donut(labels, values, mt, title="", height=300):
    """Donut sliced by province NAME. Labels under 5% are hidden on the slice
    (still visible in the legend + hover) and kept horizontal so they never clip."""
    labels = [str(l).strip() or "Unknown" for l in labels]
    values = [float(v) if pd.notna(v) else 0 for v in values]
    total = sum(values) if values else 0
    # Only label slices >= 5%; smaller ones rely on legend/tooltip
    slice_text = [f"{(v/total*100):.1f}%" if total and (v/total) >= 0.05 else "" for v in values]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=DONUT_COLORS, line=dict(color=WHITE, width=2.5)),
        text=slice_text, textinfo="text", textposition="inside",
        insidetextorientation="horizontal",
        textfont=dict(size=11, color=WHITE, family="Inter, sans-serif"),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
        sort=False,
    ))
    fig.add_annotation(
        text=f"<span style='font-size:9px;color:{MUTED};letter-spacing:1px'>TOTAL</span><br>"
             f"<b style='font-size:17px'>{fmt(total)}</b>",
        x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
        font=dict(family="Inter, sans-serif", color=mt["accent_dk"]),
        align="center",
    )
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color=TEXT_DK, family="Inter, sans-serif", size=11),
        title=dict(
            text=f"<span style='font-weight:500'>{title}</span>" if title else "",
            font=dict(size=14, color=TEXT_DK, family="Inter, sans-serif"),
            x=0.01, xanchor="left", y=0.97
        ),
        margin=dict(t=48, b=44, l=12, r=12),
        height=height,
        showlegend=True,
        legend=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=LINE,
            borderwidth=0,
            font=dict(size=10, color=TEXT_DK),
            orientation="h",
            yanchor="top",
            y=-0.02,
            xanchor="center",
            x=0.5,
        ),
        hoverlabel=dict(bgcolor=WHITE, font_size=12, font_family="Inter, sans-serif",
                        bordercolor=LINE, font_color=TEXT_DK),
    )
    return fig

def line_fig(df_in, x_col, y_col, mt, title="", height=300):
    fig = go.Figure(go.Scatter(
        x=df_in[x_col], y=df_in[y_col], mode="lines+markers+text",
        line=dict(color=mt["accent"], width=3, shape="spline"),
        marker=dict(color=mt["accent"], size=9, line=dict(color=WHITE, width=2.5)),
        text=[fmt(v) for v in df_in[y_col]], textposition="top center",
        textfont=dict(size=10, color=MUTED),
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
        fill="tozeroy", fillcolor=mt["accent_lt"],
    ))
    return tf(fig, mt, title, height)

def stacked_bar(df_melt, x_col, y_col, color_col, mt, title="", height=300):
    fig = px.bar(df_melt, x=x_col, y=y_col, color=color_col, barmode="stack",
                 color_discrete_sequence=PERIL_COLORS, text=y_col)
    fig.update_traces(texttemplate="%{text:.2s}", textposition="inside",
                      textfont=dict(size=9, color=WHITE), marker_line_width=0,
                      hovertemplate="<b>%{x}</b><br>%{fullData.name}: $%{y:,.0f}<extra></extra>")
    fig = tf(fig, mt, title, height)
    fig.update_layout(
        margin=dict(t=48, b=64, l=12, r=12),
        xaxis=dict(title=None),
        yaxis=dict(title=None),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=10, color=TEXT_DK),
        ),
    )
    return fig

def peril_mini_bar(y_vals, x_vals, color, title, height=230):
    # Rank ascending so the highest-rate account sits at the top
    pairs = sorted(zip([str(v).strip() or "Unknown" for v in y_vals],
                       [float(v) if pd.notna(v) else 0 for v in x_vals]),
                   key=lambda t: t[1])
    labels = [p[0] for p in pairs]
    xvals  = [p[1] for p in pairs]
    xmax = max(xvals) if xvals else 0
    fig = go.Figure(go.Bar(
        y=labels, x=xvals, orientation="h",
        marker=dict(color=color, opacity=0.88, line=dict(width=0)),
        text=[f"{v:.3f}%" for v in xvals],
        textposition="outside", textfont=dict(size=9, color=MUTED),
        hovertemplate="<b>%{y}</b><br>Rate: %{x:.4f}%<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(color=TEXT_DK, family="Inter, sans-serif", size=10),
        height=height, margin=dict(l=14, r=20, t=46, b=24),
        title=dict(text=f"<span style='font-weight:500'>{title}</span>",
                   font=dict(size=14, color=TEXT_DK, family="Inter, sans-serif"), x=0.01),
        yaxis=dict(type="category", categoryorder="array", categoryarray=labels,
                   showgrid=False, automargin=True, tickfont=dict(size=9.5, color=LABEL_GRAY)),
        xaxis=dict(showticklabels=False, showgrid=False,
                   range=[0, xmax * 1.28 if xmax else 1]),
        hoverlabel=dict(bgcolor="#ffffff", font_size=11, bordercolor=LINE, font_color=TEXT_DK),
    )
    return fig

# ── Compare view ──────────────────────────────────────────────────────────────
def render_compare(df_rms, cols_rms, avail_rms, df_air, cols_air, avail_air):
    mr = MODEL_THEMES["RMS"]
    ma = MODEL_THEMES["AIR"]
    st.markdown(f"""<div class="compare-banner">
        <span style="width:12px;height:12px;border-radius:50%;background:{mr['accent']};display:inline-block;box-shadow:0 0 0 3px {mr['accent']}33"></span>
        <span style="font-weight:700">RMS</span>
        <span style="color:{MUTED};font-weight:400">vs</span>
        <span style="width:12px;height:12px;border-radius:50%;background:{ma['accent']};display:inline-block;box-shadow:0 0 0 3px {ma['accent']}33"></span>
        <span style="font-weight:700">AIR</span>
        <span style="color:{MUTED};font-weight:400;font-size:0.78rem;margin-left:12px">Model Comparison Analysis</span>
    </div>""", unsafe_allow_html=True)

    # ── Shared filters (apply to both models) ──────────────────────────────────
    q_set = set()
    if "_quarter" in df_rms.columns: q_set |= set(df_rms["_quarter"].dropna().unique())
    if "_quarter" in df_air.columns: q_set |= set(df_air["_quarter"].dropna().unique())
    q_opts = ["All"] + sorted(s for s in q_set if s and s != "Unknown")
    fc1, fc2, _sp = st.columns([1, 1, 3])
    with fc1:
        top_n = st.selectbox("Top N", [5, 8, 10, 15, 20], index=1, key="cmp_topn")
    with fc2:
        quarter_filter = st.selectbox("Quarter", q_opts, key="cmp_qf")
    if quarter_filter != "All":
        if "_quarter" in df_rms.columns: df_rms = df_rms[df_rms["_quarter"] == quarter_filter].copy()
        if "_quarter" in df_air.columns: df_air = df_air[df_air["_quarter"] == quarter_filter].copy()
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    metrics = [("Total TIV","_TIV"),("Total AAL","_TotalAAL")]
    kc = st.columns(4)
    for i,(lbl,col) in enumerate(metrics):
        vr = df_rms[col].sum()
        va = df_air[col].sum()
        with kc[i*2]:
            st.markdown(f"""<div class="kpi-card" style="border-top:3px solid {mr['accent']}">
                <div class="kpi-label" style="color:{mr['accent_dk']}">
                    <span style="width:6px;height:6px;border-radius:50%;background:{mr['accent']};display:inline-block"></span>
                    RMS — {lbl}
                </div>
                <div class="kpi-value">{fmt(vr)}</div>
            </div>""", unsafe_allow_html=True)
        with kc[i*2+1]:
            st.markdown(f"""<div class="kpi-card" style="border-top:3px solid {ma['accent']}">
                <div class="kpi-label" style="color:{ma['accent_dk']}">
                    <span style="width:6px;height:6px;border-radius:50%;background:{ma['accent']};display:inline-block"></span>
                    AIR — {lbl}
                </div>
                <div class="kpi-value">{fmt(va)}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    sc_rms = cols_rms["state"] or cols_rms["city"]
    sc_air = cols_air["state"] or cols_air["city"]
    with c1:
        if sc_rms:
            agg = df_rms.groupby(sc_rms)["_TotalAAL"].sum().reset_index().nlargest(top_n,"_TotalAAL")
            st.plotly_chart(h_bar(agg, sc_rms, "_TotalAAL", mr, "RMS — AAL by Province", top_n, 340),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})
    with c2:
        if sc_air:
            agg = df_air.groupby(sc_air)["_TotalAAL"].sum().reset_index().nlargest(top_n,"_TotalAAL")
            st.plotly_chart(h_bar(agg, sc_air, "_TotalAAL", ma, "AIR — AAL by Province", top_n, 340),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})

    common = list(set(avail_rms.keys()) & set(avail_air.keys()))
    if common:
        st.markdown("<div class='sec-lbl'>Peril AAL Comparison <span class='sec-lbl-sub'>Common perils across both models</span></div>", unsafe_allow_html=True)
        rows = [{"Peril":PERIL_NAMES.get(p,p),"RMS":df_rms[f"_p_{p}"].sum(),"AIR":df_air[f"_p_{p}"].sum()} for p in common]
        cdf = pd.DataFrame(rows)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="RMS", x=cdf["Peril"], y=cdf["RMS"], marker_color=PALETTE[0],
                             text=[fmt(v) for v in cdf["RMS"]], textposition="outside",
                             textfont=dict(size=10, color=LABEL_GRAY), marker_line_width=0))
        fig.add_trace(go.Bar(name="AIR", x=cdf["Peril"], y=cdf["AIR"], marker_color=PALETTE[1],
                             text=[fmt(v) for v in cdf["AIR"]], textposition="outside",
                             textfont=dict(size=10, color=LABEL_GRAY), marker_line_width=0))
        cmp_max = float(cdf[["RMS","AIR"]].max().max()) if len(cdf) else 0
        fig.update_layout(barmode="group", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                          font=dict(color=TEXT_DK, family="Inter, sans-serif"), height=320,
                          margin=dict(l=14, r=20, t=54, b=44),
                          legend=dict(bgcolor="rgba(255,255,255,0.95)", bordercolor=LINE,
                                      orientation="h", yanchor="top", y=1.12, x=1, xanchor="right",
                                      font=dict(size=11)),
                          xaxis=dict(gridcolor=GRID, gridwidth=1, automargin=True, tickfont=dict(size=10, color=TEXT_DK)),
                          yaxis=dict(showticklabels=False, gridcolor=GRID, gridwidth=1,
                                     range=[0, cmp_max * 1.18 if cmp_max else 1]),
                          hoverlabel=dict(bgcolor="#ffffff", font_size=12, bordercolor=LINE))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})

# ── Main dashboard ────────────────────────────────────────────────────────────
def render_dashboard(df, cols, avail, mt, top_n, filter_by, filter_peril, quarter_filter):
    if quarter_filter and quarter_filter != "All" and "_quarter" in df.columns:
        df = df[df["_quarter"] == quarter_filter].copy()

    city_col  = cols["city"]
    state_col = cols["state"] or city_col
    acct_col  = cols["account"] or state_col

    total_tiv  = df["_TIV"].sum()
    total_aal  = df["_TotalAAL"].sum()
    n_locs     = len(df)
    loss_ratio = (total_aal / total_tiv * 100) if total_tiv > 0 else 0

    # KPIs — each tinted with its own accent (24px icon + 3px top border)
    def kpi_icon(name, c):
        paths = {
            "tiv":   '<path d="M3 21h18M5 21V8l7-5 7 5v13M9 21v-6h6v6" stroke="{c}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>',
            "aal":   '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
            "loc":   '<path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" stroke="{c}" stroke-width="2" stroke-linejoin="round"/><circle cx="12" cy="10" r="2.5" stroke="{c}" stroke-width="2"/>',
            "ratio": '<path d="M5 19 19 5M8 8h.01M16 16h.01" stroke="{c}" stroke-width="2" stroke-linecap="round"/><circle cx="7.5" cy="7.5" r="2.5" stroke="{c}" stroke-width="2"/><circle cx="16.5" cy="16.5" r="2.5" stroke="{c}" stroke-width="2"/>',
            "avg":   '<path d="M3 17l5-5 4 4 8-8M21 8v5M16 8h5" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
        }
        return f'<svg width="24" height="24" viewBox="0 0 24 24" fill="none">{paths[name].format(c=c)}</svg>'

    k1,k2,k3,k4,k5 = st.columns(5)
    for col_w, lbl, val, sub, icon in [
        (k1,"Total TIV",fmt(total_tiv),"Sum of TRV","tiv"),
        (k2,"Total AAL",fmt(total_aal),"All perils","aal"),
        (k3,"Locations",f"{n_locs:,}","Records","loc"),
        (k4,"Loss Ratio",f"{loss_ratio:.2f}%","AAL / TIV","ratio"),
        (k5,"Avg AAL / Loc",fmt(total_aal/n_locs if n_locs else 0),"Per location","avg"),
    ]:
        ac = KPI_ACCENTS[icon]
        with col_w:
            st.markdown(f"""<div class="kpi-card" style="border-top:3px solid {ac}">
                <div class="kpi-head">
                    <div class="kpi-label">{lbl}</div>
                    <div class="kpi-icon">{kpi_icon(icon, ac)}</div>
                </div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Sort column logic
    sort_col, sort_lbl = "_TotalAAL", "Total AAL"
    if filter_by == "TIV":
        sort_col, sort_lbl = "_TIV", "Total TIV"
    elif filter_by == "Peril AAL" and filter_peril and filter_peril in avail:
        sort_col, sort_lbl = f"_p_{filter_peril}", f"{PERIL_NAMES.get(filter_peril,filter_peril)} AAL"

    CH = 300  # tile height — every chart visible at once (Power BI style), roomy enough to avoid clipping

    # Pre-compute account aggregates (shared across tiles)
    acct_agg = None
    if acct_col:
        agg_d = {"_TotalAAL":"sum","_TIV":"sum"}
        for k in avail: agg_d[f"_p_{k}"] = "sum"
        acct_agg = df.groupby(acct_col).agg(agg_d).reset_index()
        acct_agg["LossRatio"] = (acct_agg["_TotalAAL"] / acct_agg["_TIV"].replace(0,np.nan)*100).fillna(0)
        for k in avail:
            acct_agg[f"_rate_{k}"] = acct_agg[f"_p_{k}"] / acct_agg["_TIV"].replace(0,np.nan)*100

    def tile_label(text):
        st.markdown(f"<div class='tile-group'>{text}</div>", unsafe_allow_html=True)

    # ════════ Power BI–style grid: all chart tiles laid out together ════════════

    # Row 1 — Geographic distribution
    tile_label("Geographic Distribution")
    r1a, r1b, r1c = st.columns([1, 1, 0.95])
    with r1a:
        if state_col:
            agg = df.groupby(state_col)[sort_col].sum().reset_index()
            agg.columns = [state_col, sort_lbl]
            st.plotly_chart(h_bar(agg, state_col, sort_lbl, mt, f"{sort_lbl} by Province", top_n, CH),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})
    with r1b:
        if city_col:
            agg = df.groupby(city_col)[sort_col].sum().reset_index()
            agg.columns = [city_col, sort_lbl]
            st.plotly_chart(h_bar(agg, city_col, sort_lbl, mt, f"{sort_lbl} by City", top_n, CH),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})
    with r1c:
        if state_col:
            agg = df.groupby(state_col)["_TotalAAL"].sum().reset_index()
            top6 = agg.nlargest(6,"_TotalAAL")
            rest = agg["_TotalAAL"].sum() - top6["_TotalAAL"].sum()
            if rest > 0:
                top6 = pd.concat([top6, pd.DataFrame({state_col:["Other"],"_TotalAAL":[rest]})])
            st.plotly_chart(donut(top6[state_col].astype(str), top6["_TotalAAL"], mt, "AAL Share by Province", CH),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})

    # Row 2 — Trends & peril breakdown
    tile_label("Trends & Peril Breakdown")
    r2a, r2b = st.columns([1, 1.3])
    with r2a:
        if "_quarter" in df.columns and df["_quarter"].nunique() > 1:
            qdf = df.groupby("_quarter")["_TotalAAL"].sum().reset_index().sort_values("_quarter")
            st.plotly_chart(line_fig(qdf, "_quarter", "_TotalAAL", mt, "AAL Trend by Quarter", CH),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})
        elif city_col:
            agg = df.groupby(city_col)["_TIV"].sum().reset_index().nlargest(top_n,"_TIV")
            agg.columns = [city_col,"Total TIV"]
            st.plotly_chart(v_bar(agg, city_col, "Total TIV", mt, "TIV by City", top_n, CH),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})
    with r2b:
        if city_col and len(avail) > 1:
            cp = df.groupby(city_col)[[f"_p_{k}" for k in avail]].sum()
            cp.columns = [PERIL_NAMES.get(k,k) for k in avail]
            cp["_t"] = cp.sum(axis=1)
            cp = cp.nlargest(top_n,"_t").drop(columns="_t").reset_index()
            melted = cp.melt(id_vars=city_col, var_name="Peril", value_name="AAL")
            st.plotly_chart(stacked_bar(melted, city_col, "AAL", "Peril", mt, "All Perils by City (Stacked)", CH),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})

    # Row 3 — Account analysis
    if acct_col:
        tile_label("Account Analysis")
        top_acct = acct_agg.nlargest(top_n,"_TotalAAL")
        r3a, r3b, r3c = st.columns(3)
        with r3a:
            st.plotly_chart(h_bar(top_acct, acct_col, "_TotalAAL", mt, "Top Accounts — Total AAL", top_n, CH),
                            use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})
        with r3b:
            lr_df = acct_agg.nlargest(top_n,"LossRatio").sort_values("LossRatio", ascending=True)
            lr_labels = clean_labels(lr_df[acct_col]).tolist()
            lr_vals = pd.to_numeric(lr_df["LossRatio"], errors="coerce").fillna(0).tolist()
            lr_max = max(lr_vals) if lr_vals else 0
            lr_avg = float(np.mean(lr_vals)) if lr_vals else 0
            fig = go.Figure(go.Bar(
                y=lr_labels, x=lr_vals, orientation="h",
                marker=dict(color=lr_vals,
                            colorscale=[[0,mt["accent_lt"]],[0.5,mt["accent"]],[1,"#E76F51"]],
                            line=dict(width=0)),
                text=[f"{v:.2f}%" for v in lr_vals],
                textposition="outside", textfont=dict(size=10, color=MUTED),
                hovertemplate="<b>%{y}</b><br>Loss Ratio: %{x:.3f}%<extra></extra>",
                cliponaxis=False,
            ))
            fig.update_layout(
                yaxis=dict(type="category", categoryorder="array", categoryarray=lr_labels),
                # Clearly labelled value axis (0 → max) with a % suffix
                xaxis=dict(showticklabels=True, ticksuffix="%", rangemode="tozero",
                           range=[0, lr_max * 1.25 if lr_max else 1],
                           tickfont=dict(size=9, color=LABEL_GRAY)),
            )
            # Reference line at the portfolio average loss ratio (benchmark)
            if lr_avg > 0:
                fig.add_vline(x=lr_avg, line=dict(color="#E76F51", width=1.4, dash="dash"),
                              annotation_text=f"avg {lr_avg:.2f}%",
                              annotation_position="top",
                              annotation_font=dict(size=9, color="#E76F51"))
            fig = tf(fig, mt, "Loss Ratio by Account", CH)
            fig.update_layout(margin=dict(l=14, r=24, t=48, b=44))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})
        with r3c:
            sdf = acct_agg.nlargest(min(30,len(acct_agg)),"_TotalAAL").copy()
            sdf["_sz"] = sdf["_TIV"].clip(lower=1)
            fig = px.scatter(sdf, x="_TIV", y="_TotalAAL", size="_sz", color="LossRatio",
                             hover_name=acct_col,
                             color_continuous_scale=[[0,mt["accent_lt"]],[1,mt["accent"]]],
                             size_max=24, labels={"_TIV":"TIV","_TotalAAL":"AAL","LossRatio":"Loss %"})
            fig.update_traces(marker=dict(line=dict(width=1.2,color=BORDER)),
                              hovertemplate="<b>%{hovertext}</b><br>TIV: $%{x:,.0f}<br>AAL: $%{y:,.0f}<extra></extra>")
            fig.update_layout(xaxis=dict(showticklabels=True))
            fig = tf(fig, mt, "TIV vs AAL — Risk Profile", CH)
            # Room on the right for the Loss% colour bar so it never clips
            fig.update_layout(margin=dict(l=14, r=72, t=48, b=44),
                              coloraxis_colorbar=dict(thickness=10, len=0.8, x=1.02,
                                                      tickfont=dict(size=9), title_font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})

        # Row 4 — Peril drivers
        if avail:
            tile_label("Peril Drivers by Account")
            pcols = st.columns(len(avail))
            for idx,(pk,_) in enumerate(avail.items()):
                rate_col = f"_rate_{pk}"
                n8 = acct_agg.nlargest(min(8,len(acct_agg)), rate_col)
                with pcols[idx]:
                    fig = peril_mini_bar(
                        n8[acct_col].tolist(),
                        n8[rate_col].tolist(),
                        PERIL_COLORS[idx % len(PERIL_COLORS)],
                        PERIL_NAMES.get(pk,pk), height=CH-40,
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})

# ── App entry ─────────────────────────────────────────────────────────────────
def main():
    for k,v in [("active_model","RMS"),("compare_mode",False),("file_data",None),("selected_model","RMS")]:
        if k not in st.session_state:
            st.session_state[k] = v

    mt = MODEL_THEMES[st.session_state.active_model]
    inject_css(mt)

    has_file = st.session_state.file_data is not None
    am = st.session_state.active_model
    cm = st.session_state.compare_mode

    # ── STICKY HEADER BAR ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="pro-header">
      <div class="ph-left">
        <span style="font-size:20px;line-height:1">🛡️</span>
        <div>
          <div class="ph-title">Risk Analytics Dashboard</div>
        </div>
      </div>
      <div class="ph-right">
        <span class="ph-gear" title="Settings">⚙</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


    # ── Upload screen ──────────────────────────────────────────────────────────
    if not has_file:
        _, mid, _ = st.columns([1, 1.6, 1])
        with mid:
            st.markdown(f"""
            <div style="text-align:center;margin-top:54px;margin-bottom:28px;
                        animation:fadeUp 0.6s cubic-bezier(0.22,1,0.36,1) both">
                <div style="width:76px;height:76px;margin:0 auto 22px auto;border-radius:20px;
                            background:{mt['gradient']};display:flex;align-items:center;justify-content:center;
                            box-shadow:0 14px 36px {mt['soft_glow']};position:relative">
                    <div style="position:absolute;inset:-6px;border-radius:24px;
                                border:1.5px solid {mt['accent']}33"></div>
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
                      <path d="M12 16V4M12 4L7 9M12 4l5 5" stroke="white" stroke-width="2"
                            stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" stroke="white"
                            stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.7rem;font-weight:700;
                            color:{TEXT};margin-bottom:10px;letter-spacing:-0.6px">
                    Upload Exposure Data
                </div>
                <div style="font-size:0.9rem;color:{MUTED};line-height:1.7">
                    Excel file with sheets named
                    <span style="color:{mt['accent_dk']};font-weight:700;background:{mt['accent_lt']};
                                 padding:3px 10px;border-radius:5px;margin:0 3px;
                                 border:1px solid {mt['accent']}44">RMS</span>
                    and
                    <span style="color:#1B4332;font-weight:700;background:#E8F5EE;
                                 padding:3px 10px;border-radius:5px;margin:0 3px;
                                 border:1px solid #4E8B6F44">AIR</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            uploaded = st.file_uploader("Upload exposure workbook (.xlsx / .xls)", type=["xlsx","xls"],
                                        label_visibility="collapsed", key="uploader_main")
            if uploaded:
                st.session_state.file_data = uploaded.read()
                st.session_state.file_name = uploaded.name
                st.rerun()
        return

    # ── Load data ──────────────────────────────────────────────────────────────
    buf = io.BytesIO(st.session_state.file_data)
    try:
        xl = pd.ExcelFile(buf)
        sheets = {s.upper().strip(): s for s in xl.sheet_names}
        rms_sheet = sheets.get("RMS")
        air_sheet = sheets.get("AIR")
        if not rms_sheet and not air_sheet:
            found = ", ".join(xl.sheet_names) or "none"
            st.error(
                "**No sheet named `RMS` or `AIR` was found.**\n\n"
                f"Sheets in this file: *{found}*.\n\n"
                "Rename your data sheet(s) to `RMS` and/or `AIR`, then re-upload using **↻ Restart**."
            )
            return
    except Exception as e:
        st.error(
            f"**Could not open this file.**\n\n`{e}`\n\n"
            "Make sure it is a valid `.xlsx` / `.xls` workbook and try again."
        )
        return

    df_rms = df_air = None
    cols_rms = cols_air = {}
    avail_rms = avail_air = {}

    with st.spinner("Reading exposure data…"):
        if rms_sheet:
            buf.seek(0)
            df_rms = pd.read_excel(buf, sheet_name=rms_sheet)
            df_rms.columns = [str(c).strip() for c in df_rms.columns]
            cols_rms = detect_cols(df_rms)
            df_rms, avail_rms = prepare(df_rms, cols_rms)

        if air_sheet:
            buf.seek(0)
            df_air = pd.read_excel(buf, sheet_name=air_sheet)
            df_air.columns = [str(c).strip() for c in df_air.columns]
            cols_air = detect_cols(df_air)
            df_air, avail_air = prepare(df_air, cols_air)

    # Guard: a sheet loaded but no usable AAL/TIV columns were detected
    def _empty(df):
        return df is not None and df["_TotalAAL"].sum() == 0 and df["_TIV"].sum() == 0
    if _empty(df_rms) and _empty(df_air):
        st.warning(
            "**The data loaded, but no AAL or TIV columns could be detected.**\n\n"
            "Expected column names like `WS AAL`, `FL AAL`, `Total AAL`, `WS Trv`, `FL Trv`. "
            "Check your headers and re-upload using **↻ Restart**."
        )
        return

    model_names = (["RMS"] if df_rms is not None else []) + (["AIR"] if df_air is not None else [])

    # ── Model selector (segmented pill control) ─────────────────────────────────
    COMPARE_LBL = "Compare RMS vs AIR"
    opts = list(model_names)
    if len(model_names) >= 2:
        opts.append(COMPARE_LBL)

    current = COMPARE_LBL if cm else am
    idx = opts.index(current) if current in opts else 0

    st.markdown("<div class='model-row-label'>Select Model</div>", unsafe_allow_html=True)
    msel, _msp, mrst = st.columns([5, 2, 1])
    with msel:
        choice = st.radio("Select Model", opts, index=idx, horizontal=True,
                          label_visibility="collapsed", key="model_radio")
    with mrst:
        if st.button("↻  Restart", key="btn_restart", use_container_width=True):
            st.session_state.file_data = None
            st.session_state.active_model = "RMS"
            st.session_state.compare_mode = False
            st.session_state.selected_model = "RMS"
            st.session_state.pop("model_radio", None)
            st.rerun()

    # Sync the pill selection back to existing state (logic unchanged)
    new_cm = (choice == COMPARE_LBL)
    new_am = am if new_cm else choice
    if new_cm != cm or new_am != am:
        st.session_state.compare_mode = new_cm
        st.session_state.active_model = new_am
        st.session_state.selected_model = "Compare" if new_cm else new_am
        st.rerun()

    # Active indicator — in Compare mode it shows the dual-model pill; in single
    # model the file name is shown inside the filter control panel (below).
    fname = getattr(st.session_state, "file_name", "Data.xlsx")
    if cm:
        st.markdown(f"""<div class="active-bar">
            <span style="width:9px;height:9px;border-radius:50%;background:{MODEL_THEMES['RMS']['accent']};
                         display:inline-block;box-shadow:0 0 0 3px {MODEL_THEMES['RMS']['accent']}33"></span>
            <span style="width:9px;height:9px;border-radius:50%;background:{MODEL_THEMES['AIR']['accent']};
                         display:inline-block;box-shadow:0 0 0 3px {MODEL_THEMES['AIR']['accent']}33;margin-left:-4px"></span>
            <span style="font-size:0.72rem;font-weight:700;color:{TEXT};letter-spacing:1.2px;text-transform:uppercase;margin-left:4px">Compare Mode</span>
            <span style="color:{BORDER_DK}">|</span>
            <span style="color:{MUTED};font-size:0.76rem;font-weight:500">{fname}</span>
        </div>""", unsafe_allow_html=True)

    # Compare mode
    if cm and df_rms is not None and df_air is not None:
        render_compare(df_rms, cols_rms, avail_rms, df_air, cols_air, avail_air)
        return

    # Single model
    if am == "RMS" and df_rms is not None:
        df, cols, avail = df_rms, cols_rms, avail_rms
    elif am == "AIR" and df_air is not None:
        df, cols, avail = df_air, cols_air, avail_air
    elif df_rms is not None:
        df, cols, avail = df_rms, cols_rms, avail_rms
    else:
        df, cols, avail = df_air, cols_air, avail_air

    mt = MODEL_THEMES[am]

    # ── Filter control panel (carded zone) ──────────────────────────────────────
    with st.container(key="filterpanel"):
        # File indicator sits inside the control panel (not floating above it)
        st.markdown(f"""<div class="panel-file">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="flex-shrink:0">
              <path d="M14 2H6C5 2 4 3 4 4V20C4 21 5 22 6 22H18C19 22 20 21 20 20V8L14 2Z"
                    stroke="{MUTED}" stroke-width="2" fill="none"/>
              <path d="M14 2V8H20" stroke="{MUTED}" stroke-width="2" fill="none"/>
            </svg>
            <span>Filter for:&nbsp;<strong style="color:{TEXT_DK};font-weight:600">{fname}</strong></span>
        </div>""", unsafe_allow_html=True)
        fc1, fc2, fc3, fc4 = st.columns([0.85, 1, 1, 1])
        with fc1:
            top_n = st.number_input("Top N", min_value=1, max_value=50, value=10, step=1, key="topn_num")
        with fc2:
            filter_by = st.selectbox("Sort By", ["Total AAL","TIV","Peril AAL"], key="filter_by")
        with fc3:
            peril_options = list(avail.keys())
            filter_peril = st.selectbox(
                "Peril", peril_options, key="fp",
                format_func=lambda c: f"{c} → {PERIL_NAMES.get(c, c)}",
            ) if peril_options else None
        with fc4:
            q_opts = ["All"] + sorted(df["_quarter"].dropna().unique().tolist()) if "_quarter" in df.columns else ["All"]
            quarter_filter = st.selectbox("Quarter", q_opts, key="qf")

    top_n = int(top_n)
    # Tight spacing between filters and KPI cards
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    render_dashboard(df, cols, avail, mt, top_n, filter_by, filter_peril, quarter_filter)


if __name__ == "__main__":
    main()
