"""Build frozen reporting marts and export fixed comparisons."""
from pathlib import Path
import sys,json,hashlib
import duckdb
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dashboard import data

def main():
    with duckdb.connect(str(data.DB)) as con:
        con.execute((ROOT/'sql/marts/04_reporting.sql').read_text(encoding='utf-8'))
        assert con.sql('SELECT count(*) FROM flagged_dates').fetchone()[0]==18
        assert con.sql('SELECT count(*) FROM reporting_sessions').fetchone()[0]==360129
    out=ROOT/'reports/analysis';out.mkdir(parents=True,exist_ok=True)
    frames={'session_comparisons':data.summary(),'daily_coverage':data.daily(),'weekly_device':data.weekly(),'followup':data.followup()}
    for name,df in frames.items():
        df.to_csv(out/f'{name}.csv',index=False,encoding='utf-8-sig',float_format='%.12g')
    s=frames['session_comparisons'];allrow=s[(s.scope=='all')&(s.device_group=='ALL_DEVICES')].iloc[0]
    assert allrow.strict_purchase+allrow.tie_only+allrow.all_present_not_ordered+allrow.missing_prerequisite==allrow.purchase_sessions
    assert (int(allrow.strict_purchase),int(allrow.tie_only),int(allrow.all_present_not_ordered),int(allrow.missing_prerequisite))==(2778,56,14,2000)
    for _,r in s.iterrows():
        assert r.strict_purchase<=r.upper_purchase<=r.purchase_sessions
        assert r.strict_view>=r.strict_cart>=r.strict_checkout>=r.strict_purchase
        assert r.strict_view>=r.upper_cart>=r.upper_checkout>=r.upper_purchase
    # Both source histories and query hashes make future changes reviewable.
    result={'protocol':'fixed-v2','source_commit':'41c4ee829b7c18cdb52810686768edfa035a42e0',
      'no_new_exclusion':True,'query_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'sql').rglob('*.sql'))},
      'tables':{name:json.loads(df.to_json(orient='records',date_format='iso',double_precision=12)) for name,df in frames.items()}}
    (out/'analysis_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(s[s.device_group=='ALL_DEVICES'].to_string(index=False))
    print('Reporting marts and fixed comparisons exported.')

if __name__=='__main__':main()
