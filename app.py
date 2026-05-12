import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, re

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SG Jobs Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg:       #0A0E1A;
    --surface:  #111827;
    --surface2: #1C2637;
    --border:   #1E2D40;
    --accent:   #00C8FF;
    --accent2:  #7C3AED;
    --accent3:  #10B981;
    --text:     #E2E8F0;
    --muted:    #64748B;
    --danger:   #F43F5E;
}

/* Global */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 16px;
}
[data-testid="stSidebar"] {
    background-color: #080D17 !important;
    border-right: 1px solid var(--border);
}
[data-testid="stHeader"] { background: transparent !important; }

/* Headings */
h1, h2, h3, h4 {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
    letter-spacing: -0.02em;
}

/* Metric cards */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0;
    width: 3px; height: 100%;
    background: var(--accent);
}
.metric-card.green::before { background: var(--accent3); }
.metric-card.purple::before { background: var(--accent2); }
.metric-card.red::before   { background: var(--danger); }
.metric-label {
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 6px;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.1;
}
.metric-delta {
    font-size: 0.8rem;
    color: var(--accent3);
    margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
}

/* Section headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 32px 0 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}
.section-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    background: var(--accent);
    color: var(--bg);
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.08em;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text);
}

/* Insight box */
.insight-box {
    background: var(--surface2);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.95rem;
    color: var(--text);
}

/* Sidebar labels */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text) !important;
    font-size: 0.9rem !important;
}

/* Select boxes */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-size: 1rem !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: var(--muted);
    font-size: 0.9rem;
    font-weight: 500;
    border-radius: 7px;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: var(--bg) !important;
    font-weight: 600;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── DB connection ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    db_path = os.path.join(os.path.dirname(__file__), "./data/sgJobData.db")
    return duckdb.connect(db_path, read_only=True)

con = get_conn()

# ── Helpers ─────────────────────────────────────────────────────────────────────
PALETTE = ["#00C8FF","#7C3AED","#10B981","#F43F5E","#F59E0B",
           "#3B82F6","#EC4899","#14B8A6","#8B5CF6","#EF4444",
           "#22D3EE","#A3E635","#FB923C","#C084FC","#34D399"]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#E2E8F0", size=13),
    title_font=dict(family="DM Sans", size=15, color="#E2E8F0"),
    margin=dict(l=10, r=10, t=40, b=10),
)

_AXIS  = dict(gridcolor="#1E2D40", linecolor="#1E2D40", tickfont=dict(size=12))
_LGND  = dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12))

def apply_style(fig, **extra):
    fig.update_layout(**CHART_LAYOUT, **extra)
    if "xaxis" not in extra:
        fig.update_xaxes(**_AXIS)
    if "yaxis" not in extra:
        fig.update_yaxes(**_AXIS)
    if "legend" not in extra and "showlegend" not in extra:
        fig.update_layout(legend=_LGND)
    return fig

def q(sql):
    return con.sql(sql).df()

def metric_card(label, value, delta=None, color="blue"):
    color_cls = {"green":"green","purple":"purple","red":"red"}.get(color, "")
    delta_html = f'<div class="metric-delta">▲ {delta}</div>' if delta else ""
    return f"""
    <div class="metric-card {color_cls}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>"""

