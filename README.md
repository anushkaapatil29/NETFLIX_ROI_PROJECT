Content ROI project
====================

This repository contains a small synthetic-data pipeline and SQL queries to analyze which Netflix Originals drive new sign-ups.

Files added:
- `data_generation.py` — generate `netflix_content.csv` (500 shows) and `user_base.csv` (10,000 users)
- `attribution.py` — run last-touch attribution (7-day window) and write `user_attribution_enriched.csv`
- `sql_queries.sql` — PostgreSQL-compatible queries for Monthly Churn, LTV by Genre, and Content ROI
- `executive_summary.md` — 3-slide template for Product Manager presentation

Quick start (Windows PowerShell)

1) Create a Python environment and install dependencies (recommended):

```powershell
# create & activate a venv (Windows PowerShell)
python -m venv venv; .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you use VS Code, after creating the venv open the Command Palette (Ctrl+Shift+P) -> "Python: Select Interpreter" and choose the `venv` interpreter. This will allow the editor to resolve imports (pandas, numpy, matplotlib, seaborn). The repository also includes `.vscode/settings.json` to recommend the venv path.

2) Generate datasets:

```powershell
python data_generation.py
```
This writes `netflix_content.csv` and `user_base.csv` in the repository root.

3) Run attribution:

```powershell
python attribution.py
```
This reads the CSVs and writes `user_attribution_enriched.csv` with `attributed_show_id` populated for users whose `sign_up_date` is within 7 days of a show's `release_date` (last-touch).

4) Load CSVs into your analytical DB or run queries locally.

Notes & next steps
- The synthetic generator includes a small fraction of signups intentionally near release dates to create attribution signal.
- For production-grade analysis, replace synthetic data with production data, add tests, and implement multi-touch attribution for validation.

Static visuals and interactive outputs
-----------------------------------

I added a `plots/` folder (generated when you run the analysis) with high-resolution PNGs, and interactive HTML charts created with Plotly. Files to look for after running the scripts:

- `plots/avg_ltv_by_genre.png` — high-res bar chart of average LTV by genre
- `plots/ltv_cac_sci_fi_comedy.png` — high-res LTV:CAC comparison for Sci‑Fi vs Comedy
- `plots/sensitivity_attribution_window.png` — sensitivity analysis across 3/7/14 day windows
- `plots/interactive_ltv_by_genre.html` — interactive Plotly chart (open in browser)
- `plots/interactive_ltv_cac.html` — interactive Plotly chart (open in browser)

To regenerate visual outputs run:

```powershell
python analysis_and_plots.py
python sensitivity_analysis.py
python viz_plotly.py
```

To run the Streamlit demo (optional):

```powershell
pip install streamlit
streamlit run app.py
```

To embed the static images into your portfolio README, open `README.md` in an editor and add markdown image links pointing to `plots/*.png` (they will display when pushed to GitHub).
