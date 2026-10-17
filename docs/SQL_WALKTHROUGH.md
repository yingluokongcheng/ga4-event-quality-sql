# SQL implementation walkthrough

This guide maps existing SQL to analytical decisions; it introduces no new analysis.

## Preserve grain

[01_stage.sql](../sql/01_stage.sql) preserves source rows and derives identity/transaction usability flags. A source hash is not assumed to be a native GA4 event ID.

Sessions group by (user_pseudo_id, ga_session_id). Session ID alone can occur under different users; a date-based key would split midnight-crossing sessions. Conflicting device values and missing session_start events remain diagnostics.

## Match an existing subsequence

[02_paths.sql](../sql/02_paths.sql) finds the first view, then the earliest eligible cart after that view, checkout after that cart, and purchase after checkout. LEFT JOIN and MIN preserve sessions when the next stage is absent.

For example, cart@1 → view@2 → cart@3 → checkout@4 → purchase@5 has a valid path. Comparing the first cart with the first view would incorrectly reject it; the eligible cart is at time 3.

Choosing the earliest eligible stage leaves at least as much time for later stages as choosing a later candidate. This establishes existence of a four-stage subsequence, not every path or every purchase's prerequisites.

## Make timestamp uncertainty explicit

Strict paths use >; a separate compatible table uses >=. Neither file order nor event names break ties.

The reporting CASE assigns purchase sessions to strict complete, otherwise tie-compatible, otherwise all stages present but unordered, otherwise missing prerequisite. No-purchase sessions are separate. The four purchase categories sum to purchase sessions; strict count ≤ compatible count ≤ purchase-session count.

## Build flags before filtering

[04_reporting.sql](../sql/marts/04_reporting.sql) uses fixed dates and BOOL_OR over all session events. A session starting before a flagged date can still touch it.

[summary.sql](../sql/marts/summary.sql) filters completed session records by first-observed date. It does not build paths from a truncated event window. CROSS JOIN and lateral VALUES expand sessions into relevant cohort/device groups. Subsequent aggregation counts each session once per applicable group.

Only touch and not-touch partition all. Summing all three rows would double-count.

## Distinguish missing records from zero

The calendar spine in [data.py](../dashboard/data.py) uses generate_series and a LEFT JOIN. A date with no records for selected devices has missing counts and has_records=false; a date with records but no cart has cart count zero.

Ratios use NULLIF(denominator,0). Undefined rates are NA, not 0%. Empty device selection does not silently revert to all devices.

## Separate units and follow-up windows

[03_quality.sql](../sql/03_quality.sql) audits transaction IDs without claiming one event equals one unique order. Correlated EXISTS in [02_paths.sql](../sql/02_paths.sql) checks purchase prerequisites and user-level follow-up.

Each pseudo-user has one first-checkout anchor. Full follow-up must fit before the last observed event timestamp: a conservative boundary, not proof of complete capture. Anchor-session ambiguity and near-start anchors remain flagged. Same-session and other-session purchasing can overlap; neither establishes a recovered cart.

## Verify the contracts

- [test_semantics.py](../tests/test_semantics.py): six synthetic cases covering repeated stages, ties, missing carts despite purchase, invalid identities, composite keys and follow-up boundaries.
- [test_reporting.py](../tests/test_reporting.py): full-history filtering, fixed flags, missing dates vs zero events, class partition, zero denominators and snapshot reconciliation.
- [test_app.py](../tests/test_app.py): three pages, flagged-group metrics and empty filters/groups.

Fixtures are separate from empirical data. Tests cannot validate the upstream collection pipeline.

DuckDB-specific features include FILTER, GROUP BY ALL, macros, generate_series and lateral VALUES. Porting requires syntax/semantic checks. No window functions or EXPLAIN-based performance benchmark were implemented.
