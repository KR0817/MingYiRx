from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from . import __version__


class DashboardError(ValueError):
    """Raised when aggregate dashboard inputs are missing or invalid."""


TABLES = {
    "cohorts": (
        "cohort_summary.csv",
        {"group", "patients", "repeat_patients", "visits", "transitions"},
    ),
    "items": (
        "first_prescription_item_prevalence.csv",
        {"group", "item_name", "exposed_patients", "group_patients", "prevalence"},
    ),
    "combinations": (
        "frequent_item_combinations.csv",
        {
            "group",
            "combination_size",
            "combination",
            "support_patients",
            "support",
            "bootstrap_core_selection_probability",
            "stable_core_combination",
        },
    ),
    "changes": (
        "longitudinal_item_change_tendency.csv",
        {
            "group",
            "item_name",
            "change_type",
            "repeat_patients",
            "patients_with_change",
            "patient_prevalence",
            "mean_patient_transition_fraction",
        },
    ),
    "longitudinal": (
        "longitudinal_summary.csv",
        {
            "group",
            "repeat_patients",
            "transitions",
            "median_patient_jaccard",
            "median_patient_retention",
            "median_patient_addition",
            "median_patient_modification_burden",
        },
    ),
}


def _read_rows(path: Path, required: set[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise DashboardError(f"Missing aggregate table: {path.name}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or ())
        missing = required - headers
        if missing:
            raise DashboardError(
                f"{path.name} is missing columns: {', '.join(sorted(missing))}"
            )
        return list(reader)


def _group_labels(input_dir: Path) -> dict[str, str]:
    path = input_dir / "network_nodes.csv"
    if not path.is_file():
        return {}
    rows = _read_rows(path, {"group", "group_label"})
    return {
        row["group"]: row["group_label"]
        for row in rows
        if row["group"] and row["group_label"]
    }


def _fallback_label(group: str) -> str:
    return group.removesuffix("_strict").replace("_", " ").upper()


def build_dashboard(input_dir: Path, output: Path, title: str) -> dict[str, object]:
    input_dir = input_dir.resolve()
    output = output.resolve()
    loaded = {
        key: _read_rows(input_dir / filename, required)
        for key, (filename, required) in TABLES.items()
    }
    labels = _group_labels(input_dir)
    groups = [
        {
            "code": row["group"],
            "label": labels.get(row["group"], _fallback_label(row["group"])),
            **row,
        }
        for row in loaded["cohorts"]
    ]
    if not groups:
        raise DashboardError("cohort_summary.csv has no reportable groups")

    payload = {
        "version": __version__,
        "groups": groups,
        "items": loaded["items"],
        "combinations": loaded["combinations"],
        "changes": loaded["changes"],
        "longitudinal": loaded["longitudinal"],
    }
    payload_text = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    document = (
        HTML_TEMPLATE.replace("__TITLE__", html.escape(title))
        .replace("__PAYLOAD__", payload_text)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    return {
        "gate": "PASS",
        "dashboard": str(output),
        "groups": len(groups),
        "source_tables": [filename for filename, _ in TABLES.values()],
        "patient_level_data_included": False,
    }


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--canvas:#edf1f0;--paper:#fbfcf9;--ink:#17231f;--muted:#64706b;--rule:#cbd3cf;--pine:#1f5a46;--pine-soft:#dce9e3;--blue:#2d5f88;--blue-soft:#dce8f0;--cinnabar:#a64b3c;--red-soft:#f1dfda;--shadow:0 14px 36px rgba(23,35,31,.08)}
*{box-sizing:border-box}html{background:var(--canvas);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif}body{margin:0;min-height:100vh;overflow-x:hidden;background:linear-gradient(90deg,rgba(31,90,70,.035) 1px,transparent 1px);background-size:28px 28px}
button,input,select{font:inherit}button{color:inherit}.safety{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:center;gap:.55rem;min-height:36px;padding:.4rem 1rem;background:var(--ink);color:#fff;font-size:12px;letter-spacing:.04em}.safety b{color:#b9e0cf}.shell{display:grid;grid-template-columns:245px minmax(0,1fr);min-height:calc(100vh - 36px)}
.rail{position:sticky;top:36px;height:calc(100vh - 36px);padding:28px 20px;border-right:1px solid var(--rule);background:rgba(251,252,249,.88);backdrop-filter:blur(10px)}.brand{margin-bottom:34px}.eyebrow{font:700 10px/1.2 ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.18em;text-transform:uppercase;color:var(--pine)}.brand h1{margin:.55rem 0 .4rem;font:600 28px/1.08 "STFangsong","FangSong",serif;letter-spacing:.04em}.brand p{margin:0;color:var(--muted);font-size:12px;line-height:1.65}
.group-nav{display:grid;gap:7px}.group-btn{width:100%;display:grid;grid-template-columns:8px 1fr auto;align-items:center;gap:10px;padding:11px 10px;border:1px solid transparent;border-radius:4px;background:transparent;text-align:left;cursor:pointer}.group-btn::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--rule)}.group-btn:hover{background:#fff}.group-btn[aria-pressed="true"]{border-color:#a9bdb4;background:var(--pine-soft)}.group-btn[aria-pressed="true"]::before{background:var(--pine);box-shadow:0 0 0 4px rgba(31,90,70,.12)}.group-btn small{color:var(--muted);font-size:10px}.rail-note{position:absolute;bottom:22px;left:20px;right:20px;padding-top:16px;border-top:1px solid var(--rule);color:var(--muted);font-size:11px;line-height:1.55}
.main{width:min(1280px,100%);margin:0 auto;padding:34px 42px 58px}.mast{display:flex;justify-content:space-between;gap:30px;align-items:flex-end;padding-bottom:22px;border-bottom:1px solid var(--ink)}.mast h2{margin:.35rem 0 0;font:600 clamp(30px,4vw,54px)/1 "STFangsong","FangSong",serif;letter-spacing:.02em}.mast-copy{max-width:420px;color:var(--muted);font-size:13px;line-height:1.7}.stats{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--rule)}.stat{padding:18px 18px 17px;border-right:1px solid var(--rule)}.stat:first-child{padding-left:0}.stat:last-child{border-right:0}.stat strong{display:block;font:600 25px/1 ui-monospace,SFMono-Regular,Consolas,monospace}.stat span{display:block;margin-top:7px;color:var(--muted);font-size:11px}
.section{padding:30px 0;border-bottom:1px solid var(--rule)}.section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:18px}.section-head h3{margin:0;font:600 23px/1.15 "STFangsong","FangSong",serif}.section-head p{margin:0;max-width:620px;color:var(--muted);font-size:12px;line-height:1.6}.trajectory{display:grid;grid-template-columns:1fr 1.15fr 1fr;min-height:230px;border:1px solid var(--rule);background:var(--paper);box-shadow:var(--shadow)}.track{padding:22px 24px}.track+ .track{border-left:1px solid var(--rule)}.track-label{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;font-size:12px;font-weight:700}.track-label em{font-style:normal;font:600 10px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}.track.removal{border-top:4px solid var(--cinnabar)}.track.core{border-top:4px solid var(--blue)}.track.addition{border-top:4px solid var(--pine)}.mini-list{display:grid;gap:9px}.mini-item{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:8px 0;border-bottom:1px dotted var(--rule)}.mini-item:last-child{border-bottom:0}.mini-item b{font-size:14px}.mini-item span{font:600 11px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}.empty{padding:24px 0;color:var(--muted);font-size:12px;line-height:1.65}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center}.search{min-width:230px;padding:9px 12px;border:1px solid var(--rule);border-radius:3px;background:#fff;color:var(--ink)}.search:focus,.filter-btn:focus-visible,.group-btn:focus-visible,select:focus{outline:3px solid rgba(45,95,136,.28);outline-offset:2px}.filter-btn,select{padding:9px 12px;border:1px solid var(--rule);border-radius:3px;background:var(--paper);cursor:pointer}.filter-btn[aria-pressed="true"]{border-color:var(--blue);background:var(--blue-soft);color:#173e5a}
.content-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);gap:26px}.ledger{background:var(--paper);border:1px solid var(--rule)}.ledger-title{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid var(--rule);font-size:12px;font-weight:700}.rank-row{display:grid;grid-template-columns:30px minmax(120px,.7fr) minmax(180px,1fr);gap:12px;align-items:center;padding:13px 16px;border-bottom:1px solid #e2e7e4}.rank-row:last-child{border-bottom:0}.rank{font:600 11px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}.drug b{display:block;font-size:14px}.drug small{color:var(--muted);font-size:10px}.meter{position:relative;height:22px;background:#e8edeb;overflow:hidden}.meter i{position:absolute;inset:0 auto 0 0;background:var(--blue-soft);border-right:2px solid var(--blue)}.meter span{position:relative;z-index:1;display:block;padding:4px 8px;text-align:right;font:600 10px ui-monospace,SFMono-Regular,Consolas,monospace}.combos{display:grid;gap:10px}.combo{padding:15px 16px;border:1px solid var(--rule);background:var(--paper)}.combo-top{display:flex;justify-content:space-between;gap:12px;align-items:center}.combo-name{font-weight:700;line-height:1.5}.combo-size{flex:0 0 auto;padding:3px 7px;background:var(--blue-soft);color:#194560;font:700 9px ui-monospace,SFMono-Regular,Consolas,monospace}.combo-meta{display:flex;gap:18px;margin-top:10px;color:var(--muted);font-size:10px}.combo-meta b{color:var(--ink)}
.change-columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.change-panel{border:1px solid var(--rule);background:var(--paper)}.change-panel.add{border-top:4px solid var(--pine)}.change-panel.remove{border-top:4px solid var(--cinnabar)}.change-row{padding:13px 15px;border-bottom:1px solid #e2e7e4}.change-row:last-child{border-bottom:0}.change-main{display:flex;justify-content:space-between;gap:12px}.change-main b{font-size:14px}.change-main span{font:600 11px ui-monospace,SFMono-Regular,Consolas,monospace}.change-sub{margin-top:5px;color:var(--muted);font-size:10px}.evidence{margin-top:24px;border:1px solid var(--rule);background:rgba(251,252,249,.7)}.evidence summary{cursor:pointer;padding:15px 17px;font-weight:700;font-size:12px}.evidence-body{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;padding:0 17px 18px;color:var(--muted);font-size:11px;line-height:1.65}.evidence-body b{display:block;margin-bottom:4px;color:var(--ink)}
.footer{display:flex;justify-content:space-between;gap:20px;padding-top:24px;color:var(--muted);font-size:10px}.footer code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
@media(max-width:900px){.shell{width:100%;max-width:100%;grid-template-columns:minmax(0,1fr)}.rail,.main{width:100%;min-width:0}.rail{position:static;height:auto;padding:18px 20px;border-right:0;border-bottom:1px solid var(--rule)}.brand{margin-bottom:16px}.brand h1{font-size:24px}.group-nav{display:flex;max-width:100%;overflow-x:auto;overflow-y:hidden;padding-bottom:7px;scroll-snap-type:x proximity;scrollbar-width:thin;scrollbar-color:var(--pine) var(--pine-soft)}.group-btn{min-width:170px;scroll-snap-align:start}.rail-note{position:static;margin-top:14px}.main{padding:26px 20px 44px}.mast{align-items:flex-start;flex-direction:column}.mast>*,.mast-copy{min-width:0;max-width:100%}.stats{grid-template-columns:1fr 1fr}.stat:nth-child(2){border-right:0}.trajectory,.content-grid{grid-template-columns:minmax(0,1fr)}.track+.track{border-left:0;border-top:1px solid var(--rule)}.track.removal,.track.core,.track.addition{border-top-width:4px}.change-columns,.evidence-body{grid-template-columns:minmax(0,1fr)}.section-head{align-items:flex-start;flex-direction:column}}
@media(max-width:520px){.safety{align-items:flex-start;justify-content:flex-start;gap:.4rem;padding:.45rem .85rem;line-height:1.45}.safety b{flex:0 0 auto}.main{padding-left:14px;padding-right:14px}.stats{grid-template-columns:1fr}.stat{padding-left:0;border-right:0}.rank-row{grid-template-columns:24px minmax(0,1fr)}.meter{grid-column:2}.controls{align-items:stretch}.search{min-width:100%;width:100%}.trajectory{box-shadow:none}.change-columns{grid-template-columns:minmax(0,1fr)}}
@media(prefers-reduced-motion:no-preference){.main{animation:enter .32s ease-out both}@keyframes enter{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}}
</style>
</head>
<body>
<div class="safety"><b>历史处方复盘</b><span>仅显示达到公开阈值的群体趋势，不生成患者级处方、剂量或疗效判断</span></div>
<div class="shell">
  <aside class="rail">
    <div class="brand"><div class="eyebrow">MingYiRx / local</div><h1>门诊处方复盘</h1><p>从真实门诊记录中回看常用骨架与复诊调整，不替代辨证、查体和临床判断。</p></div>
    <nav class="group-nav" id="group-nav" aria-label="选择记录标签病种"></nav>
    <div class="rail-note">本页面不含患者明细。所有药味、组合和变化方向均来自已通过隐私阈值的汇总表。</div>
  </aside>
  <main class="main">
    <header class="mast"><div><div class="eyebrow">Recorded-label cohort review</div><h2 id="group-title"></h2></div><div class="mast-copy">先看首诊处方骨架，再看复诊中的加减方向。排名表示本数据集中的记录频率，不表示疗效、必要性或个体患者适用性。</div></header>
    <section class="stats" id="stats"></section>
    <section class="section"><div class="section-head"><h3>处方演变轨迹</h3><p>中间是首诊常用药，左右是达到公开患者数门槛的复诊减药与加药方向。</p></div><div class="trajectory"><div class="track removal"><div class="track-label">复诊减药倾向 <em>REMOVAL</em></div><div class="mini-list" id="trajectory-removal"></div></div><div class="track core"><div class="track-label">首诊处方骨架 <em>CORE</em></div><div class="mini-list" id="trajectory-core"></div></div><div class="track addition"><div class="track-label">复诊加药倾向 <em>ADDITION</em></div><div class="mini-list" id="trajectory-addition"></div></div></div></section>
    <section class="section"><div class="section-head"><div><h3>常用处方结构</h3><p>药味按首诊患者覆盖率排序；组合仅展示达到预设支持度和公开阈值的结果。</p></div><div class="controls"><label><span class="eyebrow">搜索药味</span><input class="search" id="search" type="search" placeholder="输入药名或组合" autocomplete="off"></label><button class="filter-btn" data-size="all" aria-pressed="true">全部组合</button><button class="filter-btn" data-size="2" aria-pressed="false">药对</button><button class="filter-btn" data-size="3" aria-pressed="false">三药</button><select id="limit" aria-label="显示数量"><option value="8">前8项</option><option value="12" selected>前12项</option><option value="20">前20项</option></select></div></div><div class="content-grid"><div class="ledger"><div class="ledger-title"><span>首诊常用药</span><span>患者覆盖率</span></div><div id="item-list"></div></div><div><div class="ledger-title"><span>稳定处方组合</span><span>首诊支持度</span></div><div class="combos" id="combo-list"></div></div></div></section>
    <section class="section"><div class="section-head"><h3>复诊加减倾向</h3><p>先在每名患者内计算该药发生加/减的复诊比例，再对患者等权汇总。未显示的方向不能当作零。</p></div><div class="change-columns"><div class="change-panel add"><div class="ledger-title"><span>常见加药</span><span>发生患者占比</span></div><div id="addition-list"></div></div><div class="change-panel remove"><div class="ledger-title"><span>常见减药</span><span>发生患者占比</span></div><div id="removal-list"></div></div></div><details class="evidence"><summary>查看计算依据与使用边界</summary><div class="evidence-body"><div><b>常用药与组合</b>使用每名患者首个合格处方，避免复诊次数较多者重复贡献。组合的稳定性只表示同一队列重抽样后仍可能被选中。</div><div><b>加药与减药</b>每个方向至少由公开阈值规定数量的复诊患者发生。患者占比和患者等权复诊频率分别回答“多少患者发生”和“平均多常发生”。</div><div><b>不能回答</b>页面未纳入当前患者的症状、证候、检验、合并症、过敏、其他用药和疗效，因此不能用于自动开方、剂量选择或禁忌判断。</div></div></details></section>
    <footer class="footer"><span>本地自包含页面 · 不连接外部服务</span><code id="version"></code></footer>
  </main>
</div>
<script id="dashboard-data" type="application/json">__PAYLOAD__</script>
<script>
const data=JSON.parse(document.getElementById('dashboard-data').textContent);
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const number=value=>{const parsed=Number(value);return Number.isFinite(parsed)?parsed:0};
const percent=value=>`${(number(value)*100).toFixed(1)}%`;
let selected=data.groups[0].code,query='',comboSize='all',limit=12;
const forGroup=(rows,group=selected)=>rows.filter(row=>row.group===group);
const sorted=(rows,key)=>[...rows].sort((a,b)=>number(b[key])-number(a[key]));
const empty=message=>`<div class="empty">${escapeHtml(message)}</div>`;

function renderNav(){document.getElementById('group-nav').innerHTML=data.groups.map(group=>`<button class="group-btn" data-group="${escapeHtml(group.code)}" aria-pressed="${group.code===selected}"><span>${escapeHtml(group.label)}</span><small>${escapeHtml(group.patients)}人</small></button>`).join('');document.querySelectorAll('.group-btn').forEach(button=>button.addEventListener('click',()=>{selected=button.dataset.group;render();[...document.querySelectorAll('.group-btn')].find(item=>item.dataset.group===selected)?.focus()}))}
function renderStats(){const group=data.groups.find(row=>row.code===selected);const longitudinal=forGroup(data.longitudinal)[0]||{};document.getElementById('group-title').textContent=group.label;const stats=[['首诊患者',group.first_prescription_patients],['复诊患者',group.repeat_patients],['相邻复诊',group.transitions],['患者内连续性',longitudinal.median_patient_jaccard?percent(longitudinal.median_patient_jaccard):'—']];document.getElementById('stats').innerHTML=stats.map(([label,value])=>`<div class="stat"><strong>${escapeHtml(value||'0')}</strong><span>${escapeHtml(label)}</span></div>`).join('')}
function visibleItems(){return sorted(forGroup(data.items).filter(row=>!query||row.item_name.toLowerCase().includes(query)), 'prevalence').slice(0,limit)}
function visibleChanges(type){return sorted(forGroup(data.changes).filter(row=>row.change_type===type&&(!query||row.item_name.toLowerCase().includes(query))),'patient_prevalence').slice(0,limit)}
function mini(rows,type){if(!rows.length)return empty('未达到公开阈值，不能解释为没有发生。');return rows.slice(0,5).map(row=>`<div class="mini-item"><b>${escapeHtml(row.item_name)}</b><span>${type==='core'?percent(row.prevalence):percent(row.patient_prevalence)}</span></div>`).join('')}
function renderTrajectory(){document.getElementById('trajectory-core').innerHTML=mini(sorted(forGroup(data.items),'prevalence'),'core');document.getElementById('trajectory-addition').innerHTML=mini(sorted(forGroup(data.changes).filter(row=>row.change_type==='addition'),'patient_prevalence'),'change');document.getElementById('trajectory-removal').innerHTML=mini(sorted(forGroup(data.changes).filter(row=>row.change_type==='removal'),'patient_prevalence'),'change')}
function renderItems(){const rows=visibleItems();document.getElementById('item-list').innerHTML=rows.length?rows.map((row,index)=>`<div class="rank-row"><span class="rank">${String(index+1).padStart(2,'0')}</span><span class="drug"><b>${escapeHtml(row.item_name)}</b><small>${escapeHtml(row.exposed_patients)} / ${escapeHtml(row.group_patients)}名首诊患者</small></span><span class="meter"><i style="width:${Math.min(100,number(row.prevalence)*100)}%"></i><span>${percent(row.prevalence)}</span></span></div>`).join(''):empty('没有符合当前搜索条件的公开药味。')}
function renderCombos(){const rows=sorted(forGroup(data.combinations).filter(row=>(comboSize==='all'||row.combination_size===comboSize)&&(!query||row.combination.toLowerCase().includes(query))&&row.stable_core_combination==='True'),'support').slice(0,limit);document.getElementById('combo-list').innerHTML=rows.length?rows.map(row=>`<article class="combo"><div class="combo-top"><div class="combo-name">${escapeHtml(row.combination.split(' | ').join(' ＋ '))}</div><span class="combo-size">${row.combination_size==='2'?'PAIR':'TRIPLET'}</span></div><div class="combo-meta"><span><b>${percent(row.support)}</b> 首诊支持度</span><span><b>${escapeHtml(row.support_patients)}</b> 名患者</span><span><b>${percent(row.bootstrap_core_selection_probability)}</b> 重选概率</span></div></article>`).join(''):empty('没有符合当前条件的稳定公开组合。')}
function renderChangeList(type,target){const rows=visibleChanges(type);document.getElementById(target).innerHTML=rows.length?rows.map(row=>`<div class="change-row"><div class="change-main"><b>${escapeHtml(row.item_name)}</b><span>${percent(row.patient_prevalence)}</span></div><div class="change-sub">${escapeHtml(row.patients_with_change)} / ${escapeHtml(row.repeat_patients)}名复诊患者；患者等权复诊频率 ${percent(row.mean_patient_transition_fraction)}</div></div>`).join(''):empty('没有达到公开患者数门槛的方向。缺失不能解释为零。')}
function render(){renderNav();renderStats();renderTrajectory();renderItems();renderCombos();renderChangeList('addition','addition-list');renderChangeList('removal','removal-list');document.getElementById('version').textContent=`MingYiRx ${data.version}`}
document.getElementById('search').addEventListener('input',event=>{query=event.target.value.trim().toLowerCase();renderItems();renderCombos();renderChangeList('addition','addition-list');renderChangeList('removal','removal-list')});document.querySelectorAll('.filter-btn').forEach(button=>button.addEventListener('click',()=>{comboSize=button.dataset.size;document.querySelectorAll('.filter-btn').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));renderCombos()}));document.getElementById('limit').addEventListener('change',event=>{limit=Number(event.target.value);render()});render();
</script>
</body>
</html>
"""
