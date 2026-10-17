"""Read-only local SQL access, shared by exports, tests, and the UI."""
from pathlib import Path
import duckdb

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data/warehouse/audit.duckdb'
START='2020-11-01'
END='2021-01-31'
DEVICES=['desktop','mobile','tablet']
SCOPE_NAMES={'all':'全部会话','touch':'涉及异常日期','not_touch':'未涉及异常日期'}
CLASS_NAMES={'strict_complete':'严格顺序完整','tie_only':'仅同刻兼容','all_present_not_ordered':'四阶段齐全但不符合顺序','missing_prerequisite':'缺少前置阶段'}

def query(sql,params=None,db=DB):
    with duckdb.connect(str(db),read_only=True) as con:
        return con.execute(sql,params or []).fetchdf()

def summary(start=START,end=END,devices=None,db=DB):
    return query((ROOT/'sql/marts/summary.sql').read_text(encoding='utf-8'),[str(start),str(end),DEVICES if devices is None else devices],db)

def daily(start=START,end=END,devices=None,db=DB):
    # A calendar spine preserves missing dates; known-day absent events remain zero.
    return query('''WITH cal AS (
      SELECT d::DATE AS observed_date FROM generate_series(?::DATE,?::DATE,INTERVAL 1 DAY) t(d)
    ), agg AS (
      SELECT observed_date,sum(event_rows)::BIGINT event_rows,sum(view_events)::BIGINT view_events,
      sum(cart_events)::BIGINT cart_events,sum(checkout_events)::BIGINT checkout_events,
      sum(purchase_events)::BIGINT purchase_events,sum(unusable_transaction_events)::BIGINT unusable_transaction_events
      FROM daily_device WHERE device IN (SELECT unnest(?)) GROUP BY 1
    ) SELECT c.observed_date,a.* EXCLUDE(observed_date),a.observed_date IS NOT NULL AS has_records,
      f.observed_date IS NOT NULL AS flagged
      FROM cal c LEFT JOIN agg a USING(observed_date) LEFT JOIN flagged_dates f USING(observed_date)
      ORDER BY 1''',[str(start),str(end),DEVICES if devices is None else devices],db)

def weekly(start=START,end=END,devices=None,db=DB):
    return query('''WITH x AS (
      SELECT date_trunc('week',first_date)::DATE week_start,device,touches_flagged_date,count(*) sessions,
      count(*) FILTER(WHERE purchase_events>0) purchase_sessions,
      count(p_ts) strict_purchase,count(upper_purchase_ts) upper_purchase,
      count(*) FILTER(WHERE purchase_events>0 AND p_ts IS NULL) purchase_outside_strict
      FROM reporting_sessions WHERE first_date BETWEEN ?::DATE AND ?::DATE
      AND device IN (SELECT unnest(?)) GROUP BY 1,2,3
    ), calendar AS (
      SELECT *,date_diff('day',greatest(week_start,?::DATE),least(week_start+6,?::DATE))+1 AS selected_calendar_days
      FROM x
    ) SELECT *,selected_calendar_days<7 AS partial_week,purchase_sessions::DOUBLE/nullif(sessions,0) purchase_record_rate,
      purchase_outside_strict::DOUBLE/nullif(purchase_sessions,0) incomplete_purchase_path_rate
      FROM calendar ORDER BY 1,2,3''',[str(start),str(end),DEVICES if devices is None else devices,str(start),str(end)],db)

def followup(start=START,end=END,devices=None,db=DB):
    return query('''SELECT full_24h,near_start,anchor_session_count>1 ambiguous_anchor,
      count(*) checkout_users,count(*) FILTER(WHERE recorded_purchase_24h) recorded_purchase_users,
      count(*) FILTER(WHERE other_session_purchase_24h) other_session_purchase_users
      FROM reporting_followup WHERE anchor_date BETWEEN ?::DATE AND ?::DATE
      AND device IN (SELECT unnest(?)) GROUP BY 1,2,3 ORDER BY 1,2,3''',
      [str(start),str(end),DEVICES if devices is None else devices],db)

def purchase_examples(start,end,devices,scope,db=DB):
    # Do not expose user IDs in the interface; a row is not evidence of same-cart intent.
    return query('''SELECT first_date,last_date,device,purchase_path_class,presence_vacp,
      touches_flagged_date,has_funnel_tie,event_count,purchase_events,
      make_timestamp(v_ts) strict_view_time,make_timestamp(a_ts) strict_cart_time,
      make_timestamp(c_ts) strict_checkout_time,make_timestamp(p_ts) strict_purchase_time
      FROM reporting_sessions WHERE first_date BETWEEN ?::DATE AND ?::DATE
      AND device IN (SELECT unnest(?)) AND purchase_events>0
      AND (?='all' OR (?='touch' AND touches_flagged_date) OR (?='not_touch' AND NOT touches_flagged_date))
      ORDER BY first_date,first_ts,user_pseudo_id,ga_session_id LIMIT 100''',
      [str(start),str(end),devices,scope,scope,scope],db)
