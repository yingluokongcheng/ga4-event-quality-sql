# Validate the funnel before diagnosing drop-off

GA4 EVENT QUALITY · SQL & PRODUCT ANALYTICS

DuckDB SQL · Metric design · Event-quality diagnosis · Streamlit

[Project overview](../README.md) · [Printable one-page HTML](business-case.html) (download and open locally)

## Problem

A missing funnel step can look like customer abandonment. This project asks whether the available ecommerce records support that interpretation, and which measurement gaps should be investigated before recommending product changes.

## Method

Analyzed **4,295,584 events, 360,129 identifiable sessions and 92 dates** in a fixed third-party GA4-derived extract. Built sessions from user and session identifiers, preserving full event histories before date filtering. Used CTEs, inequality joins, conditional aggregation and correlated subqueries to identify view → cart → checkout → purchase paths, including repeated stages.

Separated strictly ordered paths from paths compatible only when equal timestamps are allowed. Retained all dates and the 18 audit-flagged dates. Delivered reusable session/daily tables and a local dashboard; 14 tests passed and a cached-input rebuild reproduced 36 result files byte for byte.

## Results

Of **4,848 sessions with purchase records, 2,070 (42.70%) lacked a complete strictly ordered path**. These were recorded purchases, not demonstrated lost customers.

| Observed purchase-session class | Sessions |
| --- | --- |
| Strictly ordered complete path | 2,778 |
| Complete only when timestamp ties are allowed | 56 |
| All stages present, but not in the required order | 14 |
| Missing prerequisite stages | 2,000 |

Sessions touching the 18 flagged dates included **815 purchase sessions but zero complete paths**. Among purchase sessions not touching those dates, 1,255 of 4,033 (31.12%) still lacked a strict path. Allowing timestamp ties added only 56 compatible paths; it did not establish their actual order.

## Recommendations

*Proposed; not implemented in a live business*

**Prioritize measurement validation before diagnosing funnel abandonment.** Reconcile cart-event collection and export transformations for the flagged dates against source logs and release records. Keep the unflagged cohort under review rather than treating it as complete. Publish path-completeness indicators alongside funnel metrics, and retain strict and tie-compatible counts separately. Use device differences to guide questions, not to justify a UX change without further evidence.

## Limits

The extract was not reconciled with Google's original tables. Pseudo-users are not verified people, sessions are not verified orders, and paths need not follow one item or cart. Missing records cannot identify tracking failure, true churn or its cause. Revenue and attribution questions were suspended because available fields did not support them. No conversion improvement or business impact was measured.

Published business case · 18 Oct 2026. Analysis and historical results remain in the project repository.
