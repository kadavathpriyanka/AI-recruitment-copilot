import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
from app import process_resume
from accuracy_check import run_accuracy_check
from auth import signup_user, login_user, get_all_users
from database import init_db, insert_candidate, get_all_candidates, clear_all_candidates, insert_job, get_all_jobs, delete_job, add_to_ats, get_ats_status, submit_feedback, get_feedback, get_satisfaction_score
from jd_extractor import analyze_job_description
from matching_engine import match_all_candidates, calculate_match, skill_gap_analysis
from matching_accuracy_check import get_accuracy_results
from interview_generator import generate_questions, QUESTION_TYPE_LABELS
from interview_simulation import start_interview, get_opening_message, submit_answer, get_current_question, compute_interview_summary, get_progress
from voice_screening import analyze_audio, speak_text, listen_to_candidate, generate_voice_feedback
from parser.pdf_reader import extract_text_from_pdf
from parser.docx_reader import extract_text_from_docx

st.set_page_config(page_title="Recruitment Copilot", layout="wide", page_icon="📄")

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 15% 0%, #fff7ed 0%, #fffaf3 45%, #fef3e2 100%);
}
.block-container {
    padding-top: 2.2rem;
}
h1, h2, h3, h4, h5, p, span, label, div {
    color: #292524;
}
.skill-badge {
    display: inline-block;
    background: rgba(249, 115, 22, 0.1);
    color: #c2410c;
    border: 1px solid rgba(249, 115, 22, 0.25);
    padding: 4px 10px;
    border-radius: 12px;
    margin: 3px 3px 3px 0;
    font-size: 13px;
    font-weight: 500;
}
.type-badge {
    display: inline-block;
    background: rgba(13, 148, 136, 0.1);
    color: #0d9488;
    border: 1px solid rgba(13, 148, 136, 0.25);
    padding: 3px 10px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 8px;
}
.glass-card {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid rgba(249, 115, 22, 0.12);
    box-shadow: 0 4px 20px rgba(249, 115, 22, 0.07);
}
.metric-box {
    background: #ffffff;
    border-radius: 14px;
    padding: 18px 20px;
    text-align: center;
    border: 1px solid rgba(249, 115, 22, 0.12);
    box-shadow: 0 3px 14px rgba(249, 115, 22, 0.07);
    transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
}
.metric-box:hover {
    box-shadow: 0 8px 24px rgba(249, 115, 22, 0.15);
    transform: translateY(-2px);
    border-color: rgba(249, 115, 22, 0.3);
}
.metric-label {
    font-size: 11px;
    color: #78716c;
    margin-bottom: 4px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(135deg, #f97316, #0d9488);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.logo-badge {
    display: inline-block;
    background: linear-gradient(135deg, #f97316, #0d9488);
    color: white;
    font-weight: 800;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 14px;
}
.profile-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 26px;
    border: 1px solid rgba(249, 115, 22, 0.12);
    box-shadow: 0 4px 20px rgba(249, 115, 22, 0.08);
}
.avatar-circle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f97316, #0d9488);
    color: white;
    font-weight: 800;
    font-size: 14px;
    margin-right: 10px;
}
.avatar-circle-lg {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 54px;
    height: 54px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f97316, #0d9488);
    color: white;
    font-weight: 800;
    font-size: 19px;
    margin: 0 auto 10px auto;
}
.page-header {
    background: linear-gradient(120deg, #ffffff 0%, #fef3e2 100%);
    border: 1px solid rgba(249, 115, 22, 0.12);
    border-radius: 18px;
    padding: 22px 28px;
    margin-bottom: 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px rgba(249, 115, 22, 0.08);
}
.page-header-icon {
    font-size: 30px;
    margin-right: 14px;
}
.page-header-title {
    font-size: 24px;
    font-weight: 800;
    color: #1c1917;
    margin: 0;
}
.page-header-subtitle {
    font-size: 13px;
    color: #78716c;
    margin-top: 2px;
}
.role-pill {
    background: linear-gradient(135deg, #f97316, #0d9488);
    color: white;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
.leaderboard-rank {
    font-size: 20px;
    margin-right: 8px;
}
.chat-bubble-ai {
    background: rgba(13, 148, 136, 0.08);
    border: 1px solid rgba(13, 148, 136, 0.2);
    border-radius: 14px 14px 14px 2px;
    padding: 10px 16px;
    margin-bottom: 8px;
    font-size: 14px;
    max-width: 90%;
    color: #292524;
}
.chat-bubble-candidate {
    background: rgba(249, 115, 22, 0.1);
    border: 1px solid rgba(249, 115, 22, 0.22);
    border-radius: 14px 14px 2px 14px;
    padding: 10px 16px;
    margin-bottom: 4px;
    font-size: 14px;
    max-width: 90%;
    margin-left: auto;
    text-align: right;
    color: #292524;
}
.relevance-tag-yes {
    color: #15803d;
    font-size: 12px;
    text-align: right;
    margin-bottom: 14px;
    background: rgba(34, 197, 94, 0.1);
    padding: 6px 10px;
    border-radius: 8px;
    max-width: 90%;
    margin-left: auto;
}
.relevance-tag-no {
    color: #b45309;
    font-size: 12px;
    text-align: right;
    margin-bottom: 14px;
    background: rgba(251, 191, 36, 0.12);
    padding: 6px 10px;
    border-radius: 8px;
    max-width: 90%;
    margin-left: auto;
}
.status-pill-Applied { background:rgba(99,102,241,0.12); color:#4338ca; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:700; border:1px solid rgba(99,102,241,0.25); }
.status-pill-Interview_Scheduled { background:rgba(251,191,36,0.15); color:#92400e; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:700; border:1px solid rgba(251,191,36,0.3); }
.status-pill-Interview_Completed { background:rgba(13,148,136,0.12); color:#0f766e; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:700; border:1px solid rgba(13,148,136,0.25); }
.status-pill-Offer_Extended { background:rgba(34,197,94,0.12); color:#15803d; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:700; border:1px solid rgba(34,197,94,0.25); }
.status-pill-Hired { background:rgba(168,85,247,0.12); color:#7e22ce; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:700; border:1px solid rgba(168,85,247,0.25); }
.status-pill-Rejected { background:rgba(248,113,113,0.12); color:#b91c1c; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:700; border:1px solid rgba(248,113,113,0.25); }

/* Global: every bordered Streamlit container gets the soft card treatment */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px !important;
    border: 1px solid rgba(249, 115, 22, 0.12) !important;
    background: #ffffff !important;
    box-shadow: 0 4px 20px rgba(249, 115, 22, 0.07) !important;
}

/* Login page — kept bold/dark as an accent panel against the light page around it */
.login-hero {
    background: linear-gradient(150deg, #1c1917 0%, #7c2d12 45%, #0d9488 100%);
    border-radius: 24px;
    padding: 46px 40px;
    color: #fff7ed;
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 100%;
    border: 1px solid rgba(0,0,0,0.05);
}
.login-hero-logo {
    background: rgba(255,255,255,0.15);
    color: #fff7ed;
    width: 54px; height: 54px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 19px;
    margin-bottom: 26px;
}
.login-hero h1 { font-size: 30px; font-weight: 800; line-height: 1.25; margin-bottom: 12px; color: #fff7ed; }
.login-hero p.tagline { font-size: 14.5px; opacity: 0.88; margin-bottom: 30px; line-height: 1.5; color: #fed7aa; }
.login-feature { display: flex; align-items: flex-start; margin-bottom: 18px; }
.login-feature-icon {
    background: rgba(255,255,255,0.12);
    width: 34px; height: 34px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; margin-right: 13px; flex-shrink: 0;
}
.login-feature-title { font-weight: 700; font-size: 13.5px; margin-bottom: 2px; color: #fff7ed; }
.login-feature-desc { font-size: 12px; opacity: 0.82; line-height: 1.4; color: #fed7aa; }
.login-stat-row { display: flex; gap: 26px; margin-top: 30px; padding-top: 22px; border-top: 1px solid rgba(255,255,255,0.18); }
.login-stat-num { font-size: 19px; font-weight: 800; color: #fdba74; }
.login-stat-label { font-size: 11px; opacity: 0.8; color: #fed7aa; }

/* Inputs */
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
    border-radius: 10px !important;
    border: 1.5px solid rgba(249, 115, 22, 0.2) !important;
    padding: 11px 14px !important;
    background: #fffaf3 !important;
    color: #292524 !important;
    font-size: 14px !important;
}
div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 3px rgba(249,115,22,0.15) !important;
}

/* Primary buttons */
button[kind="primary"] {
    background: linear-gradient(135deg, #f97316, #0d9488) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
    padding: 0.6rem 1rem !important;
    box-shadow: 0 4px 16px rgba(249, 115, 22, 0.25) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 22px rgba(249, 115, 22, 0.35) !important;
}
.stProgress > div > div > div > div {
    background: linear-gradient(135deg, #f97316, #0d9488) !important;
}
</style>
""", unsafe_allow_html=True)

init_db()

@st.cache_data(ttl=60)
def cached_accuracy_check():
    return run_accuracy_check()

@st.cache_data
def cached_matching_accuracy():
    return get_accuracy_results()

QUESTION_TYPE_OPTIONS = ["technical", "behavioral", "situational", "hr", "aptitude"]
ATS_STATUS_OPTIONS = ["Applied", "Interview Scheduled", "Interview Completed", "Offer Extended", "Hired", "Rejected"]

def get_initials(name):
    if not name:
        return "?"
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")

def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"

def page_header(icon, title, subtitle, role_label=None):
    role_html = f'<span class="role-pill">{role_label}</span>' if role_label else ""
    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex; align-items:center;">
            <span class="page-header-icon">{icon}</span>
            <div>
                <p class="page-header-title">{title}</p>
                <p class="page-header-subtitle">{subtitle}</p>
            </div>
        </div>
        {role_html}
    </div>
    """, unsafe_allow_html=True)

def extract_jd_text_from_file(uploaded_file):
    os.makedirs("data/jd_uploads", exist_ok=True)
    save_path = os.path.join("data/jd_uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    if uploaded_file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(save_path)
    elif uploaded_file.name.lower().endswith(".docx"):
        return extract_text_from_docx(save_path)
    return ""

def render_interview_progress(session):
    """Pictorial progress bar shown during an in-progress interview."""
    done, total_q, pct = get_progress(session)
    st.progress(pct / 100 if total_q else 0)
    st.caption(f"Question {min(done + 1, total_q)} of {total_q} · {pct}% complete")

def render_interview_summary_charts(session):
    """Pictorial summary (gauge + donut) shown after any interview completes."""
    summary = compute_interview_summary(session)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if summary["technical_relevant_pct"] is not None:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=summary["technical_relevant_pct"],
                number={"suffix": "%", "font": {"size": 30, "color": "#f97316"}},
                title={"text": "Technical Answer Relevance", "font": {"size": 13, "color": "#292524"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#a8a29e"},
                    "bar": {"color": "#f97316"},
                    "bgcolor": "rgba(0,0,0,0)",
                    "steps": [
                        {"range": [0, 50], "color": "rgba(248,113,113,0.18)"},
                        {"range": [50, 80], "color": "rgba(251,191,36,0.18)"},
                        {"range": [80, 100], "color": "rgba(34,197,94,0.18)"},
                    ],
                },
            ))
            fig_gauge.update_layout(height=220, margin=dict(t=40, b=10, l=15, r=15), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#292524"})
            st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.caption("No technical questions in this session to score.")

    with chart_col2:
        type_counts = summary["type_counts"]
        if type_counts:
            fig_donut = go.Figure(go.Pie(
                labels=[QUESTION_TYPE_LABELS.get(t, t.capitalize()) for t in type_counts.keys()],
                values=list(type_counts.values()),
                hole=0.55,
                marker=dict(colors=["#f97316", "#0d9488", "#a78bfa", "#fb923c", "#34d399"]),
                textinfo="percent+label"
            ))
            fig_donut.update_layout(title="Question Mix", height=220, showlegend=False,
                                     margin=dict(t=40, b=10, l=15, r=15), paper_bgcolor="rgba(0,0,0,0)",
                                     font={"color": "#292524"})
            st.plotly_chart(fig_donut, use_container_width=True)

# ---- Auth state ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

def show_login_page():
    hero_col, form_col = st.columns([1, 1], gap="large")

    with hero_col:
        st.markdown("""
        <div class="login-hero">
            <div class="login-hero-logo">RC</div>
            <h1>Find your perfect hire, faster.</h1>
            <p class="tagline">AI-powered resume parsing, candidate-job matching, and skill-gap insights — all in one platform.</p>
            <div class="login-feature">
                <div class="login-feature-icon">📄</div>
                <div>
                    <div class="login-feature-title">Automated Resume Parsing</div>
                    <div class="login-feature-desc">Upload PDF or DOCX resumes and get structured candidate profiles instantly.</div>
                </div>
            </div>
            <div class="login-feature">
                <div class="login-feature-icon">🎯</div>
                <div>
                    <div class="login-feature-title">Smart Candidate Matching</div>
                    <div class="login-feature-desc">Rank candidates against job requirements with a transparent hiring score.</div>
                </div>
            </div>
            <div class="login-feature">
                <div class="login-feature-icon">🎙️</div>
                <div>
                    <div class="login-feature-title">Interview + Voice Practice</div>
                    <div class="login-feature-desc">5 question types, live AI feedback, and voice practice for candidates.</div>
                </div>
            </div>
            <div class="login-stat-row">
                <div><div class="login-stat-num">100%</div><div class="login-stat-label">Extraction Accuracy</div></div>
                <div><div class="login-stat-num">≥85%</div><div class="login-stat-label">Match Accuracy</div></div>
                <div><div class="login-stat-num">5</div><div class="login-stat-label">Question Types</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with form_col:
        with st.container(border=True):
            tab1, tab2 = st.tabs(["Login", "Sign Up"])

            with tab1:
                st.markdown("### Welcome back")
                st.caption("Log in to continue to your dashboard")
                with st.form("login_form"):
                    username = st.text_input("👤 Username")
                    password = st.text_input("🔒 Password", type="password")
                    submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

                    if submitted:
                        success, result = login_user(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = result
                            st.rerun()
                        else:
                            st.error(result)

            with tab2:
                st.markdown("### Create an account")
                st.caption("Join as a student, recruiter, or admin")
                with st.form("signup_form"):
                    new_username = st.text_input("👤 Choose a username")
                    new_password = st.text_input("🔒 Choose a password", type="password")
                    confirm_password = st.text_input("🔒 Confirm password", type="password")
                    role = st.radio("I am a:", ["Student", "Recruiter", "Admin"], horizontal=True)
                    signup_submitted = st.form_submit_button("Sign Up", use_container_width=True, type="primary")

                    if signup_submitted:
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            success, message = signup_user(new_username, new_password, role)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)

if not st.session_state.logged_in:
    show_login_page()
    st.stop()

role = st.session_state.role
username = st.session_state.username

# ---- Sidebar navigation ----
NAV_ITEMS = ["Dashboard", "Resume Upload", "Candidates", "Job Postings", "Analytics"]
NAV_ICONS = {"Dashboard": "📊", "Resume Upload": "📄", "Candidates": "👥", "Job Postings": "💼", "Analytics": "📈"}

if role in ["Recruiter", "Admin"]:
    NAV_ITEMS = NAV_ITEMS + ["Interview Assistant", "Deployment"]
    NAV_ICONS["Interview Assistant"] = "🎙️"
    NAV_ICONS["Deployment"] = "🚀"

if role == "Admin":
    NAV_ITEMS = NAV_ITEMS + ["Manage Users"]
    NAV_ICONS["Manage Users"] = "🛡️"

with st.sidebar:
    st.markdown('<span class="logo-badge">RC</span> &nbsp; **Recruitment Copilot**', unsafe_allow_html=True)
    st.caption(f"Logged in as **{username}** ({role})")
    st.markdown("---")

    for item in NAV_ITEMS:
        label = f"{NAV_ICONS[item]} {item}"
        if st.session_state.page == item:
            st.markdown(f"**➡️ {label}**")
        else:
            if st.button(label, key=f"nav_{item}", use_container_width=True):
                st.session_state.page = item
                st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear all candidates"):
        clear_all_candidates()
        st.session_state.processed_files = set()
        st.rerun()
    if st.button("🚪 Logout"):
        for key in ["interview_session", "interview_started", "practice_session", "practice_started",
                    "voice_analysis", "voice_practice_question", "voice_practice_analysis",
                    "generated_questions", "processed_files"]:
            st.session_state.pop(key, None)
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    st.markdown("---")
    with st.expander("💬 Rate your experience"):
        fb_rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=5, key="fb_rating")
        fb_comment = st.text_area("Comments (optional)", key="fb_comment", height=70)
        if st.button("Submit Feedback", key="fb_submit"):
            submit_feedback(username, role, fb_rating, fb_comment)
            st.success("Thanks for your feedback!")

    st.caption("Recruitment Copilot · v4.4")

all_candidates = get_all_candidates()
my_candidates = all_candidates[all_candidates["uploaded_by"] == username] if not all_candidates.empty else all_candidates
total = len(all_candidates)
accuracy = cached_accuracy_check() if total > 0 else 0
all_jobs = get_all_jobs()

FIELDS = ["name", "email", "phone", "education", "skills", "experience", "certifications"]

def field_completeness(row):
    found = sum(1 for f in FIELDS if row[f] and (not isinstance(row[f], list) or len(row[f]) > 0))
    return found, len(FIELDS)

def render_full_profile(cand):
    st.markdown(f"**🎓 Education:** {', '.join(cand['education']) if cand['education'] else '—'}")
    st.markdown(f"**💼 Experience:** {', '.join(cand['experience']) if cand['experience'] else '—'}")
    st.markdown(f"**📜 Certifications:** {', '.join(cand['certifications']) if cand['certifications'] else '—'}")
    if cand["skills"]:
        badges = "".join([f'<span class="skill-badge">{s}</span>' for s in cand["skills"]])
        st.markdown(f"**🛠️ Skills:** {badges}", unsafe_allow_html=True)

# =========================================================
# PAGE: Dashboard
# =========================================================
if st.session_state.page == "Dashboard":

    if role == "Student":
        page_header("👋", f"{get_greeting()}, {username}", "Here's where your job search stands today", role)

        if my_candidates.empty:
            st.warning("You haven't uploaded a resume yet.")
            if st.button("📤 Upload your resume now"):
                st.session_state.page = "Resume Upload"
                st.rerun()
        else:
            latest = my_candidates.iloc[-1]
            found, of_total = field_completeness(latest)
            completeness = round((found / of_total) * 100)

            profile_col, gauge_col = st.columns([1.4, 1])

            with profile_col:
                st.markdown('<div class="profile-card">', unsafe_allow_html=True)
                st.markdown(f"### {latest['name']}")
                st.markdown(f"📧 {latest['email']}  &nbsp;|&nbsp;  📱 {latest['phone']}")
                edu = ", ".join(latest["education"]) if latest["education"] else "—"
                st.markdown(f"**Education:** {edu}")
                st.markdown("**Skills:**")
                if latest["skills"]:
                    badges = "".join([f'<span class="skill-badge">{s}</span>' for s in latest["skills"]])
                    st.markdown(badges, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("")
                if st.button("💼 Check my match against a job posting"):
                    st.session_state.page = "Job Postings"
                    st.rerun()

            with gauge_col:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=completeness,
                    number={"suffix": "%", "font": {"size": 32, "color": "#f97316"}},
                    title={"text": "Profile Completeness", "font": {"size": 14, "color": "#292524"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#a8a29e"},
                        "bar": {"color": "#f97316"},
                        "bgcolor": "rgba(0,0,0,0)",
                        "steps": [
                            {"range": [0, 60], "color": "rgba(248,113,113,0.18)"},
                            {"range": [60, 90], "color": "rgba(251,191,36,0.18)"},
                            {"range": [90, 100], "color": "rgba(34,197,94,0.18)"},
                        ],
                    },
                ))
                fig.update_layout(height=260, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#292524"})
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("📋 Open Job Postings")
            if all_jobs.empty:
                st.info("No job postings available yet.")
            else:
                for _, job in all_jobs.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{job['title']}**")
                        if job["required_skills"]:
                            badges = "".join([f'<span class="skill-badge">{s}</span>' for s in job["required_skills"]])
                            st.markdown(f"Requires: {badges}", unsafe_allow_html=True)

    else:  # Recruiter / Admin
        # =========================================================
        # RECRUITER / ADMIN DASHBOARD
        # =========================================================
        page_header("📊", f"{get_greeting()}, {username}", "Recruitment pipeline overview", role)

        def dashboard_list(value):
            if value is None:
                return []
            if isinstance(value, list):
                return [str(x).strip() for x in value if str(x).strip()]
            if isinstance(value, str):
                return [x.strip() for x in value.split(",") if x.strip()]
            return []

        # Live candidate-job matching data
        candidate_best_scores = {}
        candidate_best_jobs = {}
        missing_skill_counter = Counter()

        if not all_candidates.empty and not all_jobs.empty:
            for _, job in all_jobs.iterrows():
                job_dict = job.to_dict()
                try:
                    results = match_all_candidates(all_candidates, job_dict)
                except Exception:
                    results = []

                required_skills = dashboard_list(job_dict.get("required_skills", []))

                for result in results:
                    name = result.get("name", "Unknown")
                    score = result.get("hiring_score", result.get("score", 0))
                    try:
                        score = float(score)
                    except (TypeError, ValueError):
                        score = 0.0

                    if name not in candidate_best_scores or score > candidate_best_scores[name]:
                        candidate_best_scores[name] = score
                        candidate_best_jobs[name] = job_dict.get("title", "Unknown Job")

                    result_missing = result.get("missing_skills", [])
                    if result_missing:
                        for skill in dashboard_list(result_missing):
                            missing_skill_counter[skill] += 1
                    else:
                        candidate_row = all_candidates[all_candidates["name"] == name]
                        if not candidate_row.empty:
                            candidate_skills = {
                                x.lower() for x in dashboard_list(candidate_row.iloc[0].get("skills", []))
                            }
                            for skill in required_skills:
                                if skill.lower() not in candidate_skills:
                                    missing_skill_counter[skill] += 1

        # ATS / interview status
        ats_df = get_ats_status()
        if ats_df is None:
            ats_df = pd.DataFrame()

        status_counts = {}
        if not ats_df.empty and "status" in ats_df.columns:
            status_counts = ats_df["status"].value_counts().to_dict()

        applied = status_counts.get("Applied", 0)
        scheduled = status_counts.get("Interview Scheduled", 0)
        completed = status_counts.get("Interview Completed", 0)
        hired = status_counts.get("Hired", 0)
        pending = max(total - applied - scheduled - completed - hired, 0)

        # =========================================================
        # KPI CARDS
        # =========================================================
        st.markdown("### 📌 Recruitment Overview")
        m1, m2, m3, m4 = st.columns(4)

        average_score = (
            round(sum(candidate_best_scores.values()) / len(candidate_best_scores))
            if candidate_best_scores else 0
        )

        with m1:
            st.markdown(
                f'<div class="metric-box"><div class="metric-label">👥 Total Candidates</div><div class="metric-value">{total}</div><div style="color:#64748b;font-size:12px;">Resumes processed</div></div>',
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f'<div class="metric-box"><div class="metric-label">💼 Open Job Postings</div><div class="metric-value">{len(all_jobs)}</div><div style="color:#64748b;font-size:12px;">Active recruitment roles</div></div>',
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                f'<div class="metric-box"><div class="metric-label">🎯 Average Hiring Score</div><div class="metric-value">{average_score}%</div><div style="color:#64748b;font-size:12px;">Best available job match</div></div>',
                unsafe_allow_html=True
            )
        with m4:
            st.markdown(
                f'<div class="metric-box"><div class="metric-label">🎤 Interviews Completed</div><div class="metric-value">{completed}</div><div style="color:#64748b;font-size:12px;">ATS interview status</div></div>',
                unsafe_allow_html=True
            )

        # =========================================================
        # PIPELINE + SCORE DISTRIBUTION
        # =========================================================
        st.markdown("---")
        pipeline_col, score_col = st.columns(2)

        with pipeline_col:
            st.markdown("### 🔄 Candidate Pipeline")
            pipeline_df = pd.DataFrame({
                "Stage": ["Pending", "Applied", "Interview Scheduled", "Interview Completed", "Hired"],
                "Candidates": [pending, applied, scheduled, completed, hired]
            })
            if pipeline_df["Candidates"].sum() > 0:
                fig = px.bar(
                    pipeline_df,
                    x="Candidates",
                    y="Stage",
                    orientation="h",
                    text="Candidates"
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    height=330,
                    margin=dict(t=20, b=20, l=10, r=30),
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Candidate status information will appear after candidates enter the ATS.")

        with score_col:
            st.markdown("### 🎯 Hiring Score Distribution")
            bins = {"90–100": 0, "80–89": 0, "70–79": 0, "60–69": 0, "Below 60": 0}
            for score in candidate_best_scores.values():
                if score >= 90:
                    bins["90–100"] += 1
                elif score >= 80:
                    bins["80–89"] += 1
                elif score >= 70:
                    bins["70–79"] += 1
                elif score >= 60:
                    bins["60–69"] += 1
                else:
                    bins["Below 60"] += 1

            score_df = pd.DataFrame({"Score Range": list(bins.keys()), "Candidates": list(bins.values())})
            if score_df["Candidates"].sum() > 0:
                fig = px.bar(score_df, x="Score Range", y="Candidates", text="Candidates")
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    height=330,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Hiring scores will appear after candidate-job matching.")

        # =========================================================
        # CANDIDATE RANKINGS
        # =========================================================
        st.markdown("---")
        st.markdown("### 🏆 Candidate Rankings")

        if not all_candidates.empty:
            ranking_rows = []
            for _, candidate in all_candidates.iterrows():
                name = candidate.get("name", "Unknown")
                ranking_rows.append({
                    "Candidate": name,
                    "Hiring Score": round(candidate_best_scores.get(name, 0)),
                    "Best Fit For": candidate_best_jobs.get(name, "No job matched yet"),
                    "Skills": ", ".join(dashboard_list(candidate.get("skills", []))) or "—",
                    "Email": candidate.get("email", "—")
                })

            ranking_df = pd.DataFrame(ranking_rows).sort_values("Hiring Score", ascending=False)
            ranking_display = ranking_df.copy()
            ranking_display["Hiring Score"] = ranking_display["Hiring Score"].astype(str) + "%"
            st.dataframe(ranking_display.head(10), use_container_width=True, hide_index=True)
        else:
            st.info("No candidates available. Upload resumes to populate the dashboard.")

        # =========================================================
        # SKILL GAP REPORT
        # =========================================================
        st.markdown("---")
        st.markdown("### 🧩 Skill Gap Reports")
        st.caption("Required job skills that are missing from candidate profiles.")

        if missing_skill_counter:
            gap_df = pd.DataFrame(
                missing_skill_counter.most_common(10),
                columns=["Missing Skill", "Candidates Missing Skill"]
            )
            fig = px.bar(
                gap_df,
                x="Candidates Missing Skill",
                y="Missing Skill",
                orientation="h",
                text="Candidates Missing Skill"
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                height=380,
                margin=dict(t=20, b=20, l=20, r=30),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Skill-gap information will appear after candidates and job requirements are available.")

        # =========================================================
        # SKILL LANDSCAPE + RECRUITMENT FUNNEL
        # =========================================================
        skill_col, funnel_col = st.columns(2)

        with skill_col:
            st.markdown("### 🛠️ Candidate Skill Landscape")
            skill_counter = Counter()
            for _, candidate in all_candidates.iterrows():
                for skill in dashboard_list(candidate.get("skills", [])):
                    skill_counter[skill] += 1

            if skill_counter:
                skill_df = pd.DataFrame(
                    skill_counter.most_common(8),
                    columns=["Skill", "Candidates"]
                )
                fig = px.bar(skill_df, x="Skill", y="Candidates", text="Candidates")
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    height=350,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Candidate skills will appear after resume processing.")

        with funnel_col:
            st.markdown("### 📋 Recruitment Funnel")
            funnel_df = pd.DataFrame({
                "Stage": ["Resume Uploaded", "Applied", "Interview Scheduled", "Interview Completed", "Hired"],
                "Count": [total, applied, scheduled, completed, hired]
            })
            fig = px.funnel(funnel_df, x="Count", y="Stage")
            fig.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)

        # =========================================================
        # ATS STATUS
        # =========================================================
        st.markdown("---")
        st.markdown("### 📌 Current ATS Status")

        if not ats_df.empty:
            display_cols = [
                c for c in ["candidate_name", "job_title", "status", "updated_at"]
                if c in ats_df.columns
            ]
            if display_cols:
                display_ats = ats_df[display_cols].copy()
                display_ats.rename(columns={
                    "candidate_name": "Candidate",
                    "job_title": "Job",
                    "status": "Interview Status",
                    "updated_at": "Last Updated"
                }, inplace=True)
                st.dataframe(display_ats, use_container_width=True, hide_index=True)
        else:
            st.info("No ATS activity yet. Interview and candidate status updates will appear here.")

        # =========================================================
        # QUICK ACTIONS
        # =========================================================
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")
        q1, q2, q3 = st.columns(3)

        with q1:
            if st.button("📄 Upload Resume", use_container_width=True, key="dashboard_upload_resume"):
                st.session_state.page = "Resume Upload"
                st.rerun()
        with q2:
            if st.button("💼 Manage Jobs", use_container_width=True, key="dashboard_manage_jobs"):
                st.session_state.page = "Job Postings"
                st.rerun()
        with q3:
            if st.button("🎙️ Interview Assistant", use_container_width=True, key="dashboard_interview"):
                st.session_state.page = "Interview Assistant"
                st.rerun()

# =========================================================
# PAGE: Resume Upload
# =========================================================
elif st.session_state.page == "Resume Upload":
    subtitle = "Upload your resume to create your structured profile" if role == "Student" else "Upload candidate resumes on their behalf to add them to the candidate pool"
    page_header("📄", "Resume Parsing & Candidate Profiling", subtitle, role)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        with st.container(border=True):
            st.subheader("📤 Upload Resume")
            uploaded_files = st.file_uploader(
                "Drag and drop resumes or click to browse",
                type=["pdf", "docx"],
                accept_multiple_files=True,
                label_visibility="collapsed"
            )

            if "processed_files" not in st.session_state:
                st.session_state.processed_files = set()

            if uploaded_files:
                os.makedirs("data/uploaded", exist_ok=True)
                success_count = 0
                for file in uploaded_files:
                    file_id = f"{file.name}_{file.size}"
                    if file_id in st.session_state.processed_files:
                        continue

                    save_path = os.path.join("data/uploaded", file.name)
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())

                    profile_df = process_resume(save_path)
                    if profile_df is not None:
                        candidate_dict = profile_df.iloc[0].to_dict()
                        insert_candidate(candidate_dict, username)
                        st.session_state.processed_files.add(file_id)
                        success_count += 1
                    else:
                        st.error(f"⚠️ Couldn't process {file.name} — file may be corrupted or unreadable")

                if success_count > 0:
                    st.success(f"✅ Processed {success_count} resume(s) successfully")
                    st.balloons()
                    st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader("📊 Parsing Progress")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f'<div class="metric-box"><div class="metric-label">Resumes Processed</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-box"><div class="metric-label">Extraction Accuracy</div><div class="metric-value">{accuracy}%</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-box"><div class="metric-label">Profiles Created</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)

            st.markdown("")

            if total > 0:
                latest = all_candidates.iloc[-1]
                st.markdown(f"**Name:** {latest['name']}")
                st.markdown(f"**Email:** {latest['email']}")
                st.markdown(f"**Phone:** {latest['phone']}")
                edu = ", ".join(latest["education"]) if latest["education"] else "—"
                st.markdown(f"**Education:** {edu}")

                st.markdown("**Skills:**")
                if latest["skills"]:
                    badges = "".join([f'<span class="skill-badge">{s}</span>' for s in latest["skills"]])
                    st.markdown(badges, unsafe_allow_html=True)
                else:
                    st.markdown("—")

# =========================================================
# PAGE: Candidates
# =========================================================
elif st.session_state.page == "Candidates":

    if role == "Student":
        page_header("👤", "My Profile", "The structured profile generated from your uploaded resume", role)

        if my_candidates.empty:
            st.warning("You haven't uploaded a resume yet.")
            if st.button("📤 Upload your resume now"):
                st.session_state.page = "Resume Upload"
                st.rerun()
        else:
            latest = my_candidates.iloc[-1]
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown(f"## {latest['name']}")
            st.markdown(f"📧 {latest['email']}  &nbsp;|&nbsp;  📱 {latest['phone']}")
            st.markdown("---")
            render_full_profile(latest)
            st.markdown('</div>', unsafe_allow_html=True)

    else:  # Recruiter / Admin
        page_header("👥", "Candidate Pool", "All candidates processed across the platform", role)

        if all_candidates.empty:
            st.info("No candidates processed yet.")
        else:
            search_col, sort_col, export_col = st.columns([2, 1, 1])
            with search_col:
                search_term = st.text_input("🔍 Search by name or skill", placeholder="e.g. Python or Ananya")
            with sort_col:
                sort_by = st.selectbox("Sort by", ["Most Recent", "Name (A-Z)", "Most Skills"])

            filtered = all_candidates.copy()
            if search_term.strip():
                term = search_term.strip().lower()
                filtered = filtered[
                    filtered["name"].str.lower().str.contains(term, na=False) |
                    filtered["skills"].apply(lambda skills: any(term in s.lower() for s in skills))
                ]

            if sort_by == "Name (A-Z)":
                filtered = filtered.sort_values("name")
            elif sort_by == "Most Skills":
                filtered = filtered.iloc[filtered["skills"].apply(len).sort_values(ascending=False).index]

            with export_col:
                export_df = filtered.copy()
                for col in ["education", "skills", "experience", "certifications"]:
                    export_df[col] = export_df[col].apply(lambda x: ", ".join(x) if x else "")
                st.download_button("⬇️ Export CSV", to_csv_bytes(export_df), "candidates.csv", "text/csv", use_container_width=True)

            st.caption(f"Showing {len(filtered)} of {len(all_candidates)} candidates")
            st.markdown("---")

            filtered_list = list(filtered.iterrows())
            cols_per_row = 3
            for i in range(0, len(filtered_list), cols_per_row):
                row_items = filtered_list[i:i + cols_per_row]
                grid_cols = st.columns(cols_per_row)
                for grid_col, (_, cand) in zip(grid_cols, row_items):
                    with grid_col:
                        with st.container(border=True):
                            initials = get_initials(cand["name"])
                            st.markdown(f'<div class="avatar-circle-lg">{initials}</div>', unsafe_allow_html=True)
                            st.markdown(f"<p style='text-align:center; font-weight:700; margin-bottom:2px;'>{cand['name']}</p>", unsafe_allow_html=True)
                            st.markdown(f"<p style='text-align:center; font-size:12px; color:#78716c; margin-bottom:10px;'>{cand['email']}</p>", unsafe_allow_html=True)
                            top_skills = cand["skills"][:3]
                            if top_skills:
                                badges = "".join([f'<span class="skill-badge">{s}</span>' for s in top_skills])
                                st.markdown(f"<div style='text-align:center;'>{badges}</div>", unsafe_allow_html=True)
                            with st.expander("View full profile"):
                                render_full_profile(cand)

# =========================================================
# PAGE: Job Postings
# =========================================================
elif st.session_state.page == "Job Postings":

    if role == "Student":
        page_header("💼", "Job Postings", "Check your match, or practice interviewing for a role", role)

        st.subheader("🎯 Check My Match")
        with st.container(border=True):
            job_title_input = st.text_input("Job Title", placeholder="e.g. Software Development Intern")
            jd_text = st.text_area("Paste job description", height=150)
            jd_file = st.file_uploader("Or upload a JD file (PDF/DOCX)", type=["pdf", "docx"], key="jd_file_student")

            final_jd_text = jd_text
            if jd_file is not None:
                extracted = extract_jd_text_from_file(jd_file)
                if extracted.strip():
                    final_jd_text = extracted
                    st.caption(f"📄 Using text extracted from {jd_file.name}")

            if st.button("🔍 Check My Match"):
                if final_jd_text.strip() and job_title_input.strip():
                    if my_candidates.empty:
                        st.error("Upload your resume first from the Resume Upload page.")
                    else:
                        job = analyze_job_description(final_jd_text)
                        job["title"] = job_title_input.strip()
                        my_latest = my_candidates.iloc[-1]
                        score, matched = calculate_match(my_latest.to_dict(), job)
                        gap = skill_gap_analysis(my_latest.to_dict(), job)

                        color = "#15803d" if score >= 85 else "#b45309" if score >= 60 else "#b91c1c"
                        st.markdown(f"<h2 style='color:{color}'>{score}% Match</h2>", unsafe_allow_html=True)
                        if matched:
                            badges = "".join([f'<span class="skill-badge">{s}</span>' for s in matched])
                            st.markdown(f"Matched skills: {badges}", unsafe_allow_html=True)
                        if gap["missing_skills"]:
                            st.markdown(f"⚠️ Missing: {', '.join(gap['missing_skills'])}")
                            for rec in gap["recommendations"]:
                                st.caption(f"💡 {rec}")
                else:
                    st.error("Please enter a job title and paste or upload a job description")

        st.markdown("---")
        st.subheader("🎤 Practice Interview")
        st.caption("Practice answering role-specific questions before the real thing — questions and feedback work the same way recruiters see them.")

        if all_jobs.empty:
            st.info("No job postings available yet to practice against.")
        elif my_candidates.empty:
            st.info("Upload your resume first from the Resume Upload page to start practicing.")
        else:
            with st.container(border=True):
                prac_job_title = st.selectbox("Job Position", all_jobs["title"].tolist(), key="prac_job")
                prac_difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], index=1, key="prac_difficulty")

                st.caption("Choose how many questions of each type:")
                prac_row1 = st.columns(3)
                with prac_row1[0]:
                    prac_num_tech = st.number_input("Technical", min_value=0, max_value=20, value=2, step=1, key="prac_num_tech")
                with prac_row1[1]:
                    prac_num_beh = st.number_input("Behavioral", min_value=0, max_value=20, value=1, step=1, key="prac_num_beh")
                with prac_row1[2]:
                    prac_num_sit = st.number_input("Situational", min_value=0, max_value=20, value=0, step=1, key="prac_num_sit")
                prac_row2 = st.columns(3)
                with prac_row2[0]:
                    prac_num_hr = st.number_input("HR / Culture Fit", min_value=0, max_value=20, value=0, step=1, key="prac_num_hr")
                with prac_row2[1]:
                    prac_num_apt = st.number_input("Aptitude", min_value=0, max_value=20, value=0, step=1, key="prac_num_apt")

                if st.button("▶️ Start Practice", type="primary"):
                    if prac_num_tech + prac_num_beh + prac_num_sit + prac_num_hr + prac_num_apt == 0:
                        st.error("Add at least one question of any type.")
                    else:
                        prac_job = all_jobs[all_jobs["title"] == prac_job_title].iloc[0].to_dict()
                        my_latest = my_candidates.iloc[-1]
                        st.session_state.practice_session = start_interview(
                            my_latest["name"], prac_job,
                            num_technical=int(prac_num_tech), num_behavioral=int(prac_num_beh),
                            num_situational=int(prac_num_sit), num_hr=int(prac_num_hr),
                            num_aptitude=int(prac_num_apt), difficulty=prac_difficulty
                        )
                        st.session_state.practice_started = True

                if st.session_state.get("practice_started") and "practice_session" in st.session_state:
                    psession = st.session_state.practice_session

                    st.markdown(f"<div class='chat-bubble-ai'>{get_opening_message(psession['candidate_name'], psession['job_title'])}</div>", unsafe_allow_html=True)

                    for turn in psession["transcript"]:
                        type_label = QUESTION_TYPE_LABELS.get(turn.get("type", "technical"), "Question")
                        st.markdown(f"<span class='type-badge'>{type_label}</span>", unsafe_allow_html=True)
                        st.markdown(f"<div class='chat-bubble-ai'>{turn['question']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='chat-bubble-candidate'>{turn['answer']}</div>", unsafe_allow_html=True)
                        tag_class = "relevance-tag-yes" if turn.get("mentions_skill") else "relevance-tag-no"
                        st.markdown(f"<div class='{tag_class}'>🤖 {turn.get('feedback', '')}</div>", unsafe_allow_html=True)
                        if turn.get("correct_answer"):
                            with st.expander("👁️ View Solution"):
                                st.markdown(turn["correct_answer"])

                    prac_current_q = get_current_question(psession)
                    if prac_current_q:
                        render_interview_progress(psession)
                        current_type = psession["questions"][psession["current_index"]].get("type", "technical")
                        st.markdown(f"<span class='type-badge'>{QUESTION_TYPE_LABELS.get(current_type, 'Question')}</span>", unsafe_allow_html=True)
                        st.markdown(f"<div class='chat-bubble-ai'>{prac_current_q}</div>", unsafe_allow_html=True)
                        prac_answer = st.text_area("Type response...", key=f"prac_answer_{psession['current_index']}", label_visibility="collapsed")
                        if st.button("➤ Send", key=f"prac_send_{psession['current_index']}", type="primary"):
                            if prac_answer.strip():
                                st.session_state.practice_session = submit_answer(psession, prac_answer.strip())
                                st.rerun()
                            else:
                                st.warning("Please type a response before sending.")
                    else:
                        st.success("Practice complete! Here's how you did:")
                        render_interview_summary_charts(psession)

                        prac_transcript_df = pd.DataFrame(psession["transcript"])
                        if "feedback" in prac_transcript_df.columns:
                            prac_transcript_df = prac_transcript_df[["question", "skill", "type", "answer", "mentions_skill", "feedback"]]
                            prac_transcript_df.columns = ["Question", "Skill Tested", "Question Type", "Answer", "Relevant", "AI Feedback"]
                        st.download_button(
                            "⬇️ Download Practice Transcript",
                            to_csv_bytes(prac_transcript_df),
                            f"practice_transcript_{psession['candidate_name'].replace(' ', '_')}.csv",
                            "text/csv",
                            key="prac_download"
                        )

                        if st.button("🔄 Practice Again"):
                            st.session_state.practice_started = False
                            del st.session_state.practice_session
                            st.rerun()

        st.markdown("---")
        st.subheader("🎙️ Voice-Based Screening")
        st.caption("Practice a real voice interview: the AI asks the question aloud, you record your answer in the browser, and the app converts your speech to text and provides feedback.")

        if all_jobs.empty:
            st.info("No job postings available yet to practice against.")
        else:
            with st.container(border=True):
                vp_job_title = st.selectbox(
                    "Job Position",
                    all_jobs["title"].tolist(),
                    key="vp_job"
                )
                vp_qtype = st.selectbox(
                    "Question Type",
                    QUESTION_TYPE_OPTIONS,
                    format_func=lambda t: QUESTION_TYPE_LABELS.get(t, t.capitalize()),
                    key="vp_qtype"
                )
                vp_difficulty = st.selectbox(
                    "Difficulty",
                    ["Beginner", "Intermediate", "Advanced"],
                    index=1,
                    key="vp_difficulty"
                )

                if st.button("🎯 Get Voice Interview Question", key="vp_get_question", type="primary"):
                    vp_job = all_jobs[all_jobs["title"] == vp_job_title].iloc[0].to_dict()
                    vp_questions = generate_questions(vp_job, vp_qtype, 1, vp_difficulty)

                    if vp_questions:
                        st.session_state.voice_practice_question = vp_questions[0]
                        st.session_state.pop("voice_practice_response", None)
                        st.session_state.pop("voice_practice_feedback", None)
                        st.session_state.pop("voice_practice_analysis", None)
                        st.session_state.voice_practice_started = False
                        st.session_state.pop("vp_audio_processed", None)
                        st.rerun()

                if "voice_practice_question" in st.session_state:
                    vpq = st.session_state.voice_practice_question
                    type_label = QUESTION_TYPE_LABELS.get(
                        vpq.get("type", "technical"),
                        "Question"
                    )

                    st.markdown(
                        f"<span class='type-badge'>{type_label}</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<div class='chat-bubble-ai'>🎙️ {vpq['question']}</div>",
                        unsafe_allow_html=True
                    )

                    if not st.session_state.get("voice_practice_started", False):
                        st.info("Click Start Voice Interview. The AI will ask the question aloud, then you can record your answer below.")

                        if st.button("🎤 Start Voice Interview", key="vp_start_voice", type="primary"):
                            with st.spinner("AI interviewer is speaking..."):
                                spoken = speak_text(vpq["question"])

                            if not spoken:
                                st.warning(
                                    "The AI interviewer could not start text-to-speech. "
                                    "You can still read the question above and record your answer."
                                )

                            st.session_state.voice_practice_started = True
                            st.rerun()
                    else:
                        st.success("🎤 The AI has asked the question. Now record your answer below.")

                        try:
                            vp_audio = st.audio_input(
                                "Record your answer",
                                key="vp_audio"
                            )
                        except AttributeError:
                            vp_audio = None
                            st.error(
                                "Your Streamlit version does not support st.audio_input(). "
                                "Run: python -m pip install --upgrade streamlit"
                            )

                        if vp_audio is not None:
                            st.audio(vp_audio)

                            if st.button("📝 Transcribe My Answer", key="vp_transcribe", type="primary"):
                                with st.spinner("Converting your speech to text..."):
                                    result = listen_to_candidate(vp_audio.getvalue())

                                if result["success"]:
                                    response = result["text"]
                                    st.session_state.voice_practice_response = response
                                    st.session_state.voice_practice_analysis = analyze_audio(vp_audio.getvalue())
                                    st.session_state.voice_practice_feedback = generate_voice_feedback(response)
                                    st.session_state.vp_audio_processed = True
                                else:
                                    st.session_state.voice_practice_response = result["text"]
                                    st.session_state.voice_practice_feedback = result["text"]
                                    st.session_state.pop("voice_practice_analysis", None)
                                    st.session_state.vp_audio_processed = False

                                st.rerun()

                        if "voice_practice_response" in st.session_state:
                            response = st.session_state.voice_practice_response

                            st.markdown("**📝 Your Transcribed Response**")
                            st.markdown(
                                f"<div class='chat-bubble-candidate'>{response}</div>",
                                unsafe_allow_html=True
                            )

                            if st.session_state.get("vp_audio_processed") and "voice_practice_analysis" in st.session_state:
                                vpa = st.session_state.voice_practice_analysis
                                vp_col1, vp_col2 = st.columns(2)
                                with vp_col1:
                                    st.metric("Duration", f"{vpa['duration_seconds']}s")
                                with vp_col2:
                                    st.metric("Volume Score", f"{vpa['volume_score']}%")

                            if "voice_practice_feedback" in st.session_state:
                                st.markdown("**🤖 AI Feedback**")
                                st.info(st.session_state.voice_practice_feedback)

                                if st.session_state.get("vp_audio_processed"):
                                    if st.button("🔊 Hear AI Feedback", key="vp_speak_feedback"):
                                        speak_text(st.session_state.voice_practice_feedback)

                    if st.button("🔄 New Voice Question", key="vp_new_question"):
                        for key in [
                            "voice_practice_question",
                            "voice_practice_response",
                            "voice_practice_feedback",
                            "voice_practice_analysis",
                            "voice_practice_started",
                            "vp_audio_processed"
                        ]:
                            st.session_state.pop(key, None)
                        st.rerun()

    else:  # Recruiter or Admin
        page_header("💼", "Job Postings", "Post a job requirement and rank all candidates against it", role)

        post_tab, view_tab = st.tabs(["➕ Post New Job", "📋 View & Match Candidates"])

        with post_tab:
            with st.container(border=True):
                st.subheader("Post a New Job")
                job_title_input = st.text_input("Job Title", placeholder="e.g. Software Development Intern")
                jd_text = st.text_area("Paste job description", height=150)
                jd_file = st.file_uploader("Or upload a JD file (PDF/DOCX)", type=["pdf", "docx"], key="jd_file_recruiter")

                final_jd_text = jd_text
                if jd_file is not None:
                    extracted = extract_jd_text_from_file(jd_file)
                    if extracted.strip():
                        final_jd_text = extracted
                        st.caption(f"📄 Using text extracted from {jd_file.name}")

                if st.button("🔍 Analyze & Save Job", type="primary"):
                    if final_jd_text.strip() and job_title_input.strip():
                        job = analyze_job_description(final_jd_text)
                        job["title"] = job_title_input.strip()
                        insert_job(job, username)
                        st.success(f"Job \"{job['title']}\" saved — {len(job['required_skills'])} required skills detected")
                        st.rerun()
                    else:
                        st.error("Please enter a job title and paste or upload a job description")

        with view_tab:
            if all_jobs.empty:
                st.info("No jobs posted yet — switch to the 'Post New Job' tab to add one.")
            else:
                job_titles = all_jobs["title"].tolist()
                selected_title = st.selectbox("Select a job to view matched candidates", job_titles)
                selected_job_row = all_jobs[all_jobs["title"] == selected_title].iloc[0]
                selected_job = selected_job_row.to_dict()

                can_delete = (role == "Admin") or (selected_job.get("created_by") == username)
                if can_delete:
                    if st.button("🗑️ Delete this job posting"):
                        delete_job(int(selected_job["id"]))
                        st.success("Job posting deleted")
                        st.rerun()

                if all_candidates.empty:
                    st.info("No candidates in the system yet to match against.")
                else:
                    results = match_all_candidates(all_candidates, selected_job)
                    results_df = pd.DataFrame(results)

                    strong_match_pct = round((sum(1 for r in results if r["hiring_score"] >= 85) / len(results)) * 100, 1) if results else 0

                    fig_match_gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=strong_match_pct,
                        number={"suffix": "%", "font": {"size": 36, "color": "#f97316"}},
                        title={"text": f"% of Candidates ≥85% Match — {selected_title}", "font": {"size": 14, "color": "#292524"}},
                        gauge={
                            "axis": {"range": [0, 100], "tickcolor": "#a8a29e"},
                            "bar": {"color": "#f97316"},
                            "bgcolor": "rgba(0,0,0,0)",
                            "steps": [
                                {"range": [0, 50], "color": "rgba(248,113,113,0.18)"},
                                {"range": [50, 85], "color": "rgba(251,191,36,0.18)"},
                                {"range": [85, 100], "color": "rgba(34,197,94,0.18)"},
                            ],
                            "threshold": {"line": {"color": "#0d9488", "width": 4}, "thickness": 0.8, "value": 85},
                        },
                    ))
                    fig_match_gauge.update_layout(height=260, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#292524"})
                    st.plotly_chart(fig_match_gauge, use_container_width=True)

                    st.markdown("---")
                    st.subheader("📉 Missing Skills Report")

                    all_missing = []
                    for r in results:
                        all_missing.extend(r["missing_skills"])

                    report_rows = [{"Candidate": r["name"], "Email": r["email"],
                                     "Missing Skills": ", ".join(r["missing_skills"]) or "None",
                                     "Recommendations": "; ".join(r["recommendations"]) or "—"} for r in results]
                    report_df = pd.DataFrame(report_rows)

                    st.download_button(
                        "⬇️ Download Missing Skills Report",
                        to_csv_bytes(report_df),
                        f"missing_skills_report_{selected_title}.csv",
                        "text/csv"
                    )

                    if all_missing:
                        missing_counts = Counter(all_missing).most_common()
                        missing_df = pd.DataFrame(missing_counts, columns=["Skill", "Candidates Missing It"])

                        fig_missing = px.bar(
                            missing_df.sort_values("Candidates Missing It"),
                            x="Candidates Missing It", y="Skill", orientation="h",
                            color="Candidates Missing It", color_continuous_scale=["#fed7aa", "#f97316"],
                            text="Candidates Missing It", title=f"Most Common Skill Gaps — {selected_title}"
                        )
                        fig_missing.update_traces(textposition="outside")
                        fig_missing.update_layout(height=280, showlegend=False, coloraxis_showscale=False,
                                                   margin=dict(t=50, b=10, l=10, r=30), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                                   font={"color": "#292524"})
                        st.plotly_chart(fig_missing, use_container_width=True)

                        table_html = "<table style='width:100%; border-collapse: collapse;'>"
                        table_html += "<tr style='text-align:left; border-bottom: 2px solid rgba(41,37,36,0.12);'>"
                        for col in report_df.columns:
                            table_html += f"<th style='padding:8px;'>{col}</th>"
                        table_html += "</tr>"
                        for _, row in report_df.iterrows():
                            table_html += "<tr style='border-bottom: 1px solid rgba(41,37,36,0.06);'>"
                            for val in row:
                                table_html += f"<td style='padding:8px;'>{val}</td>"
                            table_html += "</tr>"
                        table_html += "</table>"
                        st.markdown(table_html, unsafe_allow_html=True)
                    else:
                        st.success("No skill gaps — every candidate matches all required skills.")

                    st.markdown("---")
                    st.markdown(f"**Ranked candidates for: {selected_title}**")

                    export_df = results_df.copy()
                    export_df["matched_skills"] = export_df["matched_skills"].apply(lambda x: ", ".join(x))
                    export_df["missing_skills"] = export_df["missing_skills"].apply(lambda x: ", ".join(x))
                    export_df["recommendations"] = export_df["recommendations"].apply(lambda x: "; ".join(x))
                    st.download_button("⬇️ Export Full Match Results CSV", to_csv_bytes(export_df), f"matches_{selected_title}.csv", "text/csv")

                    for r in results:
                        score = r["hiring_score"]
                        color = "#15803d" if score >= 85 else "#b45309" if score >= 60 else "#b91c1c"
                        rank_badge = {1: "🥇", 2: "🥈", 3: "🥉"}.get(r["rank"], f"#{r['rank']}")
                        with st.container(border=True):
                            mcol1, mcol2 = st.columns([3, 1])
                            with mcol1:
                                st.markdown(f"**{rank_badge}&nbsp;&nbsp;{r['name']}** — {r['email']}", unsafe_allow_html=True)
                                if r["matched_skills"]:
                                    badges = "".join([f'<span class="skill-badge">{s}</span>' for s in r["matched_skills"]])
                                    st.markdown(f"Matched: {badges}", unsafe_allow_html=True)
                                if r["missing_skills"]:
                                    st.markdown(f"⚠️ Missing: {', '.join(r['missing_skills'])}")
                                    for rec in r["recommendations"]:
                                        st.caption(f"💡 {rec}")
                            with mcol2:
                                st.markdown(f"<div style='text-align:center;'><span style='font-size:32px; font-weight:800; color:{color}'>{score}%</span><br><span style='font-size:12px; color:#78716c;'>Match Score</span></div>", unsafe_allow_html=True)

# =========================================================
# PAGE: Interview Assistant (Recruiter/Admin only)
# =========================================================
elif st.session_state.page == "Interview Assistant":
    page_header("🎙️", "Interview Assistance & ATS Integration", "Generate interview questions, simulate interviews, and manage candidates", role)

    gen_col, sim_col = st.columns([1, 1], gap="large")

    with gen_col:
        with st.container(border=True):
            st.subheader("📋 Interview Question Generator")
            if all_jobs.empty:
                st.info("No job postings yet — add one from the Job Postings page.")
            else:
                job_titles = all_jobs["title"].tolist()
                gen_job_title = st.selectbox("Job Position", job_titles, key="gen_job_select")
                q_type = st.selectbox("Question Type", QUESTION_TYPE_OPTIONS,
                                       format_func=lambda t: QUESTION_TYPE_LABELS.get(t, t.capitalize()), key="gen_qtype")
                gen_difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], index=1, key="gen_difficulty")
                num_q = st.number_input("Number of questions", min_value=1, max_value=50, value=3, step=1, key="gen_numq")

                if st.button("🔄 Generate Questions", type="primary"):
                    gen_job = all_jobs[all_jobs["title"] == gen_job_title].iloc[0].to_dict()
                    st.session_state.generated_questions = generate_questions(gen_job, q_type, int(num_q), gen_difficulty)

                if "generated_questions" in st.session_state:
                    for i, q in enumerate(st.session_state.generated_questions, start=1):
                        st.markdown(f"**{i}.** {q['question']}")
                        with st.expander("👁️ View Solution"):
                            if q.get("answer"):
                                st.markdown(q["answer"])
                            else:
                                st.caption("No single correct answer — evaluate based on the candidate's specific example and reasoning.")

    with sim_col:
        with st.container(border=True):
            st.subheader("🎤 AI Interview Simulation")

            if all_candidates.empty or all_jobs.empty:
                st.info("Need at least one candidate and one job posting to start a simulation.")
            else:
                sim_candidate_name = st.selectbox("Candidate", all_candidates["name"].tolist(), key="sim_candidate")
                sim_job_title = st.selectbox("Job Position", all_jobs["title"].tolist(), key="sim_job")
                sim_difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], index=1, key="sim_difficulty")

                st.caption("Choose how many questions of each type:")
                sim_row1 = st.columns(3)
                with sim_row1[0]:
                    sim_num_tech = st.number_input("Technical", min_value=0, max_value=20, value=2, step=1, key="sim_num_tech")
                with sim_row1[1]:
                    sim_num_beh = st.number_input("Behavioral", min_value=0, max_value=20, value=1, step=1, key="sim_num_beh")
                with sim_row1[2]:
                    sim_num_sit = st.number_input("Situational", min_value=0, max_value=20, value=0, step=1, key="sim_num_sit")
                sim_row2 = st.columns(3)
                with sim_row2[0]:
                    sim_num_hr = st.number_input("HR / Culture Fit", min_value=0, max_value=20, value=0, step=1, key="sim_num_hr")
                with sim_row2[1]:
                    sim_num_apt = st.number_input("Aptitude", min_value=0, max_value=20, value=0, step=1, key="sim_num_apt")

                if st.button("▶️ Start Interview"):
                    if sim_num_tech + sim_num_beh + sim_num_sit + sim_num_hr + sim_num_apt == 0:
                        st.error("Add at least one question of any type.")
                    else:
                        sim_job = all_jobs[all_jobs["title"] == sim_job_title].iloc[0].to_dict()
                        st.session_state.interview_session = start_interview(
                            sim_candidate_name, sim_job,
                            num_technical=int(sim_num_tech), num_behavioral=int(sim_num_beh),
                            num_situational=int(sim_num_sit), num_hr=int(sim_num_hr),
                            num_aptitude=int(sim_num_apt), difficulty=sim_difficulty
                        )
                        st.session_state.interview_started = True

                if st.session_state.get("interview_started") and "interview_session" in st.session_state:
                    session = st.session_state.interview_session

                    st.markdown(f"<div class='chat-bubble-ai'>{get_opening_message(session['candidate_name'], session['job_title'])}</div>", unsafe_allow_html=True)

                    for turn in session["transcript"]:
                        type_label = QUESTION_TYPE_LABELS.get(turn.get("type", "technical"), "Question")
                        st.markdown(f"<span class='type-badge'>{type_label}</span>", unsafe_allow_html=True)
                        st.markdown(f"<div class='chat-bubble-ai'>{turn['question']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='chat-bubble-candidate'>{turn['answer']}</div>", unsafe_allow_html=True)
                        tag_class = "relevance-tag-yes" if turn.get("mentions_skill") else "relevance-tag-no"
                        feedback_text = turn.get("feedback", "")
                        st.markdown(f"<div class='{tag_class}'>🤖 {feedback_text}</div>", unsafe_allow_html=True)
                        if turn.get("correct_answer"):
                            with st.expander("👁️ View Solution"):
                                st.markdown(turn["correct_answer"])

                    current_q = get_current_question(session)
                    if current_q:
                        render_interview_progress(session)
                        current_type = session["questions"][session["current_index"]].get("type", "technical")
                        st.markdown(f"<span class='type-badge'>{QUESTION_TYPE_LABELS.get(current_type, 'Question')}</span>", unsafe_allow_html=True)
                        st.markdown(f"<div class='chat-bubble-ai'>{current_q}</div>", unsafe_allow_html=True)

                        # -------------------------------------------------
                        # Recruiter/Admin AI Interview Simulation - Voice Mode
                        # -------------------------------------------------
                        st.markdown("### 🎙️ Voice Interview")
                        st.caption(
                            "Let the AI interviewer ask the question aloud, then record the candidate's answer. "
                            "The recording is converted to text and submitted to the interview simulation."
                        )

                        voice_q_key = f"voice_question_{session['current_index']}"
                        voice_audio_key = f"interview_voice_audio_{session['current_index']}"
                        voice_result_key = f"interview_voice_result_{session['current_index']}"

                        if st.button("🔊 Ask Question by Voice", key=f"ask_voice_{session['current_index']}"):
                            speak_text(current_q)
                            st.session_state[voice_q_key] = True
                            st.session_state.pop(voice_result_key, None)

                        if st.session_state.get(voice_q_key):
                            st.info(
                                "🎤 The AI has asked the question. "
                                "Use the microphone below and speak the candidate's answer."
                            )

                            try:
                                voice_audio = st.audio_input(
                                    "🎤 Record candidate answer",
                                    key=voice_audio_key
                                )
                            except AttributeError:
                                voice_audio = None
                                st.warning(
                                    "Your Streamlit version does not support `st.audio_input`. "
                                    "Run `python -m pip install --upgrade streamlit` and restart the app."
                                )

                            if voice_audio is not None:
                                st.audio(voice_audio)

                                if st.button(
                                    "📝 Transcribe & Submit Voice Answer",
                                    key=f"submit_voice_{session['current_index']}",
                                    type="primary"
                                ):
                                    with st.spinner("Converting the candidate's speech to text..."):
                                        voice_result = listen_to_candidate(voice_audio.getvalue())

                                    if voice_result["success"]:
                                        voice_response = voice_result["text"]
                                        st.session_state[voice_result_key] = voice_response

                                        st.subheader("📝 Transcribed Response")
                                        st.success(voice_response)

                                        audio_analysis = analyze_audio(voice_audio.getvalue())
                                        if audio_analysis:
                                            analysis_col1, analysis_col2 = st.columns(2)
                                            with analysis_col1:
                                                st.metric(
                                                    "Duration",
                                                    f"{audio_analysis['duration_seconds']}s"
                                                )
                                            with analysis_col2:
                                                st.metric(
                                                    "Volume Score",
                                                    f"{audio_analysis['volume_score']}%"
                                                )

                                        st.info(
                                            generate_voice_feedback(voice_response)
                                        )

                                        # Submit the transcribed response to the
                                        # existing AI interview simulation engine.
                                        st.session_state.interview_session = submit_answer(
                                            session,
                                            voice_response.strip()
                                        )
                                        st.session_state.pop(voice_q_key, None)
                                        st.session_state.pop(voice_result_key, None)
                                        st.rerun()
                                    else:
                                        st.error(voice_result["text"])

                        st.markdown("---")
                        st.markdown("**⌨️ Or type the candidate's answer**")
                        answer = st.text_area(
                            "Type response...",
                            key=f"answer_{session['current_index']}",
                            label_visibility="collapsed"
                        )
                        if st.button(
                            "➤ Send",
                            key=f"send_{session['current_index']}",
                            type="primary"
                        ):
                            if answer.strip():
                                st.session_state.interview_session = submit_answer(
                                    session, answer.strip()
                                )
                                st.session_state.pop(voice_q_key, None)
                                st.rerun()
                            else:
                                st.warning("Please type a response before sending.")
                    else:
                        st.success("Interview completed. Candidate responses stored for ATS review.")
                        render_interview_summary_charts(session)

                        transcript_df = pd.DataFrame(session["transcript"])
                        if "feedback" in transcript_df.columns:
                            transcript_df = transcript_df[["question", "skill", "type", "answer", "mentions_skill", "feedback"]]
                            transcript_df.columns = ["Question", "Skill Tested", "Question Type", "Answer", "Relevant", "AI Feedback"]
                        st.download_button(
                            "⬇️ Download Interview Transcript",
                            to_csv_bytes(transcript_df),
                            f"interview_transcript_{session['candidate_name'].replace(' ', '_')}.csv",
                            "text/csv"
                        )

                        candidate_match = all_candidates[all_candidates["name"] == session["candidate_name"]]
                        if not candidate_match.empty and st.button("✅ Mark as 'Interview Completed' in ATS"):
                            candidate_row = candidate_match.iloc[0]
                            add_to_ats(session["candidate_name"], candidate_row["email"], session["job_title"], "Interview Completed", username)
                            st.success("ATS status updated.")
                            st.session_state.interview_started = False
                            del st.session_state.interview_session
                            st.rerun()

    st.markdown("---")
    st.subheader("🔗 ATS Integration")

    if all_candidates.empty or all_jobs.empty:
        st.info("Add candidates and job postings to use ATS tracking.")
    else:
        with st.container(border=True):
            ats_col1, ats_col2, ats_col3, ats_col4 = st.columns([2, 2, 2, 1])
            with ats_col1:
                ats_candidate = st.selectbox("Candidate", all_candidates["name"].tolist(), key="ats_candidate")
            with ats_col2:
                ats_job = st.selectbox("Job", all_jobs["title"].tolist(), key="ats_job")
            with ats_col3:
                ats_new_status = st.selectbox("Status", ATS_STATUS_OPTIONS, key="ats_status_select")
            with ats_col4:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("Update", key="ats_update_btn"):
                    cand_row = all_candidates[all_candidates["name"] == ats_candidate].iloc[0]
                    add_to_ats(ats_candidate, cand_row["email"], ats_job, ats_new_status, username)
                    st.success("ATS status updated")
                    st.rerun()

        ats_df = get_ats_status()
        if not ats_df.empty:
            for _, row in ats_df.iterrows():
                status_class = row["status"].replace(" ", "_")
                with st.container(border=True):
                    acol1, acol2, acol3 = st.columns([2, 2, 1])
                    with acol1:
                        st.markdown(f"**{row['candidate_name']}**")
                        st.caption(row["job_title"])
                    with acol2:
                        st.markdown(f"<span class='status-pill-{status_class}'>{row['status']}</span>", unsafe_allow_html=True)
                    with acol3:
                        st.caption(row["updated_at"][:16].replace("T", " "))
        else:
            st.info("No ATS records yet — update a status above to start tracking.")

# =========================================================
# PAGE: Dashboard & Deployment (Recruiter/Admin only) — Milestone 4
# =========================================================
elif st.session_state.page == "Deployment":
    page_header("🚀", "Dashboard & Deployment", "Recruitment analytics, voice screening, and system status", role)

    ats_df = get_ats_status()
    applied_count = ats_df["candidate_email"].nunique() if not ats_df.empty else 0
    interviews_scheduled = len(ats_df[ats_df["status"].isin(["Interview Scheduled", "Interview Completed"])]) if not ats_df.empty else 0
    hired_df = ats_df[ats_df["status"] == "Hired"] if not ats_df.empty else pd.DataFrame()
    hired_count = len(hired_df)
    hiring_success_rate = round((hired_count / applied_count) * 100, 1) if applied_count else 0

    avg_time_to_hire = None
    if not hired_df.empty:
        days_list = []
        for _, hrow in hired_df.iterrows():
            cand_match = all_candidates[all_candidates["email"] == hrow["candidate_email"]]
            if not cand_match.empty and "created_at" in cand_match.columns:
                try:
                    created = pd.to_datetime(cand_match.iloc[0]["created_at"])
                    hired_at = pd.to_datetime(hrow["updated_at"])
                    days_list.append((hired_at - created).days)
                except Exception:
                    pass
        if days_list:
            avg_time_to_hire = round(sum(days_list) / len(days_list), 1)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f'<div class="metric-box"><div class="metric-label">Total Candidates</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><div class="metric-label">Interviews Scheduled</div><div class="metric-value">{interviews_scheduled}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><div class="metric-label">Hiring Success Rate</div><div class="metric-value">{hiring_success_rate}%</div></div>', unsafe_allow_html=True)
    with m4:
        display_days = f"{avg_time_to_hire}d" if avg_time_to_hire is not None else "—"
        st.markdown(f'<div class="metric-box"><div class="metric-label">Avg Time to Hire</div><div class="metric-value" style="font-size:22px;">{display_days}</div></div>', unsafe_allow_html=True)
    with m5:
        satisfaction_score, feedback_count = get_satisfaction_score()
        display_satisfaction = f"{satisfaction_score}%" if satisfaction_score is not None else "—"
        st.markdown(f'<div class="metric-box"><div class="metric-label">User Satisfaction</div><div class="metric-value">{display_satisfaction}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    if satisfaction_score is not None:
        st.subheader("😊 User Satisfaction")
        sat_gauge_col, sat_comments_col = st.columns([1, 1.4])
        with sat_gauge_col:
            fig_sat = go.Figure(go.Indicator(
                mode="gauge+number",
                value=satisfaction_score,
                number={"suffix": "%", "font": {"size": 34, "color": "#f97316"}},
                title={"text": f"Based on {feedback_count} response(s) vs 85% target", "font": {"size": 12, "color": "#292524"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#a8a29e"},
                    "bar": {"color": "#f97316"},
                    "bgcolor": "rgba(0,0,0,0)",
                    "steps": [
                        {"range": [0, 60], "color": "rgba(248,113,113,0.18)"},
                        {"range": [60, 85], "color": "rgba(251,191,36,0.18)"},
                        {"range": [85, 100], "color": "rgba(34,197,94,0.18)"},
                    ],
                    "threshold": {"line": {"color": "#0d9488", "width": 4}, "thickness": 0.8, "value": 85},
                },
            ))
            fig_sat.update_layout(height=240, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#292524"})
            st.plotly_chart(fig_sat, use_container_width=True)
        with sat_comments_col:
            st.markdown("**Recent feedback:**")
            fb_df = get_feedback().head(5)
            for _, fb in fb_df.iterrows():
                stars = "⭐" * int(fb["rating"])
                with st.container(border=True):
                    st.markdown(f"{stars} — *{fb['role']}*")
                    if fb["comment"]:
                        st.caption(fb["comment"])
        st.markdown("---")

    pipeline_col, voice_col = st.columns([1.2, 1])

    with pipeline_col:
        st.subheader("📊 Recruitment Pipeline")
        if all_candidates.empty:
            st.info("No candidates yet to build a pipeline view.")
        else:
            screened_count = 0
            interviewed_count = interviews_scheduled
            offered_count = len(ats_df[ats_df["status"].isin(["Offer Extended", "Hired"])]) if not ats_df.empty else 0

            if not all_jobs.empty:
                screened_emails = set()
                for _, job in all_jobs.iterrows():
                    job_results = match_all_candidates(all_candidates, job.to_dict())
                    for r in job_results:
                        if r["hiring_score"] >= 60:
                            screened_emails.add(r["email"])
                screened_count = len(screened_emails)

            funnel_df = pd.DataFrame({
                "Stage": ["Applied", "Screened", "Interviewed", "Offered", "Hired"],
                "Count": [total, screened_count, interviewed_count, offered_count, hired_count]
            })
            fig_funnel = px.bar(funnel_df, x="Stage", y="Count", color="Count",
                                 color_continuous_scale=["#fed7aa", "#f97316"], text="Count")
            fig_funnel.update_layout(height=340, showlegend=False, coloraxis_showscale=False,
                                      margin=dict(t=20, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font={"color": "#292524"})
            st.plotly_chart(fig_funnel, use_container_width=True)
            st.caption("'Screened' = candidates scoring ≥60% match on at least one posted job. 'Applied' = all processed candidates.")

    with voice_col:
        st.subheader("🎙️ Voice Screening Module")
        st.caption("Recruiter/Admin voice screening: generate a question, let the AI ask it aloud, record the candidate's response in the browser, and review the transcript.")

        if all_candidates.empty or all_jobs.empty:
            st.info("Add at least one candidate and one job posting to use voice screening.")
        else:
            vs_candidate = st.selectbox(
                "Candidate",
                all_candidates["name"].tolist(),
                key="vs_candidate"
            )
            vs_job = st.selectbox(
                "Job",
                all_jobs["title"].tolist(),
                key="vs_job"
            )
            vs_qtype = st.selectbox(
                "Question Type",
                QUESTION_TYPE_OPTIONS,
                format_func=lambda t: QUESTION_TYPE_LABELS.get(t, t.capitalize()),
                key="vs_qtype"
            )
            vs_difficulty = st.selectbox(
                "Difficulty",
                ["Beginner", "Intermediate", "Advanced"],
                index=1,
                key="vs_difficulty"
            )

            if st.button("🎯 Generate Screening Question", key="vs_generate_question", type="primary"):
                vs_job_row = all_jobs[all_jobs["title"] == vs_job].iloc[0].to_dict()
                vs_questions = generate_questions(vs_job_row, vs_qtype, 1, vs_difficulty)

                if vs_questions:
                    st.session_state.voice_screening_question = vs_questions[0]
                    st.session_state.pop("voice_screening_response", None)
                    st.session_state.pop("voice_screening_feedback", None)
                    st.session_state.pop("voice_screening_analysis", None)
                    st.session_state.voice_screening_started = False
                    st.session_state.pop("vs_audio_processed", None)
                    st.rerun()

            if "voice_screening_question" in st.session_state:
                vsq = st.session_state.voice_screening_question
                vs_type = QUESTION_TYPE_LABELS.get(
                    vsq.get("type", "technical"),
                    "Question"
                )

                st.markdown(
                    f"<span class='type-badge'>{vs_type}</span>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='chat-bubble-ai'>🎙️ {vsq['question']}</div>",
                    unsafe_allow_html=True
                )

                if not st.session_state.get("voice_screening_started", False):
                    st.info("Click Start Candidate Voice Screening. The AI will ask the question aloud, then record the candidate's response below.")

                    if st.button("🎤 Start Candidate Voice Screening", key="vs_start_voice", type="primary"):
                        with st.spinner("AI interviewer is asking the question..."):
                            spoken = speak_text(vsq["question"])

                        if not spoken:
                            st.warning(
                                "The AI interviewer could not start text-to-speech. "
                                "You can still read the question above and record the candidate's answer."
                            )

                        st.session_state.voice_screening_started = True
                        st.rerun()
                else:
                    st.success(f"🎤 The AI has asked the question. Record {vs_candidate}'s answer below.")

                    try:
                        vs_audio = st.audio_input(
                            f"Record {vs_candidate}'s response",
                            key="vs_audio"
                        )
                    except AttributeError:
                        vs_audio = None
                        st.error(
                            "Your Streamlit version does not support st.audio_input(). "
                            "Run: python -m pip install --upgrade streamlit"
                        )

                    if vs_audio is not None:
                        st.audio(vs_audio)

                        if st.button("📝 Transcribe Candidate Response", key="vs_transcribe", type="primary"):
                            with st.spinner("Converting the candidate's speech to text..."):
                                result = listen_to_candidate(vs_audio.getvalue())

                            if result["success"]:
                                response = result["text"]
                                st.session_state.voice_screening_response = response
                                st.session_state.voice_screening_analysis = analyze_audio(vs_audio.getvalue())
                                st.session_state.voice_screening_feedback = generate_voice_feedback(response)
                                st.session_state.vs_audio_processed = True
                            else:
                                st.session_state.voice_screening_response = result["text"]
                                st.session_state.voice_screening_feedback = result["text"]
                                st.session_state.pop("voice_screening_analysis", None)
                                st.session_state.vs_audio_processed = False

                            st.rerun()

                    if "voice_screening_response" in st.session_state:
                        response = st.session_state.voice_screening_response

                        st.markdown("**📝 Candidate Transcript**")
                        st.markdown(
                            f"<div class='chat-bubble-candidate'>{response}</div>",
                            unsafe_allow_html=True
                        )

                        if st.session_state.get("vs_audio_processed") and "voice_screening_analysis" in st.session_state:
                            va = st.session_state.voice_screening_analysis
                            vcol1, vcol2 = st.columns(2)
                            with vcol1:
                                st.metric("Duration", f"{va['duration_seconds']}s")
                            with vcol2:
                                st.metric("Volume Score", f"{va['volume_score']}%")

                        if "voice_screening_feedback" in st.session_state:
                            st.markdown("**🤖 Screening Feedback**")
                            st.info(st.session_state.voice_screening_feedback)

                        st.caption(
                            "⚠️ Speech-to-text and automated voice feedback are screening aids. "
                            "Review the transcript and candidate information yourself; do not use automated voice feedback as the sole hiring decision."
                        )

                        if st.session_state.get("vs_audio_processed"):
                            if st.button("🔊 Hear Screening Feedback", key="vs_speak_feedback"):
                                speak_text(st.session_state.voice_screening_feedback)

                            if st.button("✅ Save to ATS as Interview Scheduled", key="vs_save_ats"):
                                cand_row = all_candidates[
                                    all_candidates["name"] == vs_candidate
                                ].iloc[0]

                                add_to_ats(
                                    vs_candidate,
                                    cand_row["email"],
                                    vs_job,
                                    "Interview Scheduled",
                                    username
                                )

                                st.success(
                                    "Candidate moved to 'Interview Scheduled' in ATS."
                                )
                                st.rerun()

                if st.button("🔄 New Screening Question", key="vs_new_question"):
                    for key in [
                        "voice_screening_question",
                        "voice_screening_response",
                        "voice_screening_feedback",
                        "voice_screening_analysis",
                        "voice_screening_started",
                        "vs_audio_processed"
                    ]:
                        st.session_state.pop(key, None)
                    st.rerun()


# =========================================================
# PAGE: Analytics
# =========================================================
elif st.session_state.page == "Analytics":
    page_header("📈", "Analytics", "Extraction and matching performance across your data", role)

    if total == 0:
        st.info("No data yet — process some resumes first.")
    else:
        gauge_col, skills_col = st.columns([1, 1.4])

        with gauge_col:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=accuracy,
                number={"suffix": "%", "font": {"size": 40, "color": "#f97316"}},
                title={"text": "Extraction Accuracy vs 95% Target", "font": {"size": 14, "color": "#292524"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#a8a29e"},
                    "bar": {"color": "#f97316"},
                    "bgcolor": "rgba(0,0,0,0)",
                    "steps": [
                        {"range": [0, 70], "color": "rgba(248,113,113,0.18)"},
                        {"range": [70, 95], "color": "rgba(251,191,36,0.18)"},
                        {"range": [95, 100], "color": "rgba(34,197,94,0.18)"},
                    ],
                    "threshold": {"line": {"color": "#0d9488", "width": 4}, "thickness": 0.8, "value": 95},
                },
            ))
            fig_gauge.update_layout(height=280, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#292524"})
            st.plotly_chart(fig_gauge, use_container_width=True)

        with skills_col:
            all_skills = []
            for skills_list in all_candidates["skills"]:
                all_skills.extend(skills_list)

            if all_skills:
                skill_counts = Counter(all_skills).most_common(8)
                df_skills = pd.DataFrame(skill_counts, columns=["Skill", "Candidates"]).sort_values("Candidates")

                fig_skills = px.bar(
                    df_skills, x="Candidates", y="Skill", orientation="h",
                    color="Candidates", color_continuous_scale=["#fed7aa", "#f97316", "#c2410c"],
                    text="Candidates", title="Top Skills Across All Candidates"
                )
                fig_skills.update_traces(textposition="outside")
                fig_skills.update_layout(height=280, showlegend=False, coloraxis_showscale=False,
                                          margin=dict(t=50, b=10, l=10, r=30), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                          font={"color": "#292524"})
                st.plotly_chart(fig_skills, use_container_width=True)
            else:
                st.info("No skills extracted yet.")

        st.markdown("---")
        st.subheader("🎯 Matching Algorithm Accuracy")
        st.caption("Validated against hand-crafted test cases with known expected outcomes")

        match_accuracy, match_test_rows = cached_matching_accuracy()

        match_gauge_col, match_table_col = st.columns([1, 1.4])

        with match_gauge_col:
            fig_match_acc = go.Figure(go.Indicator(
                mode="gauge+number",
                value=match_accuracy,
                number={"suffix": "%", "font": {"size": 40, "color": "#f97316"}},
                title={"text": "Matching Accuracy vs 85% Target", "font": {"size": 14, "color": "#292524"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#a8a29e"},
                    "bar": {"color": "#f97316"},
                    "bgcolor": "rgba(0,0,0,0)",
                    "steps": [
                        {"range": [0, 60], "color": "rgba(248,113,113,0.18)"},
                        {"range": [60, 85], "color": "rgba(251,191,36,0.18)"},
                        {"range": [85, 100], "color": "rgba(34,197,94,0.18)"},
                    ],
                    "threshold": {"line": {"color": "#0d9488", "width": 4}, "thickness": 0.8, "value": 85},
                },
            ))
            fig_match_acc.update_layout(height=280, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#292524"})
            st.plotly_chart(fig_match_acc, use_container_width=True)

        with match_table_col:
            match_df = pd.DataFrame(match_test_rows)
            table_html = "<table style='width:100%; border-collapse: collapse; font-size:13px;'>"
            table_html += "<tr style='text-align:left; border-bottom: 2px solid rgba(41,37,36,0.12);'>"
            for col in match_df.columns:
                table_html += f"<th style='padding:6px;'>{col}</th>"
            table_html += "</tr>"
            for _, row in match_df.iterrows():
                table_html += "<tr style='border-bottom: 1px solid rgba(41,37,36,0.06);'>"
                for val in row:
                    table_html += f"<td style='padding:6px;'>{val}</td>"
                table_html += "</tr>"
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)

        radar_col, donut_col = st.columns([1.4, 1])

        with radar_col:
            field_rates = []
            for f in FIELDS:
                count = sum(1 for v in all_candidates[f] if v and (not isinstance(v, list) or len(v) > 0))
                field_rates.append(round((count / total) * 100, 1))

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=field_rates + [field_rates[0]],
                theta=[f.capitalize() for f in FIELDS] + [FIELDS[0].capitalize()],
                fill="toself",
                fillcolor="rgba(249, 115, 22, 0.2)",
                line=dict(color="#f97316", width=2),
                name="Extraction rate"
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100], color="#a8a29e"),
                           angularaxis=dict(color="#292524"),
                           bgcolor="rgba(0,0,0,0)"),
                title="Field Extraction Coverage (%)",
                height=320, margin=dict(t=50, b=10, l=40, r=40), paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "#292524"}
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with donut_col:
            has_cert = sum(1 for c in all_candidates["certifications"] if c and len(c) > 0)
            no_cert = total - has_cert

            fig_donut = go.Figure(go.Pie(
                labels=["Has certifications", "No certifications"],
                values=[has_cert, no_cert],
                hole=0.55,
                marker=dict(colors=["#0d9488", "rgba(41,37,36,0.08)"]),
                textinfo="percent+label"
            ))
            fig_donut.update_layout(title="Certification Coverage", height=320,
                                     showlegend=False, margin=dict(t=50, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)",
                                     font={"color": "#292524"})
            st.plotly_chart(fig_donut, use_container_width=True)

        if "created_at" in all_candidates.columns:
            dates = pd.to_datetime(all_candidates["created_at"]).dt.date
            daily_counts = dates.value_counts().sort_index().reset_index()
            daily_counts.columns = ["Date", "Resumes"]
            daily_counts["Cumulative"] = daily_counts["Resumes"].cumsum()

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=daily_counts["Date"].astype(str), y=daily_counts["Cumulative"],
                fill="tozeroy", mode="lines+markers",
                line=dict(color="#0d9488", width=3),
                fillcolor="rgba(13, 148, 136, 0.15)",
                name="Total resumes processed"
            ))
            fig_trend.update_layout(title="Cumulative Resumes Processed Over Time",
                                     height=280, margin=dict(t=50, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                     font={"color": "#292524"})
            st.plotly_chart(fig_trend, use_container_width=True)

# =========================================================
# PAGE: Manage Users (Admin only)
# =========================================================
elif st.session_state.page == "Manage Users":
    page_header("🛡️", "Manage Users", "All registered accounts on the platform", role)

    users = get_all_users()
    if not users:
        st.info("No users found.")
    else:
        users_df = pd.DataFrame(users)
        users_df.columns = ["Username", "Role"]

        table_html = "<table style='width:100%; border-collapse: collapse;'>"
        table_html += "<tr style='text-align:left; border-bottom: 2px solid rgba(41,37,36,0.12);'>"
        for col in users_df.columns:
            table_html += f"<th style='padding:8px;'>{col}</th>"
        table_html += "</tr>"
        for _, row in users_df.iterrows():
            table_html += "<tr style='border-bottom: 1px solid rgba(41,37,36,0.06);'>"
            for val in row:
                table_html += f"<td style='padding:8px;'>{val}</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        role_counts = users_df["Role"].value_counts()
        st.markdown("---")
        st.subheader("User Breakdown")
        fig_users = px.pie(values=role_counts.values, names=role_counts.index, hole=0.5,
                            color_discrete_sequence=["#f97316", "#0d9488", "#a78bfa"])
        fig_users.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", font={"color": "#292524"})
        st.plotly_chart(fig_users, use_container_width=True)