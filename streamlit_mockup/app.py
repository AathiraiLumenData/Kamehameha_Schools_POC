"""
Streamlit mockup — exact replica of the React Genie Chat frontend.
Run:  streamlit run streamlit_mockup/app.py
"""

import time
import html as esc
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ── Design tokens (from SPEC.md / index.css) ──────────────────
INK = "#15181C"
PAGE = "#F6F6F3"
SURFACE = "#FFFFFF"
BORDER = "#E3E3DD"
MUTED = "#5A606A"
ACCENT = "#0B6E6E"
ACCENT_SOFT = "#E3F1F0"
ACCENT_DARK = "#074F4F"
CHART_COLORS = ["#0B6E6E", "#7DA7A3", "#C9CDD2", "#5A606A"]
SQL_BG = "#15181C"

DB_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg>'
CHECK_SVG = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 5 5 9-10"/></svg>'
THUMBUP_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15181C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 11v9H4v-9h3zm0 0 4-8c1.7 0 3 1.3 3 3v3h5.5a2 2 0 0 1 2 2.3l-1.2 7a2 2 0 0 1-2 1.7H7"/></svg>'
THUMBDN_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15181C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 13V4h3v9h-3zm0 0-4 8c-1.7 0-3-1.3-3-3v-3H4.5a2 2 0 0 1-2-2.3l1.2-7a2 2 0 0 1 2-1.7H17"/></svg>'
CHEVRON_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#5A606A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>'

st.set_page_config(page_title="Ask your data", page_icon="🗄️", layout="wide", initial_sidebar_state="expanded")

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Global */
html, body, .stApp {
    background: %(page)s !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: %(ink)s !important;
}
#MainMenu, footer, header[data-testid="stHeader"],
div[data-testid="stDecoration"], div[data-testid="stToolbar"] {
    display: none !important;
}
h1,h2,h3,h4,h5,h6,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2 {
    color: %(ink)s !important;
    font-family: 'Inter', sans-serif !important;
}
p, span, div, li, label {
    font-family: 'Inter', sans-serif !important;
}
hr { border-color: %(border)s !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: %(surface)s !important;
    border-right: 1px solid %(border)s !important;
    width: 272px !important; min-width: 272px !important;
}
section[data-testid="stSidebar"] > div:first-child {
    display: flex !important; flex-direction: column !important;
    height: 100vh !important; padding: 20px 16px 16px !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    display: flex !important; flex-direction: column !important; height: 100%% !important;
}

/* ALL buttons in sidebar → teal new-chat style by default */
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
    background: %(accent_soft)s !important; color: %(accent_dark)s !important;
    border: 1px solid %(accent)s !important; border-radius: 10px !important;
    font-weight: 500 !important; font-size: 14px !important; min-height: 44px !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
    background: %(accent)s !important; color: white !important;
}
/* Recent chat buttons override — plain text look */
section[data-testid="stSidebar"] .recent-btn button[data-testid="stBaseButton-secondary"] {
    background: transparent !important; border: none !important;
    border-radius: 8px !important; text-align: left !important;
    font-size: 14px !important; color: %(ink)s !important;
    font-weight: 400 !important; padding: 10px 12px !important;
    min-height: 36px !important;
}
section[data-testid="stSidebar"] .recent-btn button[data-testid="stBaseButton-secondary"]:hover {
    background: %(accent_soft)s !important; color: %(ink)s !important;
}

/* Main area secondary buttons — white card style (starters & suggestions) */
div.stMainBlockContainer button[data-testid="stBaseButton-secondary"] {
    background: %(surface)s !important; color: %(ink)s !important;
    border: 1px solid %(border)s !important; border-radius: 12px !important;
    font-size: 14px !important; text-align: left !important;
    padding: 14px 16px !important; min-height: 44px !important;
    white-space: normal !important; line-height: 1.45 !important;
}
div.stMainBlockContainer button[data-testid="stBaseButton-secondary"]:hover {
    border-color: %(accent)s !important; background: %(surface)s !important; color: %(ink)s !important;
}
div.stMainBlockContainer button[data-testid="stBaseButton-secondary"] p {
    color: %(ink)s !important; margin: 0 !important;
}
div.stMainBlockContainer button[data-testid="stBaseButton-secondary"] strong {
    color: %(accent)s !important; font-size: 12px !important; font-weight: 500 !important;
}

/* Primary button */
button[data-testid="stBaseButton-primary"] {
    background: %(accent)s !important; color: white !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 500 !important; min-height: 44px !important;
}

