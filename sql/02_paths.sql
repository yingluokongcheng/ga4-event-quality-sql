-- Greedy earliest *eligible* timestamps find an existing ordered subsequence.
-- A later repeat of a stage can match; global first timestamps are not compared.
CREATE OR REPLACE TABLE paths AS
WITH v AS (
    SELECT user_pseudo_id,ga_session_id,min(event_timestamp) AS v_ts
    FROM events WHERE session_identifiable AND event_name='view_item'
    GROUP BY ALL
), a AS (
    SELECT v.*, min(e.event_timestamp) AS a_ts
    FROM v LEFT JOIN events e ON e.session_identifiable
    AND e.user_pseudo_id=v.user_pseudo_id AND e.ga_session_id=v.ga_session_id
    AND e.event_name='add_to_cart' AND e.event_timestamp>v.v_ts
    GROUP BY ALL
), c AS (
    SELECT a.*,min(e.event_timestamp) AS c_ts
    FROM a LEFT JOIN events e ON e.session_identifiable
    AND e.user_pseudo_id=a.user_pseudo_id AND e.ga_session_id=a.ga_session_id
    AND e.event_name='begin_checkout' AND e.event_timestamp>a.a_ts
    GROUP BY ALL
), p AS (
    SELECT c.*,min(e.event_timestamp) AS p_ts
    FROM c LEFT JOIN events e ON e.session_identifiable
    AND e.user_pseudo_id=c.user_pseudo_id AND e.ga_session_id=c.ga_session_id
    AND e.event_name='purchase' AND e.event_timestamp>c.c_ts
    GROUP BY ALL
)
SELECT s.*,v_ts,a_ts,c_ts,p_ts,
    CASE WHEN p_ts IS NOT NULL THEN '4_full_ordered_path'
         WHEN c_ts IS NOT NULL THEN '3_no_later_recorded_purchase'
         WHEN a_ts IS NOT NULL THEN '2_no_later_recorded_checkout'
         WHEN v_ts IS NOT NULL THEN '1_no_later_recorded_cart'
         ELSE '0_no_recorded_view' END AS observed_path,
    (view_events>0)::INT::VARCHAR || (cart_events>0)::INT::VARCHAR ||
    (checkout_events>0)::INT::VARCHAR || (purchase_events>0)::INT::VARCHAR AS presence_vacp
FROM sessions s LEFT JOIN p USING(user_pseudo_id,ga_session_id);

-- Upper bound ONLY: allow adjacent stages tied in time. This does not establish
-- their actual ordering and must never replace the strict funnel silently.
CREATE OR REPLACE TABLE tie_permissive_paths AS
WITH v AS (
    SELECT user_pseudo_id,ga_session_id,min(event_timestamp) AS v_ts
    FROM events WHERE session_identifiable AND event_name='view_item' GROUP BY ALL
), a AS (
    SELECT v.*,min(e.event_timestamp) AS a_ts FROM v LEFT JOIN events e
    ON e.session_identifiable AND e.user_pseudo_id=v.user_pseudo_id AND e.ga_session_id=v.ga_session_id
    AND e.event_name='add_to_cart' AND e.event_timestamp>=v.v_ts GROUP BY ALL
), c AS (
    SELECT a.*,min(e.event_timestamp) AS c_ts FROM a LEFT JOIN events e
    ON e.session_identifiable AND e.user_pseudo_id=a.user_pseudo_id AND e.ga_session_id=a.ga_session_id
    AND e.event_name='begin_checkout' AND e.event_timestamp>=a.a_ts GROUP BY ALL
)
SELECT c.*,min(e.event_timestamp) AS p_ts FROM c LEFT JOIN events e
    ON e.session_identifiable AND e.user_pseudo_id=c.user_pseudo_id AND e.ga_session_id=c.ga_session_id
    AND e.event_name='purchase' AND e.event_timestamp>=c.c_ts GROUP BY ALL;

-- Event-level evidence, including later/absent prerequisites and timestamp ties.
CREATE OR REPLACE TABLE purchase_paths AS
SELECT e.event_id,e.user_pseudo_id,e.ga_session_id,e.event_timestamp,
    s.device,s.first_acquisition,e.observed_date,
    s.view_events>0 AS any_view,s.cart_events>0 AS any_cart,s.checkout_events>0 AS any_checkout,
    EXISTS(SELECT 1 FROM events x WHERE x.user_pseudo_id=e.user_pseudo_id AND x.ga_session_id=e.ga_session_id
           AND x.event_name='view_item' AND x.event_timestamp<e.event_timestamp) AS prior_view,
    EXISTS(SELECT 1 FROM events x WHERE x.user_pseudo_id=e.user_pseudo_id AND x.ga_session_id=e.ga_session_id
           AND x.event_name='add_to_cart' AND x.event_timestamp<e.event_timestamp) AS prior_cart,
    EXISTS(SELECT 1 FROM events x WHERE x.user_pseudo_id=e.user_pseudo_id AND x.ga_session_id=e.ga_session_id
           AND x.event_name='begin_checkout' AND x.event_timestamp<e.event_timestamp) AS prior_checkout
FROM events e JOIN sessions s USING(user_pseudo_id,ga_session_id)
WHERE e.event_name='purchase' AND e.session_identifiable;

CREATE OR REPLACE TABLE timestamp_ties AS
SELECT user_pseudo_id,ga_session_id,event_timestamp,count(*) AS tied_rows,
       count(DISTINCT event_name) AS distinct_event_names,
       count(DISTINCT event_name) FILTER(WHERE event_name IN ('view_item','add_to_cart','begin_checkout','purchase')) AS distinct_funnel_stages
FROM events WHERE session_identifiable GROUP BY ALL HAVING count(*)>1;

-- One anchor per pseudo-user; incomplete follow-up is a separate group.
-- Same user does NOT establish same cart or order intent.
CREATE OR REPLACE TABLE checkout_followup AS
WITH anchors AS (
    SELECT user_pseudo_id,min(event_timestamp) AS anchor_ts
    FROM events WHERE session_identifiable AND event_name='begin_checkout' GROUP BY 1
), anchor_sessions AS (
    SELECT a.*,min(e.ga_session_id) AS anchor_session,
           count(DISTINCT e.ga_session_id) AS anchor_session_count
    FROM anchors a JOIN events e ON a.user_pseudo_id=e.user_pseudo_id
      AND a.anchor_ts=e.event_timestamp AND e.event_name='begin_checkout'
    GROUP BY ALL
)
SELECT a.*,
    anchor_ts <= (SELECT max(event_timestamp) FROM events)-86400000000 AS full_24h,
    anchor_ts < (SELECT min(event_timestamp) FROM events)+86400000000 AS near_start,
    EXISTS(SELECT 1 FROM events p WHERE p.user_pseudo_id=a.user_pseudo_id
      AND p.event_name='purchase' AND p.event_timestamp>a.anchor_ts
      AND p.event_timestamp<=a.anchor_ts+86400000000) AS recorded_purchase_24h,
    EXISTS(SELECT 1 FROM events p WHERE p.user_pseudo_id=a.user_pseudo_id
      AND p.event_name='purchase' AND p.session_identifiable AND p.ga_session_id<>a.anchor_session
      AND p.event_timestamp>a.anchor_ts AND p.event_timestamp<=a.anchor_ts+86400000000) AS other_session_purchase_24h
FROM anchor_sessions a;
