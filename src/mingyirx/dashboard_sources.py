"""Switch complete reviewed dashboards without merging their denominators."""
import json
from pathlib import Path
import re
from .dashboard import DashboardError

def build_source_dashboard(primary: Path, supplement: Path, output: Path) -> dict:
    pages = [p.read_text(encoding='utf-8') for p in [primary, supplement]]
    pattern = r'<script id="dashboard-data" type="application/json">(.*?)</script>'
    payloads = []
    for page in pages:
        match = re.search(pattern, page, re.S)
        if not match:
            raise DashboardError('Input must be a reviewed MingYiRx dashboard')
        payload = json.loads(match[1])
        if not payload.get('groups'):
            raise DashboardError('Source has no disclosed groups')
        payloads.append(payload)
    page = pages[0]
    anchor = "const data=JSON.parse(document.getElementById('dashboard-data').textContent);"
    if anchor not in page or 'id="analysis-source"' in page:
        raise DashboardError('Unsupported or already combined dashboard template')
    extra = json.dumps(payloads[1],ensure_ascii=False).replace('<','\\u003c')
    page = page.replace('<script id="dashboard-data"', '<script id="supplement-data" type="application/json">'+extra+'</script><script id="dashboard-data"',1)
    page = page.replace(anchor,"const sourceData={primary:JSON.parse(document.getElementById('dashboard-data').textContent),supplement:JSON.parse(document.getElementById('supplement-data').textContent)};let data=sourceData.primary;")
    page = page.replace('const research = data.research || {};','let research = data.research || {};').replace('const provenance = data.provenance || {};','let provenance = data.provenance || {};')
    control = '<section style="padding:20px;background:#edf3eb;margin-bottom:24px"><label for="analysis-source">数据来源</label> <select id="analysis-source"><option value="primary">主要导出</option><option value="supplement">补充导出</option></select><p>年度、人数、药味、加减及网络随来源一起切换。两来源不相加，切换不代表已完成患者去重。</p></section>'
    page = page.replace('<main class="main">','<main class="main">'+control,1)
    script = '''
document.getElementById('analysis-source').addEventListener('change',event=>{
  data=sourceData[event.target.value];research=data.research||{};provenance=data.provenance||{};
  selected=data.groups.some(r=>r.code===selected)?selected:data.groups[0].code;
  stratumType='overall';stratum='all';comparisonKey='';annualItem='';annualMetric='prevalence';researchItem='';strictGroup=selected;networkItem='';query='';
  document.getElementById('search').value='';
  document.getElementById('reference-diagnosis').innerHTML=data.groups.map(g=>`<option value="${escapeHtml(g.code)}">${escapeHtml(groupLabel(g.label))}</option>`).join('');
  document.getElementById('reference-age').value='';populateReferenceSex();renderReferenceResult();render();renderStrictResearch();renderResearchQuality();
});
'''
    initialization = 'initializeResearch();initializeReference();render();'
    if initialization not in page:
        raise DashboardError('Source-switch initialization is unavailable')
    page = page.replace(initialization,initialization+script,1)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(page,encoding='utf-8')
    return {'gate':'PASS','sources':2,'patient_identity_merge':False,'patient_level_data_added':False}
