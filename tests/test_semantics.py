"""Tiny synthetic edge cases, never mixed into empirical audit outputs."""
from pathlib import Path
import unittest
import duckdb

ROOT=Path(__file__).resolve().parents[1]

class SemanticsTest(unittest.TestCase):
    def setUp(self):
        self.c=duckdb.connect()
        self.c.execute('''CREATE TABLE raw_events(event_id VARCHAR,event_date VARCHAR,event_timestamp BIGINT,
        event_ts TIMESTAMP,event_name VARCHAR,user_pseudo_id VARCHAR,ga_session_id BIGINT,
        device_category VARCHAR,source VARCHAR,medium VARCHAR,transaction_id VARCHAR,event_value_in_usd DOUBLE)''')

    def add(self,user,session,name,ts,tx=None):
        self.c.execute("INSERT INTO raw_events VALUES (?, '20201101',?,make_timestamp(?),?,?,?,'desktop','(direct)','(none)',?,NULL)",
                       [f'{user}-{session}-{name}-{ts}',ts,ts,name,user,session,tx])

    def build(self):
        for p in sorted((ROOT/'sql').glob('*.sql')):
            self.c.execute(p.read_text(encoding='utf-8'))

    def tearDown(self):self.c.close()

    def test_later_repeated_stage_can_complete_path(self):
        for name,ts in [('add_to_cart',1),('view_item',2),('add_to_cart',3),('begin_checkout',4),('purchase',5)]:
            self.add('repeat',1,name,ts)
        self.build()
        self.assertEqual(self.c.sql('SELECT a_ts,p_ts FROM paths').fetchone(),(3,5))

    def test_ties_are_bounds_not_assumed_order(self):
        for name in ['view_item','add_to_cart','begin_checkout','purchase']:self.add('tie',1,name,10)
        self.build()
        self.assertIsNone(self.c.sql('SELECT p_ts FROM paths').fetchone()[0])
        self.assertEqual(self.c.sql('SELECT p_ts FROM tie_permissive_paths').fetchone()[0],10)

    def test_missing_cart_not_classified_as_failed_purchase(self):
        for name,ts in [('view_item',1),('begin_checkout',2),('purchase',3)]:self.add('skip',1,name,ts)
        self.build()
        self.assertEqual(self.c.sql('SELECT purchase_events,presence_vacp,p_ts FROM paths').fetchone(),(1,'1011',None))

    def test_missing_identity_is_not_an_unknown_session(self):
        self.add(None,1,'purchase',1);self.add('u',None,'purchase',2)
        self.build()
        self.assertEqual(self.c.sql('SELECT count(*) FROM sessions').fetchone()[0],0)
        self.assertEqual(self.c.sql('SELECT count(*) FROM events').fetchone()[0],2)

    def test_session_key_includes_user_and_placeholders_invalid(self):
        self.add('a',1,'purchase',1,'(not set)');self.add('b',1,'purchase',2,'valid')
        self.build()
        self.assertEqual(self.c.sql('SELECT count(*) FROM sessions').fetchone()[0],2)
        self.assertEqual(self.c.sql('SELECT count(*) FROM transaction_quality').fetchone()[0],1)
        self.assertFalse(self.c.sql("SELECT usable('(data deleted)')").fetchone()[0])

    def test_followup_boundary_and_other_session(self):
        self.add('u',1,'begin_checkout',1)
        self.add('u',2,'purchase',86400000001)
        self.add('late',1,'begin_checkout',86400000000)
        self.build()
        self.assertEqual(self.c.sql("SELECT full_24h,recorded_purchase_24h,other_session_purchase_24h FROM checkout_followup WHERE user_pseudo_id='u'").fetchone(),(True,True,True))
        self.assertFalse(self.c.sql("SELECT full_24h FROM checkout_followup WHERE user_pseudo_id='late'").fetchone()[0])

if __name__=='__main__':unittest.main()
