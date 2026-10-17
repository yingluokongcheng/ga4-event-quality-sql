-- Keep every source row. event_id is a third-party hash, not a native GA4 ID.
CREATE OR REPLACE MACRO usable(x) AS
    x IS NOT NULL AND lower(trim(CAST(x AS VARCHAR))) NOT IN
    ('', '(not set)', '<other>', 'null', 'undefined', '(data not available)', '(data deleted)');

CREATE OR REPLACE TABLE events AS
SELECT *,
    try_strptime(event_date, '%Y%m%d')::DATE AS observed_date,
    usable(user_pseudo_id) AND ga_session_id IS NOT NULL AND ga_session_id > 0 AS session_identifiable,
    usable(transaction_id) AS transaction_usable
FROM raw_events;

CREATE OR REPLACE TABLE sessions AS
SELECT user_pseudo_id, ga_session_id,
    min(event_timestamp) AS first_ts, max(event_timestamp) AS last_ts,
    min(observed_date) AS first_date, max(observed_date) AS last_date,
    count(*) AS event_count,
    count(DISTINCT device_category) FILTER (WHERE usable(device_category)) AS device_values,
    CASE WHEN count(DISTINCT device_category) FILTER (WHERE usable(device_category)) = 1
         THEN min(device_category) FILTER (WHERE usable(device_category))
         WHEN count(DISTINCT device_category) FILTER (WHERE usable(device_category)) = 0
         THEN 'UNKNOWN' ELSE 'CONFLICT' END AS device,
    count(*) FILTER (WHERE NOT usable(device_category)) AS device_missing_events,
    count(DISTINCT (source,medium)) AS source_medium_values,
    CASE WHEN count(DISTINCT (source,medium))=1 AND bool_and(usable(source) AND usable(medium))
         THEN min(source)||' / '||min(medium)
         WHEN count(DISTINCT (source,medium))>1 THEN 'CONFLICT' ELSE 'UNKNOWN' END AS first_acquisition,
    count(*) FILTER(WHERE event_name='session_start') AS session_start_events,
    count(*) FILTER(WHERE event_name='view_item') AS view_events,
    count(*) FILTER(WHERE event_name='add_to_cart') AS cart_events,
    count(*) FILTER(WHERE event_name='begin_checkout') AS checkout_events,
    count(*) FILTER(WHERE event_name='purchase') AS purchase_events
FROM events WHERE session_identifiable
GROUP BY user_pseudo_id, ga_session_id;
