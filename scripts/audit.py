"""Run SQL audit offline against the verified local event extract."""
import csv
import hashlib
import json
from pathlib import Path
import time
import duckdb

ROOT = Path(__file__).resolve().parents[1]

QUERIES = {
 'cart_zero_days': """SELECT observed_date,count(*) event_rows,
    count(*) FILTER(WHERE event_name='view_item') view_events,
    count(*) FILTER(WHERE event_name='begin_checkout') checkout_events,
    count(*) FILTER(WHERE event_name='purchase') purchase_events
    FROM events GROUP BY 1 HAVING count(*) FILTER(WHERE event_name='add_to_cart')=0 ORDER BY 1""",
 'cart_zero_day_devices': """SELECT observed_date,device_category,count(*) event_rows,
    count(*) FILTER(WHERE event_name='add_to_cart') cart_events,
    count(*) FILTER(WHERE event_name='begin_checkout') checkout_events,
    count(*) FILTER(WHERE event_name='purchase') purchase_events
    FROM events WHERE observed_date IN (SELECT observed_date FROM events GROUP BY 1
      HAVING count(*) FILTER(WHERE event_name='add_to_cart')=0)
    GROUP BY 1,2 ORDER BY 1,2""",
 'weekly_coverage': """SELECT date_trunc('week',observed_date)::DATE week_start,
    count(DISTINCT observed_date) covered_days,count(*) event_rows,
    count(*) FILTER(WHERE event_name='add_to_cart') cart_events,
    count(*) FILTER(WHERE event_name='purchase') purchase_events
    FROM events GROUP BY 1 ORDER BY 1""",
 'schema_consistency': """WITH per_file AS (
    SELECT file_name,string_agg(name||':'||coalesce(type,'')||':'||coalesce(logical_type,''),'|' ORDER BY name) signature
    FROM parquet_schema('data/raw/*.parquet') GROUP BY 1)
    SELECT count(*) files,count(DISTINCT signature) schema_signatures FROM per_file""",
 'ordering_bounds': """SELECT count(*) view_sessions,count(a_ts) cart_upper_bound,
    count(c_ts) checkout_upper_bound,count(p_ts) complete_upper_bound,
    (SELECT count(*) FROM paths WHERE presence_vacp='1111') all_four_present
    FROM tie_permissive_paths""",
 'ordering_by_device': """SELECT s.device,count(*) view_sessions,count(t.a_ts) cart_upper_bound,
    count(t.c_ts) checkout_upper_bound,count(t.p_ts) complete_upper_bound,
    count(*) FILTER(WHERE p.presence_vacp='1111') all_four_present
    FROM tie_permissive_paths t JOIN sessions s USING(user_pseudo_id,ga_session_id)
    JOIN paths p USING(user_pseudo_id,ga_session_id) GROUP BY 1 ORDER BY 1""",
 'coverage': """SELECT count(*) event_rows,min(observed_date) first_date,max(observed_date) last_date,
    count(DISTINCT observed_date) observed_days,count(DISTINCT user_pseudo_id) pseudo_users,
    (SELECT count(*) FROM sessions) identifiable_sessions,count(DISTINCT event_name) event_types,
    count(*) FILTER(WHERE NOT session_identifiable) unidentifiable_events,
    count(*) FILTER(WHERE observed_date IS NULL) invalid_dates,
    count(*) FILTER(WHERE event_timestamp IS NULL OR event_timestamp<=0) invalid_timestamps,
    count(*) FILTER(WHERE event_ts IS DISTINCT FROM make_timestamp(event_timestamp)) timestamp_disagreements,
    min(make_timestamp(event_timestamp)) first_timestamp,max(make_timestamp(event_timestamp)) last_timestamp
    FROM events""",
 'events': 'SELECT event_name,count(*) event_rows,count(DISTINCT user_pseudo_id) pseudo_users FROM events GROUP BY 1 ORDER BY 2 DESC',
 'daily': """SELECT observed_date,count(*) event_rows,count(DISTINCT user_pseudo_id) pseudo_users,
    count(DISTINCT (user_pseudo_id,ga_session_id)) FILTER(WHERE session_identifiable) sessions_touched,
    count(*) FILTER(WHERE event_name='view_item') view_events,
    count(*) FILTER(WHERE event_name='add_to_cart') cart_events,
    count(*) FILTER(WHERE event_name='begin_checkout') checkout_events,
    count(*) FILTER(WHERE event_name='purchase') purchase_events
    FROM events GROUP BY 1 ORDER BY 1""",
 'session_quality': """SELECT count(*) sessions,
    count(*) FILTER(WHERE session_start_events=0) without_session_start,
    count(*) FILTER(WHERE session_start_events>1) multiple_session_starts,
    count(*) FILTER(WHERE device_values>1) device_conflicts,
    count(*) FILTER(WHERE device_values=0) missing_device,
    count(*) FILTER(WHERE source_medium_values>1) source_medium_conflicts,
    count(*) FILTER(WHERE first_date<>last_date) cross_date_sessions,
    count(*) FILTER(WHERE last_ts-first_ts>86400000000) spans_over_24h,
    max((last_ts-first_ts)/3600000000.0) max_span_hours,
    count(*) FILTER(WHERE first_date=(SELECT min(observed_date) FROM events)) starts_on_first_observed_day,
    count(*) FILTER(WHERE last_date=(SELECT max(observed_date) FROM events)) ends_on_last_observed_day
    FROM sessions""",
 'path_matrix': """SELECT presence_vacp,count(*) sessions,
    count(*) FILTER(WHERE p_ts IS NOT NULL) strict_complete_sessions FROM paths GROUP BY 1 ORDER BY 1""",
 'strict_path_status': 'SELECT observed_path,count(*) sessions FROM paths GROUP BY 1 ORDER BY 1',
 'funnel_coverage': """SELECT count(*) sessions,count(*) FILTER(WHERE view_events>0) any_view,
    count(*) FILTER(WHERE cart_events>0) any_cart,count(*) FILTER(WHERE checkout_events>0) any_checkout,
    count(*) FILTER(WHERE purchase_events>0) any_purchase,
    count(*) FILTER(WHERE v_ts IS NOT NULL) strict_view,count(*) FILTER(WHERE a_ts IS NOT NULL) strict_cart,
    count(*) FILTER(WHERE c_ts IS NOT NULL) strict_checkout,count(*) FILTER(WHERE p_ts IS NOT NULL) strict_purchase,
    count(*) FILTER(WHERE purchase_events>0 AND p_ts IS NULL) purchase_outside_strict_path FROM paths""",
 'device_audit': """SELECT device,count(*) sessions,
    count(*) FILTER(WHERE view_events>0) view_sessions,count(*) FILTER(WHERE cart_events>0) cart_sessions,
    count(*) FILTER(WHERE checkout_events>0) checkout_sessions,count(*) FILTER(WHERE purchase_events>0) purchase_sessions,
    count(*) FILTER(WHERE p_ts IS NOT NULL) strict_complete_sessions,
    count(*) FILTER(WHERE purchase_events>0 AND p_ts IS NULL) purchase_outside_strict_path,
    count(*) FILTER(WHERE session_start_events=0) without_session_start,
    count(*) FILTER(WHERE last_ts-first_ts>86400000000) spans_over_24h
    FROM paths GROUP BY 1 ORDER BY 2 DESC""",
 'weekly_device_audit': """SELECT date_trunc('week',first_date)::DATE week_start,device,count(*) sessions,
    count(*) FILTER(WHERE purchase_events>0) purchase_sessions,count(*) FILTER(WHERE p_ts IS NOT NULL) strict_complete_sessions,
    count(*) FILTER(WHERE purchase_events>0 AND p_ts IS NULL) purchase_outside_strict_path
    FROM paths GROUP BY 1,2 ORDER BY 1,2""",
 'acquisition_audit': """SELECT first_acquisition,count(*) sessions,
    count(*) FILTER(WHERE purchase_events>0) purchase_sessions,
    count(*) FILTER(WHERE purchase_events>0 AND p_ts IS NULL) purchase_outside_strict_path
    FROM paths GROUP BY 1 ORDER BY 2 DESC""",
 'purchase_path_audit': """SELECT count(*) purchase_events,
    count(*) FILTER(WHERE NOT any_view) without_any_view,
    count(*) FILTER(WHERE NOT any_cart) without_any_cart,
    count(*) FILTER(WHERE NOT any_checkout) without_any_checkout,
    count(*) FILTER(WHERE NOT prior_view) without_prior_view,
    count(*) FILTER(WHERE NOT prior_cart) without_prior_cart,
    count(*) FILTER(WHERE NOT prior_checkout) without_prior_checkout FROM purchase_paths""",
 'purchase_path_by_device': """SELECT device,count(*) purchase_events,
    count(*) FILTER(WHERE NOT prior_view) without_prior_view,
    count(*) FILTER(WHERE NOT prior_cart) without_prior_cart,
    count(*) FILTER(WHERE NOT prior_checkout) without_prior_checkout FROM purchase_paths GROUP BY 1 ORDER BY 2 DESC""",
 'ties': """SELECT count(*) tied_timestamp_groups,coalesce(sum(tied_rows),0) rows_in_ties,
    count(*) FILTER(WHERE distinct_event_names>1) multi_event_type_groups,
    count(*) FILTER(WHERE distinct_funnel_stages>1) multi_funnel_stage_groups,
    count(DISTINCT (user_pseudo_id,ga_session_id)) FILTER(WHERE distinct_funnel_stages>1) sessions_with_funnel_ties
    FROM timestamp_ties""",
 'duplicate_keys': """SELECT count(*) repeated_hash_groups,coalesce(sum(n-1),0) excess_rows
    FROM (SELECT event_id,count(*) n FROM events GROUP BY 1 HAVING count(*)>1)""",
 'same_user_time_name': """SELECT count(*) repeated_natural_key_groups,coalesce(sum(n-1),0) excess_rows
    FROM (SELECT user_pseudo_id,event_timestamp,event_name,count(*) n FROM events GROUP BY 1,2,3 HAVING count(*)>1)""",
 'purchase_fields': """SELECT count(*) purchase_events,
    count(*) FILTER(WHERE NOT transaction_usable) invalid_transaction_events,
    count(*) FILTER(WHERE transaction_id IS NULL) null_transaction_events,
    count(*) FILTER(WHERE transaction_usable) usable_transaction_events,
    count(*) FILTER(WHERE event_value_in_usd IS NULL) missing_observed_values,
    count(*) FILTER(WHERE event_value_in_usd<0) negative_observed_values,
    count(*) FILTER(WHERE event_value_in_usd=0) zero_observed_values
    FROM events WHERE event_name='purchase'""",
 'transactions': """SELECT count(*) usable_transaction_ids,
    count(*) FILTER(WHERE purchase_rows>1) repeated_transaction_ids,
    count(*) FILTER(WHERE pseudo_users>1) cross_user_transaction_ids,
    count(*) FILTER(WHERE session_keys>1) cross_session_transaction_ids,
    count(*) FILTER(WHERE distinct_observed_values>1) conflicting_value_transaction_ids,
    count(*) FILTER(WHERE missing_values>0) transaction_ids_with_missing_value
    FROM transaction_quality""",
 'followup': """SELECT full_24h,near_start,anchor_session_count>1 AS ambiguous_anchor_session,
    count(*) checkout_users,count(*) FILTER(WHERE recorded_purchase_24h) recorded_purchase_users,
    count(*) FILTER(WHERE other_session_purchase_24h) other_session_purchase_users
    FROM checkout_followup GROUP BY 1,2,3 ORDER BY 1,2,3""",
 'field_missingness': """SELECT count(*) event_rows,
    count(*) FILTER(WHERE NOT usable(source)) unusable_source,
    count(*) FILTER(WHERE NOT usable(medium)) unusable_medium,
    count(*) FILTER(WHERE NOT usable(campaign_name)) unusable_campaign,
    count(*) FILTER(WHERE usable(utm_source)) populated_utm_source,
    count(*) FILTER(WHERE usable(utm_medium)) populated_utm_medium,
    count(*) FILTER(WHERE usable(gclid)) populated_gclid,
    count(*) FILTER(WHERE NOT usable(device_category)) unusable_device FROM events""",
 'missing_days': """SELECT day::DATE missing_day FROM generate_series(DATE '2020-11-01',DATE '2021-01-31',INTERVAL 1 DAY) t(day)
    WHERE day::DATE NOT IN (SELECT DISTINCT observed_date FROM events) ORDER BY 1""",
 'schema': 'DESCRIBE raw_events',
 'quality_by_date_device_source': 'SELECT * FROM quality_by_date_device_source ORDER BY ALL',
}