/* Chat input */
div[data-testid="stChatInput"] { background: transparent !important; border-top: none !important; }
div[data-testid="stChatInput"] textarea {
    border: 1px solid #BFC3C9 !important; border-radius: 14px !important;
    font-size: 15px !important; background: %(surface)s !important;
}
div[data-testid="stChatInput"] button { background: %(accent)s !important; border-radius: 10px !important; }

/* Expander */
details[data-testid="stExpander"] {
    border: 1px solid %(border)s !important; border-radius: 10px !important; background: %(surface)s !important;
}
details summary { font-size: 13px !important; color: %(muted)s !important; }

/* Radio as tab pills */
div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 0 !important; }
div[data-testid="stRadio"] > label { display: none !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] {
    padding: 0 14px !important; height: 36px !important; margin: 0 !important;
    border-radius: 7px !important; font-size: 13px !important; display: flex !important;
    align-items: center !important; background: transparent !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] span { color: %(muted)s !important; }
div[data-testid="stRadio"] input:checked + div { display: none !important; }
div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child { display: none !important; }

/* Hide default Streamlit dataframe border */
[data-testid="stDataFrame"] { border: none !important; }

/* ── Custom HTML classes ── */
.sidebar-brand { display:flex; align-items:center; gap:10px; padding:0 4px 16px; font-size:16px; font-weight:600; color:%(ink)s; }
.sidebar-brand .icon { width:28px; height:28px; border-radius:8px; background:%(accent)s; display:flex; align-items:center; justify-content:center; }
.section-label { font-size:12px; font-weight:500; color:%(muted)s; padding:0 4px; margin:14px 0 4px; }
.space-card { display:flex; align-items:center; justify-content:space-between; padding:10px 12px; border:1px solid %(border)s; border-radius:10px; background:%(page)s; margin:4px 0; cursor:pointer; }
.space-name { font-weight:500; font-size:14px; color:%(ink)s; }
.space-meta { font-size:12px; color:%(muted)s; }
.sidebar-spacer { flex:1 1 auto; min-height:20px; }
.sidebar-user { display:flex; align-items:center; gap:10px; padding:12px 4px; border-top:1px solid %(border)s; }
.user-avatar { width:32px; height:32px; border-radius:50%%; background:%(accent_soft)s; color:%(accent_dark)s; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:600; flex-shrink:0; }
.recent-active { display:block; padding:10px 12px; border-radius:8px; background:%(accent_soft)s; font-size:14px; font-weight:500; color:%(ink)s; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.table-chip { display:inline-block; padding:4px 8px; border-radius:6px; background:%(page)s; border:1px solid %(border)s; font-family:'JetBrains Mono',monospace; font-size:11px; color:%(ink)s; margin:2px; }
.user-bubble { max-width:560px; margin-left:auto; padding:12px 16px; border-radius:16px 16px 4px 16px; background:%(sql_bg)s; color:#FFF; font-size:15px; line-height:1.5; }
.assistant-row { display:flex; gap:12px; align-items:flex-start; }
.db-icon { flex:0 0 28px; width:28px; height:28px; border-radius:8px; background:%(accent)s; display:flex; align-items:center; justify-content:center; }
.asst-body { font-size:15px; line-height:1.6; color:%(ink)s; flex:1; min-width:0; }
.asst-body code { font-family:'JetBrains Mono',monospace; font-size:13px; padding:2px 6px; border-radius:4px; background:%(page)s; }
.genie-note { padding:12px 16px; border-radius:10px; background:%(surface)s; border:1px solid %(border)s; font-size:13px; line-height:1.5; color:%(muted)s; margin-top:12px; }
.genie-note strong { font-weight:600; color:%(ink)s; }
.main-hdr { display:flex; align-items:center; justify-content:space-between; padding:14px 0; border-bottom:1px solid %(border)s; margin-bottom:24px; background:transparent; }
.main-hdr-title { font-size:16px; font-weight:600; color:%(ink)s; margin:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.space-pill { padding:5px 12px; border-radius:999px; background:%(surface)s; border:1px solid %(border)s; font-size:13px; color:%(muted)s; white-space:nowrap; }

/* Result card — single bordered container */
.result-card { background:%(surface)s; border:1px solid %(border)s; border-radius:14px; overflow:hidden; margin:16px 0 0; }
.rc-header { display:flex; align-items:center; justify-content:space-between; padding:14px 20px; border-bottom:1px solid %(border)s; }
.rc-title { font-size:15px; font-weight:600; color:%(ink)s; }
.rc-subtitle { font-size:13px; color:%(muted)s; }
.rc-tabs { display:flex; padding:3px; border-radius:10px; background:%(page)s; border:1px solid %(border)s; }
.rc-tab { padding:0 14px; height:32px; border:0; border-radius:7px; background:transparent; font-size:13px; color:%(muted)s; cursor:pointer; font-family:'Inter',sans-serif; }
.rc-tab.active { background:%(surface)s; box-shadow:0 1px 2px rgba(0,0,0,.12); font-weight:500; color:%(ink)s; }
.rc-body { min-height:0; }

/* HTML table */
.rc-table { width:100%%; border-collapse:collapse; font-size:14px; }
.rc-table thead tr { background:%(page)s; }
.rc-table th { padding:10px 20px; text-align:left; font-weight:500; font-size:12px; color:%(muted)s; }
.rc-table td { padding:11px 20px; text-align:left; color:%(ink)s; }
.rc-table tbody tr { border-top:1px solid %(border)s; }

/* SQL block inside card */
.sql-block { background:%(sql_bg)s; }
.sql-hdr { display:flex; justify-content:space-between; padding:10px 20px; border-bottom:1px solid #2C3038; font-size:13px; color:#C7CBD1; }
.sql-code { margin:0; padding:16px 20px; overflow-x:auto; font-family:'JetBrains Mono',monospace; font-size:13px; line-height:1.7; color:#E6E8EB; white-space:pre; }

/* Footer */
.rc-footer { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px; padding:12px 20px; border-top:1px solid %(border)s; background:#FBFBF9; font-size:13px; color:%(muted)s; }
.rc-footer-actions { display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
.rc-icon-btn { width:44px; height:36px; border:1px solid #D4D4CC; border-radius:8px; background:%(surface)s; display:flex; align-items:center; justify-content:center; cursor:pointer; }
.rc-action-btn { min-height:36px; padding:0 12px; border:1px solid #D4D4CC; border-radius:8px; background:%(surface)s; font-size:13px; color:%(ink)s; cursor:pointer; font-family:'Inter',sans-serif; }

/* Suggestions */
.suggest-label { font-size:14px; font-weight:500; color:%(muted)s; margin:20px 0 10px; }

/* Working state */
.working-card { background:%(surface)s; border:1px solid %(border)s; border-radius:14px; padding:20px; max-width:640px; }
.working-title { font-size:15px; font-weight:600; color:%(ink)s; margin-bottom:18px; }
.step-item { display:flex; align-items:center; gap:12px; padding:7px 0; font-size:14px; }
.step-done { width:22px; height:22px; border-radius:50%%; background:%(accent)s; display:inline-flex; align-items:center; justify-content:center; flex-shrink:0; }
.step-active { width:22px; height:22px; border-radius:50%%; border:2px solid %(accent)s; border-top-color:%(accent_soft)s; animation:spin .8s linear infinite; display:inline-block; flex-shrink:0; }
.step-pending { width:22px; height:22px; border-radius:50%%; border:2px solid #C9CDD2; display:inline-block; flex-shrink:0; }
@keyframes spin { to { transform:rotate(360deg); } }
.skel { height:10px; border-radius:4px; background:#EDEDE8; margin:5px 0; }

/* Tables panel */
.tables-panel { background:%(surface)s; border:1px solid %(border)s; border-radius:12px; padding:16px; }
.composer-note { font-size:12px; color:%(muted)s; text-align:center; padding:4px 0 0; }
</style>
""" % {
    "ink": INK, "page": PAGE, "surface": SURFACE, "border": BORDER,
    "muted": MUTED, "accent": ACCENT, "accent_soft": ACCENT_SOFT,
    "accent_dark": ACCENT_DARK, "sql_bg": SQL_BG,
}, unsafe_allow_html=True)


# ── Mock data ──────────────────────────────────────────────────
SPACE_NAME = "Kamehameha Schools Student Journey Insights"
SPACE_INFO = {
    "space_name": SPACE_NAME,
    "description": "Answers questions about the full Kamehameha Schools student journey: admissions, enrollment, withdrawals, graduation, SAT scores, and parent/guardian context.",
    "catalog": "ld_analytics.kschools",
}
TABLES = [
    "student_admission_data", "student_enrollment", "student_information",
    "student_parent_guardian_data", "student_sat_score_data_file_1",
    "student_sat_score_data_file_2",
]
STARTERS = [
    {"label": "Outcomes", "text": "What share of students admitted in each school year are still enrolled or have graduated?"},
    {"label": "SAT", "text": "What is the average latest SAT total and percent meeting the math benchmark by campus?"},
    {"label": "Enrollment", "text": "What are the main grade levels and school years covered in the enrollment data?"},
    {"label": "Overview", "text": "Summarize the datasets in this space"},
]

MOCK_RESPONSES = {
    STARTERS[0]["text"]: {
        "text": "The share of admitted students who are still enrolled or have graduated varies by school year. For the most recent cohorts, retention rates hover around 75\u201385%, with earlier cohorts showing higher graduation completion rates as expected.",
        "description": "Counts distinct students from admissions who appear in enrollment or have graduated, grouped by entry school year.",
        "sql": "SELECT\n  si.EntrySchoolYearDesc AS school_year,\n  COUNT(DISTINCT si.StdNumber) AS total_admitted,\n  COUNT(DISTINCT CASE\n    WHEN se.StdNumber IS NOT NULL OR si.HasGraduated = 1\n    THEN si.StdNumber\n  END) AS enrolled_or_graduated,\n  ROUND(\n    COUNT(DISTINCT CASE\n      WHEN se.StdNumber IS NOT NULL OR si.HasGraduated = 1\n      THEN si.StdNumber\n    END) * 100.0 / COUNT(DISTINCT si.StdNumber), 1\n  ) AS pct_retained\nFROM student_information si\nLEFT JOIN student_enrollment se\n  ON si.StdNumber = se.StdNumber\nGROUP BY si.EntrySchoolYearDesc\nORDER BY si.EntrySchoolYearDesc",
        "result": {
            "columns": [{"name":"school_year","type":"STRING"},{"name":"total_admitted","type":"INT"},{"name":"enrolled_or_graduated","type":"INT"},{"name":"pct_retained","type":"DOUBLE"}],
            "rows": [["2018-2019","342","289","84.5"],["2019-2020","356","295","82.9"],["2020-2021","318","271","85.2"],["2021-2022","365","298","81.6"],["2022-2023","371","312","84.1"],["2023-2024","389","321","82.5"],["2024-2025","402","345","85.8"]],
            "row_count": 7, "truncated": False,
        },
        "tables_used": ["student_information", "student_enrollment"],
        "suggested_questions": ["How does retention differ by campus?", "What is the graduation rate by entry cohort?", "Show me the trend of admitted students over time"],
    },
    STARTERS[1]["text"]: {
        "text": "SAT performance varies across campuses. The average latest SAT total ranges from about 980 to 1120, and the percent meeting the math college-readiness benchmark ranges from 38% to 62%.",
        "description": "Calculates the average SAT total and percentage meeting the math benchmark, grouped by campus.",
        "sql": "SELECT\n  se.CampusAbbr AS campus,\n  ROUND(AVG(CAST(s1.LATEST_SAT_TOTAL AS DOUBLE)), 0) AS avg_sat_total,\n  ROUND(\n    SUM(CASE WHEN s1.MATH_CCR_BENCHMARK = 'Met' THEN 1 ELSE 0 END)\n    * 100.0 / COUNT(*), 1\n  ) AS pct_math_benchmark\nFROM student_sat_score_data_file_1 s1\nJOIN student_enrollment se\n  ON s1.`Student Id` = se.StdNumber\nGROUP BY se.CampusAbbr\nORDER BY avg_sat_total DESC",
        "result": {
            "columns": [{"name":"campus","type":"STRING"},{"name":"avg_sat_total","type":"DOUBLE"},{"name":"pct_math_benchmark","type":"DOUBLE"}],
            "rows": [["KSK","1120","62.3"],["KSM","1045","51.7"],["KSH","1010","45.2"],["KSBE","985","38.9"]],
            "row_count": 4, "truncated": False,
        },
        "tables_used": ["student_sat_score_data_file_1", "student_enrollment"],
        "suggested_questions": ["Show SAT trends over cohort years", "What is the average GPA by campus?", "How do SAT scores compare by gender?"],
    },
    STARTERS[2]["text"]: {
        "text": "The enrollment data spans school years from 2015-2016 through 2024-2025 and covers grades K through 12, plus PK (pre-kindergarten). The largest enrollment counts are in the high school grades (9\u201312).",
        "description": "Lists distinct grade levels and school year ranges in the enrollment table.",
        "sql": "SELECT\n  Grade AS grade_level,\n  MIN(SchoolYearStart) AS earliest_year,\n  MAX(SchoolYearStart) AS latest_year,\n  COUNT(DISTINCT StdNumber) AS student_count\nFROM student_enrollment\nGROUP BY Grade\nORDER BY\n  CASE WHEN Grade = 'PK' THEN -1\n       WHEN Grade = 'K' THEN 0\n       ELSE CAST(Grade AS INT) END",
        "result": {
            "columns": [{"name":"grade_level","type":"STRING"},{"name":"earliest_year","type":"INT"},{"name":"latest_year","type":"INT"},{"name":"student_count","type":"INT"}],
            "rows": [["PK","2017","2024","245"],["K","2015","2024","892"],["1","2015","2024","876"],["2","2015","2024","851"],["3","2015","2024","843"],["4","2015","2024","867"],["5","2015","2024","889"],["6","2015","2024","1203"],["7","2015","2024","1256"],["8","2015","2024","1234"],["9","2015","2024","1489"],["10","2015","2024","1467"],["11","2015","2024","1398"],["12","2015","2024","1345"]],
            "row_count": 14, "truncated": False,
        },
        "tables_used": ["student_enrollment"],
        "suggested_questions": ["Which campus has the most students?", "How has total enrollment changed year over year?", "What is the breakdown of boarder vs day students?"],
    },
}
DEFAULT_MOCK = {
    "text": "Based on the data, here is a summary of enrollment patterns across campuses and school years.",
    "description": "Aggregated enrollment counts by campus and recent school years.",
    "sql": "SELECT CampusAbbr AS campus, SchoolYearDesc AS school_year,\n  COUNT(DISTINCT StdNumber) AS student_count\nFROM student_enrollment\nWHERE SchoolYearStart >= 2022\nGROUP BY CampusAbbr, SchoolYearDesc\nORDER BY CampusAbbr, SchoolYearDesc",
    "result": {
        "columns": [{"name":"campus","type":"STRING"},{"name":"school_year","type":"STRING"},{"name":"student_count","type":"INT"}],
        "rows": [["KSH","2022-2023","1245"],["KSH","2023-2024","1267"],["KSH","2024-2025","1289"],["KSK","2022-2023","2134"],["KSK","2023-2024","2156"],["KSK","2024-2025","2198"],["KSM","2022-2023","1089"],["KSM","2023-2024","1102"],["KSM","2024-2025","1134"]],
        "row_count": 9, "truncated": False,
    },
    "tables_used": ["student_enrollment"],
    "suggested_questions": ["What are the retention rates by campus?", "Show me graduation outcomes for the latest cohort"],
}
WORKING_STEPS = [
    {"label": "Read your question", "statuses": ["SUBMITTED"]},
    {"label": "Found the tables it needs", "statuses": ["FETCHING_METADATA", "FILTERING_CONTEXT"]},
    {"label": "Writing the SQL", "statuses": ["ASKING_AI"]},
    {"label": "Running it on the SQL warehouse", "statuses": ["PENDING_WAREHOUSE", "EXECUTING_QUERY"]},
    {"label": "Writing the summary", "statuses": ["COMPLETED"]},
]

# ── State ──────────────────────────────────────────────────────
for k, v in [("auth", False), ("convs", []), ("idx", None), ("pending", None)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ────────────────────────────────────────────────────
def e(s):
    return esc.escape(str(s))


def pick_chart(result):
    cols, rows = result["columns"], result["rows"]
    if not rows or len(cols) < 2:
        return None
    nums = [i for i, c in enumerate(cols) if c["type"].upper() in ("INT","LONG","BIGINT","DOUBLE","FLOAT","DECIMAL")]
    cats = [i for i in range(len(cols)) if i not in nums]
    if not nums or not cats:
        return None
    cn = cols[cats[0]]["name"].lower()
    if any(w in cn for w in ("date","year","month","quarter")):
        return "line"
    vals = [r[cats[0]] for r in rows]
    if vals and all(v and v[:4].isdigit() for v in vals):
        return "line"
    if len(nums) <= 3:
        return "bar"
    return None


def html_table(result):
    cols, rows = result["columns"], result["rows"]
    h = "<table class='rc-table'><thead><tr>"
    for c in cols:
        h += f"<th>{e(c['name'])}</th>"
    h += "</tr></thead><tbody>"
    for row in rows[:100]:
        h += "<tr>"
        for cell in row:
            h += f"<td>{e(cell)}</td>"
        h += "</tr>"
    h += "</tbody></table>"
    return h


def html_sql(sql):
    return f"""<div class="sql-block"><div class="sql-hdr"><span>SQL generated by Genie</span><span>Databricks SQL</span></div><pre class="sql-code">{e(sql)}</pre></div>"""


def html_footer(tables_used, row_count, elapsed):
    parts = []
    if tables_used:
        parts.append(", ".join(tables_used))
    if row_count is not None:
        parts.append(f"{row_count} rows")
    if elapsed:
        parts.append(f"{elapsed} s")
    meta = " &middot; ".join(parts)
    return f"""<div class="rc-footer">
<span>{meta}</span>
<div class="rc-footer-actions">
    <span class="rc-icon-btn">{THUMBUP_SVG}</span>
    <span class="rc-icon-btn">{THUMBDN_SVG}</span>
    <span class="rc-action-btn">Copy SQL</span>
    <span class="rc-action-btn">Export CSV</span>
</div>
</div>"""


def render_chart(result, chart_type):
    cols, rows = result["columns"], result["rows"]
    nums = [i for i, c in enumerate(cols) if c["type"].upper() in ("INT","LONG","BIGINT","DOUBLE","FLOAT","DECIMAL")]
    ci = next(i for i in range(len(cols)) if i not in nums)
    data = {cols[ci]["name"]: [r[ci] for r in rows]}
    for ni in nums:
        data[cols[ni]["name"]] = [float(r[ni]) if r[ni] else 0 for r in rows]
    df = pd.DataFrame(data)
    ck = cols[ci]["name"]
    nks = [cols[ni]["name"] for ni in nums]
    fig = go.Figure()
    for i, k in enumerate(nks):
        c = CHART_COLORS[i % len(CHART_COLORS)]
        if chart_type == "line":
            fig.add_trace(go.Scatter(x=df[ck], y=df[k], name=k, mode="lines+markers", line=dict(color=c, width=2), marker=dict(size=5)))
        else:
            fig.add_trace(go.Bar(x=df[ck], y=df[k], name=k, marker_color=c))
    fig.update_layout(barmode="group", plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter", size=12, color=MUTED),
        margin=dict(l=20, r=20, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(gridcolor=BORDER), yaxis=dict(gridcolor=BORDER),
        height=340 if chart_type == "line" else max(len(rows)*48+60, 300))
    st.plotly_chart(fig, use_container_width=True)


def submit(q):
    st.session_state.pending = q


# ── Sidebar ────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f'<div class="sidebar-brand"><div class="icon">{DB_SVG}</div><span>Ask your data</span></div>', unsafe_allow_html=True)

        if st.button("+ New chat", use_container_width=True, type="secondary"):
            st.session_state.idx = None
            st.rerun()

        st.markdown('<div class="section-label">Genie space</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="space-card">
<div><div class="space-name">{SPACE_NAME}</div><div class="space-meta">Databricks Genie &middot; {len(TABLES)} tables</div></div>
<span>{CHEVRON_SVG}</span></div>""", unsafe_allow_html=True)

        with st.expander("Space details"):
            st.caption(SPACE_INFO["description"])
            st.caption(f"Catalog: {SPACE_INFO['catalog']}")
            st.markdown(" ".join(f'<span class="table-chip">{t}</span>' for t in TABLES), unsafe_allow_html=True)

        convs = st.session_state.convs
        if convs:
            st.markdown('<div class="section-label">Recent</div>', unsafe_allow_html=True)
            for i, c in enumerate(convs):
                if i == st.session_state.idx:
                    st.markdown(f'<div class="recent-active">{e(c["title"])}</div>', unsafe_allow_html=True)
                else:
                    with st.container():
                        st.markdown('<div class="recent-btn">', unsafe_allow_html=True)
                        if st.button(c["title"], key=f"c{i}", use_container_width=True, type="secondary"):
                            st.session_state.idx = i
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="sidebar-user"><div class="user-avatar">U</div>
<div><div style="font-size:14px;font-weight:500;color:{INK}">User</div>
<div style="font-size:12px;color:{MUTED}">Signed in with Databricks</div></div></div>""", unsafe_allow_html=True)


# ── Screens ────────────────────────────────────────────────────
def token_screen():
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<div style='height:120px'></div>", unsafe_allow_html=True)
        st.markdown(f"""<div style="text-align:center;margin-bottom:24px">
<h2 style="font-size:24px;font-weight:600;color:{INK};margin:0 0 12px">Sign in to Databricks</h2>
<p style="color:{MUTED};font-size:15px;margin:0">Paste your Databricks personal access token.<br/>It stays in your browser and is sent only to your workspace.</p>
</div>""", unsafe_allow_html=True)
        tok = st.text_input("Token", type="password", placeholder="dapi...", label_visibility="collapsed")
        if st.button("Continue", type="primary", use_container_width=True):
            if tok.strip():
                st.session_state.auth = True
                st.rerun()


def new_chat_screen():
    st.markdown(f"""<div style="max-width:880px;padding:48px 0 0">
<h1 style="font-size:34px;line-height:1.2;font-weight:600;letter-spacing:-0.01em;color:{INK}!important;margin:0 0 8px">What do you want to know?</h1>
<p style="font-size:16px;line-height:1.6;color:{MUTED};margin:0 0 36px">{SPACE_INFO['description']}</p>
</div>""", unsafe_allow_html=True)

    st.markdown(f'<p style="font-size:13px;font-weight:500;color:{MUTED};margin:0 0 12px">Try one of these</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, s in enumerate(STARTERS):
        with (c1 if i % 2 == 0 else c2):
            if st.button(f"**{s['label']}**\n\n{s['text']}", key=f"s{i}", use_container_width=True, type="secondary"):
                submit(s["text"])

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    chips = " ".join(f'<span class="table-chip">{t}</span>' for t in TABLES)
    st.markdown(f"""<div class="tables-panel">
<div style="font-size:13px;font-weight:500;color:{MUTED};margin-bottom:8px">Tables in this space</div>
<div>{chips}</div>
<div style="font-size:13px;color:{MUTED};margin-top:8px">Catalog: {SPACE_INFO['catalog']}. Genie only reads from tables in this space.</div>
</div>""", unsafe_allow_html=True)


def working_screen(question, step_idx, tables_used):
    st.markdown(f'<div class="user-bubble">{e(question)}</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    steps = ""
    for i, s in enumerate(WORKING_STEPS):
        if i < step_idx:
            icon, style = f'<span class="step-done">{CHECK_SVG}</span>', f"font-weight:400;color:{INK}"
        elif i == step_idx:
            icon, style = '<span class="step-active"></span>', f"font-weight:500;color:{INK}"
        else:
            icon, style = '<span class="step-pending"></span>', f"font-weight:400;color:{MUTED}"
        extra = ""
        if i == 1 and i <= step_idx and tables_used:
            extra = '<div style="margin-top:6px">' + " ".join(f'<span class="table-chip">{t}</span>' for t in tables_used) + "</div>"
        steps += f'<div class="step-item">{icon}<span style="{style}">{s["label"]}{extra}</span></div>'
    st.markdown(f"""<div class="assistant-row"><div class="db-icon">{DB_SVG}</div>
<div class="working-card"><div class="working-title">Genie is working on it</div>{steps}
<div style="margin-top:18px"><div class="skel" style="width:100%%"></div><div class="skel" style="width:82%%"></div><div class="skel" style="width:64%%"></div></div>
<div style="font-size:13px;color:{MUTED};margin-top:14px">Some questions take a minute.</div></div></div>""", unsafe_allow_html=True)


def answer_screen(conv):
    # Header
    st.markdown(f"""<div class="main-hdr">
<span class="main-hdr-title">{e(conv['title'])}</span>
<span class="space-pill">{SPACE_NAME}</span></div>""", unsafe_allow_html=True)

    for mi, msg in enumerate(conv["messages"]):
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{e(msg["content"])}</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            continue

        gs = msg.get("gs")
        if not gs:
            continue

        # Assistant text
        st.markdown(f"""<div class="assistant-row"><div class="db-icon">{DB_SVG}</div>
<div class="asst-body"><p>{e(gs['text'])}</p>
<div class="genie-note"><strong>How Genie read this:</strong> {e(gs['description'])}</div>
</div></div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Result card
        result = gs.get("result")
        if result and result["rows"]:
            chart_type = pick_chart(result)
            rc = result["row_count"]
            trunc = f" (showing first {len(result['rows'])})" if result["truncated"] else ""

            # Tab state
            tab_key = f"tab_{mi}"
            if tab_key not in st.session_state:
                st.session_state[tab_key] = "Chart" if chart_type else "Table"
            active_tab = st.session_state[tab_key]

            # Build tab buttons HTML
            tab_names = []
            if chart_type:
                tab_names.append("Chart")
            tab_names.extend(["Table", "SQL"])
            tabs_html = ""
            for tn in tab_names:
                cls = "rc-tab active" if tn == active_tab else "rc-tab"
                tabs_html += f'<span class="{cls}">{tn}</span>'

            # Card header + tab selector
            st.markdown(f"""<div class="result-card"><div class="rc-header">
<div><span class="rc-title">Query result</span><br/><span class="rc-subtitle">{rc} row{"s" if rc != 1 else ""}{trunc}</span></div>
<div class="rc-tabs">{tabs_html}</div></div>""", unsafe_allow_html=True)

            # Streamlit radio for tab switching (visually hidden, functional)
            new_tab = st.radio("tab", tab_names, index=tab_names.index(active_tab),
                               horizontal=True, label_visibility="collapsed", key=f"radio_{mi}")
            if new_tab != active_tab:
                st.session_state[tab_key] = new_tab
                st.rerun()

            # Tab content
            if active_tab == "Chart" and chart_type:
                render_chart(result, chart_type)
            elif active_tab == "Table":
                st.markdown(f'<div style="overflow-x:auto">{html_table(result)}</div>', unsafe_allow_html=True)
            elif active_tab == "SQL" and gs.get("sql"):
                st.markdown(html_sql(gs["sql"]), unsafe_allow_html=True)

            # Footer + close card
            elapsed = msg.get("elapsed")
            st.markdown(html_footer(gs.get("tables_used", []), rc, elapsed), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)  # close .result-card

        elif gs.get("sql"):
            st.markdown(f"""<div class="result-card">
<div style="padding:20px"><p style="color:{MUTED};font-size:15px;margin:0">The query ran successfully but returned no rows.</p></div>
{html_sql(gs['sql'])}</div>""", unsafe_allow_html=True)

        # Suggestions — stacked vertically
        sugs = gs.get("suggested_questions", [])
        if sugs:
            st.markdown(f'<div class="suggest-label">Genie suggests</div>', unsafe_allow_html=True)
            for j, q in enumerate(sugs):
                if st.button(q, key=f"sug_{mi}_{j}", use_container_width=True, type="secondary"):
                    submit(q)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)


def composer(disabled=False):
    ph = "Waiting for Genie..." if disabled else "Ask a question about your data"
    q = st.chat_input(ph, disabled=disabled)
    if q and not disabled:
        submit(q)
    st.markdown(f'<div class="composer-note">Genie writes the SQL, so check the query before you rely on a number.</div>', unsafe_allow_html=True)


def process(question):
    idx = st.session_state.idx
    title = question[:50] + "..." if len(question) > 50 else question
    if idx is None:
        c = {"title": title, "messages": []}
        st.session_state.convs.append(c)
        idx = len(st.session_state.convs) - 1
        st.session_state.idx = idx
    else:
        c = st.session_state.convs[idx]
    c["messages"].append({"role": "user", "content": question})
    mock = MOCK_RESPONSES.get(question, DEFAULT_MOCK)
    ph = st.empty()
    for status in ["SUBMITTED", "FETCHING_METADATA", "ASKING_AI", "EXECUTING_QUERY", "COMPLETED"]:
        si = 0
        for j, s in enumerate(WORKING_STEPS):
            if status in s["statuses"]:
                si = j
                break
        with ph.container():
            working_screen(question, si, mock.get("tables_used", []) if si >= 1 else [])
        if status != "COMPLETED":
            time.sleep(0.7)
    ph.empty()
    c["messages"].append({"role": "assistant", "content": mock["text"], "gs": mock, "elapsed": "3.2"})
    st.session_state.pending = None


# ── Main ───────────────────────────────────────────────────────
def main():
    if not st.session_state.auth:
        token_screen()
        return
    sidebar()
    if st.session_state.pending:
        process(st.session_state.pending)
        st.rerun()
    idx = st.session_state.idx
    if idx is not None and idx < len(st.session_state.convs):
        c = st.session_state.convs[idx]
        if c["messages"]:
            answer_screen(c)
            composer()
        else:
            new_chat_screen()
            composer()
    else:
        new_chat_screen()
        composer()


if __name__ == "__main__":
    main()
