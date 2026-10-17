CREATE OR REPLACE TABLE transaction_quality AS
SELECT transaction_id,count(*) AS purchase_rows,
       count(DISTINCT user_pseudo_id) AS pseudo_users,
       count(DISTINCT (user_pseudo_id,ga_session_id)) AS session_keys,
       count(DISTINCT event_value_in_usd) AS distinct_observed_values,
       count(*) FILTER(WHERE event_value_in_usd IS NULL) AS missing_values,
       min(event_value_in_usd) AS min_value,max(event_value_in_usd) AS max_value,
       min(event_timestamp) AS first_ts,max(event_timestamp) AS last_ts
FROM events WHERE event_name='purchase' AND transaction_usable GROUP BY 1;

CREATE OR REPLACE TABLE quality_by_date_device_source AS
SELECT observed_date,device_category,source,medium,
    count(*) AS events,count(*) FILTER(WHERE NOT session_identifiable) AS unidentifiable_events,
    count(*) FILTER(WHERE event_name='view_item') AS view_events,
    count(*) FILTER(WHERE event_name='add_to_cart') AS cart_events,
    count(*) FILTER(WHERE event_name='begin_checkout') AS checkout_events,
    count(*) FILTER(WHERE event_name='purchase') AS purchase_events,
    count(*) FILTER(WHERE event_name='purchase' AND NOT transaction_usable) AS invalid_transaction_events,
    count(*) FILTER(WHERE event_name='purchase' AND event_value_in_usd IS NULL) AS missing_purchase_values
FROM events GROUP BY ALL;
