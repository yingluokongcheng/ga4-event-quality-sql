# Metric contracts

V = view_item; A = add_to_cart; C = begin_checkout; P = purchase.

| Metric | Numerator | Denominator / unit |
|---|---|---|
| Event count | Source rows | Events, not orders |
| Purchase-record session rate | Sessions with any P | All identifiable sessions |
| Strict complete path share | Sessions with V < A < C < P subsequence | Sessions with any V |
| Incomplete purchase path share | Purchase sessions without a strict complete path | Sessions with any P |
| Independent stage presence | Sessions containing a stage | Counts, without prerequisite requirements |
| Strict step continuation | Sessions reaching next strict stage | Sessions reaching preceding strict stage |
| Compatible step continuation | Sessions reaching next compatible stage | Sessions reaching preceding compatible stage |
| Purchase within 24h | Anchored pseudo-users with later purchase within 24h | Report full and censored follow-up separately |

Purchase-record rate (4,848 / 360,129) and strict-complete share (2,778 / 77,020) answer different questions. Do not label both “conversion rate” without denominators.

## Time filters

Event coverage uses event date. Session comparison uses first-observed session date after full-history construction. Follow-up uses first-checkout anchor date after user-level construction. Weekly summaries use the week of session first observation, with selected calendar-day counts and partial-week flags.

Session flags consider every event in the complete observed history. Filters do not redefine the 18 dates. The independent user-level follow-up panel does not inherit the session-cohort selector.

## Interpretation

Zero denominators yield NA. Empty filters do not reset to all data. Missing all records is distinct from a recorded zero for one event.

Compatible counts do not establish actual order. Strict and compatible step rates do not form bounds because their denominators can change.

Missing purchase is not churn; a purchase outside the complete path remains a purchase record. First/last-day and long sessions remain with flags. See the [frozen protocol](PROTOCOL.md).
