import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="HeartCare AI", page_icon="🫀", layout="wide", initial_sidebar_state="expanded")

# ============================================================================
# THEME — purple / pink gradient, glassmorphism
# ============================================================================
THEMES = {
    "light": {
        "bg": "linear-gradient(135deg, #F7F5F2 0%, #FAF8F6 55%, #F7F5F2 100%)",
        "text": "#241B3D", "muted": "#8B85A0",
        "glass": "rgba(255,255,255,0.94)", "glass_border": "rgba(36,27,61,0.08)",
        "shadow": "0 8px 24px rgba(36,27,61,0.08)",
    },
    "dark": {
        "bg": "linear-gradient(135deg, #1E1033 0%, #271642 55%, #1E1033 100%)",
        "text": "#F3E8FF", "muted": "#B4A6D1",
        "glass": "rgba(39,22,66,0.75)", "glass_border": "rgba(124,92,252,0.20)",
        "shadow": "0 8px 30px rgba(0,0,0,0.45)",
    },
}
PRIMARY, SECONDARY = "#7C5CFC", "#EC4899"
GRAD = f"linear-gradient(135deg, {PRIMARY} 0%, {SECONDARY} 100%)"
SUCCESS, SUCCESS_PALE, SUCCESS_DARK = "#22C55E", "#DCFCE7", "#166534"
WARNING, WARNING_PALE, WARNING_DARK = "#F59E0B", "#FEF3C7", "#92400E"
DANGER, DANGER_PALE, DANGER_DARK = "#EF4444", "#FEE2E2", "#991B1B"

# Initialize session state
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
    st.session_state.last_form = None
if "sidebar_initialized" not in st.session_state:
    st.session_state.sidebar_initialized = False

# Apply any pending page navigation (e.g. from the "Start Prediction" button)
# BEFORE the sidebar radio widget below is instantiated -- this is required
# because Streamlit forbids changing a widget's own key after it has already
# been created earlier in the same run.
if "pending_nav" in st.session_state:
    st.session_state.sidebar_navigation = st.session_state.pending_nav
    st.session_state.page = st.session_state.pending_nav
    del st.session_state.pending_nav

T = THEMES[st.session_state.theme]

# ============================================================================
# SIDEBAR CSS - Premium Healthcare Style
# ============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

/* Main app background */
h1,h2,h3,h4 {{ font-family: 'Poppins', sans-serif !important; color: {T['text']} !important; }}
.stApp {{ background: {T['bg']}; }}

/* ===== SIDEBAR - Premium Purple/Pink Gradient ===== */
section[data-testid="stSidebar"] {{
    background: linear-gradient(
        180deg,
        #1E1033 0%,
        #140A22 100%
    ) !important;
    color: white !important;
    padding-top: 20px !important;
}}

/* Sidebar text always white */
section[data-testid="stSidebar"] * {{
    color: white !important;
}}

/* Sidebar navigation radio buttons */
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    background: rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    margin: 4px 0 !important;
    transition: all 0.3s ease !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    cursor: pointer !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    background: rgba(236, 72, 153, 0.25) !important;
    transform: translateX(4px) !important;
    border-color: rgba(236, 72, 153, 0.3) !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label[data-selected="true"] {{
    background: rgba(236, 72, 153, 0.3) !important;
    border: 1px solid rgba(236, 72, 153, 0.5) !important;
}}

/* Sidebar toggle (dark mode) */
section[data-testid="stSidebar"] .stCheckbox label span {{
    color: white !important;
}}

section[data-testid="stSidebar"] .stCheckbox div[data-testid="stMarkdownContainer"] p {{
    color: white !important;
}}

/* Sidebar footer */
.sidebar-footer {{
    margin-top: 30px !important;
    padding-top: 20px !important;
    border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
    text-align: center !important;
}}

.sidebar-footer .footer-title {{
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    color: white !important;
    margin-bottom: 4px !important;
}}

