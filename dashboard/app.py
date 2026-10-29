
"""PATRON // Cybersecurity Operations Center
Read-only honeypot monitoring dashboard.
Four pages: Overview, Detection Alerts, Incidents, Incident Timeline.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

# -------------------------------------------------------------------
# PROJECT IMPORTS
# -------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard import queries as q

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

APP_NAME = "PATRON"
APP_SUBTITLE = "CYBER DEFENSE PLATFORM"
PROJECT_LABEL = "HONEYPOT // INTRUSION DETECTION"
REFRESH_SECONDS = 5

SEVERITY = {
    "critical": {
        "color": "#FF4566",
        "icon": "🔴",
        "label": "CRITICAL",
    },
    "high": {
        "color": "#FF9F43",
        "icon": "🟠",
        "label": "HIGH",
    },
    "medium": {
        "color": "#FFD166",
        "icon": "🟡",
        "label": "MEDIUM",
    },
    "low": {
        "color": "#35D49A",
        "icon": "🟢",
        "label": "LOW",
    },
}

COLORS = {
    "background": "#080D18",
    "sidebar": "#0B1220",
    "panel": "#101A2B",
    "panel_alt": "#142138",
    "border": "#24334B",
    "text": "#EAF2FF",
    "muted": "#8294B0",
    "cyan": "#35D7FF",
    "blue": "#6488FF",
    "violet": "#A78BFA",
    "green": "#35D49A",
    "red": "#FF4566",
    "orange": "#FF9F43",
}

# -------------------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------------------

st.set_page_config(
    page_title="PATRON | Security Operations",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# GLOBAL DESIGN SYSTEM
# -------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap'
    );

    :root {
        --bg: #080D18;
        --sidebar: #0B1220;
        --panel: #101A2B;
        --panel-alt: #142138;
        --border: #24334B;
        --text: #EAF2FF;
        --muted: #8294B0;
        --cyan: #35D7FF;
        --blue: #6488FF;
        --violet: #A78BFA;
        --green: #35D49A;
        --red: #FF4566;
        --orange: #FF9F43;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(
                ellipse at 10% 0%,
                rgba(53, 215, 255, 0.055),
                transparent 35%
            ),
            radial-gradient(
                ellipse at 95% 20%,
                rgba(167, 139, 250, 0.045),
                transparent 30%
            ),
            var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(8, 13, 24, 0.92);
    }

    [data-testid="stToolbar"] {
        right: 1rem;
    }

    .block-container {
        max-width: 1800px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }

    section[data-testid="stSidebar"] {
        background: var(--sidebar);
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    h1, h2, h3, h4 {
        color: var(--text) !important;
        letter-spacing: -0.035em;
    }

    h1 {
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    h2 {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
    }

    h3 {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }

    p, label, .stCaption {
        color: var(--muted);
    }

    [data-testid="stMetric"] {
        background: linear-gradient(
            145deg,
            rgba(20, 33, 56, 0.98),
            rgba(16, 26, 43, 0.96)
        );
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 20px 20px 17px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.13);
        transition: border-color 0.2s, transform 0.2s;
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(53, 215, 255, 0.45);
        transform: translateY(-2px);
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-size: 0.77rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }

    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.78rem !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(16, 26, 43, 0.72);
        border-color: var(--border) !important;
        border-radius: 14px;
    }

    .stTextInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stDateInput input,
    .stNumberInput input,
    .stTextArea textarea {
        background-color: var(--panel) !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
        border-radius: 9px !important;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(
            110deg,
            rgba(53, 215, 255, 0.14),
            rgba(100, 136, 255, 0.14)
        );
        color: var(--text);
        border: 1px solid rgba(53, 215, 255, 0.38);
        border-radius: 9px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: rgba(53, 215, 255, 0.2);
        border-color: var(--cyan);
        color: white;
    }

    div[role="radiogroup"] label {
        background: transparent;
        border-radius: 9px;
    }

    hr {
        border-color: var(--border) !important;
        margin-top: 1.1rem;
        margin-bottom: 1.1rem;
    }

    [data-testid="stAlert"] {
        border-radius: 11px;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 13px;
        padding: 5px 0 18px;
    }

    .brand-mark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 47px;
        height: 47px;
        flex-shrink: 0;
        border: 1px solid rgba(53, 215, 255, 0.5);
        border-radius: 14px;
        background: linear-gradient(
            135deg,
            rgba(53, 215, 255, 0.18),
            rgba(100, 136, 255, 0.17)
        );
        color: var(--cyan);
        font-size: 24px;
    }

    .brand-name {
        color: var(--text);
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        line-height: 1.15;
    }

    .brand-subtitle {
        color: var(--cyan);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        letter-spacing: 0.08em;
        margin-top: 5px;
    }

    .eyebrow {
        color: var(--cyan);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .page-heading {
        color: var(--text);
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: -0.055em;
        line-height: 1.2;
        margin-bottom: 8px;
    }

    .page-description {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.6;
        margin-bottom: 22px;
    }

    .section-heading {
        color: var(--text);
        font-size: 1rem;
        font-weight: 700;
        margin: 4px 0 12px;
    }

    .panel {
        background: linear-gradient(
            145deg,
            rgba(20, 33, 56, 0.82),
            rgba(16, 26, 43, 0.88)
        );
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .panel-label {
        color: var(--muted);
        font-size: 0.73rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .panel-value {
        color: var(--text);
        font-size: 1.65rem;
        font-weight: 800;
        margin-top: 8px;
    }

    .mono {
        font-family: 'JetBrains Mono', monospace;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--green);
        box-shadow: 0 0 11px rgba(53, 212, 154, 0.6);
        margin-right: 8px;
    }

    .status-label {
        color: var(--green);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.73rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }

    .severity-pill {
        display: inline-block;
        border: 1px solid currentColor;
        border-radius: 6px;
        padding: 4px 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }

    .timeline-line {
        border-left: 2px solid var(--border);
        padding: 0 0 18px 20px;
        margin-left: 8px;
    }

    .timeline-line:last-child {
        border-left-color: transparent;
    }

    .footer {
        color: #5F718D;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.69rem;
        padding-top: 22px;
        text-align: center;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .page-heading {
            font-size: 1.7rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.45rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------


def safe_str(value) -> str:
    """Convert nullable database values into readable text."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def severity_info(value) -> dict:
    key = safe_str(value).lower()
    return SEVERITY.get(
        key,
        {
            "color": "#8294B0",
            "icon": "⚪",
            "label": key.upper() or "UNKNOWN",
        },
    )


