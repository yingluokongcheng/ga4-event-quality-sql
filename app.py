"""Local-only diagnostic dashboard; every metric originates in shared SQL."""
from datetime import date,timedelta
import json
import altair as alt
import pandas as pd
import streamlit as st
from dashboard import data

st.set_page_config(page_title='购买路径诊断 | Local SQL',page_icon='◈',layout='wide')
st.markdown('''<style>
.block-container{padding-top:4rem;max-width:1440px}h1{letter-spacing:-.025em}
[data-testid="stMetric"]{background:white;border:1px solid #DCE5EC;border-radius:10px;padding:16px}
[data-testid="stSidebar"]{border-right:1px solid #DCE5EC}
[data-testid="stMetricValue"]{font-size:1.85rem}.small-label{font-size:12px;letter-spacing:.14em;color:#176B80;font-weight:700}
</style>''',unsafe_allow_html=True)
st.sidebar.markdown('### ◈ 购买路径诊断')
st.sidebar.caption('LOCAL SQL · FIXED PROTOCOL V2')
page=st.sidebar.radio('查看内容',['事件覆盖与质量','观察到的购买路径','设备辅助比较'],key='page')
period=st.sidebar.date_input('日期范围',value=(date(2020,11,1),date(2021,1,31)),min_value=date(2020,11,1),max_value=date(2021,1,31),key='period')
devices=st.sidebar.multiselect('设备',data.DEVICES,default=data.DEVICES,key='devices')
st.sidebar.divider()
st.sidebar.caption('固定标记：11/02–11/15、11/21–11/24。筛选不重新定义异常日；未涉及日期不代表数据正常。')
st.sidebar.caption('本地 DuckDB + Streamlit。收入、客单价、品类和会话渠道归因不在本版范围内。')
st.markdown('<div class="small-label">EVENT QUALITY / OBSERVED PURCHASE PATHS</div>',unsafe_allow_html=True)
st.title(page)
st.info('第三方 GA4 扁平化副本 · 未与 Google 原表逐行核对。未记录购买 ≠ 真实流失；记录异常 ≠ 已证实的埋点故障。')
if not data.DB.exists():
    st.error('本地数据库尚未构建。请先运行 setup.ps1，或按 README 完成数据准备。');st.stop()
if len(period)!=2:
    st.warning('请选择完整的开始和结束日期。');st.stop()
if not devices:
    st.warning('请至少选择一种设备；空选择不自动解释为全部设备。');st.stop()
start,end=period

@st.cache_data(show_spinner=False)
def load_summary(start,end,devices,version):return data.summary(start,end,devices)
@st.cache_data(show_spinner=False)
def load_daily(start,end,devices,version):return data.daily(start,end,devices)
version=data.DB.stat().st_mtime_ns
s=load_summary(start,end,devices,version)
daily=load_daily(start,end,devices,version)
scope='all'
def integer(x):return f'{int(x):,}'
def pct(x):return '—' if pd.isna(x) else f'{x:.2%}'
def csv_download(df,label,key):
    st.download_button(label,df.to_csv(index=False).encode('utf-8-sig'),file_name=f'{key}.csv',mime='text/csv',key=key)
def group_table(frame):
    frame=frame.copy();frame['display_order']=frame.scope.map({'all':0,'touch':1,'not_touch':2});frame=frame.sort_values('display_order')
    cols=['scope','sessions','purchase_sessions','purchase_record_rate','strict_purchase','upper_purchase','purchase_outside_strict','incomplete_purchase_path_rate']
    out=frame[cols].copy();out['scope']=out.scope.map(data.SCOPE_NAMES)
    for c in ['purchase_record_rate','incomplete_purchase_path_rate']:out[c]=out[c].map(pct)
    return out.rename(columns={'scope':'会话组','sessions':'会话数','purchase_sessions':'有购买记录','purchase_record_rate':'购买记录会话率','strict_purchase':'严格完整路径','upper_purchase':'同刻兼容上界','purchase_outside_strict':'购买但路径不完整','incomplete_purchase_path_rate':'路径不完整占购买会话'})

