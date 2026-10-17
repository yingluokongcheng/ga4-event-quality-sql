# GA4 Local Event-Quality Audit

Historical milestone documentation. Commands and status below describe the original audit; use the [current README](../README.md) to run this dashboard package.

A local SQL portfolio project auditing observed ecommerce paths **before** interpreting conversion or building a dashboard. This milestone is an audit only. No missing purchase is labelled as confirmed churn.

## Status and findings

- 4,295,584 event rows, 270,154 pseudo-users, 360,129 identifiable sessions, 92 dates (2020-11-01–2021-01-31).
- 18 dates have no recorded `add_to_cart` but contain 1,071 purchase events. Cause cannot be identified from the extract alone.
- 4,848 sessions contain purchases; 2,778 meet a strict view → cart → checkout → purchase sequence. The other 2,070 are **not purchase failures**.
- Allowing timestamp ties raises possible complete paths to 2,834, but does not establish their true order.
- Revenue and session-acquisition analysis are suspended: required fields are missing and transaction identifiers have missingness/collisions.
- Device comparisons can be descriptive, subject to explicit event coverage and observation-window caveats. Further analysis/dashboard design awaits discussion.

Read [中文审计报告](../reports/audit_v1/GA4本地数据审计.html) or [machine-readable results](../reports/audit_v1/audit_results.json).

## Source limitation

This is an independently written audit of a **third-party flattened GA4-derived extract**, not a verified export directly obtained from Google. All 114 downloaded Parquet files are pinned to a commit and hash-verified, but source completeness against BigQuery is unverified. The original nested parameters/items are unavailable in this event table. Never claim that zero local duplicate keys proves the original export was unmodified.

See [source notes](../provenance/SOURCE_NOTES.md) and [file manifest](../provenance/source_manifest.json). Our analysis does not use the source repository's dbt metrics or funnel logic. Its export notebook is retained only as provenance, not executed.

## Run locally (Python 3.12 tested)

From this directory, Windows PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/download.py
.venv/Scripts/python scripts/audit.py
.venv/Scripts/python scripts/report.py
.venv/Scripts/python -m unittest discover -s tests -v
```

On macOS/Linux use `.venv/bin/python` in place of `.venv/Scripts/python`.

Only installation and first download need ordinary internet access. No Google Cloud project, billing, credential, BigQuery, MotherDuck, dbt, or Spark is required. Once files are present, `audit.py` and `report.py` run offline. Download footprint: 274 MB (decimal); the DuckDB database uses additional disk space. SQL memory limit is 2 GB, 4 threads; spill space may be needed. Actual results are stored in this project. Do not infer performance on other machines from this run.

`download.py --verify-only` verifies cached files without network access. Every audit checks SHA-256 and the exact file set before reading data. To rerun calculations, rerun the audit; it rebuilds derived tables but preserves downloaded source files.

## Structure

```text
requirements.txt              # pinned DuckDB
scripts/download.py           # commit-pinned files + Git blob/SHA-256 checks
scripts/audit.py              # orchestration, audit queries, reconciliation checks
scripts/report.py             # static audit report, not a business dashboard
sql/01_stage.sql              # preserved source rows, identity and session contracts
sql/02_paths.sql              # strict subsequences, timestamp bounds, follow-up
sql/03_quality.sql            # transaction and stratified quality checks
tests/test_semantics.py       # six isolated synthetic semantic edge cases
provenance/                   # pinned source manifest, reference docs, limitations
data/raw/                     # cached 114 source files, excluded from Git/package
data/warehouse/               # generated local DuckDB, excluded from Git/package
reports/                      # empirical audit JSON, CSVs, Chinese HTML
```

## Metric contracts

- Event grain is one source row. No data-dependent deduplication/deletion is applied.
- Session key is the pair `(user_pseudo_id, ga_session_id)`, with valid identifiers. Unknown keys are quarantined; midnight does not split sessions.
- Placeholder strings such as `(not set)`, `<Other>`, `(data deleted)` and empty/NULL values are not meaningful identity/acquisition values. `(direct)/(none)` is retained as a valid recorded source pair.
- The strict path matches an existing ordered subsequence using successive earliest eligible timestamps, not the global first event of each type. Same timestamps are not arbitrarily ordered. The tie-permissive result is only a possible upper bound.
- Paths are session-level, not same-SKU or same-cart paths. Purchases outside the path remain purchases in independent stage-presence counts.
- Session-level purchase-event presence is separate from an independently verified order. Event count, session count, user count and transaction count are never interchanged.
- First-acquisition source/medium is not current-session marketing attribution. No reconstructed channel is invented.
- 24-hour follow-up uses each pseudo-user's first identifiable checkout and the last observed event as a conservative end bound. Censored tail users and near-start users are reported separately. Cross-session purchases do not establish the same cart or intent.
- No recorded purchase is an observation, not evidence of true churn. Potential causes include actual nonpurchase, tracking gaps, identity changes, export transformations and obfuscation.

## Verification and interpretation

Six semantic tests and aggregate reconciliation checks pass. Review the timestamp upper bound alongside strict paths, zero-cart days alongside weekly/device metrics, and missing transaction coverage before discussing commercial outcomes. Tests validate our SQL semantics; they cannot validate Google's original source completeness or recover unobserved behavior.

No business hypothesis testing, model fitting, date-window optimization, dashboard implementation or GitHub publication was performed in this audit milestone.

## Data use

The source repository's MIT statement applies to its code and does not establish a separate open redistribution grant for Google's underlying data. This project links to the source and provides a downloader; raw data and the local database are not bundled in the shareable project ZIP or intended GitHub tree. Original source notices remain in `provenance/`. Confirm data redistribution terms separately if raw data publication is later requested.
