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
from database import init_db, insert_candidate, get_all_candidates, clear_all_candidates, insert_job, get_all_jobs, delete_job, add_to_ats, get_ats_status
from jd_extractor import analyze_job_description
from matching_engine import match_all_candidates, calculate_match, skill_gap_analysis
from matching_accuracy_check import get_accuracy_results
from interview_generator import generate_questions
from interview_simulation import start_interview, get_opening_message, submit_answer, get_current_question
from parser.pdf_reader import extract_text_from_pdf
from parser.docx_reader import extract_text_from_docx

st.set_page_config(page_title="Recruitment Copilot", layout="wide", page_icon="📄")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #faf9ff 0%, #f7f5ff 100%);
}
.block-container {
    padding-top: 2.2rem;
}
.skill-badge {
    display: inline-block;
    background-color: #ede9fe;
    color: #5b21b6;
    padding: 4px 10px;
    border-radius: 12px;
    margin: 3px 3px 3px 0;
    font-size: 13px;
    font-weight: 500;
}
.metric-box {
    background: #ffffff;
    border-radius: 14px;
    padding: 18px 20px;
    text-align: center;
    border: 1px solid #ece8ff;
    box-shadow: 0 2px 8px rgba(124, 58, 237, 0.06);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.metric-box:hover {
    box-shadow: 0 6px 18px rgba(124, 58, 237, 0.14);
    transform: translateY(-2px);
}
.metric-label {
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 4px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.logo-badge {
    display: inline-block;
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    color: white;
    font-weight: 700;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 14px;
}
.profile-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 26px;
    border: 1px solid #ece8ff;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.08);
    transition: box-shadow 0.2s ease;
}
.profile-card:hover {
    box-shadow: 0 8px 24px rgba(124, 58, 237, 0.14);
}
.avatar-circle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    color: white;
    font-weight: 700;
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
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    color: white;
    font-weight: 700;
    font-size: 19px;
    margin: 0 auto 10px auto;
}
.page-header {
    background: linear-gradient(120deg, #ffffff 0%, #f5f2ff 100%);
    border: 1px solid #ece8ff;
    border-radius: 18px;
    padding: 22px 28px;
    margin-bottom: 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 3px 12px rgba(124, 58, 237, 0.07);
}
.page-header-icon {
    font-size: 30px;
    margin-right: 14px;
}
.page-header-title {
    font-size: 24px;
    font-weight: 800;
    color: #1f2937;
    margin: 0;
}
.page-header-subtitle {
    font-size: 13px;
    color: #6b7280;
    margin-top: 2px;
}
.role-pill {
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    color: white;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.02em;
    white-space: nowrap;
}
.leaderboard-rank {
    font-size: 20px;
    margin-right: 8px;
}
.chat-bubble-ai {
    background: #f3f0ff;
    border-radius: 14px 14px 14px 2px;
    padding: 10px 16px;
    margin-bottom: 8px;
    font-size: 14px;
    max-width: 90%;
}
.chat-bubble-candidate {
    background: #ede9fe;
    border-radius: 14px 14px 2px 14px;
    padding: 10px 16px;
    margin-bottom: 4px;
    font-size: 14px;
    max-width: 90%;
    margin-left: auto;
    text-align: right;
}
.relevance-tag-yes {
    color: #16a34a;
    font-size: 12px;
    text-align: right;
    margin-bottom: 14px;
    background: #f0fdf4;
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
    background: #fffbeb;
    padding: 6px 10px;
    border-radius: 8px;
    max-width: 90%;
    margin-left: auto;
}
.status-pill-Applied { background:#e0e7ff; color:#3730a3; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600; }
.status-pill-Interview_Scheduled { background:#fef9c3; color:#854d0e; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600; }
.status-pill-Interview_Completed { background:#dbeafe; color:#1e40af; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600; }
.status-pill-Offer_Extended { background:#dcfce7; color:#166534; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600; }
.status-pill-Rejected { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600; }

/* Global: every bordered container gets the premium card look */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px !important;
    border: 1px solid #ece8ff !important;
    box-shadow: 0 4px 16px rgba(124, 58, 237, 0.08) !important;
}

/* Login page */
.login-hero {
    background: linear-gradient(150deg, #7c3aed 0%, #a855f7 55%, #ec4899 100%);
    border-radius: 24px;
    padding: 46px 40px;
    color: white;
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 100%;
}
.login-hero-logo {
    background: rgba(255,255,255,0.18);
    width: 54px; height: 54px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 19px;
    margin-bottom: 26px;
}
.login-hero h1 { font-size: 30px; font-weight: 800; line-height: 1.25; margin-bottom: 12px; }
.login-hero p.tagline { font-size: 14.5px; opacity: 0.9; margin-bottom: 30px; line-height: 1.5; }
.login-feature { display: flex; align-items: flex-start; margin-bottom: 18px; }
.login-feature-icon {
    background: rgba(255,255,255,0.18);
    width: 34px; height: 34px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; margin-right: 13px; flex-shrink: 0;
}
.login-feature-title { font-weight: 700; font-size: 13.5px; margin-bottom: 2px; }
.login-feature-desc { font-size: 12px; opacity: 0.85; line-height: 1.4; }
.login-stat-row { display: flex; gap: 26px; margin-top: 30px; padding-top: 22px; border-top: 1px solid rgba(255,255,255,0.25); }
.login-stat-num { font-size: 19px; font-weight: 800; }
.login-stat-label { font-size: 11px; opacity: 0.8; }

/* Inputs */
div[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    border: 1.5px solid #e6e1ff !important;
    padding: 11px 14px !important;
    background: #faf9ff !important;
    font-size: 14px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.13) !important;
}

/* Primary buttons */
button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #ec4899) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 0.6rem 1rem !important;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.25) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.35) !important;
}
</style>
""", unsafe_allow_html=True)

init_db()

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
                    <div class="login-feature-title">Interview Assistant</div>
                    <div class="login-feature-desc">Generate role-specific questions and simulate interviews with ATS tracking.</div>
                </div>
            </div>
            <div class="login-stat-row">
                <div><div class="login-stat-num">100%</div><div class="login-stat-label">Extraction Accuracy</div></div>
                <div><div class="login-stat-num">≥85%</div><div class="login-stat-label">Match Accuracy</div></div>
                <div><div class="login-stat-num">3</div><div class="login-stat-label">User Roles</div></div>
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
    NAV_ITEMS = NAV_ITEMS + ["Interview Assistant"]
    NAV_ICONS["Interview Assistant"] = "🎙️"

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
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    st.markdown("---")
    st.caption("Recruitment Copilot · v3.0")

all_candidates = get_all_candidates()
my_candidates = all_candidates[all_candidates["uploaded_by"] == username] if not all_candidates.empty else all_candidates
total = len(all_candidates)
accuracy = run_accuracy_check() if total > 0 else 0
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
                    number={"suffix": "%", "font": {"size": 32, "color": "#7c3aed"}},
                    title={"text": "Profile Completeness", "font": {"size": 14}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#7c3aed"},
                        "steps": [
                            {"range": [0, 60], "color": "#fee2e2"},
                            {"range": [60, 90], "color": "#fef9c3"},
                            {"range": [90, 100], "color": "#dcfce7"},
                        ],
                    },
                ))
                fig.update_layout(height=260, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)")
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
        page_header("📊", f"{get_greeting()}, {username}", "Recruitment pipeline overview", role)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Total Candidates</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Open Job Postings</div><div class="metric-value">{len(all_jobs)}</div></div>', unsafe_allow_html=True)
        with m3:
            top_skill = "—"
            if total > 0:
                all_skills = [s for skills in all_candidates["skills"] for s in skills]
                if all_skills:
                    top_skill = Counter(all_skills).most_common(1)[0][0]
            st.markdown(f'<div class="metric-box"><div class="metric-label">Most Common Skill</div><div class="metric-value" style="font-size:20px;">{top_skill}</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-box"><div class="metric-label">Extraction Accuracy</div><div class="metric-value">{accuracy}%</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        if all_jobs.empty:
            st.info("No job postings yet — add one from the Job Postings page.")
        elif all_candidates.empty:
            st.info("No candidates in the pool yet.")
        else:
            rows = []
            best_overall = []
            for _, job in all_jobs.iterrows():
                job_results = match_all_candidates(all_candidates, job.to_dict())
                strong_matches = sum(1 for r in job_results if r["hiring_score"] >= 85)
                avg_score = round(sum(r["hiring_score"] for r in job_results) / len(job_results), 1) if job_results else 0
                rows.append({"Job Title": job["title"], "Candidates Evaluated": len(job_results),
                             "Strong Matches (≥85%)": strong_matches, "Avg Match Score": f"{avg_score}%"})
                if job_results:
                    top = job_results[0]
                    best_overall.append({"name": top["name"], "score": top["hiring_score"], "job_title": job["title"]})

            best_overall.sort(key=lambda x: x["score"], reverse=True)

            chart_col, leaderboard_col = st.columns([1.6, 1])

            with chart_col:
                st.subheader("📋 Strong Match Count by Job")
                summary_df = pd.DataFrame(rows)
                fig_pipeline = px.bar(summary_df, x="Job Title", y="Strong Matches (≥85%)",
                                       color="Strong Matches (≥85%)", color_continuous_scale=["#ddd6fe", "#7c3aed"],
                                       text="Strong Matches (≥85%)")
                fig_pipeline.update_layout(height=340, showlegend=False, coloraxis_showscale=False,
                                            margin=dict(t=20, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_pipeline, use_container_width=True)

                table_html = "<table style='width:100%; border-collapse: collapse;'>"
                table_html += "<tr style='text-align:left; border-bottom: 2px solid #ece8ff;'>"
                for col in summary_df.columns:
                    table_html += f"<th style='padding:8px;'>{col}</th>"
                table_html += "</tr>"
                for _, row in summary_df.iterrows():
                    table_html += "<tr style='border-bottom: 1px solid #f0edff;'>"
                    for val in row:
                        table_html += f"<td style='padding:8px;'>{val}</td>"
                    table_html += "</tr>"
                table_html += "</table>"
                st.markdown(table_html, unsafe_allow_html=True)

            with leaderboard_col:
                st.subheader("🏆 Top Matches Overall")
                if best_overall:
                    medals = ["🥇", "🥈", "🥉"]
                    for i, entry in enumerate(best_overall[:3]):
                        with st.container(border=True):
                            st.markdown(f"<span class='leaderboard-rank'>{medals[i]}</span> **{entry['name']}**", unsafe_allow_html=True)
                            st.caption(f"Best fit for: {entry['job_title']}")
                            st.markdown(f"<span style='color:#22c55e; font-weight:800; font-size:20px;'>{entry['score']}%</span>", unsafe_allow_html=True)
                else:
                    st.info("No matches computed yet.")

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
                            st.markdown(f"<p style='text-align:center; font-size:12px; color:#6b7280; margin-bottom:10px;'>{cand['email']}</p>", unsafe_allow_html=True)
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
        page_header("💼", "Job Postings", "Paste a job description, or upload a JD file, to check your match", role)

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

                        color = "#22c55e" if score >= 85 else "#f59e0b" if score >= 60 else "#ef4444"
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
                        number={"suffix": "%", "font": {"size": 36, "color": "#7c3aed"}},
                        title={"text": f"% of Candidates ≥85% Match — {selected_title}", "font": {"size": 14}},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#7c3aed"},
                            "steps": [
                                {"range": [0, 50], "color": "#fee2e2"},
                                {"range": [50, 85], "color": "#fef9c3"},
                                {"range": [85, 100], "color": "#dcfce7"},
                            ],
                            "threshold": {"line": {"color": "#ec4899", "width": 4}, "thickness": 0.8, "value": 85},
                        },
                    ))
                    fig_match_gauge.update_layout(height=260, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)")
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
                            color="Candidates Missing It", color_continuous_scale=["#fed7aa", "#f59e0b", "#ea580c"],
                            text="Candidates Missing It", title=f"Most Common Skill Gaps — {selected_title}"
                        )
                        fig_missing.update_traces(textposition="outside")
                        fig_missing.update_layout(height=280, showlegend=False, coloraxis_showscale=False,
                                                   margin=dict(t=50, b=10, l=10, r=30), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_missing, use_container_width=True)

                        table_html = "<table style='width:100%; border-collapse: collapse;'>"
                        table_html += "<tr style='text-align:left; border-bottom: 2px solid #ece8ff;'>"
                        for col in report_df.columns:
                            table_html += f"<th style='padding:8px;'>{col}</th>"
                        table_html += "</tr>"
                        for _, row in report_df.iterrows():
                            table_html += "<tr style='border-bottom: 1px solid #f0edff;'>"
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
                        color = "#22c55e" if score >= 85 else "#f59e0b" if score >= 60 else "#ef4444"
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
                                st.markdown(f"<div style='text-align:center;'><span style='font-size:32px; font-weight:800; color:{color}'>{score}%</span><br><span style='font-size:12px; color:#6b7280;'>Match Score</span></div>", unsafe_allow_html=True)

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
                q_type = st.selectbox("Question Type", ["technical", "behavioral"], key="gen_qtype")
                gen_difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], index=1, key="gen_difficulty")
                num_q = st.slider("Number of questions", 1, 5, 3, key="gen_numq")

                if st.button("🔄 Generate Questions", type="primary"):
                    gen_job = all_jobs[all_jobs["title"] == gen_job_title].iloc[0].to_dict()
                    st.session_state.generated_questions = generate_questions(gen_job, q_type, num_q, gen_difficulty)

                if "generated_questions" in st.session_state:
                    for i, q in enumerate(st.session_state.generated_questions, start=1):
                        st.markdown(f"**{i}.** {q['question']}")

    with sim_col:
        with st.container(border=True):
            st.subheader("🎤 AI Interview Simulation")

            if all_candidates.empty or all_jobs.empty:
                st.info("Need at least one candidate and one job posting to start a simulation.")
            else:
                sim_candidate_name = st.selectbox("Candidate", all_candidates["name"].tolist(), key="sim_candidate")
                sim_job_title = st.selectbox("Job Position", all_jobs["title"].tolist(), key="sim_job")
                sim_difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"], index=1, key="sim_difficulty")

                if st.button("▶️ Start Interview"):
                    sim_job = all_jobs[all_jobs["title"] == sim_job_title].iloc[0].to_dict()
                    st.session_state.interview_session = start_interview(sim_candidate_name, sim_job, difficulty=sim_difficulty)
                    st.session_state.interview_started = True

                if st.session_state.get("interview_started") and "interview_session" in st.session_state:
                    session = st.session_state.interview_session

                    st.markdown(f"<div class='chat-bubble-ai'>{get_opening_message(session['candidate_name'], session['job_title'])}</div>", unsafe_allow_html=True)

                    for turn in session["transcript"]:
                        st.markdown(f"<div class='chat-bubble-ai'>{turn['question']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='chat-bubble-candidate'>{turn['answer']}</div>", unsafe_allow_html=True)
                        tag_class = "relevance-tag-yes" if turn.get("mentions_skill") else "relevance-tag-no"
                        feedback_text = turn.get("feedback", "")
                        st.markdown(f"<div class='{tag_class}'>🤖 {feedback_text}</div>", unsafe_allow_html=True)

                    current_q = get_current_question(session)
                    if current_q:
                        st.markdown(f"<div class='chat-bubble-ai'>{current_q}</div>", unsafe_allow_html=True)
                        answer = st.text_area("Type response...", key=f"answer_{session['current_index']}", label_visibility="collapsed")
                        if st.button("➤ Send", key=f"send_{session['current_index']}", type="primary"):
                            if answer.strip():
                                st.session_state.interview_session = submit_answer(session, answer.strip())
                                st.rerun()
                            else:
                                st.warning("Please type a response before sending.")
                    else:
                        st.success("Interview completed. Candidate responses stored for ATS review.")

                        transcript_df = pd.DataFrame(session["transcript"])
                        if "feedback" in transcript_df.columns:
                            transcript_df = transcript_df[["question", "skill", "answer", "mentions_skill", "feedback"]]
                            transcript_df.columns = ["Question", "Skill Tested", "Answer", "Relevant", "AI Feedback"]
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
                ats_new_status = st.selectbox("Status", ["Applied", "Interview Scheduled", "Interview Completed", "Offer Extended", "Rejected"], key="ats_status_select")
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
                number={"suffix": "%", "font": {"size": 40, "color": "#7c3aed"}},
                title={"text": "Extraction Accuracy vs 95% Target", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#7c3aed"},
                    "steps": [
                        {"range": [0, 70], "color": "#fee2e2"},
                        {"range": [70, 95], "color": "#fef9c3"},
                        {"range": [95, 100], "color": "#dcfce7"},
                    ],
                    "threshold": {"line": {"color": "#ec4899", "width": 4}, "thickness": 0.8, "value": 95},
                },
            ))
            fig_gauge.update_layout(height=280, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)")
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
                    color="Candidates", color_continuous_scale=["#ddd6fe", "#7c3aed", "#4c1d95"],
                    text="Candidates", title="Top Skills Across All Candidates"
                )
                fig_skills.update_traces(textposition="outside")
                fig_skills.update_layout(height=280, showlegend=False, coloraxis_showscale=False,
                                          margin=dict(t=50, b=10, l=10, r=30), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_skills, use_container_width=True)
            else:
                st.info("No skills extracted yet.")

        st.markdown("---")
        st.subheader("🎯 Matching Algorithm Accuracy")
        st.caption("Validated against hand-crafted test cases with known expected outcomes")

        match_accuracy, match_test_rows = get_accuracy_results()

        match_gauge_col, match_table_col = st.columns([1, 1.4])

        with match_gauge_col:
            fig_match_acc = go.Figure(go.Indicator(
                mode="gauge+number",
                value=match_accuracy,
                number={"suffix": "%", "font": {"size": 40, "color": "#7c3aed"}},
                title={"text": "Matching Accuracy vs 85% Target", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#7c3aed"},
                    "steps": [
                        {"range": [0, 60], "color": "#fee2e2"},
                        {"range": [60, 85], "color": "#fef9c3"},
                        {"range": [85, 100], "color": "#dcfce7"},
                    ],
                    "threshold": {"line": {"color": "#ec4899", "width": 4}, "thickness": 0.8, "value": 85},
                },
            ))
            fig_match_acc.update_layout(height=280, margin=dict(t=50, b=10, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_match_acc, use_container_width=True)

        with match_table_col:
            match_df = pd.DataFrame(match_test_rows)
            table_html = "<table style='width:100%; border-collapse: collapse; font-size:13px;'>"
            table_html += "<tr style='text-align:left; border-bottom: 2px solid #ece8ff;'>"
            for col in match_df.columns:
                table_html += f"<th style='padding:6px;'>{col}</th>"
            table_html += "</tr>"
            for _, row in match_df.iterrows():
                table_html += "<tr style='border-bottom: 1px solid #f0edff;'>"
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
                fillcolor="rgba(124, 58, 237, 0.25)",
                line=dict(color="#7c3aed", width=2),
                name="Extraction rate"
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                title="Field Extraction Coverage (%)",
                height=320, margin=dict(t=50, b=10, l=40, r=40), paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with donut_col:
            has_cert = sum(1 for c in all_candidates["certifications"] if c and len(c) > 0)
            no_cert = total - has_cert

            fig_donut = go.Figure(go.Pie(
                labels=["Has certifications", "No certifications"],
                values=[has_cert, no_cert],
                hole=0.55,
                marker=dict(colors=["#a78bfa", "#f3f0ff"]),
                textinfo="percent+label"
            ))
            fig_donut.update_layout(title="Certification Coverage", height=320,
                                     showlegend=False, margin=dict(t=50, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
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
                line=dict(color="#ec4899", width=3),
                fillcolor="rgba(236, 72, 153, 0.15)",
                name="Total resumes processed"
            ))
            fig_trend.update_layout(title="Cumulative Resumes Processed Over Time",
                                     height=280, margin=dict(t=50, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
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
        table_html += "<tr style='text-align:left; border-bottom: 2px solid #ece8ff;'>"
        for col in users_df.columns:
            table_html += f"<th style='padding:8px;'>{col}</th>"
        table_html += "</tr>"
        for _, row in users_df.iterrows():
            table_html += "<tr style='border-bottom: 1px solid #f0edff;'>"
            for val in row:
                table_html += f"<td style='padding:8px;'>{val}</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        role_counts = users_df["Role"].value_counts()
        st.markdown("---")
        st.subheader("User Breakdown")
        fig_users = px.pie(values=role_counts.values, names=role_counts.index, hole=0.5,
                            color_discrete_sequence=["#7c3aed", "#a78bfa", "#ec4899"])
        fig_users.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_users, use_container_width=True)