.sidebar-footer .footer-sub {{
    font-size: 11px !important;
    color: rgba(255, 255, 255, 0.7) !important;
    line-height: 1.4 !important;
}}

/* Logo/title in sidebar */
.sidebar-logo {{
    text-align: center !important;
    padding: 10px 0 20px 0 !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
    margin-bottom: 20px !important;
}}

.sidebar-logo .logo-icon {{
    font-size: 42px !important;
    display: block !important;
    margin-bottom: 6px !important;
}}

.sidebar-logo .logo-text {{
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
    font-size: 22px !important;
    background: linear-gradient(135deg, #ffffff 0%, #f0abfc 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}}

.sidebar-logo .logo-sub {{
    font-size: 11px !important;
    color: rgba(255, 255, 255, 0.6) !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}}

/* Mobile hamburger menu */
button[kind="header"] {{
    background: transparent !important;
    color: {T['text']} !important;
}}

/* Ensure sidebar stays visible on mobile */
@media (max-width: 768px) {{
    section[data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg,
            #1E1033 0%,
            #140A22 100%
        ) !important;
        color: white !important;
    }}
    
    section[data-testid="stSidebar"] * {{
        color: white !important;
    }}
    
    /* Keep hamburger visible */
    button[kind="header"] {{
        display: flex !important;
        opacity: 1 !important;
        color: {T['text']} !important;
    }}
}}

/* ===== GLASS CARDS (main content) ===== */
.glass {{
    background: {T['glass']}; backdrop-filter: blur(14px); border-radius: 20px;
    border: 1px solid {T['glass_border']}; box-shadow: {T['shadow']};
    padding: 22px 24px; margin-bottom: 18px; color: {T['text']};
}}
.hero {{
    background: {GRAD}; border-radius: 24px; padding: 46px 40px; color: white;
    box-shadow: 0 15px 40px rgba(124,92,252,0.35); margin-bottom: 24px;
}}
.badge {{
    display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.25);
    padding: 6px 14px; border-radius: 999px; font-size: 12.5px; font-weight: 600; color: white; margin-bottom: 14px;
}}
.metric-mini {{
    background: {T['glass']}; border-radius: 14px; padding: 14px 16px; text-align: center;
    border: 1px solid {T['glass_border']}; box-shadow: {T['shadow']};
}}
.metric-mini .val {{ font-size: 20px; font-weight: 700; color: {PRIMARY}; }}
.metric-mini .lbl {{ font-size: 11.5px; color: {T['muted']}; }}
.tip-card {{
    background: {T['glass']}; border-left: 4px solid {PRIMARY}; border-radius: 12px;
    padding: 12px 16px; margin-bottom: 10px; font-size: 13.5px; color: {T['text']};
}}
.section-title {{ font-family:'Poppins',sans-serif; font-weight:700; font-size:16px; color:{T['text']}; margin:6px 0 12px; }}
div.stButton>button, div.stFormSubmitButton>button {{
    background: {GRAD} !important; color: white !important; border: none !important;
    border-radius: 12px !important; font-weight: 600 !important; padding: 0.65em 1.4em !important;
    box-shadow: 0 6px 18px rgba(124,92,252,0.3) !important; transition: transform .12s ease;
}}
div.stButton>button:hover {{ transform: translateY(-2px); }}
.disclaimer {{ background: {T['glass']}; border: 1px dashed {T['muted']}; border-radius: 12px; padding: 14px 16px; font-size: 12px; color: {T['muted']}; }}

/* ===== Expander (Heart Health FAQ) — force readable text per theme ===== */
div[data-testid="stExpander"] {{
    background: {T['glass']} !important;
    border-radius: 14px !important;
    border: 1px solid {T['glass_border']} !important;
}}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p {{
    color: {T['text']} !important;
}}
div[data-testid="stExpander"] svg {{
    fill: {T['text']} !important;
}}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Load real trained artifacts
# ============================================================================
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

