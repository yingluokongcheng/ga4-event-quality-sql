from pathlib import Path
import sys,tempfile,unittest
from datetime import datetime,timezone
import duckdb
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dashboard import data

class ReportingSemantics(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/'test.duckdb'
        self.c=duckdb.connect(str(self.db))
        self.c.execute('''CREATE TABLE raw_events(event_id VARCHAR,event_date VARCHAR,event_timestamp BIGINT,
        event_ts TIMESTAMP,event_name VARCHAR,user_pseudo_id VARCHAR,ga_session_id BIGINT,
        device_category VARCHAR,source VARCHAR,medium VARCHAR,transaction_id VARCHAR,event_value_in_usd DOUBLE)''')
    def add(self,user,event,day,second,device='desktop'):
        ts=int(datetime.strptime(day,'%Y%m%d').replace(tzinfo=timezone.utc).timestamp()*1000000)+second*1000000
        self.c.execute("INSERT INTO raw_events VALUES (?,?,?,make_timestamp(?),?,?,1,?,'google','organic','test',1)",[f'{user}-{event}-{ts}',day,ts,ts,event,user,device])
    def build(self):
        for p in sorted((ROOT/'sql').glob('*.sql')):self.c.execute(p.read_text(encoding='utf-8'))
        self.c.execute((ROOT/'sql/marts/04_reporting.sql').read_text(encoding='utf-8'))
        self.c.close()
    def tearDown(self):self.c.close();self.tmp.cleanup()
    def test_filter_keeps_full_cross_date_history_and_any_date_flag(self):
        for e,d,t in [('view_item','20201101',1),('add_to_cart','20201102',1),('begin_checkout','20201103',1),('purchase','20201103',2)]:self.add('cross',e,d,t)
        self.build()
        r=data.summary('2020-11-01','2020-11-01',['desktop'],self.db)
        a=r[(r.scope=='all')&(r.device_group=='ALL_DEVICES')].iloc[0]
        self.assertEqual((a.sessions,a.strict_purchase,a.touches_flagged),(1,1,1))
        self.assertTrue(data.summary('2020-11-02','2020-11-03',['desktop'],self.db).empty)
    def test_four_classes_partition_and_zero_denominators(self):
        for user,events in [('strict',[('view_item',1),('add_to_cart',2),('begin_checkout',3),('purchase',4)]),('tie',[(e,1) for e in ['view_item','add_to_cart','begin_checkout','purchase']]),('reverse',[('purchase',1),('begin_checkout',2),('add_to_cart',3),('view_item',4)]),('missing',[('begin_checkout',1),('purchase',2)])]:
            for e,t in events:self.add(user,e,'20201201',t)
        self.build();s=data.summary(db=self.db);r=s[(s.scope=='all')&(s.device_group=='ALL_DEVICES')].iloc[0]
        self.assertEqual((r.purchase_sessions,r.strict_purchase,r.tie_only,r.all_present_not_ordered,r.missing_prerequisite),(4,1,1,1,1))
        self.assertEqual(r.upper_purchase,2)
    def test_fixed_date_flags_survive_device_filter_and_empty_days(self):
        self.add('d','purchase','20201102',1,'desktop');self.add('m','view_item','20201103',1,'mobile');self.build()
        d=data.daily('2020-11-02','2020-11-03',['mobile'],self.db)
        self.assertTrue(d.flagged.all());self.assertFalse(d.iloc[0].has_records)
        self.assertTrue(d.iloc[0].isna()['cart_events']);self.assertEqual(d.iloc[1].cart_events,0)
        self.assertTrue(data.summary(devices=[],db=self.db).empty)
    def test_groups_reconcile_and_missing_purchase_stays_observation(self):
        self.add('one','view_item','20201102',1);self.add('two','purchase','20201201',1);self.build()
        s=data.summary(db=self.db);s=s[s.device_group=='ALL_DEVICES'].set_index('scope')
        self.assertEqual(s.loc['all','sessions'],s.loc['touch','sessions']+s.loc['not_touch','sessions'])
        self.assertEqual(s.loc['touch','purchase_sessions'],0)
        self.assertTrue(__import__('pandas').isna(s.loc['touch','incomplete_purchase_path_rate']))

class FullSnapshotChecks(unittest.TestCase):
    def test_current_snapshot_matches_frozen_audit(self):
        s=data.summary();r=s[(s.scope=='all')&(s.device_group=='ALL_DEVICES')].iloc[0]
        self.assertEqual((r.sessions,r.purchase_sessions,r.strict_purchase,r.upper_purchase),(360129,4848,2778,2834))
        groups=s[s.device_group=='ALL_DEVICES'].set_index('scope')
        for k in ['sessions','purchase_sessions','strict_purchase','upper_purchase','purchase_outside_strict']:
            self.assertEqual(groups.loc['all',k],groups.loc['touch',k]+groups.loc['not_touch',k])
        self.assertEqual(int(data.daily().flagged.sum()),18)
        self.assertEqual(int(data.daily().event_rows.sum()),4295584)

if __name__=='__main__':unittest.main()
