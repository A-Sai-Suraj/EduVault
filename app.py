"""
app.py
------
EduVault — Streamlit V1
VNR Vignana Jyothi Institute of Engineering and Technology
R25 | Computer Science and Engineering
"""

import hmac
import os

import streamlit as st
from sqlite3 import IntegrityError
from utils.database import (
    add_resource,
    add_semester,
    add_subject,
    database_stats,
    delete_resource,
    delete_semester,
    delete_subject,
    get_resources,
    get_semesters as db_get_semesters,
    get_subjects,
    get_app_data,
    init_db,
    search_resources,
    update_resource,
    update_semester,
    update_subject,
)
from utils.data_loader import (
    get_semesters,
    get_theory_subjects,
    get_subject_resources,
    make_download_url,
    is_drive_url,
    search_subjects,
    compute_stats,
)

# ──────────────────────────────────────────────────────────────────────────────
# Page config  (must be the very first Streamlit call)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduVault",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global typography ───────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* ── Sidebar ─────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(160deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: none;
        color: #94a3b8 !important;
        padding: 0.45rem 0.75rem;
        border-radius: 6px;
        font-size: 0.92rem;
        font-weight: 400;
        cursor: pointer;
        transition: background 0.15s, color 0.15s;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.08) !important;
        color: #f1f5f9 !important;
    }
    [data-testid="stSidebar"] .active-nav > button {
        background: rgba(99,102,241,0.25) !important;
        color: #a5b4fc !important;
        font-weight: 600;
    }

    /* ── Resource card ──────────────────────────────────── */
    .resource-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .resource-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.10);
    }
    .resource-badge {
        display: inline-block;
        background: #ede9fe;
        color: #5b21b6;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        padding: 2px 8px;
        border-radius: 999px;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
    }
    .resource-filename {
        font-size: 0.97rem;
        font-weight: 600;
        color: #1e293b;
        margin: 0.15rem 0 0.75rem 0;
        word-break: break-word;
    }

    /* ── Hero / home ────────────────────────────────────── */
    .hero-box {
        background: linear-gradient(135deg, #312e81 0%, #4338ca 60%, #6366f1 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        color: white;
    }
    .hero-box h1 {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        color: white !important;
    }
    .hero-box p {
        font-size: 1.05rem;
        opacity: 0.88;
        margin: 0;
    }
    .college-tag {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        border-radius: 999px;
        padding: 3px 14px;
        font-size: 0.82rem;
        margin-bottom: 1rem;
    }

    /* ── Section header ──────────────────────────────────── */
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e293b;
        border-left: 4px solid #6366f1;
        padding-left: 0.65rem;
        margin: 1.5rem 0 1rem 0;
    }

    /* ── Stat card ───────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.25rem;
    }

    /* ── Empty-state ─────────────────────────────────────── */
    .empty-state {
        text-align: center;
        padding: 2.5rem 1rem;
        color: #94a3b8;
        font-size: 0.95rem;
    }
    .empty-state .icon {
        font-size: 2.5rem;
        display: block;
        margin-bottom: 0.5rem;
    }

    /* ── Search result card ───────────────────────────────── */
    .search-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.7rem;
    }
    .search-sem-tag {
        font-size: 0.72rem;
        color: #6366f1;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .search-subject {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0.15rem 0 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    :root {
        --hub-bg: #f8fafc;
        --hub-surface: #ffffff;
        --hub-text: #111827;
        --hub-muted: #64748b;
        --hub-border: #e2e8f0;
        --hub-primary: #4f46e5;
        --hub-primary-soft: #eef2ff;
    }
    .stApp { background: var(--hub-bg); color: var(--hub-text); }
    .block-container { max-width: 1180px; padding-top: 2.25rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] { background: var(--hub-surface); border-right: 1px solid var(--hub-border); }
    [data-testid="stSidebar"] * { color: var(--hub-text) !important; }
    [data-testid="stSidebar"] .stButton > button { width: 100%; text-align: left; background: transparent; border: 0; color: var(--hub-muted) !important; padding: 0.55rem 0.7rem; border-radius: 8px; font-size: 0.91rem; font-weight: 500; }
    [data-testid="stSidebar"] .stButton > button:hover { background: #f1f5f9 !important; color: var(--hub-text) !important; }
    [data-testid="stSidebar"] .active-nav > button { background: var(--hub-primary-soft) !important; color: var(--hub-primary) !important; font-weight: 700; }
    [data-testid="stSidebar"] [data-testid="stExpander"] { border: 1px solid var(--hub-border); border-radius: 8px; }
    .hero-box { background: var(--hub-surface); border: 1px solid var(--hub-border); border-left: 4px solid var(--hub-primary); border-radius: 10px; padding: 1.8rem 2rem; margin-bottom: 1.8rem; }
    .hero-box h1 { font-size: clamp(1.7rem, 3vw, 2.45rem); line-height: 1.1; font-weight: 760; letter-spacing: -0.02em; margin: 0.25rem 0 0.65rem; color: var(--hub-text) !important; }
    .hero-box p { max-width: 680px; font-size: 1rem; line-height: 1.6; color: var(--hub-muted); margin: 0; }
    .college-tag { color: var(--hub-primary); font-size: 0.76rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; }
    .section-header { font-size: 1.05rem; font-weight: 750; color: var(--hub-text); margin: 1.7rem 0 0.8rem; }
    .section-kicker { color: var(--hub-muted); font-size: 0.74rem; font-weight: 750; letter-spacing: 0.1em; text-transform: uppercase; margin: 1.7rem 0 0.7rem; }
    .semester-card { background: var(--hub-surface); border: 1px solid var(--hub-border); border-radius: 9px; padding: 1rem 1.1rem 0.85rem; min-height: 108px; }
    .semester-card strong { display: block; color: var(--hub-text); font-size: 0.98rem; margin-bottom: 0.45rem; }
    .semester-card span { display: block; color: var(--hub-muted); font-size: 0.82rem; line-height: 1.45; }
    .semester-card .count { color: var(--hub-primary); font-weight: 700; margin-top: 0.2rem; }
    [data-testid="stMetric"] { background: var(--hub-surface); border: 1px solid var(--hub-border); border-radius: 8px; padding: 0.8rem 1rem; }
    [data-testid="stMetricLabel"] { color: var(--hub-muted); }
    .resource-card { background: var(--hub-surface); border: 1px solid var(--hub-border); border-radius: 9px; padding: 1rem 1.1rem 0.85rem; margin-bottom: 0.75rem; }
    .resource-badge { display: inline-block; color: var(--hub-primary); background: var(--hub-primary-soft); font-size: 0.7rem; font-weight: 700; letter-spacing: 0.04em; padding: 3px 7px; border-radius: 5px; margin-bottom: 0.4rem; text-transform: uppercase; }
    .resource-filename { font-size: 0.96rem; font-weight: 650; color: var(--hub-text); margin: 0.15rem 0 0.65rem; word-break: break-word; }
    .empty-state { text-align: center; background: var(--hub-surface); border: 1px dashed var(--hub-border); border-radius: 9px; padding: 2rem 1rem; color: var(--hub-muted); font-size: 0.92rem; }
    .empty-state .icon { font-size: 1.8rem; display: block; margin-bottom: 0.45rem; }
    .search-card { background: var(--hub-surface); border: 1px solid var(--hub-border); border-radius: 9px; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem; }
    .search-sem-tag { font-size: 0.72rem; color: var(--hub-primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .search-subject { font-size: 1rem; font-weight: 700; color: var(--hub-text); margin: 0.15rem 0 0.25rem; }
    .stButton > button, .stLinkButton > a { border-radius: 7px; font-weight: 650; }
    .stSelectbox [data-baseweb="select"] > div, .stTextInput input { border-radius: 7px; border-color: var(--hub-border); }
    [data-testid="stExpander"] { border-color: var(--hub-border); border-radius: 9px; background: var(--hub-surface); }
    @media (max-width: 700px) { .block-container { padding: 1.25rem 1rem 2rem; } .hero-box { padding: 1.35rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ──────────────────────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "selected_semester_key" not in st.session_state:
    st.session_state.selected_semester_key = None
if "selected_subject_code" not in st.session_state:
    st.session_state.selected_subject_code = None
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False


# ──────────────────────────────────────────────────────────────────────────────
# Initialize once per process, then read the database on every rerun so admin
# changes are immediately visible to the student pages.
# ──────────────────────────────────────────────────────────────────────────────
init_db()
data = get_app_data()


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem 0 0.5rem;">
            <div style="font-size:2rem;">📚</div>
            <div style="font-size:1.05rem; font-weight:800; color:#e2e8f0; margin-top:4px;">
                EduVault
            </div>
            <div style="font-size:0.72rem; color:#64748b; margin-top:2px; letter-spacing:0.05em;">
                R25 · CSE · VNR VJIET
            </div>
        </div>
        <hr style="border-color:#334155; margin: 0.75rem 0;">
        <div style="font-size:0.72rem; color:#64748b; letter-spacing:0.09em; font-weight:600;
                    padding: 0 0.5rem; margin-bottom:0.4rem;">
            NAVIGATION
        </div>
        """,
        unsafe_allow_html=True,
    )

    configured_admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not configured_admin_password:
        configured_admin_password = str(st.secrets.get("ADMIN_PASSWORD", "")).strip()
    if st.session_state.admin_authenticated:
        if st.button("🔒  Log out Admin", key="admin_logout"):
            st.session_state.admin_authenticated = False
            if st.session_state.page == "Admin":
                st.session_state.page = "Home"
            st.rerun()
    else:
        with st.expander("🔐 Admin Login"):
            if not configured_admin_password:
                st.warning("Admin login is not configured. Add ADMIN_PASSWORD to the deployment secrets or environment variables before starting Streamlit.")
            with st.form("admin_login_form"):
                admin_password = st.text_input("Password", type="password")
                if st.form_submit_button("Log in", type="primary"):
                    if configured_admin_password and hmac.compare_digest(admin_password, configured_admin_password):
                        st.session_state.admin_authenticated = True
                        st.session_state.page = "Admin"
                        st.rerun()
                    else:
                        st.error("Incorrect admin password.")

    nav_items = [
        ("🏠", "Home"),
        ("📂", "Resources"),
        ("🔍", "Search"),
    ]
    if st.session_state.admin_authenticated:
        nav_items.append(("⚙️", "Admin"))

    for icon, page_name in nav_items:
        is_active = st.session_state.page == page_name
        container = st.container()
        with container:
            if is_active:
                st.markdown('<div class="active-nav">', unsafe_allow_html=True)
            if st.button(f"{icon}  {page_name}", key=f"nav_{page_name}"):
                st.session_state.page = page_name
                st.rerun()
            if is_active:
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <hr style="border-color:#334155; margin: 1rem 0;">
        <div style="font-size:0.68rem; color:#475569; text-align:center; padding-bottom:0.5rem;">
            Version 1.0 · R25 Regulation
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Error guard — show this if the database has no usable data
# ──────────────────────────────────────────────────────────────────────────────
if data is None:
    st.error("Could not load resource data from SQLite.")
    st.stop()
# ──────────────────────────────────────────────────────────────────────────────
# Helper: render resource cards
# ──────────────────────────────────────────────────────────────────────────────
def _get_badge_label(resource: dict) -> str:
    """Return a display badge string for unit / type / both / neither."""
    unit = resource.get("unit", "").strip()
    rtype = resource.get("type", "").strip()
    if unit and rtype:
        return f"{unit} · {rtype}"
    if unit:
        return unit
    if rtype:
        return rtype
    return "Resource"


def render_resource_card(resource: dict) -> None:
    """Render a single resource as a styled card with Open & Download buttons."""
    file_name = resource.get("file", "Unnamed Resource")
    url = resource.get("url", "")
    badge = _get_badge_label(resource)
    download_url = make_download_url(url) if is_drive_url(url) else None
    regulation = resource.get("source_regulation", "R25")
    warning = "<div style='color:#b45309; font-size:0.82rem; margin-top:0.25rem;'>⚠️ R22 Source Material</div>" if regulation == "R22" else ""

    st.markdown(
        f"""
        <div class="resource-card">
            <span class="resource-badge">📄 {badge}</span>
            <div class="resource-filename">{file_name}</div>
            {warning}
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        if url:
            st.link_button("🔗 Open Resource", url, use_container_width=True)
        else:
            st.button("🔗 Open Resource", disabled=True, key=f"open_{file_name}",
                      use_container_width=True)

    with col2:
        if download_url:
            st.link_button("⬇️ Download", download_url, use_container_width=True)
        elif url:
            # Fallback: non-Drive URL or extraction failed — send to original URL
            st.link_button("⬇️ Download", url, use_container_width=True)
        else:
            st.button("⬇️ Download", disabled=True, key=f"dl_{file_name}",
                      use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Home
# ──────────────────────────────────────────────────────────────────────────────
def page_home():
    stats = database_stats()
    semesters = get_semesters(data)
    st.markdown("""
        <div class="hero-box">
            <span class="college-tag">R25 · CSE · VNR VJIET</span>
            <h1>EduVault</h1>
            <p><strong>Your CSE study resources, all in one place.</strong><br>
            Notes and study material organised semester-wise and subject-wise.</p>
        </div>
        """, unsafe_allow_html=True)
    qa, qb = st.columns(2)
    with qa:
        if st.button("📚  Browse Resources", use_container_width=True, type="primary"):
            st.session_state.page = "Resources"
            st.rerun()
    with qb:
        if st.button("🔎  Search Resources", use_container_width=True):
            st.session_state.page = "Search"
            st.rerun()
    st.markdown('<div class="section-kicker">Quick access</div>', unsafe_allow_html=True)
    if semesters:
        semester_columns = st.columns(min(len(semesters), 4))
        semester_icons = ["📘", "📗", "📙", "📕"]
        for index, semester in enumerate(semesters):
            semester_subjects = get_theory_subjects(data["semesters"][semester["key"]])
            with semester_columns[index % len(semester_columns)]:
                st.markdown(f'<div class="semester-card"><strong>{semester_icons[index % 4]} {semester["name"]}</strong><span>Theory subjects</span><span class="count">{len(semester_subjects)} subjects</span></div>', unsafe_allow_html=True)
                if st.button("Open semester", key=f"home_sem_{semester['key']}", use_container_width=True):
                    st.session_state.selected_semester_key = semester["key"]
                    st.session_state.selected_subject_code = None
                    st.session_state.page = "Resources"
                    st.rerun()
    st.markdown('<div class="section-kicker">At a glance</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Semesters", stats["semesters"])
    c2.metric("Theory Subjects", stats["theory_subjects"])
    c3.metric("Available Resources", stats["resources"])
    st.markdown('<div class="section-header">About the hub</div>', unsafe_allow_html=True)
    st.caption("R25 Computer Science and Engineering resources for VNR VJIET students. Resources marked R22 remain available as clearly labelled source material.")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Resources
# ──────────────────────────────────────────────────────────────────────────────
def page_resources():
    st.markdown("## 📚 Resources")
    st.caption("Choose a semester, then a subject to view its available study material.")

    semesters = get_semesters(data)

    if not semesters:
        st.warning("No semesters found in the data.")
        return

    # ── Semester selector ──────────────────────────────────────────────────
    sem_names = [s["name"] for s in semesters]
    sem_keys = [s["key"] for s in semesters]

    # Restore previously selected semester if valid
    default_sem_idx = 0
    if st.session_state.selected_semester_key in sem_keys:
        default_sem_idx = sem_keys.index(st.session_state.selected_semester_key)

    chosen_sem_name = st.selectbox(
        "Select Semester",
        options=sem_names,
        index=default_sem_idx,
        key="sem_select",
    )
    chosen_sem_idx = sem_names.index(chosen_sem_name)
    chosen_sem_key = sem_keys[chosen_sem_idx]
    st.session_state.selected_semester_key = chosen_sem_key

    semester_data = data["semesters"][chosen_sem_key]
    theory_subjects = get_theory_subjects(semester_data)

    if not theory_subjects:
        st.markdown(
            '<div class="empty-state"><span class="icon">🏫</span>'
            'No theory subjects are currently available for this semester.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Subject selector ───────────────────────────────────────────────────
    subject_options = {
        f"{s['name']}  ({s.get('code', '')})": s for s in theory_subjects
    }
    subject_display_names = list(subject_options.keys())
    default_sub_idx = 0
    if st.session_state.selected_subject_code:
        for i, s in enumerate(theory_subjects):
            if s.get("code") == st.session_state.selected_subject_code:
                default_sub_idx = i
                break

    chosen_sub_display = st.selectbox(
        "Select Subject",
        options=subject_display_names,
        index=default_sub_idx,
        key="sub_select",
    )
    chosen_subject = subject_options[chosen_sub_display]
    st.session_state.selected_subject_code = chosen_subject.get("code")

    # ── Resources ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-kicker">Available resources</div>', unsafe_allow_html=True)

    resources = get_subject_resources(chosen_subject)

    if not resources:
        st.markdown(
            '<div class="empty-state"><span class="icon">📭</span>'
            'No resources are currently available for this subject.</div>',
            unsafe_allow_html=True,
        )
        return

    # Group resources: if any resource has a "unit" field, group by unit;
    # otherwise list them flat.
    has_units = any(r.get("unit") for r in resources)

    if has_units:
        # Collect unit groups while preserving order
        seen_units: dict[str, list] = {}
        for r in resources:
            key = r.get("unit") or "Other"
            seen_units.setdefault(key, []).append(r)

        for unit_label, unit_resources in seen_units.items():
            with st.expander(f"📁 {unit_label}", expanded=True):
                for resource in unit_resources:
                    render_resource_card(resource)
    else:
        for resource in resources:
            render_resource_card(resource)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Search
# ──────────────────────────────────────────────────────────────────────────────
def page_search():
    st.markdown("## 🔎 Search")
    st.caption("Find subjects and files across every semester.")

    semesters = get_semesters(data)
    sem_options = ["All Semesters"] + [s["name"] for s in semesters]
    sem_keys_map = {s["name"]: s["key"] for s in semesters}

    col_q, col_scope = st.columns([3, 1])
    with col_q:
        query = st.text_input(
            "Search",
            placeholder="Search resources, subjects or files...",
            label_visibility="collapsed",
        )
    with col_scope:
        scope = st.selectbox(
            "Scope",
            options=sem_options,
            label_visibility="collapsed",
        )

    if not query.strip():
        st.markdown(
            '<div class="empty-state"><span class="icon">🔍</span>'
            'Type a subject name or file name to search.</div>',
            unsafe_allow_html=True,
        )
        return

    semester_key_filter = sem_keys_map.get(scope) if scope != "All Semesters" else None
    results = search_subjects(data, query, semester_key=semester_key_filter)

    if not results:
        st.markdown(
            f'<div class="empty-state"><span class="icon">😕</span>'
            f'No results found for <strong>"{query}"</strong>.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"**{len(results)} result(s)** for `{query}`",
        unsafe_allow_html=False,
    )

    for result in results:
        sem_name = result["semester_name"]
        subject = result["subject"]
        subject_name = subject.get("name", "")
        subject_code = subject.get("code", "")
        matching_resources = result["matching_resources"]

        with st.expander(
            f"📖 {subject_name}  —  {sem_name}",
            expanded=True,
        ):
            st.markdown(
                f'<div class="search-sem-tag">{sem_name} · {subject_code}</div>',
                unsafe_allow_html=True,
            )

            if matching_resources:
                for resource in matching_resources:
                    render_resource_card(resource)
            else:
                st.caption("No resources currently available for this subject.")

            c1, _ = st.columns([2, 4])
            with c1:
                if st.button(
                    "Go to Subject →",
                    key=f"goto_{subject_code}",
                    use_container_width=True,
                ):
                    # Navigate to the Resources page pre-selecting this semester/subject
                    st.session_state.selected_semester_key = result["semester_key"]
                    st.session_state.selected_subject_code = subject_code
                    st.session_state.page = "Resources"
                    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# PAGE: Admin
# ──────────────────────────────────────────────────────────────────────────────
def _admin_url_is_valid(url: str) -> bool:
    return url.startswith(("http://", "https://")) and "drive.google.com" in url.lower()


def _show_db_error(error: Exception) -> None:
    if isinstance(error, IntegrityError):
        st.warning("⚠️ This record already exists or is still referenced.")
    else:
        st.error(str(error))


def page_admin():
    st.markdown("## ⚙️ Admin Panel")
    st.caption("Manage the SQLite database used by the student pages.")
    semester_rows = db_get_semesters()
    tabs = st.tabs(["Manage Semesters", "Manage Subjects", "Manage Resources"])

    with tabs[0]:
        st.markdown("### Add Semester")
        with st.form("add_semester_form"):
            key = st.text_input("Semester Key", placeholder="semester_5")
            name = st.text_input("Semester Name", placeholder="Semester 5")
            if st.form_submit_button("Add Semester", type="primary"):
                if not key.strip() or not name.strip():
                    st.warning("Semester key and name are required.")
                else:
                    try:
                        add_semester(key, name)
                        st.success("Semester added.")
                        st.rerun()
                    except Exception as error:
                        _show_db_error(error)

        if semester_rows:
            st.markdown("### Edit or Delete Semester")
            semester_by_label = {f"{row['name']} ({row['semester_key']})": row for row in semester_rows}
            selected_label = st.selectbox("Semester", list(semester_by_label), key="admin_semester")
            selected = semester_by_label[selected_label]
            with st.form("edit_semester_form"):
                edited_name = st.text_input("Semester Name", value=selected["name"])
                if st.form_submit_button("Save Semester"):
                    if edited_name.strip():
                        update_semester(selected["id"], edited_name)
                        st.success("Semester updated.")
                        st.rerun()
                    else:
                        st.warning("Semester name is required.")
            confirm = st.checkbox("I understand that only empty semesters can be deleted.", key="confirm_delete_semester")
            if st.button("Delete Semester", disabled=not confirm, key="delete_semester"):
                try:
                    delete_semester(selected["id"])
                    st.success("Semester deleted.")
                    st.rerun()
                except Exception as error:
                    _show_db_error(error)

    with tabs[1]:
        semester_rows = db_get_semesters()
        if not semester_rows:
            st.info("Add a semester before adding subjects.")
        else:
            semester_by_label = {f"{row['name']} ({row['semester_key']})": row for row in semester_rows}
            st.markdown("### Add Subject")
            with st.form("add_subject_form"):
                semester_label = st.selectbox("Semester", list(semester_by_label), key="add_subject_semester")
                code = st.text_input("Subject Code")
                name = st.text_input("Subject Name")
                category = st.selectbox("Subject Category", ["Theory", "Lab / Practical"])
                if st.form_submit_button("Add Subject", type="primary"):
                    if not code.strip() or not name.strip():
                        st.warning("Subject code and name are required.")
                    else:
                        try:
                            add_subject(semester_by_label[semester_label]["id"], code, name, category == "Theory")
                            st.success("Subject added.")
                            st.rerun()
                        except Exception as error:
                            _show_db_error(error)

            subject_query = st.text_input("Search subject name or code", key="admin_subject_search").strip().lower()
            all_subjects = get_subjects()
            matching_subjects = [row for row in all_subjects if not subject_query or subject_query in row["name"].lower() or subject_query in row["code"].lower()]
            if matching_subjects:
                subject_by_label = {f"{row['name']} ({row['code']})": row for row in matching_subjects}
                st.markdown("### Edit or Delete Subject")
                subject_label = st.selectbox("Subject", list(subject_by_label), key="admin_subject")
                selected = subject_by_label[subject_label]
                with st.form("edit_subject_form"):
                    edit_semester = st.selectbox("Semester", list(semester_by_label), index=list(semester_by_label.values()).index(next(row for row in semester_rows if row["id"] == selected["semester_id"])), key="edit_subject_semester")
                    edit_code = st.text_input("Subject Code", value=selected["code"])
                    edit_name = st.text_input("Subject Name", value=selected["name"])
                    edit_category = st.selectbox("Subject Category", ["Theory", "Lab / Practical"], index=0 if selected["is_theory"] else 1)
                    if st.form_submit_button("Save Subject"):
                        try:
                            update_subject(selected["id"], semester_by_label[edit_semester]["id"], edit_code, edit_name, edit_category == "Theory")
                            st.success("Subject updated.")
                            st.rerun()
                        except Exception as error:
                            _show_db_error(error)
                confirm = st.checkbox("I understand this deletes the subject and its resources.", key="confirm_delete_subject")
                if st.button("Delete Subject", disabled=not confirm, key="delete_subject"):
                    delete_subject(selected["id"])
                    st.success("Subject deleted.")
                    st.rerun()

    with tabs[2]:
        semester_rows = db_get_semesters()
        all_subjects = get_subjects()
        if not all_subjects:
            st.info("Add a subject before adding resources.")
        else:
            semester_by_label = {f"{row['name']} ({row['semester_key']})": row for row in semester_rows}
            subject_by_semester = {row["id"]: row for row in all_subjects}
            st.markdown("### Add Resource")
            resource_semester = st.selectbox("Semester", list(semester_by_label), key="resource_semester")
            sem_id = semester_by_label[resource_semester]["id"]
            sem_subjects = [row for row in all_subjects if row["semester_id"] == sem_id]
            subject_labels = {f"{row['name']} ({row['code']})": row for row in sem_subjects}
            with st.form("add_resource_form"):
                resource_subject = st.selectbox("Subject", list(subject_labels), key="resource_subject")
                unit = st.text_input("Unit", placeholder="Unit 3")
                resource_type = st.text_input("Resource Type", placeholder="Notes")
                file_name = st.text_input("File Name")
                url = st.text_input("Google Drive URL")
                regulation = st.selectbox("Source Regulation", ["R25", "R22", "Other"])
                if st.form_submit_button("Add Resource", type="primary"):
                    if not file_name.strip() or not url.strip():
                        st.warning("File name and URL are required.")
                    elif not _admin_url_is_valid(url.strip()):
                        st.warning("Enter a valid Google Drive URL.")
                    else:
                        try:
                            add_resource(subject_labels[resource_subject]["id"], unit, resource_type, file_name, url, regulation)
                            st.success("Resource added.")
                            st.rerun()
                        except Exception as error:
                            _show_db_error(error)

            resource_query = st.text_input("Search resource file name", key="admin_resource_search").strip().lower()
            all_resources = get_resources()
            matching_resources = [row for row in all_resources if not resource_query or resource_query in row["file_name"].lower()]
            if matching_resources:
                resource_labels = {f"{row['file_name']} · {row['subject_name']}": row for row in matching_resources}
                st.markdown("### Edit or Delete Resource")
                resource_label = st.selectbox("Resource", list(resource_labels), key="admin_resource")
                selected = resource_labels[resource_label]
                with st.form("edit_resource_form"):
                    edit_unit = st.text_input("Unit", value=selected["unit"])
                    edit_type = st.text_input("Resource Type", value=selected["type"])
                    edit_file = st.text_input("File Name", value=selected["file_name"])
                    edit_url = st.text_input("Google Drive URL", value=selected["url"])
                    regulation_options = ["R25", "R22", "Other"]
                    edit_regulation = st.selectbox("Source Regulation", regulation_options, index=regulation_options.index(selected["source_regulation"]) if selected["source_regulation"] in regulation_options else 2)
                    if st.form_submit_button("Save Resource"):
                        if not edit_file.strip() or not _admin_url_is_valid(edit_url.strip()):
                            st.warning("File name and a valid Google Drive URL are required.")
                        else:
                            try:
                                update_resource(selected["id"], edit_unit, edit_type, edit_file, edit_url, edit_regulation)
                                st.success("Resource updated.")
                                st.rerun()
                            except Exception as error:
                                _show_db_error(error)
                confirm = st.checkbox(f"I understand this deletes {selected['file_name']}.", key="confirm_delete_resource")
                if st.button("Delete Resource", disabled=not confirm, key="delete_resource"):
                    delete_resource(selected["id"])
                    st.success("Resource deleted.")
                    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.page == "Admin" and not st.session_state.admin_authenticated:
    st.session_state.page = "Home"
    st.rerun()

page = st.session_state.page

if page == "Home":
    page_home()
elif page == "Resources":
    page_resources()
elif page == "Search":
    page_search()
elif page == "Admin":
    page_admin()
else:
    st.session_state.page = "Home"
    st.rerun()