@st.cache_resource
def load_artifacts():
    model = joblib.load(MODELS_DIR / "best_model.pkl")
    scaler = joblib.load(MODELS_DIR / "scaler.pkl")
    feature_columns = joblib.load(MODELS_DIR / "feature_columns.pkl")
    return model, scaler, feature_columns

try:
    MODEL, SCALER, FEATURE_COLUMNS = load_artifacts()
    MODEL_NAME = type(MODEL).__name__
except FileNotFoundError:
    st.error("Model files not found — make sure `models/best_model.pkl`, `scaler.pkl` and `feature_columns.pkl` exist.")
    st.stop()

# Metrics measured on the held-out test set in the training notebook (not recomputed live)
METRICS = {"Accuracy": 0.8478, "Precision": 0.8364, "Recall": 0.9020, "F1 Score": 0.8679, "ROC AUC": 0.9032}
CONF_MATRIX = [[64, 18], [10, 92]]  # [[TN, FP], [FN, TP]]
DATASET_INFO = {"Total patients": 918, "Training set": 734, "Test set": 184, "Features used": 18,
                 "Sources": "Cleveland, Hungary, Switzerland, VA Long Beach"}
POP_MEANS = {"healthy": {"age": 50.6, "trestbps": 130.0, "chol": 227.7, "thalch": 148.3},
             "disease": {"age": 55.9, "trestbps": 133.6, "chol": 177.4, "thalch": 129.1}}

RADAR_GROUPS = {
    "Blood pressure": ["trestbps"], "Cholesterol": ["chol"],
    "Exercise response": ["thalch", "exang", "oldpeak", "slope_flat", "slope_upsloping"],
    "Vessels & thalassemia": ["ca", "thal_normal", "thal_reversable defect"],
    "Age & sex": ["age", "sex_Male"],
    "Symptoms & metabolic": ["fbs", "cp_atypical angina", "cp_non-anginal", "cp_typical angina",
                              "restecg_normal", "restecg_st-t abnormality"],
}

TIER_META = {
    "low": {"label": "Low risk", "c": SUCCESS, "pale": SUCCESS_PALE, "dark": SUCCESS_DARK,
            "headline": "The model estimates a lower likelihood of heart disease."},
    "medium": {"label": "Medium risk", "c": WARNING, "pale": WARNING_PALE, "dark": WARNING_DARK,
               "headline": "The model estimates a moderate likelihood of heart disease."},
    "high": {"label": "High risk", "c": DANGER, "pale": DANGER_PALE, "dark": DANGER_DARK,
             "headline": "The model estimates a higher likelihood of heart disease."},
}


def encode_input(f):
    row = {col: 0 for col in FEATURE_COLUMNS}
    row["age"] = float(f["age"])
    row["trestbps"] = float(f["trestbps"])
    row["chol"] = float(f["chol"])
    row["fbs"] = 1 if f["fbs"] == "Yes" else 0
    row["thalch"] = float(f["thalch"])
    row["exang"] = 1 if f["exang"] == "Yes" else 0
    row["oldpeak"] = float(f["oldpeak"])
    row["ca"] = int(f["ca"])
    if f["sex"] == "Male":
        row["sex_Male"] = 1
    cp = f["cp"]
    if cp == "Atypical angina":
        row["cp_atypical angina"] = 1
    elif cp == "Non-anginal":
        row["cp_non-anginal"] = 1
    elif cp == "Typical angina":
        row["cp_typical angina"] = 1
    restecg = f["restecg"]
    if restecg == "Normal":
        row["restecg_normal"] = 1
    elif restecg == "ST-T wave abnormality":
        row["restecg_st-t abnormality"] = 1
    slope = f["slope"]
    if slope == "Flat":
        row["slope_flat"] = 1
    elif slope == "Upsloping":
        row["slope_upsloping"] = 1
    thal = f["thal"]
    if thal == "Normal":
        row["thal_normal"] = 1
    elif thal == "Reversable defect":
        row["thal_reversable defect"] = 1
    return pd.DataFrame([row])[FEATURE_COLUMNS]


