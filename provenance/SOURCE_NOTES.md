# Source and evidence boundary

Audit date: 2026-10-16 (America/New_York user-facing date).

## Original dataset

Google documents a three-month, obfuscated sample at `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`. The official access method requires a BigQuery-enabled Google Cloud project. The user explicitly requires local execution and cannot currently use Google Cloud.

- [Official sample documentation](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset)
- [GA4 export schema](https://support.google.com/analytics/answer/7029846?hl=en)
- [GA4 session documentation](https://support.google.com/analytics/answer/9191807?hl=en)

Google warns about placeholder values and limited internal consistency. These warnings do not identify the cause of a particular anomaly in a third-party extract.

## Local data actually audited

- Repository: [DavidKingGH/dbt_portfolio_project_1](https://github.com/DavidKingGH/dbt_portfolio_project_1)
- Commit: `41c4ee829b7c18cdb52810686768edfa035a42e0`
- Directory: `ga4_data/fct/fact_events/`
- 114 Parquet files; total 274,098,689 bytes.
- `source_manifest.json` records repository path, file size, source Git blob SHA-1, and independently computed SHA-256 for every downloaded file.
- Author README and notebook describe extraction from Google's three monthly ranges. Notebook contains no explicit event-name/date exclusion beyond the stated range in its base SELECT, but this is not proof of a complete extraction.

## Limits discovered during provenance review

The notebook mixes a flattened `BASE_SELECT` with later references to nested `event_params`, `ecommerce`, `traffic_source`, and `device`. The actual Parquet schema also includes `event_ts` and `device_category`, which do not exactly match the displayed projection. Thus the checked-in notebook is insufficient to reproduce or verify the exact original-to-Parquet transformation.

The `event_id` is a third-party hash of user/time/name, not a native GA4 event key. A uniqueness check cannot establish that no upstream deduplication occurred. Our own ingestion preserves every downloaded row and records zero locally observed repeated hashes/natural keys.

The downloaded event table omits raw nested `event_params`, `items`, currency, dedicated `ecommerce.purchase_revenue[_in_usd]`, and batch ordering fields. It retains `event_value_in_usd`, which is not silently substituted for verified order revenue. Missing raw repeated fields also prevent direct validation of parameter-key duplication and event×item join amplification. No item join was performed in this audit.

The source README describes its codebase as MIT but explicitly reserves Google's underlying data. We do not infer that it grants redistribution rights to that dataset. Original source documentation is retained locally for provenance; downloading and analyzing a public file is not proof of a data publication license.

## Search candidates not used

- `ViacheslavPomazan/GA4_Conversion_Funnel-PowerBI_Tableau_and_BigQuery_project`: documented preprocessing removes sessions with missing/multiple session_start and selects funnel events, making it unsuitable as our unfiltered audit source.
- `saumyadeepgain/funnel-retention-analysis`: repository includes a sample-data generator; not used as a substitute for observed GA4 event data.
- No source repository's existing analytical conclusions, dashboard or SQL models were used as this project's empirical findings.

## Reproducibility claim

We can reproduce this fixed extract's local audit without Google Cloud. We cannot establish source-table completeness, determine real vs unrecorded behavior, reproduce the third party's exact extraction, or infer Google Store commercial outcomes. These are separate claims and remain unresolved.
