-- Parameters: start/end inclusive session FIRST-observed dates, selected devices.
-- Full paths/flags already exist; date filtering never truncates an event sequence.
WITH selected AS (
 SELECT * FROM reporting_sessions
 WHERE first_date BETWEEN ?::DATE AND ?::DATE AND device IN (SELECT unnest(?))
), expanded AS (
 SELECT s.*,g.scope,d.device_group FROM selected s
 CROSS JOIN (VALUES ('all'),('touch'),('not_touch')) g(scope)
 CROSS JOIN LATERAL (VALUES ('ALL_DEVICES'),(s.device)) d(device_group)
 WHERE g.scope='all' OR (g.scope='touch' AND s.touches_flagged_date)
 OR (g.scope='not_touch' AND NOT s.touches_flagged_date)
), counts AS (
 SELECT scope,device_group,count(*) AS sessions,
 count(*) FILTER(WHERE purchase_events>0) AS purchase_sessions,
 count(*) FILTER(WHERE view_events>0) AS view_sessions,
 count(*) FILTER(WHERE cart_events>0) AS cart_sessions,
 count(*) FILTER(WHERE checkout_events>0) AS checkout_sessions,
 count(v_ts) AS strict_view,count(a_ts) AS strict_cart,count(c_ts) AS strict_checkout,count(p_ts) AS strict_purchase,
 count(upper_cart_ts) AS upper_cart,count(upper_checkout_ts) AS upper_checkout,count(upper_purchase_ts) AS upper_purchase,
 count(*) FILTER(WHERE purchase_path_class='tie_only') AS tie_only,
 count(*) FILTER(WHERE purchase_path_class='all_present_not_ordered') AS all_present_not_ordered,
 count(*) FILTER(WHERE purchase_path_class='missing_prerequisite') AS missing_prerequisite,
 count(*) FILTER(WHERE purchase_events>0 AND p_ts IS NULL) AS purchase_outside_strict,
 count(*) FILTER(WHERE has_funnel_tie) AS sessions_with_ties,
 count(*) FILTER(WHERE touches_flagged_date) AS touches_flagged,
 count(*) FILTER(WHERE session_start_events=0) AS no_session_start,
 count(*) FILTER(WHERE session_start_events>1) AS multiple_session_start,
 count(*) FILTER(WHERE first_date<>last_date) AS cross_date,
 count(*) FILTER(WHERE last_ts-first_ts>86400000000) AS over_24h,
 count(*) FILTER(WHERE near_sample_start) AS near_start,
 count(*) FILTER(WHERE near_sample_end) AS near_end
 FROM expanded GROUP BY 1,2
)
SELECT *,purchase_sessions::DOUBLE/nullif(sessions,0) AS purchase_record_rate,
 strict_purchase::DOUBLE/nullif(view_sessions,0) AS strict_complete_per_view,
 upper_purchase::DOUBLE/nullif(view_sessions,0) AS upper_complete_per_view,
 purchase_outside_strict::DOUBLE/nullif(purchase_sessions,0) AS incomplete_purchase_path_rate,
 strict_cart::DOUBLE/nullif(strict_view,0) AS strict_view_cart_rate,
 strict_checkout::DOUBLE/nullif(strict_cart,0) AS strict_cart_checkout_rate,
 strict_purchase::DOUBLE/nullif(strict_checkout,0) AS strict_checkout_purchase_rate,
 upper_cart::DOUBLE/nullif(strict_view,0) AS upper_view_cart_rate,
 upper_checkout::DOUBLE/nullif(upper_cart,0) AS upper_cart_checkout_rate,
 upper_purchase::DOUBLE/nullif(upper_checkout,0) AS upper_checkout_purchase_rate
FROM counts ORDER BY scope,device_group;