def section(tag, title):
    st.markdown(f"""
    <div class="section-header">
        <span class="section-tag">{tag}</span>
        <span class="section-title">{title}</span>
    </div>""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 8px;">
        <div style="font-family:'JetBrains Mono',monospace; font-size:11px;
                    color:#00C8FF; letter-spacing:0.15em; text-transform:uppercase;">
            SG Jobs Intelligence
        </div>
        <div style="font-size:1.5rem; font-weight:700; color:#E2E8F0; line-height:1.2; margin-top:4px;">
            Talent Market<br>Analytics
        </div>
        <div style="font-size:0.85rem; color:#64748B; margin-top:6px;">
            1M+ job postings · Oct 2022 – May 2024
        </div>
    </div>
    <hr style="margin: 12px 0;">
    """, unsafe_allow_html=True)

    st.markdown("**🗂 Industry Filter**")
    all_cats = q("""
        SELECT regexp_extract(categories,'"category":"([^"]+)"',1) AS cat, COUNT(*) AS cnt
        FROM sg_job_data WHERE categories IS NOT NULL
        GROUP BY cat ORDER BY cnt DESC LIMIT 20
    """)["cat"].tolist()
    selected_cats = st.multiselect("Industries", all_cats, default=[], label_visibility="collapsed")

    st.markdown("**💼 Employment Type**")
    emp_types = ["Permanent","Full Time","Contract","Part Time","Temporary","Internship/Attachment","Freelance"]
    selected_emp = st.multiselect("Employment Type", emp_types, default=[], label_visibility="collapsed")

    st.markdown("**📊 Seniority Level**")
    levels = ["Fresh/entry level","Junior Executive","Non-executive","Executive",
              "Senior Executive","Professional","Manager","Middle Management","Senior Management"]
    selected_levels = st.multiselect("Seniority", levels, default=[], label_visibility="collapsed")

    st.markdown("**💰 Salary Range (SGD/month)**")
    sal_min, sal_max = st.slider("Salary", 0, 30000, (0, 30000), step=500, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.78rem; color:#64748B; line-height:1.6;">
        <b style="color:#E2E8F0;">Data Source</b><br>
        MyCareersFuture.sg<br>
        Module 1 Assignment<br>
        Singapore Jobs Analytics
    </div>""", unsafe_allow_html=True)

# ── Build WHERE clause ──────────────────────────────────────────────────────────
def build_where(extra=""):
    clauses = ["average_salary BETWEEN {} AND {}".format(sal_min if sal_min > 0 else 1, sal_max)]
    if selected_cats:
        cats_str = ", ".join(f"'{c}'" for c in selected_cats)
        clauses.append(f"regexp_extract(categories,'\"category\":\"([^\"]+)\"',1) IN ({cats_str})")
    if selected_emp:
        emp_str = ", ".join(f"'{e}'" for e in selected_emp)
        clauses.append(f"employmentTypes IN ({emp_str})")
    if selected_levels:
        lvl_str = ", ".join(f"'{l}'" for l in selected_levels)
        clauses.append(f"positionLevels IN ({lvl_str})")
    if extra:
        clauses.append(extra)
    return "WHERE " + " AND ".join(clauses)

W = build_where()

# ── TABS ────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Overview",
    "🏭  Industry",
    "💰  Salary",
    "📈  Trends",
    "🔍  Explorer",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div style="padding: 24px 0 8px;">
        <div style="font-family:'JetBrains Mono',monospace; font-size:11px;
                    color:#00C8FF; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:6px;">
            Dashboard · Module 1 Assignment
        </div>
        <h1 style="font-size:2rem; font-weight:700; margin:0; color:#E2E8F0;">
            Singapore Jobs Market Intelligence
        </h1>
        <p style="color:#64748B; font-size:1rem; margin-top:8px;">
            Comprehensive analytics across 1M+ job postings to support talent acquisition strategy
        </p>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    kpi = q(f"""
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT postedCompany_name) AS companies,
            ROUND(AVG(average_salary), 0) AS avg_sal,
            COUNT(DISTINCT regexp_extract(categories,'"category":"([^"]+)"',1)) AS industries
        FROM sg_job_data {W}
    """).iloc[0]

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(metric_card("Total Postings", f"{int(kpi['total']):,}"), unsafe_allow_html=True)
    c2.markdown(metric_card("Active Companies", f"{int(kpi['companies']):,}", color="purple"), unsafe_allow_html=True)
    c3.markdown(metric_card("Avg Monthly Salary", f"S${int(kpi['avg_sal']):,}", color="green"), unsafe_allow_html=True)
    c4.markdown(metric_card("Industries", f"{int(kpi['industries'])}", color="red"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2: Top industries + salary bands
    section("01", "Market Composition")
    col_a, col_b = st.columns([3, 2])

    with col_a:
        top_ind = q(f"""
            SELECT regexp_extract(categories,'"category":"([^"]+)"',1) AS industry,
                   COUNT(*) AS postings, ROUND(AVG(average_salary),0) AS avg_salary
            FROM sg_job_data {W}
            AND categories IS NOT NULL
            GROUP BY industry ORDER BY postings DESC LIMIT 12
        """)
        fig = px.bar(top_ind, x="postings", y="industry", orientation="h",
                     color="avg_salary", color_continuous_scale=["#1E2D40","#00C8FF","#7C3AED"],
                     labels={"postings":"Job Postings","industry":"","avg_salary":"Avg Salary (S$)"},
                     title="Top 12 Industries by Posting Volume")
        apply_style(fig, height=380, coloraxis_colorbar=dict(
            title="Avg S$", tickfont=dict(size=11), len=0.6))
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        bands = q(f"""
            SELECT
                CASE WHEN average_salary < 3000 THEN 'Low (<S$3K)'
                     WHEN average_salary <= 6000 THEN 'Mid (S$3K–6K)'
                     WHEN average_salary <= 10000 THEN 'High (S$6K–10K)'
                     ELSE 'Premium (>S$10K)' END AS band,
                COUNT(*) AS count
            FROM sg_job_data {W}
            GROUP BY band ORDER BY MIN(average_salary)
        """)
        fig2 = px.pie(bands, values="count", names="band",
                      color_discrete_sequence=["#00C8FF","#7C3AED","#10B981","#F43F5E"],
                      title="Salary Band Distribution", hole=0.55)
        apply_style(fig2, height=380,
                           legend=dict(orientation="h", y=-0.1, font=dict(size=11)))
        fig2.update_traces(textfont_size=12)
        st.plotly_chart(fig2, use_container_width=True)

    # Row 3: Seniority + Employment type
    section("02", "Workforce Composition")
    col_c, col_d = st.columns(2)

    with col_c:
        seniority = q(f"""
            SELECT positionLevels AS level, COUNT(*) AS count,
                   ROUND(AVG(average_salary),0) AS avg_salary
            FROM sg_job_data {W}
            AND positionLevels IS NOT NULL
            GROUP BY level ORDER BY avg_salary
        """)
        fig3 = px.bar(seniority, x="avg_salary", y="level", orientation="h",
                      text="count", color="count",
                      color_continuous_scale=["#1E2D40","#10B981"],
                      title="Seniority vs Avg Salary",
                      labels={"avg_salary":"Avg Salary (S$)","level":"","count":"Postings"})
        fig3.update_traces(texttemplate='%{text:,}', textposition='outside',
                           textfont=dict(size=11, color="#64748B"))
        apply_style(fig3, height=320, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        emp = q(f"""
            SELECT employmentTypes AS type, COUNT(*) AS count
            FROM sg_job_data {W}
            AND employmentTypes IS NOT NULL
            GROUP BY type ORDER BY count DESC
        """)
        fig4 = px.bar(emp, x="type", y="count",
                      color="count", color_continuous_scale=["#1E2D40","#7C3AED"],
                      title="Postings by Employment Type",
                      labels={"type":"","count":"Postings"})
        apply_style(fig4, height=320, showlegend=False)
        fig4.update_xaxes(tickangle=-20)
        st.plotly_chart(fig4, use_container_width=True)

    # Key Insights
    section("03", "Key Insights")
    ins_cols = st.columns(3)
    insights = [
        ("🔵", "IT dominates demand", "Information Technology & Engineering lead with 100K+ postings each, signaling strong digital transformation investment."),
        ("🟣", "Mid-salary majority", "64% of roles fall in the S$3K–6K monthly bracket, anchoring Singapore's professional middle market."),
        ("🟢", "Recruitment agencies dominate", "Top 5 posting companies are all recruitment agencies, reflecting high contractor & temp workforce demand."),
    ]
    for col, (icon, title, body) in zip(ins_cols, insights):
        col.markdown(f"""
        <div class="insight-box">
            <div style="font-weight:600; margin-bottom:6px;">{icon} {title}</div>
            <div style="color:#94A3B8; font-size:0.9rem; line-height:1.5;">{body}</div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INDUSTRY
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    section("01", "Industry Deep Dive")

    col1, col2 = st.columns([1,3])
    with col1:
        selected_industry = st.selectbox("Select Industry", all_cats)

    ind_stats = q(f"""
        SELECT COUNT(*) AS total,
               ROUND(AVG(average_salary),0) AS avg_sal,
               ROUND(MEDIAN(average_salary),0) AS median_sal,
               MAX(average_salary) AS max_sal,
               COUNT(DISTINCT postedCompany_name) AS companies
        FROM sg_job_data
        WHERE regexp_extract(categories,'"category":"([^"]+)"',1) = '{selected_industry}'
          AND average_salary > 0
    """).iloc[0]

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(metric_card("Postings", f"{int(ind_stats['total']):,}"), unsafe_allow_html=True)
    k2.markdown(metric_card("Avg Salary", f"S${int(ind_stats['avg_sal']):,}", color="green"), unsafe_allow_html=True)
    k3.markdown(metric_card("Median Salary", f"S${int(ind_stats['median_sal']):,}", color="purple"), unsafe_allow_html=True)
    k4.markdown(metric_card("Companies", f"{int(ind_stats['companies']):,}", color="red"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        top_roles = q(f"""
            SELECT title, COUNT(*) AS count, ROUND(AVG(average_salary),0) AS avg_sal
            FROM sg_job_data
            WHERE regexp_extract(categories,'"category":"([^"]+)"',1) = '{selected_industry}'
              AND average_salary > 0
            GROUP BY title ORDER BY count DESC LIMIT 10
        """)
        fig = px.bar(top_roles, x="count", y="title", orientation="h",
                     color="avg_sal", color_continuous_scale=["#1E2D40","#00C8FF"],
                     title=f"Top Roles in {selected_industry}",
                     labels={"count":"Postings","title":"","avg_sal":"Avg S$"})
        fig.update_yaxes(categoryorder="total ascending")
        apply_style(fig, height=360)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        salary_dist = q(f"""
            SELECT average_salary FROM sg_job_data
            WHERE regexp_extract(categories,'"category":"([^"]+)"',1) = '{selected_industry}'
              AND average_salary BETWEEN 500 AND 30000
            LIMIT 5000
        """)
        fig2 = px.histogram(salary_dist, x="average_salary", nbins=40,
                            color_discrete_sequence=["#7C3AED"],
                            title=f"Salary Distribution — {selected_industry}",
                            labels={"average_salary":"Monthly Salary (S$)"})
        apply_style(fig2, height=360)
        st.plotly_chart(fig2, use_container_width=True)

    section("02", "Top Hiring Companies")
    top_cos = q(f"""
        SELECT postedCompany_name AS company,
               COUNT(*) AS postings,
               ROUND(AVG(average_salary),0) AS avg_salary
        FROM sg_job_data
        WHERE regexp_extract(categories,'"category":"([^"]+)"',1) = '{selected_industry}'
          AND average_salary > 0
        GROUP BY company ORDER BY postings DESC LIMIT 15
    """)
    fig3 = px.scatter(top_cos, x="postings", y="avg_salary", text="company",
                      size="postings", color="avg_salary",
                      color_continuous_scale=["#00C8FF","#7C3AED","#F43F5E"],
                      title="Companies: Volume vs Salary",
                      labels={"postings":"Job Postings","avg_salary":"Avg Salary (S$)","company":""})
    fig3.update_traces(textposition="top center", textfont=dict(size=10, color="#94A3B8"))
    apply_style(fig3, height=400)
    st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SALARY
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    section("01", "Salary Intelligence")

    # Salary heatmap by industry × seniority
    heat_data = q(f"""
        SELECT
            regexp_extract(categories,'"category":"([^"]+)"',1) AS industry,
            positionLevels AS seniority,
            ROUND(AVG(average_salary),0) AS avg_salary,
            COUNT(*) AS count
        FROM sg_job_data
        WHERE categories IS NOT NULL AND positionLevels IS NOT NULL
          AND average_salary BETWEEN 500 AND 30000
        GROUP BY industry, seniority
        HAVING count > 50
    """)

    # Pivot for heatmap
    top12_ind = heat_data.groupby("industry")["count"].sum().nlargest(12).index.tolist()
    seniority_order = ["Fresh/entry level","Junior Executive","Non-executive","Executive",
                       "Senior Executive","Professional","Manager","Middle Management","Senior Management"]
    heat_pivot = (heat_data[heat_data["industry"].isin(top12_ind)]
                  .pivot_table(index="industry", columns="seniority", values="avg_salary")
                  .reindex(columns=[s for s in seniority_order if s in heat_data["seniority"].unique()]))

    fig = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns.tolist(),
        y=heat_pivot.index.tolist(),
        colorscale=[[0,"#0A0E1A"],[0.3,"#1E3A5F"],[0.6,"#00C8FF"],[1,"#7C3AED"]],
        text=[[f"S${int(v):,}" if not pd.isna(v) else "" for v in row] for row in heat_pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10),
        hoverongaps=False,
    ))
    apply_style(fig, title="Avg Monthly Salary: Industry × Seniority",
                      height=480, xaxis=dict(tickangle=-30, tickfont=dict(size=11)),
                      yaxis=dict(tickfont=dict(size=11)))
    st.plotly_chart(fig, use_container_width=True)

    section("02", "Salary Benchmarks")
    col_a, col_b = st.columns(2)

    with col_a:
        # Box plot top industries
        box_data = q(f"""
            SELECT regexp_extract(categories,'"category":"([^"]+)"',1) AS industry,
                   average_salary
            FROM sg_job_data
            WHERE categories IS NOT NULL AND average_salary BETWEEN 500 AND 20000
            QUALIFY COUNT(*) OVER (PARTITION BY regexp_extract(categories,'"category":"([^"]+)"',1)) > 500
            LIMIT 50000
        """)
        top10 = box_data.groupby("industry")["average_salary"].median().nlargest(10).index.tolist()
        box_filtered = box_data[box_data["industry"].isin(top10)]

        fig2 = px.box(box_filtered, x="industry", y="average_salary",
                      color="industry", color_discrete_sequence=PALETTE,
                      title="Salary Range by Top 10 Industries",
                      labels={"average_salary":"Monthly Salary (S$)","industry":""})
        apply_style(fig2, height=400, showlegend=False)
        fig2.update_xaxes(tickangle=-30, tickfont=dict(size=10))
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        # Salary by employment type
        emp_sal = q(f"""
            SELECT employmentTypes AS type, ROUND(AVG(average_salary),0) AS avg_sal,
                   ROUND(MEDIAN(average_salary),0) AS median_sal, COUNT(*) AS count
            FROM sg_job_data
            WHERE employmentTypes IS NOT NULL AND average_salary BETWEEN 500 AND 30000
            GROUP BY type ORDER BY avg_sal DESC
        """)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Avg Salary", x=emp_sal["type"], y=emp_sal["avg_sal"],
                               marker_color="#00C8FF", opacity=0.85))
        fig3.add_trace(go.Bar(name="Median Salary", x=emp_sal["type"], y=emp_sal["median_sal"],
                               marker_color="#7C3AED", opacity=0.85))
        apply_style(fig3, barmode="group",
                           title="Avg vs Median Salary by Employment Type",
                           yaxis_title="Salary (S$)", height=400)
        fig3.update_xaxes(tickangle=-25, tickfont=dict(size=11))
        st.plotly_chart(fig3, use_container_width=True)

    section("03", "Top-Paying Roles")
    top_paying = q(f"""
        SELECT title,
               regexp_extract(categories,'"category":"([^"]+)"',1) AS industry,
               ROUND(AVG(average_salary),0) AS avg_salary,
               COUNT(*) AS postings
        FROM sg_job_data {W}
        AND average_salary > 0
        GROUP BY title, industry
        HAVING postings >= 5
        ORDER BY avg_salary DESC LIMIT 20
    """)
    fig4 = px.bar(top_paying, x="avg_salary", y="title", orientation="h",
                  color="industry", color_discrete_sequence=PALETTE,
                  text="avg_salary",
                  title="Top 20 Highest-Paying Roles (≥5 postings)",
                  labels={"avg_salary":"Avg Monthly Salary (S$)","title":"","industry":"Industry"})
    fig4.update_traces(texttemplate="S$%{text:,.0f}", textposition="outside",
                       textfont=dict(size=11))
    fig4.update_yaxes(categoryorder="total ascending")
    apply_style(fig4, height=520)
    st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<br>", unsafe_allow_html=True)
    section("01", "Temporal Trends")

    monthly = q("""
        SELECT DATE_TRUNC('month', metadata_originalPostingDate) AS month,
               COUNT(*) AS postings,
               ROUND(AVG(average_salary),0) AS avg_salary,
               COUNT(DISTINCT postedCompany_name) AS companies
        FROM sg_job_data
        WHERE metadata_originalPostingDate IS NOT NULL AND average_salary > 0
        GROUP BY month ORDER BY month
    """)
    monthly = monthly[monthly["month"] >= "2023-01-01"]  # filter ramp-up

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=monthly["month"], y=monthly["postings"],
                         name="Postings", marker_color="#1E3A5F", opacity=0.9), secondary_y=False)
    fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["avg_salary"],
                             name="Avg Salary", line=dict(color="#00C8FF", width=2.5),
                             mode="lines+markers", marker=dict(size=5)), secondary_y=True)
    apply_style(fig, title="Monthly Job Postings vs Average Salary",
                      height=380, legend=dict(orientation="h", y=1.1))
    fig.update_yaxes(title_text="Job Postings", secondary_y=False,
                     gridcolor="#1E2D40", title_font=dict(size=12))
    fig.update_yaxes(title_text="Avg Salary (S$)", secondary_y=True,
                     gridcolor="rgba(0,0,0,0)", title_font=dict(size=12))
    st.plotly_chart(fig, use_container_width=True)

    section("02", "Industry Momentum")
    # Quarter-over-quarter growth by industry
    qoq = q("""
        SELECT
            regexp_extract(categories,'"category":"([^"]+)"',1) AS industry,
            DATE_TRUNC('quarter', metadata_originalPostingDate) AS quarter,
            COUNT(*) AS postings
        FROM sg_job_data
        WHERE metadata_originalPostingDate >= '2023-01-01'
          AND categories IS NOT NULL
        GROUP BY industry, quarter
        ORDER BY industry, quarter
    """)

    top6 = qoq.groupby("industry")["postings"].sum().nlargest(6).index.tolist()
    qoq_top = qoq[qoq["industry"].isin(top6)]
    fig2 = px.line(qoq_top, x="quarter", y="postings", color="industry",
                   color_discrete_sequence=PALETTE,
                   title="Quarterly Posting Trends — Top 6 Industries",
                   labels={"postings":"Postings","quarter":"Quarter","industry":"Industry"},
                   markers=True)
    apply_style(fig2, height=380)
    st.plotly_chart(fig2, use_container_width=True)

    section("03", "Demand Shifts")
    col_a, col_b = st.columns(2)

    with col_a:
        repost = q("""
            SELECT
                CASE WHEN metadata_repostCount = 0 THEN 'First Post'
                     WHEN metadata_repostCount <= 2 THEN 'Reposted 1-2x'
                     WHEN metadata_repostCount <= 5 THEN 'Reposted 3-5x'
                     ELSE 'Reposted 6x+' END AS category,
                COUNT(*) AS count,
                ROUND(AVG(average_salary),0) AS avg_sal
            FROM sg_job_data WHERE average_salary > 0
            GROUP BY category ORDER BY MIN(metadata_repostCount)
        """)
        fig3 = px.bar(repost, x="category", y="count", color="avg_sal",
                      color_continuous_scale=["#1E2D40","#F43F5E"],
                      title="Reposting Behaviour (hard-to-fill roles)",
                      labels={"count":"Postings","category":"","avg_sal":"Avg S$"})
        apply_style(fig3, height=340)
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        apps = q("""
            SELECT
                CASE WHEN metadata_totalNumberJobApplication < 5 THEN '<5 apps'
                     WHEN metadata_totalNumberJobApplication < 20 THEN '5-19 apps'
                     WHEN metadata_totalNumberJobApplication < 50 THEN '20-49 apps'
                     ELSE '50+ apps' END AS tier,
                COUNT(*) AS count,
                ROUND(AVG(average_salary),0) AS avg_sal
            FROM sg_job_data WHERE metadata_totalNumberJobApplication IS NOT NULL AND average_salary > 0
            GROUP BY tier
        """)
        fig4 = px.bar(apps, x="tier", y="count", color="avg_sal",
                      color_continuous_scale=["#1E2D40","#10B981"],
                      title="Application Volume per Posting",
                      labels={"count":"Postings","tier":"Applications Received","avg_sal":"Avg S$"})
        apply_style(fig4, height=340)
        st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("<br>", unsafe_allow_html=True)
    section("01", "Job Search Explorer")

    search_col, filter_col = st.columns([3, 1])
    with search_col:
        keyword = st.text_input("🔍 Search job titles", placeholder="e.g. data engineer, software, accountant...",
                                 label_visibility="collapsed")
    with filter_col:
        sort_by = st.selectbox("Sort by", ["Salary (High→Low)", "Salary (Low→High)", "Postings (Most)"],
                               label_visibility="collapsed")

    sort_map = {
        "Salary (High→Low)": "avg_salary DESC",
        "Salary (Low→High)": "avg_salary ASC",
        "Postings (Most)": "cnt DESC",
    }

    kw_clause = f"AND LOWER(title) LIKE '%{keyword.lower()}%'" if keyword else ""
    results = q(f"""
        SELECT title,
               regexp_extract(categories,'"category":"([^"]+)"',1) AS industry,
               positionLevels AS seniority,
               employmentTypes AS type,
               ROUND(AVG(average_salary),0) AS avg_salary,
               ROUND(MIN(salary_minimum),0) AS min_sal,
               ROUND(MAX(salary_maximum),0) AS max_sal,
               COUNT(*) AS cnt,
               AVG(metadata_totalNumberJobApplication) AS avg_apps
        FROM sg_job_data {W} {kw_clause}
        GROUP BY title, industry, seniority, type
        HAVING cnt >= 3
        ORDER BY {sort_map[sort_by]}
        LIMIT 200
    """)

    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace; font-size:11px;
                color:#00C8FF; padding: 8px 0; letter-spacing:0.08em;">
        ↳ {len(results):,} role combinations found
    </div>""", unsafe_allow_html=True)

    if not results.empty:
        # Format for display
        display = results.copy()
        display["avg_salary"] = display["avg_salary"].apply(lambda x: f"S${int(x):,}" if pd.notna(x) else "-")
        display["sal_range"] = display.apply(
            lambda r: f"S${int(r['min_sal']):,}–{int(r['max_sal']):,}" if pd.notna(r['min_sal']) else "-", axis=1)
        display["avg_apps"] = display["avg_apps"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
        display = display.rename(columns={
            "title":"Title","industry":"Industry","seniority":"Seniority",
            "type":"Type","avg_salary":"Avg Salary","sal_range":"Range",
            "cnt":"Postings","avg_apps":"Avg Apps"
        })
        st.dataframe(
            display[["Title","Industry","Seniority","Type","Avg Salary","Range","Postings","Avg Apps"]],
            use_container_width=True,
            height=480,
        )

        section("02", "Salary Distribution for Search Results")
        sal_hist = q(f"""
            SELECT average_salary FROM sg_job_data {W} {kw_clause}
            AND average_salary BETWEEN 500 AND 25000
            LIMIT 10000
        """)
        fig = px.histogram(sal_hist, x="average_salary", nbins=50,
                           color_discrete_sequence=["#00C8FF"],
                           title=f"Salary Distribution{' for: ' + keyword if keyword else ''}",
                           labels={"average_salary":"Monthly Salary (S$)"})
        apply_style(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<hr>
<div style="text-align:center; color:#64748B; font-size:0.8rem; padding: 12px 0;
            font-family:'JetBrains Mono',monospace; letter-spacing:0.05em;">
    SG Jobs Intelligence · Module 1 Assignment · Data: MyCareersFuture.sg · 1,048,585 postings
</div>
""", unsafe_allow_html=True)