def severity_badge(value) -> str:
    item = severity_info(value)
    return f"{item['icon']} {item['label']}"


def page_header(eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="eyebrow">{eyebrow}</div>
        <div class="page-heading">{title}</div>
        <div class="page-description">{description}</div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str | None = None) -> None:
    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.caption(subtitle)


def panel(label: str, value, color: str | None = None) -> None:
    value_color = color or COLORS["text"]
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-label">{label}</div>
            <div class="panel-value" style="color:{value_color}">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message: str, hint: str | None = None) -> None:
    st.markdown(
        """
        <div class="panel" style="text-align:center;padding:34px 18px">
            <div style="font-size:27px;margin-bottom:10px">◈</div>
            <div style="font-weight:700;color:#EAF2FF">
                Nothing to display
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(message)
    if hint:
        st.caption(hint)


def prepare_severity_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy, avoiding mutation of query-layer data."""
    result = df.copy()
    if "severity" in result.columns:
        result["severity"] = result["severity"].map(severity_badge)
    return result


def dataframe_height(df: pd.DataFrame, row_height: int = 35) -> int:
    return min(520, max(100, (len(df) + 1) * row_height + 5))


def show_dataframe(df: pd.DataFrame, *, height: int | None = None) -> None:
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        height=height or dataframe_height(df),
    )


def show_database_warning() -> bool:
    try:
        exists = q.db_exists()
    except Exception as exc:
        st.error("Unable to check the database.")
        with st.expander("Technical details"):
            st.code(str(exc))
        return False

    if not exists:
        st.warning(
            "PATRON has not found its database. "
            "Start your project with `make replay` or `make run`."
        )
        return False

    return True


def set_incident(incident_id) -> None:
    st.session_state["incident_id"] = incident_id


