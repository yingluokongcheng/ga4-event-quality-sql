# Project structure

Repository: [yingluokongcheng/ga4-event-quality-sql](https://github.com/yingluokongcheng/ga4-event-quality-sql).

```text
ga4-event-quality-sql/
├── README.md / README.zh-CN.md    English homepage / Chinese explanation
├── NOTICE.md                     Attribution and data-use boundaries
├── app.py                        Three-page local dashboard
├── dashboard/data.py             Shared read-only reporting SQL
├── sql/
│   ├── 01_stage.sql              Events and composite-key sessions
│   ├── 02_paths.sql              Strict/compatible paths and follow-up
│   ├── 03_quality.sql            Transaction and stratified quality
│   └── marts/
│       ├── 04_reporting.sql      Fixed flags and reporting tables
│       └── summary.sql           Cohort/device metrics
├── scripts/                      Download, audit, analysis, report, setup
├── tests/                        Semantics, reporting, dashboard
├── docs/
│   ├── SQL_WALKTHROUGH.md         Implemented SQL decisions
│   ├── METRICS.md                 Units, denominators, time anchors
│   ├── PROTOCOL.md                Frozen analysis plan
│   ├── STRUCTURE.md               This guide
│   ├── RELEASE_REVIEW.md          Review status and verification boundary
│   └── AUDIT_V1_README.md         Historical documentation
├── reports/
│   ├── README.md                 Results/history index
│   ├── audit_v1/                 All original audit results
│   ├── analysis/                 All fixed follow-up results
│   ├── screenshots/              Three dashboard captures
│   ├── verification.json         Prior implementation checks
│   └── packaging_verification.json
├── provenance/                   Manifest, source notes, upstream notices
├── .streamlit/config.toml        Local service, no usage collection
├── .gitignore / .gitattributes
├── requirements*.txt             Dependency pins
├── Setup.cmd / Start_dashboard.cmd
└── package_manifest.json         SHA-256 review inventory
```

Generated locally and excluded: .venv/, data/raw/, data/warehouse/, __pycache__/ and DuckDB runtime files. No cloud credentials are needed.

The root README presents the question and findings, then links each SQL skill to source. Chinese material and historical results remain directly accessible.
