-- FROZEN before follow-up comparisons: these dates are not re-detected by filters.
CREATE OR REPLACE TABLE flagged_dates AS
SELECT d::DATE AS observed_date FROM generate_series(DATE '2020-11-02',DATE '2020-11-15',INTERVAL 1 DAY) t(d)
UNION ALL SELECT d::DATE FROM generate_series(DATE '2020-11-21',DATE '2020-11-24',INTERVAL 1 DAY) t(d);

CREATE OR REPLACE TABLE reporting_sessions AS
WITH flags AS (
 SELECT e.user_pseudo_id,e.ga_session_id,bool_or(f.observed_date IS NOT NULL) touches_flagged_date
 FROM events e LEFT JOIN flagged_dates f USING(observed_date)
 WHERE e.session_identifiable GROUP BY 1,2
), ties AS (
 SELECT DISTINCT user_pseudo_id,ga_session_id FROM timestamp_ties WHERE distinct_funnel_stages>1
)
SELECT p.*,f.touches_flagged_date,t.a_ts AS upper_cart_ts,t.c_ts AS upper_checkout_ts,t.p_ts AS upper_purchase_ts,
  ties.user_pseudo_id IS NOT NULL AS has_funnel_tie,
  CASE WHEN p.purchase_events=0 THEN 'no_recorded_purchase'
       WHEN p.p_ts IS NOT NULL THEN 'strict_complete'
       WHEN t.p_ts IS NOT NULL THEN 'tie_only'
       WHEN p.presence_vacp='1111' THEN 'all_present_not_ordered'
       ELSE 'missing_prerequisite' END AS purchase_path_class,
  p.first_date=(SELECT min(observed_date) FROM events) AS near_sample_start,
  p.last_date=(SELECT max(observed_date) FROM events) AS near_sample_end
FROM paths p JOIN flags f USING(user_pseudo_id,ga_session_id)
LEFT JOIN tie_permissive_paths t USING(user_pseudo_id,ga_session_id)
LEFT JOIN ties USING(user_pseudo_id,ga_session_id);

CREATE OR REPLACE TABLE daily_device AS
SELECT observed_date,device_category AS device,count(*) AS event_rows,
 count(*) FILTER(WHERE event_name='view_item') view_events,
 count(*) FILTER(WHERE event_name='add_to_cart') cart_events,
 count(*) FILTER(WHERE event_name='begin_checkout') checkout_events,
 count(*) FILTER(WHERE event_name='purchase') purchase_events,
 count(*) FILTER(WHERE NOT session_identifiable) unidentifiable_events,
 count(*) FILTER(WHERE event_name='purchase' AND NOT transaction_usable) unusable_transaction_events,
 count(*) FILTER(WHERE event_name='purchase' AND event_value_in_usd IS NULL) missing_value_events
FROM events GROUP BY 1,2;

-- One user-level anchor, selected only AFTER full-history follow-up construction.
CREATE OR REPLACE TABLE reporting_followup AS
SELECT f.*,s.first_date AS anchor_session_first_date,s.device,s.touches_flagged_date,
       e.anchor_date
FROM checkout_followup f
JOIN reporting_sessions s ON s.user_pseudo_id=f.user_pseudo_id AND s.ga_session_id=f.anchor_session
JOIN (SELECT user_pseudo_id,event_timestamp,min(observed_date) anchor_date
      FROM events WHERE event_name='begin_checkout' GROUP BY 1,2) e
  ON e.user_pseudo_id=f.user_pseudo_id AND e.event_timestamp=f.anchor_ts;