def main():
    start = time.monotonic()
    manifest = json.loads((ROOT/'provenance/source_manifest.json').read_text(encoding='utf-8'))
    for f in manifest['files']:
        p = ROOT/'data/raw'/Path(f['path']).name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != f['sha256']:
            raise RuntimeError(f'Missing or changed input: {p}')
    actual = {p.name for p in (ROOT/'data/raw').glob('*.parquet')}
    assert actual == {Path(f['path']).name for f in manifest['files']}
    reports = ROOT/'reports/audit_v1'; reports.mkdir(parents=True,exist_ok=True)
    warehouse = ROOT/'data/warehouse'; warehouse.mkdir(parents=True,exist_ok=True)
    con = duckdb.connect(str(warehouse/'audit.duckdb'))
    con.execute("SET threads=4; SET memory_limit='2GB'")
    path = (ROOT/'data/raw/*.parquet').as_posix().replace("'","''")
    con.execute(f"CREATE OR REPLACE VIEW raw_events AS SELECT * FROM read_parquet('{path}')")
    for sql in sorted((ROOT/'sql').glob('*.sql')):
        con.execute(sql.read_text(encoding='utf-8')); print(f'Built {sql.name}',flush=True)
    results = {}
    for name,sql in QUERIES.items():
        sql=sql.replace("'data/raw/*.parquet'", "'"+path+"'")
        cur=con.execute(sql); fields=[d[0] for d in cur.description]; rows=cur.fetchall()
        with (reports/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f); writer.writerow(fields);writer.writerows(rows)
        results[name]=[dict(zip(fields,row)) for row in rows]
    f=results['funnel_coverage'][0]
    assert f['strict_view'] >= f['strict_cart'] >= f['strict_checkout'] >= f['strict_purchase']
    assert f['any_purchase'] == f['strict_purchase']+f['purchase_outside_strict_path']
    assert sum(r['sessions'] for r in results['path_matrix']) == f['sessions']
    assert sum(r['event_rows'] for r in results['events']) == results['coverage'][0]['event_rows']
    result = {'scope':'third-party flattened extract; no original BigQuery verification',
              'duckdb_version':duckdb.__version__,'source_commit':manifest['commit'],
              'source_files':len(manifest['files']),'audit':results}
    (reports/'audit_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    con.close()
    print(f'Audit complete, {time.monotonic()-start:.1f}s. {reports}')

if __name__ == '__main__':
    main()
