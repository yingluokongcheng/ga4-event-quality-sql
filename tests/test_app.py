from pathlib import Path
import sys,unittest
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest

class DashboardChecks(unittest.TestCase):
    def app(self):return AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    def test_quality_and_navigation_have_no_exceptions(self):
        a=self.app();self.assertEqual(len(a.exception),0)
        self.assertEqual(a.metric[0].value,'4,295,584')
        for page in ['观察到的购买路径','设备辅助比较']:
            a.radio(key='page').set_value(page).run();self.assertEqual(len(a.exception),0)
            self.assertEqual(a.metric[0].value,'1.35%')
    def test_flagged_group_keeps_purchases_and_zero_path(self):
        a=self.app();a.radio(key='page').set_value('观察到的购买路径').run()
        a.selectbox(key='scope').set_value('涉及异常日期').run()
        self.assertEqual(len(a.exception),0);self.assertEqual(a.metric[1].value,'0.00%');self.assertEqual(a.metric[2].value,'100.00%')
    def test_empty_filter_and_empty_group_do_not_fall_back(self):
        a=self.app();a.multiselect(key='devices').set_value([]).run()
        self.assertEqual(len(a.exception),0);self.assertEqual(len(a.metric),0);self.assertGreater(len(a.warning),0)
        a.multiselect(key='devices').set_value(['desktop']).run()
        a.radio(key='page').set_value('观察到的购买路径').run()
        a.date_input(key='period').set_value((date(2020,12,1),date(2020,12,31))).run()
        a.selectbox(key='scope').set_value('涉及异常日期').run()
        self.assertEqual(len(a.exception),0);self.assertEqual(len(a.metric),0);self.assertGreater(len(a.warning),0)

if __name__=='__main__':unittest.main()