def compute_risk(f):
    row = encode_input(f)
    scaled = SCALER.transform(row)
    proba = MODEL.predict_proba(scaled)[0]
    p_disease = proba[1]
    score = max(1, min(99, round(p_disease * 100)))
    tier = "low" if score < 33 else "medium" if score < 66 else "high"
    confidence = round(max(proba) * 100)

    importances = getattr(MODEL, "feature_importances_", np.ones(len(FEATURE_COLUMNS)) / len(FEATURE_COLUMNS))
    z = scaled[0]
    contrib = {feat: importances[i] * z[i] for i, feat in enumerate(FEATURE_COLUMNS)}
    radar = []
    for label, feats in RADAR_GROUPS.items():
        total = sum(contrib[feat] for feat in feats)
        radar.append({"factor": label, "value": max(0, min(100, round((total + 1.5) / 3 * 100)))})

    return {"score": score, "tier": tier, "confidence": confidence, "radar": radar}


def hex_to_rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def ecg_line_html(color, bpm, glass_bg="rgba(255,255,255,0.9)", muted="#8A8F8C"):
    """A single heartbeat pulse that draws in, then immediately redraws again (loop) —
    gradient stroke + glow for a premium 'amazing' look."""
    beat_unit = "l14,0 l6,-34 l10,54 l8,-70 l8,86 l10,-36 l14,0 l18,0 l6,-34 l10,54 l8,-70 l8,86 l10,-36 l14,0 l18,0 l6,-34 l10,54 l8,-70 l8,86 l10,-36 l14,0 l30,0"
    path_d = "M0,50 " + beat_unit
    width = 300

    return f"""
    <div style="background:{glass_bg}; border-radius:14px; padding:14px 18px; margin-bottom:14px;
                overflow:hidden; position:relative;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <span style="font-size:12px; color:{muted}; font-weight:600; letter-spacing:0.5px;">LIVE READING</span>
        <span style="font-size:20px; font-weight:700; color:{color};">{bpm} <span style="font-size:11px;color:{muted};font-weight:500;">bpm</span></span>
      </div>
      <div style="width:100%; height:70px;">
        <svg width="100%" height="70" viewBox="0 0 {width} 100" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="ecgGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="{PRIMARY}"/>
              <stop offset="100%" stop-color="{color}"/>
            </linearGradient>
            <filter id="ecgGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="blur"/>
              <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <path d="{path_d}" pathLength="1000" fill="none" stroke="url(#ecgGrad)" stroke-width="3"
                stroke-linecap="round" stroke-linejoin="round" filter="url(#ecgGlow)"
                stroke-dasharray="1000" stroke-dashoffset="1000"
                style="animation: ecgPulse 3.4s linear infinite;"/>
        </svg>
      </div>
    </div>
    <style>
      @keyframes ecgPulse {{
        0%   {{ stroke-dashoffset: 1000; }}
        95%  {{ stroke-dashoffset: 0; }}
        100% {{ stroke-dashoffset: 0; }}
      }}
    </style>
    """


def gauge(score, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, number={"suffix": "/100", "font": {"size": 30, "color": T["text"]}},
        gauge={"axis": {"range": [0, 100], "tickwidth": 0}, "bar": {"color": color, "thickness": 0.28},
               "bgcolor": "rgba(0,0,0,0)",
               "steps": [{"range": [0, 33], "color": hex_to_rgba(SUCCESS, 0.25)},
                         {"range": [33, 66], "color": hex_to_rgba(WARNING, 0.25)},
                         {"range": [66, 100], "color": hex_to_rgba(DANGER, 0.25)}]}))
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)",
                       font=dict(color=T["text"]))
    return fig


