import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
from app import process_resume
from accuracy_check import run_accuracy_check
from auth import signup_user, login_user, get_all_users
from database import init_db, insert_candidate, get_all_candidates, clear_all_candidates, insert_job, get_all_jobs, delete_job
from jd_extractor import analyze_job_description
from matching_engine import match_all_candidates, calculate_match, skill_gap_analysis
from matching_accuracy_check import get_accuracy_results
from parser.pdf_reader import extract_text_from_pdf
from parser.docx_reader import extract_text_from_docx

st.set_page_config(page_title="Recruitment Copilot", layout="wide", page_icon="📄")

st.markdown("""
<style>
.skill-badge {
    display: inline-block;
    background-color: #e8f0fe;
    color: #1a56db;
    padding: 4px 10px;
    border-radius: 12px;
    margin: 3px 3px 3px 0;
    font-size: 13px;
    font-weight: 500;
}
.metric-box {
    background: linear-gradient(135deg, #f5f3ff, #fdf2f8);
    border-radius: 12px;
    padding: 16px 18px;
    text-align: center;
    border: 1px solid #ede9fe;
}
.metric-label {
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.logo-badge {
    display: inline-block;
    background: linear-gradient(135deg, #6366f1, #ec4899);
    color: white;
    font-weight: 700;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 14px;
}
.profile-card {
    background: linear-gradient(135deg, #f5f3ff, #fdf2f8);
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #ede9fe;
}
.avatar-circle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #ec4899);
    color: white;
    font-weight: 700;
    font-size: 14px;
    margin-right: 10px;
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
    st.title("🔐 Recruitment Copilot")
    st.caption("Please log in or create an account to continue")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In")

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
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            role = st.radio("I am a:", ["Student", "Recruiter", "Admin"], horizontal=True)
            signup_submitted = st.form_submit_button("Sign Up")

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
        st.title("👋 My Dashboard")
        st.caption(f"Welcome back, {username}")
        st.markdown("---")

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
                    number={"suffix": "%", "font": {"size": 32, "color": "#6366f1"}},
                    title={"text": "Profile Completeness", "font": {"size": 14}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#6366f1"},
                        "steps": [
                            {"range": [0, 60], "color": "#fee2e2"},
                            {"range": [60, 90], "color": "#fef9c3"},
                            {"range": [90, 100], "color": "#dcfce7"},
                        ],
                    },
                ))
                fig.update_layout(height=260, margin=dict(t=50, b=10, l=20, r=20))
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
        st.title("📊 Recruiter Dashboard" if role == "Recruiter" else "📊 Admin Dashboard")
        st.caption("Recruitment pipeline overview")
        st.markdown("---")

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
        st.subheader("📋 Job Postings — Strong Match Count")

        if all_jobs.empty:
            st.info("No job postings yet — add one from the Job Postings page.")
        elif all_candidates.empty:
            st.info("No candidates in the pool yet.")
        else:
            rows = []
            for _, job in all_jobs.iterrows():
                results = match_all_candidates(all_candidates, job.to_dict())
                strong_matches = sum(1 for r in results if r["hiring_score"] >= 85)
                avg_score = round(sum(r["hiring_score"] for r in results) / len(results), 1) if results else 0
                rows.append({"Job Title": job["title"], "Candidates Evaluated": len(results),
                             "Strong Matches (≥85%)": strong_matches, "Avg Match Score": f"{avg_score}%"})

            summary_df = pd.DataFrame(rows)
            fig_pipeline = px.bar(summary_df, x="Job Title", y="Strong Matches (≥85%)",
                                   color="Strong Matches (≥85%)", color_continuous_scale=["#c7d2fe", "#6366f1"],
                                   text="Strong Matches (≥85%)")
            fig_pipeline.update_layout(height=300, showlegend=False, coloraxis_showscale=False,
                                        margin=dict(t=20, b=10, l=10, r=10))
            st.plotly_chart(fig_pipeline, use_container_width=True)

            table_html = "<table style='width:100%; border-collapse: collapse;'>"
            table_html += "<tr style='text-align:left; border-bottom: 2px solid #ddd;'>"
            for col in summary_df.columns:
                table_html += f"<th style='padding:8px;'>{col}</th>"
            table_html += "</tr>"
            for _, row in summary_df.iterrows():
                table_html += "<tr style='border-bottom: 1px solid #eee;'>"
                for val in row:
                    table_html += f"<td style='padding:8px;'>{val}</td>"
                table_html += "</tr>"
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)

# =========================================================
# PAGE: Resume Upload
# =========================================================
elif st.session_state.page == "Resume Upload":
    st.title("📄 Resume Parsing & Candidate Profiling")
    if role == "Student":
        st.caption("Upload your resume to create your structured profile")
    else:
        st.caption("Upload candidate resumes on their behalf to add them to the candidate pool")
    st.markdown("---")

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
        st.title("👤 My Profile")
        st.caption("This is the structured profile generated from your uploaded resume")
        st.markdown("---")

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
        st.title("👥 Candidate Pool")
        st.caption("All candidates processed across the platform")
        st.markdown("---")

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

            st.caption(f"Showing {len(filtered)} of {len(all_candidates)} candidates — click a candidate to expand their full profile")

            for _, cand in filtered.iterrows():
                initials = get_initials(cand["name"])
                header = f"{cand['name']}  —  {cand['email']}"
                with st.expander(header):
                    st.markdown(
                        f'<span class="avatar-circle">{initials}</span> **{cand["name"]}**',
                        unsafe_allow_html=True
                    )
                    render_full_profile(cand)

# =========================================================
# PAGE: Job Postings
# =========================================================
elif st.session_state.page == "Job Postings":
    st.title("💼 Job Postings")

    if role == "Student":
        st.caption("Paste a job description, or upload a JD file, to see how well your latest resume matches")
        st.markdown("---")

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
        st.caption("Post a job requirement (paste text or upload a file) and rank all candidates against it")
        st.markdown("---")

        with st.container(border=True):
            st.subheader("➕ Post a New Job")
            job_title_input = st.text_input("Job Title", placeholder="e.g. Software Development Intern")
            jd_text = st.text_area("Paste job description", height=150)
            jd_file = st.file_uploader("Or upload a JD file (PDF/DOCX)", type=["pdf", "docx"], key="jd_file_recruiter")

            final_jd_text = jd_text
            if jd_file is not None:
                extracted = extract_jd_text_from_file(jd_file)
                if extracted.strip():
                    final_jd_text = extracted
                    st.caption(f"📄 Using text extracted from {jd_file.name}")

            if st.button("🔍 Analyze & Save Job"):
                if final_jd_text.strip() and job_title_input.strip():
                    job = analyze_job_description(final_jd_text)
                    job["title"] = job_title_input.strip()
                    insert_job(job, username)
                    st.success(f"Job \"{job['title']}\" saved — {len(job['required_skills'])} required skills detected")
                    st.rerun()
                else:
                    st.error("Please enter a job title and paste or upload a job description")

        st.markdown("---")
        st.subheader("📋 Saved Job Postings")

        if all_jobs.empty:
            st.info("No jobs posted yet — add one above.")
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
                    number={"suffix": "%", "font": {"size": 36, "color": "#6366f1"}},
                    title={"text": f"% of Candidates ≥85% Match — {selected_title}", "font": {"size": 14}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#6366f1"},
                        "steps": [
                            {"range": [0, 50], "color": "#fee2e2"},
                            {"range": [50, 85], "color": "#fef9c3"},
                            {"range": [85, 100], "color": "#dcfce7"},
                        ],
                        "threshold": {"line": {"color": "#ec4899", "width": 4}, "thickness": 0.8, "value": 85},
                    },
                ))
                fig_match_gauge.update_layout(height=260, margin=dict(t=50, b=10, l=20, r=20))
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
                                               margin=dict(t=50, b=10, l=10, r=30))
                    st.plotly_chart(fig_missing, use_container_width=True)

                    table_html = "<table style='width:100%; border-collapse: collapse;'>"
                    table_html += "<tr style='text-align:left; border-bottom: 2px solid #ddd;'>"
                    for col in report_df.columns:
                        table_html += f"<th style='padding:8px;'>{col}</th>"
                    table_html += "</tr>"
                    for _, row in report_df.iterrows():
                        table_html += "<tr style='border-bottom: 1px solid #eee;'>"
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
# PAGE: Analytics
# =========================================================
elif st.session_state.page == "Analytics":
    st.title("📈 Analytics")
    st.markdown("---")

    if total == 0:
        st.info("No data yet — process some resumes first.")
    else:
        gauge_col, skills_col = st.columns([1, 1.4])

        with gauge_col:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=accuracy,
                number={"suffix": "%", "font": {"size": 40, "color": "#6366f1"}},
                title={"text": "Extraction Accuracy vs 95% Target", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#6366f1"},
                    "steps": [
                        {"range": [0, 70], "color": "#fee2e2"},
                        {"range": [70, 95], "color": "#fef9c3"},
                        {"range": [95, 100], "color": "#dcfce7"},
                    ],
                    "threshold": {"line": {"color": "#ec4899", "width": 4}, "thickness": 0.8, "value": 95},
                },
            ))
            fig_gauge.update_layout(height=280, margin=dict(t=50, b=10, l=20, r=20))
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
                    color="Candidates", color_continuous_scale=["#c7d2fe", "#6366f1", "#4338ca"],
                    text="Candidates", title="Top Skills Across All Candidates"
                )
                fig_skills.update_traces(textposition="outside")
                fig_skills.update_layout(height=280, showlegend=False, coloraxis_showscale=False,
                                          margin=dict(t=50, b=10, l=10, r=30))
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
                number={"suffix": "%", "font": {"size": 40, "color": "#6366f1"}},
                title={"text": "Matching Accuracy vs 85% Target", "font": {"size": 14}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#6366f1"},
                    "steps": [
                        {"range": [0, 60], "color": "#fee2e2"},
                        {"range": [60, 85], "color": "#fef9c3"},
                        {"range": [85, 100], "color": "#dcfce7"},
                    ],
                    "threshold": {"line": {"color": "#ec4899", "width": 4}, "thickness": 0.8, "value": 85},
                },
            ))
            fig_match_acc.update_layout(height=280, margin=dict(t=50, b=10, l=20, r=20))
            st.plotly_chart(fig_match_acc, use_container_width=True)

        with match_table_col:
            match_df = pd.DataFrame(match_test_rows)
            table_html = "<table style='width:100%; border-collapse: collapse; font-size:13px;'>"
            table_html += "<tr style='text-align:left; border-bottom: 2px solid #ddd;'>"
            for col in match_df.columns:
                table_html += f"<th style='padding:6px;'>{col}</th>"
            table_html += "</tr>"
            for _, row in match_df.iterrows():
                table_html += "<tr style='border-bottom: 1px solid #eee;'>"
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
                fillcolor="rgba(99, 102, 241, 0.3)",
                line=dict(color="#6366f1", width=2),
                name="Extraction rate"
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                title="Field Extraction Coverage (%)",
                height=320, margin=dict(t=50, b=10, l=40, r=40)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with donut_col:
            has_cert = sum(1 for c in all_candidates["certifications"] if c and len(c) > 0)
            no_cert = total - has_cert

            fig_donut = go.Figure(go.Pie(
                labels=["Has certifications", "No certifications"],
                values=[has_cert, no_cert],
                hole=0.55,
                marker=dict(colors=["#8b5cf6", "#f3f4f6"]),
                textinfo="percent+label"
            ))
            fig_donut.update_layout(title="Certification Coverage", height=320,
                                     showlegend=False, margin=dict(t=50, b=10, l=10, r=10))
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
                                     height=280, margin=dict(t=50, b=10, l=10, r=10))
            st.plotly_chart(fig_trend, use_container_width=True)

# =========================================================
# PAGE: Manage Users (Admin only)
# =========================================================
elif st.session_state.page == "Manage Users":
    st.title("🛡️ Manage Users")
    st.caption("All registered accounts on the platform")
    st.markdown("---")

    users = get_all_users()
    if not users:
        st.info("No users found.")
    else:
        users_df = pd.DataFrame(users)
        users_df.columns = ["Username", "Role"]

        table_html = "<table style='width:100%; border-collapse: collapse;'>"
        table_html += "<tr style='text-align:left; border-bottom: 2px solid #ddd;'>"
        for col in users_df.columns:
            table_html += f"<th style='padding:8px;'>{col}</th>"
        table_html += "</tr>"
        for _, row in users_df.iterrows():
            table_html += "<tr style='border-bottom: 1px solid #eee;'>"
            for val in row:
                table_html += f"<td style='padding:8px;'>{val}</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

        role_counts = users_df["Role"].value_counts()
        st.markdown("---")
        st.subheader("User Breakdown")
        fig_users = px.pie(values=role_counts.values, names=role_counts.index, hole=0.5,
                            color_discrete_sequence=["#6366f1", "#8b5cf6", "#ec4899"])
        fig_users.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_users, use_container_width=True)