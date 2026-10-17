# Results and evidence archive

Packaging does not change SQL, filters or empirical values.

| Record | Role |
|---|---|
| [audit_v1/](audit_v1/) | All original audit CSV/JSON, Chinese HTML and reproducibility evidence |
| [analysis/](analysis/) | All fixed follow-up cohort, daily, weekly/device and follow-up results |
| [screenshots/](screenshots/) | Existing browser-reviewed local dashboard captures |
| [verification.json](verification.json) | Preserved implementation-stage verification |
| [packaging_verification.json](packaging_verification.json) | New packaging checks, not new analysis |

Start with the [comparison CSV](analysis/session_comparisons.csv), [full JSON](analysis/analysis_results.json), [Chinese results](analysis/固定分析结果与解释.html) or [Chinese audit](audit_v1/GA4本地数据审计.html).

GitHub displays Markdown/source files. Download HTML for local viewing; run Streamlit locally for interactive filtering.

## History

1. Audit v1 identified feasible questions and limitations before the dashboard existed.
2. Fixed analysis v2 retained anomaly/tie diagnostics and added descriptive comparisons and the local dashboard.
3. Repository packaging adds English/Chinese navigation and SQL documentation without new experiments.

Historical prose may say “audit only” or “dashboard not yet built”; it describes that milestone. The root README describes current status.

scripts/audit.py regenerates audit CSV/JSON; historical audit HTML is retained. scripts/report_analysis.py regenerates the current analysis HTML. Preserve a copy before comparing future rebuilds. Existing locality-specific references describe earlier runs, not runtime requirements.
