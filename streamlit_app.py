import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
from app import process_resume
from accuracy_check import run_accuracy_check
from auth import signup_user, login_user
from database import init_db, insert_candidate, get_all_candidates, clear_all_candidates

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
</style>
""", unsafe_allow_html=True)

init_db()

BRAND_COLORS = ["#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#ec4899", "#f43f5e", "#fb923c", "#facc15"]

# ---- Auth state ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

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
                success, message = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            signup_submitted = st.form_submit_button("Sign Up")

            if signup_submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = signup_user(new_username, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

if not st.session_state.logged_in:
    show_login_page()
    st.stop()

# ---- Sidebar ----
with st.sidebar:
    st.markdown('<span class="logo-badge">RC</span> &nbsp; **Recruitment Copilot**', unsafe_allow_html=True)
    st.caption(f"Logged in as **{st.session_state.username}**")
    st.markdown("---")
    st.markdown("📊 Dashboard")
    st.markdown("**📄 Resume Upload**")
    st.markdown("👥 Candidates")
    st.markdown("💼 Job Postings")
    st.markdown("📈 Analytics")
    st.markdown("⚙️ Settings")
    st.markdown("---")
    if st.button("🗑️ Clear all candidates"):
        clear_all_candidates()
        st.session_state.processed_files = set()
        st.rerun()
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

# ---- Header ----
st.title("📄 Resume Parsing & Candidate Profiling")
st.caption("Upload and process resumes to create structured candidate profiles")
st.markdown("---")

all_candidates = get_all_candidates()

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
                    insert_candidate(candidate_dict, st.session_state.username)
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
        total = len(all_candidates)
        accuracy = run_accuracy_check() if total > 0 else 0

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

# ---- Visual Insights ----
if total > 0:
    st.markdown("---")
    st.subheader("📈 Parsing Insights")

    # --- Row 1: Accuracy Gauge + Skills bar ---
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

    # --- Row 2: Field extraction radar + Certification donut ---
    radar_col, donut_col = st.columns([1.4, 1])

    with radar_col:
        fields = ["name", "email", "phone", "education", "skills", "experience", "certifications"]
        field_rates = []
        for f in fields:
            count = sum(1 for v in all_candidates[f] if v and (not isinstance(v, list) or len(v) > 0))
            field_rates.append(round((count / total) * 100, 1))

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=field_rates + [field_rates[0]],
            theta=[f.capitalize() for f in fields] + [fields[0].capitalize()],
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

    # --- Row 3: Resumes over time ---
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

st.markdown("---")
st.subheader("👥 Recently Processed Candidates")

if not all_candidates.empty:
    display_df = all_candidates[["name", "email", "phone", "skills"]].copy()
    display_df["skills"] = display_df["skills"].apply(lambda x: ", ".join(x) if x else "")
    display_df["status"] = "✅ Processed"
    display_df.columns = ["Candidate Name", "Email", "Phone", "Key Skills", "Status"]

    table_html = "<table style='width:100%; border-collapse: collapse;'>"
    table_html += "<tr style='text-align:left; border-bottom: 2px solid #ddd;'>"
    for col in display_df.columns:
        table_html += f"<th style='padding:8px;'>{col}</th>"
    table_html += "</tr>"
    for _, row in display_df.iterrows():
        table_html += "<tr style='border-bottom: 1px solid #eee;'>"
        for val in row:
            table_html += f"<td style='padding:8px;'>{val}</td>"
        table_html += "</tr>"
    table_html += "</table>"

    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.info("No candidates processed yet. Upload a resume to get started.")