def radar_chart(radar, color):
    labels = [r["factor"] for r in radar]
    values = [r["value"] for r in radar]
    fig = go.Figure(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], fill="toself",
                                     line=dict(color=color), fillcolor=hex_to_rgba(color, 0.35)))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
                                  bgcolor="rgba(0,0,0,0)"),
                       showlegend=False, height=280, margin=dict(l=40, r=40, t=20, b=20),
                       paper_bgcolor="rgba(0,0,0,0)", font=dict(color=T["text"], size=10))
    return fig


def comparison_chart(form):
    labels = ["Age", "Blood pressure", "Cholesterol", "Max heart rate"]
    you = [float(form["age"]), float(form["trestbps"]), float(form["chol"]), float(form["thalch"])]
    healthy_avg = [POP_MEANS["healthy"]["age"], POP_MEANS["healthy"]["trestbps"],
                   POP_MEANS["healthy"]["chol"], POP_MEANS["healthy"]["thalch"]]
    fig = go.Figure()
    fig.add_bar(name="You", x=labels, y=you, marker_color=PRIMARY)
    fig.add_bar(name="Healthy avg (dataset)", x=labels, y=healthy_avg, marker_color=hex_to_rgba(SECONDARY, 0.55))
    fig.update_layout(barmode="group", height=280, margin=dict(l=20, r=20, t=20, b=20),
                       paper_bgcolor="rgba(0,0,0,0)", font=dict(color=T["text"]),
                       legend=dict(orientation="h", y=1.1))
    return fig


def bmi_status(weight, height):
    if not weight or not height:
        return None, None
    bmi = weight / ((height / 100) ** 2)
    cat = "Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obese"
    return round(bmi, 1), cat


def recommendations(form, tier):
    cards = []
    if tier == "high":
        cards.append(("🏥 Medical follow-up", "See a doctor or cardiologist soon to review these results in detail."))
    if form.get("smoking") == "Yes":
        cards.append(("🚭 Smoking", "Quitting smoking is one of the highest-impact changes for heart health."))
    if form.get("stress") == "High":
        cards.append(("🧘 Stress management", "Try daily breathing exercises, short walks, or mindfulness breaks."))
    cards.append(("🥗 Diet", "Favor vegetables, whole grains and lean protein; cut back on salt and saturated fat."))
    cards.append(("🏃 Exercise", "Aim for 20-30 minutes of moderate activity most days, if medically cleared."))
    cards.append(("😴 Sleep", "Target 7-9 hours of consistent sleep — poor sleep is linked to cardiac risk."))
    return cards


