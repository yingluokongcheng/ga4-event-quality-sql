# Frozen analysis protocol — v2

Accepted by the user before execution: event quality and observed purchase paths are the main question; device comparisons are supplementary. All 92 dates and tied timestamps are retained. No optimizing results by deleting dates, adjusting path definitions, or selecting favorable windows. Local execution only; GitHub publication is not authorized for this milestone.

## Cohorts and dates

- Full interval: 2020-11-01 through 2021-01-31 inclusive.
- Fixed flagged days: 2020-11-02–11-15 and 2020-11-21–11-24 (18 days).
- Flag any session that has **any event** on those dates. Flags do not change when a device or date filter is applied.
- Build sessions and paths from complete observed history, then filter on session first-observed date. Keep midnight-crossing sessions intact.
- Event coverage panels instead use event_date and say so. Follow-up uses first checkout anchor date and says so. Do not mix these denominators.
- Present all, touches-flagged, and not-touches-flagged cohorts. These form a partition; not-touches is not assumed complete/normal or a corrected dataset.
- All first/last-day, missing/multiple-session_start and >24h sessions remain. Quality flags are reported, not exclusion rules.

## Metrics

- Purchase-record session rate = any-purchase sessions / all identifiable sessions.
- Strict complete path share = strictly ordered V→A→C→P sessions / any-view sessions.
- Incomplete purchase path share = (any-purchase sessions − strict complete sessions) / any-purchase sessions.
- Independent stage presence counts require no preceding stages. Strict path counts find an existing subsequence (not each stage's global first timestamp).
- Timestamp-tolerant path counts use ≥ solely as a possible upper bound for the observed sequence. No assumed event-name/file-row ordering. The gap from > is an uncertainty category, not confirmed behavior.
- Strict and timestamp-tolerant step continuation ratios have their own numerators/denominators. They are **not** ratio bounds because denominators change. A zero denominator yields missing/NA, never 0%.
- Purchase sessions are partitioned: strict complete; only tie-compatible; all stages present but not ordered even allowing ties; missing prerequisite. No-purchase sessions remain separate observed outcomes, not confirmed churn.
- Cross-session 24h follow-up has one anchor per pseudo-user; censor incomplete follow-up, flag near-start anchors. Other-session and same-session purchases can overlap; no same-cart or recovered-customer claim.

## Device comparisons and non-goals

Show desktop/mobile/tablet counts, rates, numerators/denominators, coverage and tie diagnostics. Compare descriptive records only, without best-device ranking, significance testing, causal UX claims or revenue optimization. Do not implement revenue/AOV/category/current-session-channel analysis on this extract.

## Evidence limits

The extract is a pinned third-party projection; Google original completeness is unverified. An empty event type on a date is not the same as an absent date, and neither identifies its cause. Lack of recorded purchase cannot distinguish real nonpurchase from tracking, export, obfuscation, identity or observation-window limitations.
