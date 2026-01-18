# Content ROI — 3-Slide Executive Summary

Slide 1 — Key Question & Headline

- Title: "Which Netflix Originals Drive New Sign-ups?"
- One-line answer (example): "Sci‑Fi titles deliver the highest LTV per attributed user, but Comedy shows have a better LTV:CAC ratio after accounting for production cost."
- Metrics shown (visuals):
  - Bar chart: Average LTV by Genre (top 6 genres)
  - Bar chart: LTV to CAC ratio (LTV / (Production Cost / #Attributed Signups)) for Sci‑Fi and Comedy
- Action callout: "Recommend targeted reinvestment in [genre] for next quarter and experiment with lower-cost Sci‑Fi formats if CAC too high."

Slide 2 — Findings & Evidence

- Subheading: What we measured
  - "Attributed users: last-touch within 7 days of content release"
  - LTV defined as monthly_revenue * months_active (observed)
  - CAC approximated as production_cost / #attributed_users
- Table/visual: Top 5 shows by ROI (revenue attributed - production_cost) and top 5 by absolute revenue
- Bullet summary of key numbers (example placeholders):
  - Sci‑Fi: avg LTV = $X, avg CAC = $Y, LTV:CAC = Z
  - Comedy: avg LTV = $A, avg CAC = $B, LTV:CAC = C
- Short note on confidence and data limitations (sample period, synthetic data assumptions, attribution window)

Slide 3 — Recommendation & Next Steps

- Recommendation: concise action (e.g., "Invest in targeted Sci‑Fi franchises with lower per‑episode production cost OR invest in Comedy marketing which yields better LTV:CAC")
- Suggested experiments (A/B tests or small pilots):
  - Price / promotion experiments around Comedy releases to grow attributed signups
  - Lower-cost Sci‑Fi pilots (limited series) to reduce CAC and monitor LTV
- Analytics follow-ups (operational steps):
  - Extend attribution beyond 7-day window as sensitivity analysis
  - Use multi-touch attribution to validate last-touch conclusions
  - Track cohort retention and LTV over 12+ months

Appendix (one-liner): Data sources and SQL queries available in `sql_queries.sql` and scripts `data_generation.py` / `attribution.py`.
