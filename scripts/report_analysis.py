"""Self-contained static companion to the local interactive dashboard."""
from pathlib import Path
import sys,json,html
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dashboard import data

def n(v):return f'{int(v):,}'
def pct(v):return '—' if v is None else f'{v:.2%}'
def table(head,rows):
    return '<div class="scroll"><table><thead><tr>'+''.join(f'<th>{html.escape(str(x))}</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{html.escape(str(x))}</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def main():
    result=json.loads((ROOT/'reports/analysis/analysis_results.json').read_text(encoding='utf-8'))['tables']
    allrows=result['session_comparisons'];groups={x['scope']:x for x in allrows if x['device_group']=='ALL_DEVICES'}
    a=groups['all'];touch=groups['touch'];rest=groups['not_touch']
    desktop=next(x for x in allrows if x['scope']=='all' and x['device_group']=='desktop')
    mobile=next(x for x in allrows if x['scope']=='all' and x['device_group']=='mobile')
    h=['''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>购买路径诊断：固定分析结果</title><style>
*{box-sizing:border-box}body{margin:0;background:#f2f6f9;color:#1d3042;font:16px/1.75 "Segoe UI","Microsoft YaHei",sans-serif}main{max-width:1120px;margin:auto;padding:36px 24px 60px}h1{font-size:34px;line-height:1.3;margin:10px 0 20px}h2{font-size:23px;margin-top:0}.label{color:#176b80;font-size:13px;letter-spacing:.12em}section{background:white;padding:25px;border:1px solid #dce5ec;border-radius:12px;margin:20px 0}.note{border-left:5px solid #d99030;background:#fffaf0}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card{border:1px solid #dce5ec;border-radius:10px;padding:16px;background:white}.value{font-size:27px;font-weight:700}.muted{color:#5e7180;font-size:14px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:11px;border-bottom:1px solid #dce5ec;vertical-align:top}th{background:#edf4f7}.scroll{overflow-x:auto}a{color:#176b80}pre{overflow:auto;background:#182f40;color:white;border-radius:8px;padding:18px;font-size:14px}.pathbar{display:flex;height:40px;overflow:hidden;border-radius:6px;margin:18px 0}.segment{min-width:3px}code{background:#eef2f5;padding:2px 4px}footer{font-size:13px;color:#5e7180}@media(max-width:700px){main{padding:20px 12px}.cards{grid-template-columns:repeat(2,1fr)}section{padding:18px}h1{font-size:28px}}@media print{body{background:white}section{break-inside:avoid}}
</style></head><body><main><div class="label">LOCAL SQL / FIXED ANALYSIS V2 / 2026-10-16</div><h1>事件质量与观察到的购买路径诊断</h1>
<p>异常日期与时间并列全部保留。没有为结果好看删除日期、重选窗口或改变路径口径；设备比较只作描述。</p>''']
    h.append('<div class="cards">'+''.join(f'<div class="card"><div class="value">{value}</div>{label}</div>' for value,label in [(n(a['sessions']),'可识别会话'),(n(a['purchase_sessions']),'有购买记录的会话'),(pct(a['incomplete_purchase_path_rate']),'购买但严格路径不完整'),('18 天','固定零加购标记')])+'</div>')
    h.append('''<section class="note"><h2>先读结论与边界</h2><p><strong>完整漏斗的断层不能直接解释为真实流失。</strong>涉及固定异常日期的会话仍记录到购买，却无法组成四步路径；未涉及组也有大量不完整路径。时间并列只解释其中一小部分。</p><p>这是一份固定版本的第三方 GA4 扁平化副本分析，未与 Google 原表逐行核对。记录异常的原因可能涉及采集、导出、脱敏及购物过程差异，当前数据不能识别哪一种原因。无后台订单、支付或埋点日志对账，不估计真实流失率。</p></section>''')
    h.append('<section><h2>1. 固定的三组比较</h2>')
    h.append(table(['会话组','会话数','有购买记录','购买记录会话率','严格完整路径','购买路径不完整占比'],[[data.SCOPE_NAMES[k],n(groups[k]['sessions']),n(groups[k]['purchase_sessions']),pct(groups[k]['purchase_record_rate']),n(groups[k]['strict_purchase']),pct(groups[k]['incomplete_purchase_path_rate'])] for k in ['all','touch','not_touch']]))
    h.append(f'''<p>涉及组有 <strong>{n(touch['purchase_sessions'])}</strong> 个购买会话，但加购会话为零、完整路径为零。这是“已购买但缺少记录”的直接例子，不是100%的真实流失。</p>
<p>未涉及组仍有 <strong>{n(rest['purchase_outside_strict'])}/{n(rest['purchase_sessions'])}（{pct(rest['incomplete_purchase_path_rate'])}）</strong> 的购买会话不满足完整严格路径。不能把剩余日期当作已清洗正常数据，或认定18天异常解释了全部问题。</p>
<p>两组购买记录会话率分别为 {pct(touch['purchase_record_rate'])} 与 {pct(rest['purchase_record_rate'])}；严格路径差异远大于这一描述性差异。它提示解释路径指标时必须先检查事件覆盖，<strong>不证明业务表现稳定，也不是埋点影响的因果估计</strong>。</p>
<p class="muted">分组按会话任一事件是否落在固定18天；日期筛选按会话首次观察日期。先建完整历史路径，后筛选。全部＝涉及＋未涉及，分子分母来自同一组。</p></section>''')
    h.append('<section><h2>2. 18天异常如何保留</h2><p>2020-11-02—11-15、11-21—11-24固定标为“未记录加购，但存在结算/购买；原因未确认”。看板四张每日事件图用橙色背景标记，不插值、不平滑补齐；无整日记录使用灰色，与已知零值区分。</p><p>这18天包含1,071条购买<strong>事件</strong>；涉及组包含815个购买<strong>会话</strong>。统计单位与日期归属不同，两个数字不能直接相减当作漏失订单。</p><p>质量页使用事件日期；路径/设备页使用会话首次观察日期。会话跨日不拆分，标记不随设备筛选重新定义。看板默认全92天，未隐藏任何日期。</p></section>')
    h.append('<section><h2>3. 时间并列只解释部分路径不完整</h2><div class="pathbar">')
    values=[a['strict_purchase'],a['tie_only'],a['all_present_not_ordered'],a['missing_prerequisite']]
    colors=['#176b80','#d99030','#9a6d91','#8a99a9']
    for label,value,color in zip(data.CLASS_NAMES.values(),values,colors):h.append(f'<div class="segment" style="width:{100*value/a["purchase_sessions"]:.6f}%;background:{color}" title="{label}：{n(value)}"></div>')
    h.append('</div>'+table(['互斥类型','购买会话数','解释'],[[label,n(value),meaning] for label,value,meaning in zip(data.CLASS_NAMES.values(),values,['存在严格递增的完整子序列','允许同刻后才可能组成路径；顺序未知','阶段齐全，但所记录的时间顺序不符合标准链','至少缺少一个前置阶段；本次均缺加购'])]))
    h.append(f'''<p>严格完整路径为 {n(a['strict_purchase'])}；允许同刻的可能上界为 {n(a['upper_purchase'])}。只增加了 {n(a['tie_only'])} 个会话，不能消除 {n(a['missing_prerequisite'])} 个会话的前置记录缺失。</p>
<p>这一范围描述已记录事件的排序不确定性，<strong>不是置信区间或实际行为数量的上下界</strong>。不按事件名称、文件行号或业务直觉排序。</p>''')
    h.append(table(['阶段','独立出现会话','严格路径会话','允许同刻的可能路径'],[['浏览',n(a['view_sessions']),n(a['strict_view']),n(a['strict_view'])],['加购',n(a['cart_sessions']),n(a['strict_cart']),n(a['upper_cart'])],['结算',n(a['checkout_sessions']),n(a['strict_checkout']),n(a['upper_checkout'])],['购买',n(a['purchase_sessions']),n(a['strict_purchase']),n(a['upper_purchase'])]]))
    h.append('<p class="muted">三列口径不同，不能交叉相除。完整路径占浏览会话的比例使用同一个浏览分母；阶段继续率则各自使用严格/允许同刻的分母，两套阶段比率不能称为上下界。零分母显示“—”。</p></section>')
    h.append('<section><h2>4. 设备比较：差异小于结论所需的证据</h2>')
    h.append(table(['设备','会话数','购买会话','购买记录会话率','购买路径不完整比例'],[[r['device_group'],n(r['sessions']),n(r['purchase_sessions']),pct(r['purchase_record_rate']),pct(r['incomplete_purchase_path_rate'])] for r in allrows if r['scope']=='all' and r['device_group']!='ALL_DEVICES']))
    h.append(f'''<p>移动端购买记录会话率为 {pct(mobile['purchase_record_rate'])}，桌面端为 {pct(desktop['purchase_record_rate'])}，相差约 {(mobile['purchase_record_rate']-desktop['purchase_record_rate'])*100:.3f} 个百分点。两端均存在大量不完整购买路径。</p><p>只能陈述样本中的记录差异；没有统计显著性或因果优劣结论，也不因此建议重做某端界面。看板同时保留三组对照、设备样本量、异常日期涉及数量、同刻数量和周明细。</p><p class="muted">周一开始归周；2020-10-26所属周只覆盖11月1日。筛选边缘周可能不完整，不能和完整周直接解释为正常业务涨跌。</p></section>''')
    h.append('<section><h2>5. 辅助观察与暂不支持的结论</h2><p>以每个伪用户首次可识别结算为锚点，9,667人具有完整24小时观察区间，其中4,149人有后续购买记录；另有48人观察不足，单独展示。完整组中91人靠近样本开始。</p><p>301人在其他会话出现过后续购买，可能与同会话购买重叠，不能称作“挽回301位客户”，也不能证明同一购物车。没有记录到后续购买的用户不自动归为真实流失。</p><p>收入、客单价、品类及当前会话渠道分析继续暂停。缺失字段和交易编号冲突没有通过补值或强行去重掩盖。</p></section>')
    h.append('''<section><h2>6. 本地启动与复现</h2><p><strong>这台电脑：</strong>打开项目目录，双击 <a href="../../Start_dashboard.cmd">Start_dashboard.cmd</a>。浏览器进入 <code>http://127.0.0.1:8501</code>。保持启动窗口运行，Ctrl+C停止服务。若已有本项目实例运行，可直接访问地址。</p><p><strong>换一台电脑：</strong>先安装Python 3.12，解压代码包后运行 <a href="../../Setup.cmd">Setup.cmd</a>；首次安装与274MB数据下载需要普通网络，不需要Google Cloud。数据准备完成后再启动。原始数据及虚拟环境没有装进代码ZIP。</p>
<pre># 已有环境，重新计算（先停止正在运行的看板）
.venv/Scripts/python scripts/audit.py
.venv/Scripts/python scripts/build_analysis.py
.venv/Scripts/python scripts/report_analysis.py
.venv/Scripts/python -m unittest discover -s tests -v

# 启动本地服务
.venv/Scripts/python -m streamlit run app.py</pre>
<p>日常展示只读取本地数据库；无云账户和外部分析接口。原始副本、固定SQL、全部分组结果和上一版审计均保留。本地服务只监听127.0.0.1。</p>
<p><a href="analysis_results.json">完整结果 JSON</a> · <a href="session_comparisons.csv">全部固定对照 CSV</a> · <a href="daily_coverage.csv">每日覆盖</a> · <a href="weekly_device.csv">周×设备明细</a> · <a href="../../docs/PROTOCOL.md">固定口径</a> · <a href="../../README.md">完整运行说明</a></p></section>
<footer>仅本地交付，未发布GitHub。指标与交互测试记录见reports/verification.json。数据来源与限制见provenance/SOURCE_NOTES.md。观察记录不等于真实行为全貌。</footer></main></body></html>''')
    (ROOT/'reports/analysis/固定分析结果与解释.html').write_text('\n'.join(h),encoding='utf-8')
    print('Static analysis report generated.')

if __name__=='__main__':main()