if page=='事件覆盖与质量':
    st.caption('本页按事件发生日期筛选，不是会话首次观察日期。图中数字是事件记录数，不是人数或订单数。')
    cards=st.columns(4)
    vals=[('事件记录',integer(daily.event_rows.sum())),('有记录的日期',integer(daily.has_records.sum())),('选中固定异常日期',integer(daily.flagged.sum())),('购买事件记录',integer(daily.purchase_events.sum()))]
    for col,(label,value) in zip(cards,vals):col.metric(label,value)
    st.subheader('每日事件覆盖')
    st.caption('橙色背景＝固定的18天标记；灰色背景＝当前设备/日期组合没有任何事件记录。零值不补齐、不平滑。四图纵轴独立。')
    shaded=daily[daily.flagged].copy();shaded['next_day']=shaded.observed_date+pd.Timedelta(days=1)
    absent=daily[~daily.has_records].copy();absent['next_day']=absent.observed_date+pd.Timedelta(days=1)
    for j,(field,label) in enumerate([('view_events','浏览商品'),('cart_events','加购'),('checkout_events','结算'),('purchase_events','购买')]):
        if j%2==0:cols=st.columns(2)
        with cols[j%2]:
            backdrop=alt.Chart(shaded).mark_rect(color='#E9A54B',opacity=.18).encode(x=alt.X('observed_date:T',title=None),x2='next_day:T')
            missing=alt.Chart(absent).mark_rect(color='#8B98A6',opacity=.35).encode(x='observed_date:T',x2='next_day:T')
            bars=alt.Chart(daily).mark_bar(color='#176B80',size=5).encode(x=alt.X('observed_date:T',title=None),y=alt.Y(f'{field}:Q',title='事件数'),tooltip=[alt.Tooltip('observed_date:T',title='日期',format='%Y-%m-%d'),alt.Tooltip(f'{field}:Q',title=label,format=',.0f'),'flagged:N'])
            st.altair_chart((backdrop+missing+bars).properties(title=label,height=210),use_container_width=True)
    st.subheader('固定异常日期明细')
    st.warning('未记录加购，但存在结算/购买。原因未确认；不能称为用户全部放弃加购。')
    selected=daily[daily.flagged]
    st.dataframe(selected.rename(columns={'observed_date':'日期','event_rows':'全部事件','view_events':'浏览','cart_events':'加购','checkout_events':'结算','purchase_events':'购买','unusable_transaction_events':'交易编号不可用','has_records':'有事件记录','flagged':'固定标记'}),hide_index=True,width='stretch')
    with st.expander('按日期和设备查看事件明细'):
        detail=data.query('SELECT * FROM daily_device WHERE observed_date BETWEEN ?::DATE AND ?::DATE AND device IN (SELECT unnest(?)) ORDER BY 1,2',[str(start),str(end),devices])
        st.dataframe(detail,hide_index=True,width='stretch')
    csv_download(daily,'导出当前每日覆盖','daily_filtered')
    st.subheader('会话与交易质量说明')
    st.caption('以下会话数字改按会话首次观察日期筛选；仅作质量背景，不与上方事件数直接相除。')
    r=s[(s.scope=='all')&(s.device_group=='ALL_DEVICES')]
    if not r.empty:
        r=r.iloc[0]
        st.write(f"无 session_start：{integer(r.no_session_start)}；多个 session_start：{integer(r.multiple_session_start)}；跨日：{integer(r.cross_date)}；跨度超过24小时：{integer(r.over_24h)}。均保留。")
    st.write('交易编号缺失、冲突及专用收入字段不全，收入拆解暂停。无 refund 记录不等于没有退款。')