def render_footer() -> None:
    st.markdown(
        """
        <div class="footer">
            PATRON SECURITY OPERATIONS // READ-ONLY MODE //
            HONEYPOT TELEMETRY
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------
# PAGE 1 — OVERVIEW
# -------------------------------------------------------------------


def page_overview() -> None:
    page_header(
        "COMMAND CENTER / 01",
        "System Overview",
        "Monitor honeypot telemetry, detection activity, and correlated threats.",
    )

    if not show_database_warning():
        return

    try:
        totals = q.totals()

        events = int(totals.get("events", 0) or 0)
        alerts = int(totals.get("alerts", 0) or 0)
        incidents = int(totals.get("incidents", 0) or 0)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("EVENTS INGESTED", f"{events:,}")

        with c2:
            st.metric("DETECTION ALERTS", f"{alerts:,}")

        with c3:
            st.metric("CORRELATED INCIDENTS", f"{incidents:,}")

        st.markdown("---")

        left, right = st.columns([1, 1.4], gap="large")

        with left:
            section("Severity distribution", "Alert volume grouped by severity.")
            severity_df = q.alerts_per_severity()

            if severity_df.empty:
                empty_state("No detection alerts have been recorded yet.")
            else:
                chart_df = severity_df.copy()
                chart_df["severity"] = (
                    chart_df["severity"].fillna("unknown").str.lower()
                )
                chart_df["severity"] = chart_df["severity"].str.title()
                chart_df = chart_df.set_index("severity")
                chart_df = chart_df.rename(columns={"n": "Alerts"})
                st.bar_chart(
                    chart_df[["Alerts"]],
                    color=COLORS["cyan"],
                    horizontal=True,
                )

                total_alerts = int(severity_df["n"].sum())
                st.caption(f"{total_alerts:,} alerts represented")

        with right:
            section("Event activity", "Recorded events over time.")
            event_df = q.events_over_time()

            if event_df.empty:
                empty_state("No event history is available yet.")
            else:
                chart_df = event_df.copy()
                chart_df["bucket"] = pd.to_datetime(
                    chart_df["bucket"], errors="coerce", utc=True
                )
                chart_df = chart_df.dropna(subset=["bucket"])
                chart_df = chart_df.sort_values("bucket")

                if chart_df.empty:
                    empty_state("Event timestamps are not available.")
                else:
                    chart_df = chart_df.set_index("bucket")
                    st.area_chart(
                        chart_df[["n"]].rename(
                            columns={"n": "Events"}
                        ),
                        color=COLORS["violet"],
                    )

        st.markdown("---")
        section("Threat intelligence snapshots", "Top observed values in stored telemetry.")

        col_a, col_b, col_c = st.columns(3, gap="medium")

        with col_a:
            with st.container(border=True):
                section("Top source IPs")
                sources = q.top_sources()
                if sources.empty:
                    st.caption("No source IPs recorded.")
                else:
                    show_dataframe(sources, height=250)

        with col_b:
            with st.container(border=True):
                section("Top usernames")
                usernames = q.top_usernames()
                if usernames.empty:
                    st.caption("No usernames recorded.")
                else:
                    show_dataframe(usernames, height=250)

        with col_c:
            with st.container(border=True):
                section("Top attempted passwords")
                passwords = q.top_passwords()
                if passwords.empty:
                    st.caption("No attempted passwords recorded.")
                else:
                    st.warning(
                        "Sensitive honeypot telemetry. "
                        "Treat these values as confidential."
                    )
                    show_dataframe(passwords, height=250)

    except Exception as exc:
        st.error("An error occurred while loading the overview.")
        with st.expander("Technical details"):
            st.code(str(exc))

    render_footer()


# -------------------------------------------------------------------
# PAGE 2 — DETECTION ALERTS
# -------------------------------------------------------------------


def page_alerts() -> None:
    page_header(
        "THREAT MONITORING / 02",
        "Detection Center",
        "Search, filter, and inspect individual rule triggers and their evidence.",
    )

    if not show_database_warning():
        return

    try:
        st.markdown(
            '<div class="section-heading">Query filters</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        with col1:
            severity_options = ["(any)"] + q.distinct_severities()
            selected_severity = st.selectbox(
                "Severity",
                severity_options,
                key="alerts_severity",
            )

        with col2:
            rule_options = ["(any)"] + q.distinct_rules()
            selected_rule = st.selectbox(
                "Detection rule",
                rule_options,
                key="alerts_rule",
            )

        with col3:
            source_ip = st.text_input(
                "Source IP contains",
                placeholder="e.g. 192.168.1",
                key="alerts_ip",
            )

        with col4:
            since = st.text_input(
                "Since (UTC ISO)",
                placeholder="e.g. 2026-10-25T12:00:00",
                key="alerts_since",
            )

        df = q.alerts_filtered(
            severity=(
                None if selected_severity == "(any)"
                else selected_severity
            ),
            rule_id=(
                None if selected_rule == "(any)"
                else selected_rule
            ),
            src_ip=source_ip.strip() or None,
            since=since.strip() or None,
        )

        st.markdown("---")

        if df.empty:
            empty_state(
                "No alerts match your current filters.",
                "Try selecting a different severity, rule, or source IP.",
            )
            render_footer()
            return

        # Keep the original IDs and data for evidence queries.
        display_df = prepare_severity_frame(df)

        k1, k2, k3 = st.columns(3)

        with k1:
            st.metric("MATCHING ALERTS", f"{len(df):,}")

        with k2:
            unique_ips = (
                df["src_ip"].nunique()
                if "src_ip" in df.columns else 0
            )
            st.metric("SOURCE IPs", f"{unique_ips:,}")

        with k3:
            unique_rules = (
                df["rule_id"].nunique()
                if "rule_id" in df.columns else 0
            )
            st.metric("RULES TRIGGERED", f"{unique_rules:,}")

        section("Detection results", "Select an alert below to examine its evidence.")
        show_dataframe(display_df, height=420)

        csv_data = display_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "↓ Export filtered alerts (CSV)",
            data=csv_data,
            file_name="patron_alerts.csv",
            mime="text/csv",
            width="stretch",
        )

        st.markdown("---")
        section("Evidence inspector")

        if "id" not in df.columns:
            st.error("Alert records do not contain the expected ID column.")
            render_footer()
            return

        alert_ids = df["id"].tolist()
        selected_id = st.selectbox(
            "Select alert ID",
            alert_ids,
            format_func=lambda value: f"Alert #{value}",
            key="selected_alert_evidence",
        )

        if selected_id is not None:
            evidence = q.evidence_for_alert(int(selected_id))

            with st.container(border=True):
                st.markdown(f"**Evidence for alert #{selected_id}**")
                if evidence.empty:
                    st.info("No linked evidence was returned.")
                else:
                    show_dataframe(evidence)

    except Exception as exc:
        st.error("Unable to load or filter detection alerts.")
        with st.expander("Technical details"):
            st.code(str(exc))

    render_footer()


# -------------------------------------------------------------------
# PAGE 3 — INCIDENTS
# -------------------------------------------------------------------


def page_incidents() -> None:
    page_header(
        "INCIDENT RESPONSE / 03",
        "Correlated Incidents",
        "Investigate attacker activity grouped into correlated incidents.",
    )

    if not show_database_warning():
        return

    try:
        df = q.incidents_list()

        if df.empty:
            empty_state(
                "No incidents have been correlated yet.",
                "Incidents will appear when the backend creates them.",
            )
            render_footer()
            return

        display_df = prepare_severity_frame(df)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("TOTAL INCIDENTS", f"{len(df):,}")

        with col2:
            critical_count = (
                df["severity"].astype(str).str.lower().eq("critical").sum()
                if "severity" in df.columns else 0
            )
            st.metric("CRITICAL INCIDENTS", f"{critical_count:,}")

        with col3:
            unique_sources = (
                df["src_ip"].nunique()
                if "src_ip" in df.columns else 0
            )
            st.metric("UNIQUE SOURCE IPs", f"{unique_sources:,}")

        st.markdown("---")
        section("Incident registry", "Choose an incident to open its timeline.")

        show_dataframe(display_df, height=420)

        if "id" not in df.columns:
            st.error("Incident records do not contain an ID column.")
            render_footer()
            return

        incident_ids = df["id"].tolist()

        selected_id = st.selectbox(
            "Incident to investigate",
            incident_ids,
            format_func=lambda value: f"Incident #{value}",
            key="incident_registry_selection",
        )

        if selected_id is not None:
            set_incident(selected_id)

            st.markdown("---")
            selected_row = df[df["id"] == selected_id]

            if not selected_row.empty:
                row = selected_row.iloc[0]

                a, b = st.columns(2)

                with a:
                    panel(
                        "Selected incident",
                        f"#{selected_id}",
                        COLORS["cyan"],
                    )

                with b:
                    panel(
                        "Severity",
                        severity_badge(
                            row.get("severity", "unknown")
                        ),
                        severity_info(
                            row.get("severity", "unknown")
                        )["color"],
                    )

            if st.button(
                "Open incident timeline →",
                type="primary",
                width="stretch",
            ):
                st.session_state["requested_page"] = "Incident Timeline"
                st.rerun()

    except Exception as exc:
        st.error("Unable to load the incident registry.")
        with st.expander("Technical details"):
            st.code(str(exc))

    render_footer()


# -------------------------------------------------------------------
# PAGE 4 — INCIDENT TIMELINE
# -------------------------------------------------------------------


def page_incident_detail() -> None:
    page_header(
        "FORENSIC INVESTIGATION / 04",
        "Incident Timeline",
        "Review the incident summary, ordered detection stages, and supporting evidence.",
    )

    if not show_database_warning():
        return

    try:
        incident_df = q.incidents_list()

        if incident_df.empty:
            empty_state("No incidents are available for investigation.")
            render_footer()
            return

        incident_ids = incident_df["id"].tolist()

        previous_id = st.session_state.get(
            "incident_id",
            incident_ids[0],
        )

        if previous_id not in incident_ids:
            previous_id = incident_ids[0]

        default_index = incident_ids.index(previous_id)

        selected_id = st.selectbox(
            "Incident ID",
            incident_ids,
            index=default_index,
            format_func=lambda value: f"Incident #{value}",
            key="timeline_incident_selector",
        )

        set_incident(selected_id)

        header = q.incident_header(selected_id)

        if not header:
            st.error("The selected incident could not be found.")
            render_footer()
            return

        severity = severity_info(header.get("severity"))
        source_ip = safe_str(header.get("src_ip")) or "Unknown"
        alert_count = int(header.get("alert_count", 0) or 0)

        # Main incident summary.
        st.markdown(
            f"""
            <div class="panel">
                <div class="eyebrow">INCIDENT #{selected_id}</div>
                <div style="font-size:1.6rem;font-weight:800;color:#EAF2FF">
                    {source_ip}
                </div>
                <div style="margin-top:10px">
                    <span class="severity-pill"
                        style="color:{severity['color']}">
                        {severity['icon']} {severity['label']}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric("SOURCE IP", source_ip)

        with m2:
            st.metric("LINKED ALERTS", f"{alert_count:,}")

        with m3:
            st.metric(
                "SEVERITY",
                severity["label"],
            )

        st.markdown("---")

        left, right = st.columns(2, gap="large")

        with left:
            panel(
                "First observed",
                safe_str(header.get("first_seen")) or "Unknown",
            )

        with right:
            panel(
                "Last observed",
                safe_str(header.get("last_seen")) or "Unknown",
            )

        stages = safe_str(header.get("stages")) or "(none recorded)"

        st.markdown(
            f"""
            <div class="panel">
                <div class="panel-label">Observed attack stages</div>
                <div style="color:#35D7FF;font-weight:600;margin-top:10px">
                    {stages}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        section(
            "Attack-chain timeline",
            "Detection stages in the order returned by the query layer.",
        )

        timeline = q.incident_timeline(selected_id)

        if timeline.empty:
            empty_state("No alerts are linked to this incident.")
            render_footer()
            return

        for position, (_, row) in enumerate(timeline.iterrows(), start=1):
            info = severity_info(row.get("severity"))
            rule_id = safe_str(row.get("rule_id")) or "Unknown rule"
            timestamp = safe_str(row.get("ts_utc")) or "Unknown time"
            explanation = (
                safe_str(row.get("explanation"))
                or "No explanation was recorded."
            )

            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="display:flex;align-items:center;
                                gap:12px;margin-bottom:10px">
                        <div style="
                            display:flex;align-items:center;
                            justify-content:center;
                            min-width:36px;height:36px;
                            border-radius:10px;
                            background:rgba(53,215,255,0.1);
                            border:1px solid rgba(53,215,255,0.25);
                            color:#35D7FF;
                            font-weight:800">
                            {position:02d}
                        </div>
                        <div style="flex:1">
                            <div style="font-weight:700;color:#EAF2FF">
                                {rule_id}
                            </div>
                            <div class="mono"
                                 style="font-size:0.73rem;color:#8294B0;
                                        margin-top:4px">
                                {timestamp}
                            </div>
                        </div>
                        <span class="severity-pill"
                              style="color:{info['color']}">
                            {info['label']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.write(explanation)

                command = safe_str(row.get("command"))

                if command:
                    st.caption("Recorded command evidence")
                    # Display evidence only; never execute it.
                    st.code(command, language="text")

                event_id = row.get("event_id")

                if event_id is not None and safe_str(event_id):
                    try:
                        if not pd.isna(event_id):
                            st.caption(
                                f"Evidence event ID: #{int(event_id)}"
                            )
                    except (TypeError, ValueError, OverflowError):
                        st.caption(
                            f"Evidence event ID: {safe_str(event_id)}"
                        )

        # Export the selected incident's timeline.
        export_df = timeline.copy()

        st.markdown("---")
        section("Incident evidence export")

        st.download_button(
            "↓ Export incident timeline (CSV)",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=f"patron_incident_{selected_id}.csv",
            mime="text/csv",
            width="stretch",
        )

    except Exception as exc:
        st.error("Unable to render the incident timeline.")
        with st.expander("Technical details"):
            st.code(str(exc))

    render_footer()


# -------------------------------------------------------------------
# NAVIGATION
# -------------------------------------------------------------------

PAGES = {
    "Overview": page_overview,
    "Detection Alerts": page_alerts,
    "Incidents": page_incidents,
    "Incident Timeline": page_incident_detail,
}


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <div class="brand-mark">⬡</div>
                <div>
                    <div class="brand-name">PATRON</div>
                    <div class="brand-subtitle">SECURITY OPERATIONS</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("HONEYPOT // INTRUSION DETECTION")
        st.markdown("---")

        st.markdown(
            '<div class="eyebrow">WORKSPACE</div>',
            unsafe_allow_html=True,
        )

        default_page = st.session_state.pop(
            "requested_page",
            st.session_state.get("active_page", "Overview"),
        )

        page_names = list(PAGES.keys())

        if default_page not in page_names:
            default_page = "Overview"

        current_index = page_names.index(default_page)

        choice = st.radio(
            "Navigation",
            page_names,
            index=current_index,
            key="navigation_radio",
            label_visibility="collapsed",
            format_func=lambda name: {
                "Overview": "◈  Overview",
                "Detection Alerts": "⌁  Detection Alerts",
                "Incidents": "⬡  Incidents",
                "Incident Timeline": "◎  Incident Timeline",
            }.get(name, name),
        )

        st.session_state["active_page"] = choice

        st.markdown("---")
        st.markdown(
            '<div class="eyebrow">SYSTEM CONTROLS</div>',
            unsafe_allow_html=True,
        )

        if st.button(
            "↻  Refresh data",
            width="stretch",
            help="Reload the dashboard and its database queries.",
        ):
            st.rerun()

        auto_refresh = st.toggle(
            "Auto-refresh",
            value=False,
            help="Reload the page periodically.",
            key="auto_refresh",
        )

        if auto_refresh:
            interval = st.select_slider(
                "Refresh interval",
                options=[5, 10, 15, 30, 60],
                value=REFRESH_SECONDS,
                format_func=lambda n: f"{n} seconds",
                key="refresh_interval",
            )
            st.caption(f"Refresh interval: {interval}s")
        else:
            interval = None

        st.markdown("---")

        st.markdown(
            """
            <div class="panel">
                <div class="panel-label">Platform status</div>
                <div style="margin-top:10px">
                    <span class="status-dot"></span>
                    <span class="status-label">MONITORING READY</span>
                </div>
                <div style="font-size:0.74rem;color:#8294B0;
                            margin-top:10px;line-height:1.6">
                    Read-only dashboard<br/>
                    Existing database backend
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="font-family:'JetBrains Mono',monospace;
                        font-size:0.66rem;color:#5F718D;
                        line-height:1.9">
                PATRON / COMMUNITY EDITION<br/>
                SECURITY ANALYTICS<br/>
                READ-ONLY MODE
            </div>
            """,
            unsafe_allow_html=True,
        )

    return choice


# -------------------------------------------------------------------
# APPLICATION ENTRY POINT
# -------------------------------------------------------------------


def main() -> None:
    choice = render_sidebar()

    PAGES[choice]()

    if st.session_state.get("auto_refresh", False):
        interval = st.session_state.get(
            "refresh_interval",
            REFRESH_SECONDS,
        )
        # Simple compatible polling. Disable auto-refresh to stop it.
        time.sleep(int(interval))
        st.rerun()


if __name__ == "__main__":
    main()
