import io
import hashlib
from pathlib import Path
import json
import pandas as pd
import streamlit as st
import plotly.express as px
from detect import detect_issues
from repair import repair_dataset
from validation import quality_report, build_change_log
from contract import CONFIDENCE_THRESHOLD

st.set_page_config(page_title="Integrix | Data Quality Studio", page_icon="✦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Orbitron:wght@500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --bg:#090713; --panel:#151024; --panel2:#1d1530; --purple:#a78bfa; --violet:#8b5cf6; --pink:#f472b6; --hotpink:#ec4899; --cyan:#67e8f9; --muted:#b9aecb; --line:rgba(167,139,250,.25); }
html, body, [class*="css"] {font-family:'Space Grotesk',sans-serif;}
.stApp {background:radial-gradient(ellipse at 12% 0%,rgba(139,92,246,.22),transparent 35%),radial-gradient(ellipse at 88% 14%,rgba(236,72,153,.15),transparent 31%),linear-gradient(135deg,#090713 0%,#100b1d 55%,#0b0a17 100%);color:#f4efff;}
[data-testid="stHeader"] {background:rgba(9,7,19,.84);}
.block-container {padding-top:1.7rem;padding-bottom:3rem;max-width:1480px;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#171027 0%,#0d0a18 100%);border-right:1px solid rgba(167,139,250,.25);}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#c7bbd9;}
[data-testid="stSidebar"] h2 {font-family:'Orbitron',sans-serif;color:var(--pink);letter-spacing:.12em;text-shadow:0 0 15px rgba(244,114,182,.35);}
.hero {position:relative;overflow:hidden;padding:34px 38px;border:1px solid rgba(167,139,250,.48);border-radius:12px;background:linear-gradient(112deg,rgba(24,17,42,.98),rgba(47,24,67,.94) 58%,rgba(48,19,48,.96));color:#fff;margin:4px 0 26px;box-shadow:0 12px 40px rgba(0,0,0,.22),0 0 25px rgba(139,92,246,.12),inset 0 0 35px rgba(244,114,182,.07);}
.hero:after {content:' ';position:absolute;right:-45px;top:-110px;width:320px;height:320px;border:1px solid rgba(244,114,182,.32);transform:rotate(45deg);box-shadow:0 0 35px rgba(167,139,250,.12),inset 0 0 25px rgba(244,114,182,.10);}
.hero h1 {font-family:'Orbitron',sans-serif;font-size:clamp(1.8rem,4vw,2.8rem);line-height:1.18;letter-spacing:.035em;margin:10px 0 12px;color:#fff8ff;text-shadow:0 0 18px rgba(196,181,253,.28);}
.hero p {color:#d5c9e7;margin:0;font-size:1rem;max-width:720px;}
.eyebrow {font-family:'DM Mono',monospace;letter-spacing:.2em;text-transform:uppercase;font-size:.72rem;font-weight:500;color:#f9a8d4;}
.kpi {padding:18px 19px;border:1px solid rgba(167,139,250,.3);border-radius:10px;background:linear-gradient(145deg,rgba(31,23,51,.96),rgba(17,13,29,.96));box-shadow:inset 0 0 18px rgba(167,139,250,.045);min-height:100px;}
.kpi-label {font-family:'DM Mono',monospace;font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:#b9aecb;margin-bottom:8px;}
.kpi-value {font-family:'Orbitron',sans-serif;font-size:1.75rem;font-weight:700;color:#fdf4ff;text-shadow:0 0 12px rgba(244,114,182,.2);}
.small-muted {color:var(--muted);font-size:.84rem;}
h1,h2,h3,h4 {font-family:'Orbitron','Space Grotesk',sans-serif;color:#f5efff;letter-spacing:.025em;}
h2 {font-size:1.12rem!important;}
h3,h4 {font-size:.98rem!important;}
[data-testid='stMarkdownContainer'] h1,[data-testid='stMarkdownContainer'] h2,[data-testid='stMarkdownContainer'] h3 {text-shadow:0 0 14px rgba(167,139,250,.16);}
.stMarkdown, .stText, [data-testid='stMarkdownContainer'] {font-family:'Space Grotesk',sans-serif;}
[data-testid='stWidgetLabel'] p {font-family:'DM Mono',monospace;letter-spacing:.025em;}
p, label, [data-testid="stCaptionContainer"] {color:#c7bbd9;}
hr {border-color:rgba(167,139,250,.2)!important;}
.stTabs [data-baseweb="tab-list"] {gap:7px;background:#120d20;padding:7px;border:1px solid rgba(167,139,250,.22);border-radius:9px;}
.stTabs [data-baseweb="tab"] {border-radius:7px;padding:10px 16px;color:#c7bbd9;font-family:'DM Mono',monospace;font-size:.82rem;}
.stTabs [aria-selected="true"] {background:linear-gradient(100deg,rgba(139,92,246,.27),rgba(236,72,153,.22));color:#fff!important;border:1px solid rgba(244,114,182,.42);box-shadow:0 0 15px rgba(236,72,153,.10);}
.stButton>button,.stDownloadButton>button {border:1px solid rgba(196,181,253,.55);border-radius:8px;background:linear-gradient(105deg,rgba(139,92,246,.30),rgba(236,72,153,.24));color:#fff4ff;font-family:'DM Mono',monospace;font-weight:500;letter-spacing:.025em;transition:all .18s ease;}
.stButton>button:hover,.stDownloadButton>button:hover {border-color:#f9a8d4;color:white;background:linear-gradient(105deg,rgba(139,92,246,.48),rgba(236,72,153,.4));box-shadow:0 0 18px rgba(167,139,250,.2),0 0 18px rgba(244,114,182,.12);transform:translateY(-1px);}
.stButton>button:focus,.stDownloadButton>button:focus {box-shadow:0 0 0 .15rem rgba(244,114,182,.22);}
[data-testid="stFileUploader"] {background:rgba(21,16,36,.78);border:1px dashed rgba(244,114,182,.48);border-radius:10px;padding:12px;}
[data-testid="stFileUploader"] section {background:transparent;}
[data-testid="stMetric"] {background:linear-gradient(145deg,#1b1430,#120d20);border:1px solid rgba(167,139,250,.26);border-radius:10px;padding:14px;}
[data-testid="stMetricLabel"] {color:#c7bbd9;}
[data-testid="stMetricValue"] {color:#fff5ff;font-family:'Orbitron',sans-serif;}
[data-testid="stDataFrame"], [data-testid="stTable"] {border:1px solid rgba(167,139,250,.22);border-radius:9px;overflow:hidden;}
[data-testid="stExpander"] {border:1px solid rgba(167,139,250,.28);border-radius:9px;background:rgba(21,16,36,.68);}
[data-testid="stAlert"] {background:rgba(29,21,48,.9);border:1px solid rgba(167,139,250,.24);color:#f4efff;}
.stSelectbox div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div {background:#1b1430;border-color:rgba(167,139,250,.32);}
code {font-family:'DM Mono',monospace;color:#f9a8d4;background:rgba(244,114,182,.09);}
::selection {background:rgba(236,72,153,.35);color:white;}
@media(max-width:700px){.hero{padding:25px 22px}.hero:after{opacity:.25}.hero h1{font-size:1.65rem}.block-container{padding-left:1rem;padding-right:1rem}}
</style>
""", unsafe_allow_html=True)

if "original_df" not in st.session_state:
    st.session_state.original_df = None
    st.session_state.cleaned_df = None
    st.session_state.issues = None
    st.session_state.change_log = None
    st.session_state.reviewed = set()
    st.session_state.filename = None
    st.session_state.upload_hash = None
    st.session_state.review = []

with st.sidebar:
    st.markdown("## ✦ INTEGRIX")
    st.caption("◈ NEON DATA INTELLIGENCE")
    st.divider()
    st.markdown("**Workspace**")
    st.markdown("`SYSTEM ONLINE`  ·  Local data session")
    st.divider()
    st.markdown("**Repair policy**")
    st.metric("Auto-fix threshold", f"{CONFIDENCE_THRESHOLD:.0%}")
    st.caption("Lower-confidence suggestions are held for human review.")
    if st.button("Reset workspace", use_container_width=True):
        for key in ["original_df","cleaned_df","issues","change_log","filename","upload_hash"]:
            st.session_state[key] = None
        st.session_state.reviewed = set()
        st.session_state.review = []
        st.rerun()
    st.divider()
    st.caption("INTEGRIX // EXPLAINABLE DATA REPAIR")
    st.divider()
    st.markdown("**Groq AI connection**")
    if st.button("Test Groq connection", use_container_width=True, key="test_groq_connection"):
        try:
            from groq_client import ask_groq
            with st.spinner("Checking Groq API connection..."):
                test_reply = ask_groq("Reply with exactly: Integrix AI connection successful.")
            st.success("Groq is connected.")
            st.caption(test_reply[:180])
        except Exception as exc:
            st.error(f"Groq connection failed: {exc}")

st.markdown("""
<div class="hero">
  <div class="eyebrow">◈ AUTONOMOUS DATA QUALITY // REPAIR ENGINE</div>
  <h1>Make messy data<br>mission-ready.</h1>
  <p>Scan the noise. Patch the anomalies. Keep every operation explainable.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="about-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:13px;margin:0 0 25px;">
  <div style="padding:18px;border:1px solid rgba(167,139,250,.32);border-radius:11px;background:linear-gradient(145deg,rgba(139,92,246,.13),rgba(21,16,36,.88));">
    <div style="font-family:'DM Mono',monospace;color:#c4b5fd;font-size:.72rem;letter-spacing:.13em;">01 / DETECT</div>
    <div style="font-family:'Orbitron',sans-serif;color:#f5efff;font-size:.94rem;margin:9px 0;">Find hidden issues</div>
    <div style="color:#c7bbd9;font-size:.88rem;">Identify missing values, duplicates, invalid emails and phones, inconsistent labels, date formats and numeric anomalies.</div>
  </div>
  <div style="padding:18px;border:1px solid rgba(244,114,182,.30);border-radius:11px;background:linear-gradient(145deg,rgba(236,72,153,.11),rgba(21,16,36,.88));">
    <div style="font-family:'DM Mono',monospace;color:#f9a8d4;font-size:.72rem;letter-spacing:.13em;">02 / REPAIR</div>
    <div style="font-family:'Orbitron',sans-serif;color:#f5efff;font-size:.94rem;margin:9px 0;">Clean with control</div>
    <div style="color:#c7bbd9;font-size:.88rem;">Apply safer automatic fixes while keeping uncertain changes in a human review queue.</div>
  </div>
  <div style="padding:18px;border:1px solid rgba(103,232,249,.25);border-radius:11px;background:linear-gradient(145deg,rgba(103,232,249,.08),rgba(21,16,36,.88));">
    <div style="font-family:'DM Mono',monospace;color:#67e8f9;font-size:.72rem;letter-spacing:.13em;">03 / TRUST</div>
    <div style="font-family:'Orbitron',sans-serif;color:#f5efff;font-size:.94rem;margin:9px 0;">Understand every change</div>
    <div style="color:#c7bbd9;font-size:.88rem;">Compare quality before and after, inspect the audit trail, export cleaned data and ask Groq AI to explain results.</div>
  </div>
</div>
""", unsafe_allow_html=True)
st.caption("WHY INTEGRIX?  A data-quality workspace that helps teams turn inconsistent spreadsheets into more reliable, reviewable datasets — without hiding what changed.")

left, right = st.columns([1.45, 1])
with left:
    st.subheader("Bring your dataset")
    st.write("Upload a CSV or Excel file to run a quality scan. Your data stays in this app session.")
    uploaded = st.file_uploader("Choose a dataset", type=["csv", "xlsx", "xls"], label_visibility="collapsed")
with right:
    st.subheader("What Integrix checks")
    st.markdown("**Completeness** · Missing values  \n**Uniqueness** · Duplicate records  \n**Validity** · Email and phone formats  \n**Consistency** · Labels and date formats  \n**Anomaly** · Numeric outliers")

if uploaded is not None:
    try:
        raw = uploaded.getvalue()
        upload_hash = hashlib.sha256(raw).hexdigest()
        if upload_hash != st.session_state.upload_hash:
            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(io.BytesIO(raw))
            else:
                df = pd.read_excel(io.BytesIO(raw))
            if df.empty or len(df.columns) == 0:
                st.error("The uploaded file has no usable rows or columns.")
            else:
                st.session_state.original_df = df.copy()
                st.session_state.filename = uploaded.name
                st.session_state.upload_hash = upload_hash
                st.session_state.cleaned_df = None
                st.session_state.issues = None
                st.session_state.change_log = None
                st.session_state.reviewed = set()
                st.session_state.review = []
    except Exception as exc:
        st.error(f"Could not read this file: {exc}")

if st.session_state.original_df is None:
    st.info("Upload a file above, or try the included sample dataset: `sample_data/messy_customers.csv`.")
    sample_path = Path(__file__).parent / "sample_data" / "messy_customers.csv"
    if st.button("Load sample dataset", type="primary"):
        st.session_state.original_df = pd.read_csv(sample_path)
        st.session_state.filename = sample_path.name
        st.rerun()
    st.stop()

original = st.session_state.original_df
st.divider()
st.subheader(f"Dataset preview · {st.session_state.filename}")
m1,m2,m3,m4 = st.columns(4)
for col, label, value in zip([m1,m2,m3,m4], ["Rows","Columns","Missing cells","Duplicate rows"],
                             [len(original),len(original.columns),int(original.isna().sum().sum()),int(original.duplicated().sum())]):
    with col:
        st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value:,}</div></div>', unsafe_allow_html=True)
with st.expander("Preview uploaded data", expanded=True):
    st.dataframe(original.head(12), width="stretch", height=260)

scan_col, note_col = st.columns([1,2])
with scan_col:
    run_scan = st.button("✦  Run quality scan", type="primary", use_container_width=True)
with note_col:
    st.caption("Detection and safe repairs run locally. Groq AI is an optional explanation assistant.")

if run_scan:
    with st.spinner("Profiling columns and detecting quality issues..."):
        issues = detect_issues(original)
        cleaned, log, review = repair_dataset(original, issues)
        st.session_state.issues = issues
        st.session_state.cleaned_df = cleaned
        st.session_state.change_log = log
        st.session_state.review = review

if st.session_state.issues is None:
    st.stop()

issues = st.session_state.issues
cleaned = st.session_state.cleaned_df
log = st.session_state.change_log
review = st.session_state.review
before = quality_report(original)
after = quality_report(cleaned)

tabs = st.tabs(["Overview","Issue explorer","Review queue","Audit trail & export"])
with tabs[0]:
    st.subheader("Quality overview")
    a,b,c,d = st.columns(4)
    a.metric("Before quality", f"{before['score']:.1f}/100")
    b.metric("After quality", f"{after['score']:.1f}/100", delta=f"{after['score']-before['score']:+.1f}")
    c.metric("Issues detected", len(issues))
    d.metric("Auto-repaired", len(log))
    st.markdown("**Groq AI assistant**")
    st.caption("AI receives only issue counts and categories—not your uploaded rows or personal data.")
    if st.button("Explain these results with Groq AI", key="groq_explain"):
        try:
            from groq_client import ask_groq
            counts = pd.DataFrame(issues).groupby("issue_type").size().to_dict() if issues else {}
            prompt = (
                "Explain this data-quality scan in simple language. Give: (1) top issues, "
                "(2) what was automatically repaired, (3) what needs human review, "
                "(4) safe next steps. Do not invent any values.\n"
                + json.dumps({"issue_counts": counts, "auto_repaired": len(log),
                              "review_required": len(review), "quality_before": before,
                              "quality_after": after}, default=str)
            )
            with st.spinner("Asking Groq AI..."):
                st.session_state.groq_explanation = ask_groq(prompt)
        except Exception as exc:
            st.error(f"Groq AI is unavailable: {exc}")
    if st.session_state.get("groq_explanation"):
        st.markdown(st.session_state.groq_explanation)
    if len(issues):
        chart = pd.DataFrame(issues).groupby("issue_type").size().reset_index(name="count")
        fig = px.bar(chart, x="issue_type", y="count", color="issue_type",
                     labels={"issue_type":"Issue category","count":"Occurrences"},
                     title="Detected issues by category", template="plotly_dark")
        fig.update_layout(showlegend=False, margin=dict(l=10,r=10,t=45,b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5f1"), title_font=dict(color="#eafcff"))
        st.plotly_chart(fig, width="stretch")
    else:
        st.success("No supported data-quality issues were detected.")
    st.markdown("**Quality dimensions**")
    dims = pd.DataFrame({"Dimension":["Completeness","Uniqueness","Validity"],"Before":[before["completeness"],before["uniqueness"],before["validity"]],"After":[after["completeness"],after["uniqueness"],after["validity"]]})
    st.dataframe(dims.style.format({"Before":"{:.1f}%","After":"{:.1f}%"}), width="stretch", hide_index=True)
    st.caption("Quality score is a transparent heuristic based on completeness, uniqueness and detected validity issues; it is not a certified industry standard.")

with tabs[1]:
    st.subheader("Issue explorer")
    if issues:
        issue_df = pd.DataFrame(issues)
        chosen = st.multiselect("Filter issue types", sorted(issue_df.issue_type.unique()), default=sorted(issue_df.issue_type.unique()))
        filtered = issue_df[issue_df.issue_type.isin(chosen)]
        st.dataframe(filtered, width="stretch", hide_index=True)
        st.caption("Confidence is the engine's estimated certainty that the suggested action is safe—not a guarantee.")
    else:
        st.success("Everything looks clean in the supported checks.")

with tabs[2]:
    st.subheader("Human-in-the-loop review")
    st.write("Low-confidence or ambiguous suggestions are never silently applied.")
    if review:
        review_df = pd.DataFrame(review)
        st.dataframe(review_df, width="stretch", hide_index=True)
        st.info(f"{len(review)} item(s) need review. This starter flags them rather than guessing.")
    else:
        st.success("No uncertain repairs are waiting for review.")
    st.markdown("**Repair policy:** confidence ≥ 0.80 can be auto-applied; below 0.80 is review-only.")

with tabs[3]:
    st.subheader("Change log")
    if log:
        st.dataframe(pd.DataFrame(log), width="stretch", hide_index=True)
    else:
        st.write("No changes were applied.")
    st.divider()
    st.subheader("Before / after")
    x,y = st.columns(2)
    with x:
        st.markdown("**Original dataset**")
        st.dataframe(original.head(10), width="stretch")
    with y:
        st.markdown("**Repaired dataset**")
        st.dataframe(cleaned.head(10), width="stretch")
    st.divider()
    csv_bytes = cleaned.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download cleaned dataset", csv_bytes, file_name="integrix_cleaned.csv", mime="text/csv", type="primary")
    report = {"source_file":st.session_state.filename,"before":before,"after":after,"issues_detected":len(issues),"auto_repairs":len(log),"review_required":len(review),"issue_summary":pd.DataFrame(issues).groupby("issue_type").size().to_dict() if issues else {}}
    st.download_button("Download quality report (JSON)", json.dumps(report, indent=2, default=str), file_name="integrix_quality_report.json", mime="application/json")
    st.download_button("Download change log (CSV)", pd.DataFrame(log).to_csv(index=False).encode("utf-8"), file_name="integrix_change_log.csv", mime="text/csv")