else:
    st.caption('按会话首次观察日期筛选；路径和“涉及异常日期”标记先由完整历史建立。涉及＝会话任一事件落在固定18天中。')
    st.subheader('三组固定对照')
    comp=s[s.device_group=='ALL_DEVICES']
    st.dataframe(group_table(comp),hide_index=True,width='stretch')
    st.caption('全部＝涉及＋未涉及。未涉及组不是“清洗后正常样本”；组间差异不是埋点故障的因果效果。')
    scope_label=st.selectbox('下方明细的会话组',list(data.SCOPE_NAMES.values()),key='scope')
    scope=next(k for k,v in data.SCOPE_NAMES.items() if v==scope_label)
    subset=s[(s.scope==scope)&(s.device_group=='ALL_DEVICES')]
    if subset.empty:
        st.warning('当前日期、设备和会话组没有样本，指标显示为空，不填成0%或恢复全部样本。');st.stop()
    r=subset.iloc[0]
    cols=st.columns(3)
    cols[0].metric('购买记录会话率',pct(r.purchase_record_rate));cols[0].caption(f'{integer(r.purchase_sessions)} / {integer(r.sessions)} 个会话')
    cols[1].metric('严格完整路径 / 浏览会话',pct(r.strict_complete_per_view));cols[1].caption(f'{integer(r.strict_purchase)} / {integer(r.view_sessions)} 个会话')
    cols[2].metric('路径不完整 / 购买会话',pct(r.incomplete_purchase_path_rate));cols[2].caption(f'{integer(r.purchase_outside_strict)} / {integer(r.purchase_sessions)} 个会话')
    if page=='观察到的购买路径':
        st.subheader('已记录购买的会话：四种路径证据')
        classes=pd.DataFrame({'类型':list(data.CLASS_NAMES.values()),'会话数':[int(r.strict_purchase),int(r.tie_only),int(r.all_present_not_ordered),int(r.missing_prerequisite)],'顺序':[0,1,2,3],'总体':['购买会话']*4})
        chart=alt.Chart(classes).mark_bar(size=56).encode(x=alt.X('会话数:Q',stack='zero'),y=alt.Y('总体:N',title=None),color=alt.Color('类型:N',scale=alt.Scale(domain=list(data.CLASS_NAMES.values()),range=['#176B80','#D99030','#9A6D91','#8A99A9']),legend=alt.Legend(orient='bottom')),order='顺序:Q',tooltip=['类型:N','会话数:Q']).properties(height=140)
        st.altair_chart(chart,use_container_width=True)
        st.dataframe(classes[['类型','会话数']],hide_index=True,width='stretch')
        st.write(f"严格完整路径 **{integer(r.strict_purchase)}**；允许同刻的可能上界 **{integer(r.upper_purchase)}**。同刻兼容部分 **{integer(r.tie_only)}** 个，顺序仍不确定。")
        st.caption('这是已记录事件的排序不确定性，不是置信区间，也不是实际行为数量的上下界。没有按照文件行号或事件名称给同刻事件排序。')
        st.subheader('独立出现与有序路径分开看')
        stages=pd.DataFrame({'阶段':['浏览商品','加购','结算','购买'],'独立出现会话':[r.view_sessions,r.cart_sessions,r.checkout_sessions,r.purchase_sessions],'严格路径会话':[r.strict_view,r.strict_cart,r.strict_checkout,r.strict_purchase],'允许同刻的可能路径':[r.strict_view,r.upper_cart,r.upper_checkout,r.upper_purchase]})
        st.dataframe(stages,hide_index=True,width='stretch')
        with st.expander('阶段继续率：同时显示分子、分母'):
            rows=[]
            for mode,label in [('strict','严格顺序'),('upper','允许同刻（仅敏感性）')]:
                vals=[r.strict_view,r[f'{mode}_cart'],r[f'{mode}_checkout'],r[f'{mode}_purchase']]
                for i,(step,key) in enumerate([('浏览→加购','view_cart'),('加购→结算','cart_checkout'),('结算→购买','checkout_purchase')]):
                    rows.append([label,step,int(vals[i+1]),int(vals[i]),pct(r[f'{mode}_{key}_rate'])])
            st.dataframe(pd.DataFrame(rows,columns=['口径','步骤','分子','分母','观察到的继续率']),hide_index=True,width='stretch')
            st.caption('分母随口径变化，因此两套阶段继续率不构成上下界，也不能解释为真实流失率。')
        with st.expander('购买会话示例（前100条，不展示用户标识）'):
            st.dataframe(data.purchase_examples(start,end,devices,scope),hide_index=True,width='stretch')
        with st.expander('24小时后续购买：独立的用户级辅助观察'):
            st.caption('按伪用户首次可识别结算的锚点日期筛选；沿用设备筛选，不跟随会话异常组。先建立完整24小时观察，再筛选锚点；与上方会话分母不同。')
            fu=data.followup(start,end,devices)
            st.dataframe(fu.rename(columns={'full_24h':'完整24小时','near_start':'靠近样本开始','ambiguous_anchor':'锚点会话不唯一','checkout_users':'结算伪用户','recorded_purchase_users':'后续购买伪用户','other_session_purchase_users':'其他会话购买伪用户'}),hide_index=True,width='stretch')
            st.caption('完整观察不代表埋点完整。跨会话购买不能证明同一购物车；其他会话购买可能与同会话购买重叠，不能称为挽回客户。')
    else:
        st.subheader('设备描述：数量、比例与质量一起展示')
        dev=s[(s.scope==scope)&(s.device_group!='ALL_DEVICES')].copy()
        display=dev[['device_group','sessions','purchase_sessions','purchase_record_rate','strict_purchase','upper_purchase','purchase_outside_strict','incomplete_purchase_path_rate','touches_flagged','sessions_with_ties']].copy()
        for col in ['purchase_record_rate','incomplete_purchase_path_rate']:display[col]=display[col].map(pct)
        display.columns=['设备','会话数','购买会话','购买记录会话率','严格完整路径','同刻兼容上界','路径不完整购买会话','不完整占购买会话','涉及异常日期会话','有同刻阶段会话']
        st.dataframe(display,hide_index=True,width='stretch')
        chart=alt.Chart(dev).mark_bar(color='#176B80',size=42).encode(x=alt.X('device_group:N',sort=data.DEVICES,title='设备'),y=alt.Y('purchase_record_rate:Q',axis=alt.Axis(format='.1%'),title='购买记录会话率'),tooltip=['device_group:N',alt.Tooltip('sessions:Q',format=',.0f'),alt.Tooltip('purchase_sessions:Q',format=',.0f'),alt.Tooltip('purchase_record_rate:Q',format='.2%')]).properties(height=250)
        st.altair_chart(chart,use_container_width=True)
        st.caption('没有最佳设备排名、显著性或因果结论。比例差异不等于界面优劣，样本覆盖、时间构成与记录质量都可能影响比较。')
        st.subheader('周 × 设备明细')
        w=data.weekly(start,end,devices)
        if scope!='all':w=w[w.touches_flagged_date==(scope=='touch')]
        st.dataframe(w,hide_index=True,width='stretch')
        st.caption('按会话首次观察日期归周，周一开始。2020-10-26所属周仅观察到11月1日；筛选边缘周也可能不完整。涉及异常日期的周不解释为正常漏斗业务趋势。')
    csv_download(s,'导出当前日期与设备下的全部固定对照','session_comparisons_filtered')

with st.expander('口径、数据来源与限制'):
    st.markdown('''- 伪用户不等于真实人数；会话联合键不等于购物车。路径不要求同一SKU。
- 数据先建立完整路径，再筛选；没有删异常日期、补造事件或事后调整窗口。
- 第一/最后观察日的会话可能被样本边界截断；无session_start和跨度异常均保留。
- 缺少原始参数、专用收入和币种等字段；无法分离真实未购买与记录缺失。
- 来源固定提交：`41c4ee829b7c18cdb52810686768edfa035a42e0`。本地文件经过哈希核验，原表完整性未核验。
- 本版本仅本地运行，尚未发布 GitHub。''')
st.caption('GA4 LOCAL DIAGNOSTICS · 数据解释优先于业务归因 · 所有筛选仅改变观察范围，不改变固定口径')