# ============================================================================
# SIDEBAR - Premium Healthcare Style (Fixed for navigation)
# ============================================================================
with st.sidebar:
    # Logo and Title
    st.markdown("""
    <div class="sidebar-logo">
        <span class="logo-icon">🫀</span>
        <div class="logo-text">HeartCare AI</div>
        <div class="logo-sub">Clinical Decision Support</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation with icons - Using session state to prevent re-render issues
    pages = ["Home", "Prediction", "About Model", "Heart Health", "History"]
    page_icons = ["🏠", "🩺", "📖", "❤️", "📜", "📞"]
    
    # Create radio with icons
    selected_page = st.radio(
        "Navigate",
        pages,
        format_func=lambda x: f"{page_icons[pages.index(x)]} {x}",
        label_visibility="collapsed",
        index=pages.index(st.session_state.page),
        key="sidebar_navigation"  # Add key to prevent rerender issues
    )
    
    # Update page if changed
    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.rerun()
    
    st.write("")
    
    # Dark mode toggle with proper state management
    dark_mode = st.toggle("🌙 Dark mode", value=(st.session_state.theme == "dark"), key="theme_toggle")
    new_theme = "dark" if dark_mode else "light"
    
    # Only update if theme changed
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()
    
    st.write("")
    
    # Model info
    st.caption(f"🤖 **{MODEL_NAME}**  •  {METRICS['Accuracy']:.1%} accuracy")
    
    # Footer
    st.markdown("""
    <div class="sidebar-footer">
        <div class="footer-title">HeartCare AI</div>
        <div class="footer-sub">Developed by M IMRAN<br>BS Artificial Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# HOME
# ============================================================================
if st.session_state.page == "Home":
    st.markdown(f"""
    <div class="hero">
        <span class="badge">✨ AI-powered clinical decision support (demo)</span>
        <h1 style="color:white; font-size:38px; margin:8px 0">🫀 Heart Disease Prediction AI</h1>
        <p style="font-size:15.5px; opacity:0.95; max-width:600px">
        AI-powered clinical decision support system that estimates heart disease risk using patient clinical
        parameters — backed by a real Random Forest model trained on 918 patient records.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in zip([c1, c2, c3, c4],
                              [f"{METRICS['Accuracy']:.1%}", f"{METRICS['ROC AUC']:.2f}", "918", "18"],
                              ["Test accuracy", "ROC AUC", "Patients trained on", "Clinical features"]):
        with col:
            st.markdown(f'<div class="metric-mini"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.write("")
    if st.button("🩺 Start Prediction", use_container_width=False):
        st.session_state.pending_nav = "Prediction"
        st.rerun()

    st.write("")
    cc1, cc2, cc3 = st.columns(3)
    for col, icon, title, desc in zip([cc1, cc2, cc3],
        ["📋", "🤖", "📊"],
        ["Enter patient data", "Real trained model", "Visual risk report"],
        ["Clinical values, ECG results and lifestyle factors.",
         "Random Forest trained on the UCI multi-site dataset.",
         "Gauge, radar breakdown, and comparison charts."]):
        with col:
            st.markdown(f'<div class="glass"><h4>{icon} {title}</h4><p style="color:{T["muted"]};font-size:13px">{desc}</p></div>', unsafe_allow_html=True)

# ============================================================================
# PREDICTION
# ============================================================================
elif st.session_state.page == "Prediction":
    st.markdown(f"<h2>🩺 Patient Risk Assessment</h2>", unsafe_allow_html=True)

    st.markdown('<div class="glass"><div class="section-title">👤 Patient Information</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    age = p1.number_input("Age", 1, 120, 50)
    sex = p2.selectbox("Sex", ["Male", "Female"])
    weight = p3.number_input("Weight (kg, optional)", 0, 250, 0)
    height = p1.number_input("Height (cm, optional)", 0, 230, 0)
    smoking = p2.selectbox("Smoking", ["No", "Yes"])
    stress = p3.selectbox("Stress level", ["Low", "Moderate", "High"])
    st.markdown('</div>', unsafe_allow_html=True)

    bmi, bmi_cat = bmi_status(weight, height)
    m1, m2, m3 = st.columns(3)
    m1.markdown(f'<div class="metric-mini"><div class="val">{age}</div><div class="lbl">Age</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-mini"><div class="val">{bmi or "—"}</div><div class="lbl">BMI {("("+bmi_cat+")") if bmi_cat else ""}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-mini"><div class="val">{sex}</div><div class="lbl">Sex</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="glass"><div class="section-title">🩸 Clinical Measurements & Lab Values</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    trestbps = c1.number_input("Resting blood pressure (mmHg)", 60, 260, 120)
    chol = c2.number_input("Cholesterol (mg/dL)", 100, 600, 200)
    fbs = c3.selectbox("Fasting blood sugar > 120 mg/dL", ["No", "Yes"])
    st.markdown('</div>', unsafe_allow_html=True)

    bp_status = "Normal" if trestbps < 120 else "Elevated" if trestbps < 140 else "High"
    chol_status = "Normal" if chol < 200 else "Borderline" if chol < 240 else "High"
    m4, m5 = st.columns(2)
    m4.markdown(f'<div class="metric-mini"><div class="val">{bp_status}</div><div class="lbl">Blood pressure status</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="metric-mini"><div class="val">{chol_status}</div><div class="lbl">Cholesterol status</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="glass"><div class="section-title">📈 ECG & Exercise Information</div>', unsafe_allow_html=True)
    e1, e2, e3 = st.columns(3)
    cp = e1.selectbox("Chest pain type", ["Typical angina", "Atypical angina", "Non-anginal", "Asymptomatic"])
    restecg = e2.selectbox("Resting ECG result", ["Normal", "ST-T wave abnormality", "LV hypertrophy"])
    thalch = e3.number_input("Max heart rate achieved (bpm)", 60, 220, 150)
    e4, e5, e6 = st.columns(3)
    exang = e4.selectbox("Exercise-induced angina", ["No", "Yes"])
    oldpeak = e5.number_input("ST depression (oldpeak)", 0.0, 7.0, 0.0, step=0.1)
    slope = e6.selectbox("Slope of peak exercise ST segment", ["Upsloping", "Flat", "Downsloping"])
    e7, e8 = st.columns(2)
    ca = e7.selectbox("Major vessels colored by fluoroscopy", ["0", "1", "2", "3", "4"])
    thal = e8.selectbox("Thalassemia result", ["Normal", "Fixed defect", "Reversable defect"])
    st.markdown('</div>', unsafe_allow_html=True)

    hr_status = "Below typical" if thalch < (220 - age) * 0.7 else "Typical"
    st.markdown(f'<div class="metric-mini" style="max-width:260px"><div class="val">{hr_status}</div><div class="lbl">Heart rate response</div></div>', unsafe_allow_html=True)

    st.write("")
    if st.button("🔮 Predict Heart Disease Risk", use_container_width=True):
        form = {"age": age, "sex": sex, "cp": cp, "trestbps": trestbps, "chol": chol, "fbs": fbs,
                "restecg": restecg, "thalch": thalch, "exang": exang, "oldpeak": oldpeak,
                "slope": slope, "ca": ca, "thal": thal, "weight": weight, "height": height,
                "smoking": smoking, "stress": stress}
        with st.spinner("Running the trained model..."):
            result = compute_risk(form)
        st.session_state.last_result = result
        st.session_state.last_form = form
        st.session_state.history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "age": age, "sex": sex,
            "score": result["score"], "tier": result["tier"].capitalize(),
        })
        st.rerun()

    if st.session_state.last_result:
        result, form = st.session_state.last_result, st.session_state.last_form
        tm = TIER_META[result["tier"]]

        st.markdown(
            ecg_line_html(tm["c"], bpm=int(form["thalch"]), glass_bg=T["glass"], muted=T["muted"]),
            unsafe_allow_html=True
        )

        st.markdown(f"""<div class="glass" style="border-left:6px solid {tm['c']}">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div>
                <div style="font-size:22px;font-weight:700;color:{tm['dark']}">🎯 {tm['label']}</div>
                <div style="color:{T['muted']};font-size:13.5px">{tm['headline']}</div>
              </div>
              <div style="text-align:right">
                <div style="font-size:34px;font-weight:700;color:{tm['dark']}">{result['score']}</div>
                <div style="font-size:11px;color:{T['muted']}">confidence {result['confidence']}%</div>
              </div>
            </div></div>""", unsafe_allow_html=True)

        gc, rc = st.columns(2)
        with gc:
            st.markdown('<div class="glass"><div class="section-title">Risk Gauge</div>', unsafe_allow_html=True)
            st.plotly_chart(gauge(result["score"], tm["c"]), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with rc:
            st.markdown('<div class="glass"><div class="section-title">Feature Contribution (Radar)</div>', unsafe_allow_html=True)
            st.plotly_chart(radar_chart(result["radar"], tm["c"]), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass"><div class="section-title">📊 You vs. Healthy Average (dataset)</div>', unsafe_allow_html=True)
        st.plotly_chart(comparison_chart(form), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">💡 Personalized Recommendations</div>', unsafe_allow_html=True)
        rcols = st.columns(2)
        for i, (title, desc) in enumerate(recommendations(form, result["tier"])):
            with rcols[i % 2]:
                st.markdown(f'<div class="tip-card"><b>{title}</b><br><span style="color:{T["muted"]};font-size:12.5px">{desc}</span></div>', unsafe_allow_html=True)

        dl1, dl2 = st.columns(2)
        report = f"HeartCare AI Report\nDate: {datetime.now()}\nRisk: {tm['label']} ({result['score']}/100)\nConfidence: {result['confidence']}%\n"
        dl1.download_button("⬇️ Download Report (.txt)", report, file_name="heartcare_report.txt", use_container_width=True)
        if dl2.button("🔄 Reset", use_container_width=True):
            st.session_state.last_result = None
            st.session_state.last_form = None
            st.rerun()

# ============================================================================
# ABOUT MODEL
# ============================================================================
elif st.session_state.page == "About Model":
    st.markdown("<h2>📖 About the AI Model</h2>", unsafe_allow_html=True)
    st.markdown(f"""<div class="glass">
        <b>Algorithm:</b> {MODEL_NAME} (200 trees) &nbsp;|&nbsp; <b>Trained on:</b> {DATASET_INFO['Sources']}<br>
        <b>Total patients:</b> {DATASET_INFO['Total patients']} &nbsp;|&nbsp;
        <b>Train/Test split:</b> {DATASET_INFO['Training set']} / {DATASET_INFO['Test set']} &nbsp;|&nbsp;
        <b>Features:</b> {DATASET_INFO['Features used']}
        </div>""", unsafe_allow_html=True)

    mc = st.columns(5)
    for col, (k, v) in zip(mc, METRICS.items()):
        col.markdown(f'<div class="metric-mini"><div class="val">{v:.1%}</div><div class="lbl">{k}</div></div>', unsafe_allow_html=True)

    st.write("")
    cm_fig = go.Figure(data=go.Heatmap(
        z=CONF_MATRIX, x=["Predicted: No Disease", "Predicted: Disease"], y=["Actual: No Disease", "Actual: Disease"],
        colorscale=[[0, "#F7F5F2"], [1, PRIMARY]], text=CONF_MATRIX, texttemplate="%{text}", showscale=False))
    cm_fig.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", font=dict(color=T["text"]))
    st.markdown('<div class="glass"><div class="section-title">Confusion Matrix (held-out test set)</div>', unsafe_allow_html=True)
    st.plotly_chart(cm_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""<div class="disclaimer">These metrics were measured once during training on a held-out
    test split and are not recomputed live. This is a real trained model, but it has not been clinically
    validated and should not be used for actual diagnosis.</div>""", unsafe_allow_html=True)

# ============================================================================
# HEART HEALTH
# ============================================================================
elif st.session_state.page == "Heart Health":
    st.markdown("<h2>❤️ Heart Health Information</h2>", unsafe_allow_html=True)
    faqs = {
        "What is heart disease?": "An umbrella term for conditions affecting the heart, including coronary artery disease, arrhythmias, and heart valve problems.",
        "Common symptoms": "Chest pain or discomfort, shortness of breath, fatigue, irregular heartbeat, dizziness.",
        "Key risk factors": "High blood pressure, high cholesterol, smoking, diabetes, obesity, family history, sedentary lifestyle.",
        "Prevention": "Regular exercise, balanced diet, not smoking, managing stress, routine checkups.",
        "⚠️ Emergency warning signs": "Sudden chest pain/pressure, pain radiating to arm/jaw, severe shortness of breath, cold sweats — seek emergency care immediately.",
    }
    for q, a in faqs.items():
        with st.expander(q):
            st.write(a)

# ============================================================================
# HISTORY
# ============================================================================
elif st.session_state.page == "History":
    st.markdown("<h2>📜 Prediction History (this session)</h2>", unsafe_allow_html=True)
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history)
        st.dataframe(hist_df, use_container_width=True)
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Export CSV", hist_df.to_csv(index=False), file_name="history.csv", use_container_width=True)
        if c2.button("🗑️ Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.info("No predictions yet this session — run one from the Prediction page.")

