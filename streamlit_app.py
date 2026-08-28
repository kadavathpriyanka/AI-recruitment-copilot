import streamlit as st
import pandas as pd
import os
from app import process_resume
from accuracy_check import run_accuracy_check

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
.status-badge {
    display: inline-block;
    background-color: #e6f7ed;
    color: #0f9d58;
    padding: 3px 10px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 600;
}
.metric-box {
    background-color: #f8f9fb;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.metric-label {
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #111827;
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

# ---- Sidebar ----
with st.sidebar:
    st.markdown('<span class="logo-badge">RC</span> &nbsp; **Recruitment Copilot**', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("📊 Dashboard")
    st.markdown("**📄 Resume Upload**")
    st.markdown("👥 Candidates")
    st.markdown("💼 Job Postings")
    st.markdown("📈 Analytics")
    st.markdown("⚙️ Settings")

# ---- Header ----
st.title("📄 Resume Parsing & Candidate Profiling")
st.caption("Upload and process resumes to create structured candidate profiles")
st.markdown("---")

if "all_candidates" not in st.session_state:
    st.session_state.all_candidates = pd.DataFrame()

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

        if uploaded_files:
            os.makedirs("data/uploaded", exist_ok=True)
            for file in uploaded_files:
                save_path = os.path.join("data/uploaded", file.name)
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())

                profile = process_resume(save_path)
                st.session_state.all_candidates = pd.concat(
                    [st.session_state.all_candidates, profile], ignore_index=True
                )
            st.success(f"✅ Processed {len(uploaded_files)} resume(s)")

with col2:
    with st.container(border=True):
        st.subheader("📊 Parsing Progress")
        total = len(st.session_state.all_candidates)
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
            latest = st.session_state.all_candidates.iloc[-1]
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

st.markdown("---")
st.subheader("👥 Recently Processed Candidates")

if not st.session_state.all_candidates.empty:
    display_df = st.session_state.all_candidates[["name", "email", "phone", "skills"]].copy()
    display_df["skills"] = display_df["skills"].apply(lambda x: ", ".join(x) if x else "")
    display_df["status"] = "✅ Processed"
    display_df.columns = ["Candidate Name", "Email", "Phone", "Key Skills", "Status"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("No candidates processed yet. Upload a resume to get started.")