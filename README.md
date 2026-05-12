# SG Jobs Intelligence Dashboard

**Module 1 Assignment — Singapore Jobs Analytics**  
NTU Data Coaching Programme · May 2024

---

## Business Case

**Scenario**: Talent acquisition teams struggle to benchmark salaries and identify high-demand roles across Singapore's job market efficiently.

**Objective**: Transform 1,048,585 real job postings from MyCareersFuture.sg into an interactive dashboard that enables data-driven hiring and compensation decisions.

**Users**: HR Directors, Talent Acquisition Managers, Career Coaches  
**Value**: Replace manual benchmarking (days) with real-time analytics (seconds)

---

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/jinava/sg-jobs-analytics.git
cd sg-jobs-analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Place DuckDB file
# Ensure sgJobData.db is in the project data directory

# 4. Run dashboard
streamlit run app.py
# Open: http://localhost:8501

Or

# 5. Run Online
# Open: https://sg-jobs-analytics.streamlit.app

```

---

## Streamlit Cloud Deployment

1. Push this repository to GitHub
2. Log in at [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select this repo → `main` branch → `app.py`
4. Click **Deploy** — dependencies install automatically

> **Note**: For DuckDB files > 100MB, use [Git LFS](https://git-lfs.github.com/) or host the file externally and load via URL.

---

## Project Structure

```
sg-jobs-analytics/
├── app.py                    # Main Streamlit dashboard
├── data/
│   └── sgJobData.db          # DuckDB database (1,048,585 rows)
├── requirements.txt          # Python dependencies
├── environment.yml           # Conda Environment
└── .streamlit/
    └── config.toml           # Dark theme configuration
```

---

## Dashboard Tabs

| Tab | Purpose |
|-----|---------|
| 📊 Overview | KPI cards, industry breakdown, salary bands, seniority analysis |
| 🏭 Industry | Per-sector deep-dive: top roles, salary dist, top companies |
| 💰 Salary | Heatmap, box plots, top-paying roles benchmarking |
| 📈 Trends | Monthly/quarterly trends, repost analysis, application tiers |
| 🔍 Explorer | Free-text job search with salary histogram |

---

## Data Pipeline Summary

| Step | Tool | Description |
|------|------|-------------|
| Load | DuckDB | `read_csv_auto()` → 1M+ rows in-process |
| Clean | SQL | Exclude 3,988 NULL salary rows |
| Engineer | SQL | `regexp_extract()` for categories, `CASE WHEN` salary bands |
| Analyse | SQL | CTEs, window functions, `DATE_TRUNC()`, `MEDIAN()` |
| Visualise | Streamlit + Plotly | 5-tab dark-theme interactive dashboard |

---

## Key Findings

- **64%** of roles fall in the S$3K–6K monthly band (mid-market)
- **Banking & Finance** (S$7,695) and **IT** (S$7,308) are the top-paying sectors
- **Engineering** is the best ROI: high volume (99K postings) + solid salary (S$4,990)
- Job posting volume grew **8× from Q1 to Q3 2023**, then stabilised at ~225K/quarter
- **Senior Management** averages S$11,561 — **4.2× entry level**

---

## Tech Stack

- **DuckDB** ≥ 0.10.0 — in-process OLAP engine
- **Streamlit** ≥ 1.35.0 — web framework
- **Plotly** ≥ 5.20.0 — interactive charts
- **Pandas** ≥ 2.0.0 — DataFrames

---

## Deliverables

- ✅ `app.py` — Streamlit dashboard (5 tabs, dark theme, 16px+ fonts)
- ✅ `requirements.txt` + `.streamlit/config.toml`
- ✅ `environment.yml` + `.streamlit/config.toml`
