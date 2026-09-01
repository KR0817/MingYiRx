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
        {"group", "item_name", "exposed_patients", "group_patients", "prevalence", "dose_patients", "median_dose_g", "dose_q1_g", "dose_q3_g"},
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
            "dose_patients",
            "median_dose_g",
            "dose_q1_g",
            "dose_q3_g",
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

CLINICAL_TABLES = {
    "summaries": (
        "clinical_phenotype_summary.csv",
        {
            "group",
            "group_label",
            "disease_count",
            "stratum_type",
            "stratum",
            "stratum_label",
            "patients",
            "repeat_patients",
            "visits",
            "transitions",
            "median_age",
            "age_q1",
            "age_q3",
            "age_min",
            "age_max",
        },
    ),
    "items": (
        "clinical_first_prescription_item_prevalence.csv",
        {"group", "stratum_type", "stratum", "item_name", "exposed_patients", "group_patients", "prevalence", "dose_patients", "median_dose_g", "dose_q1_g", "dose_q3_g"},
    ),
    "combinations": (
        "clinical_frequent_item_combinations.csv",
        {"group", "stratum_type", "stratum", "combination_size", "combination", "support_patients", "support", "bootstrap_core_selection_probability", "stable_core_combination"},
    ),
    "changes": (
        "clinical_item_change_tendency.csv",
        {"group", "stratum_type", "stratum", "item_name", "change_type", "repeat_patients", "patients_with_change", "patient_prevalence", "mean_patient_transition_fraction", "dose_patients", "median_dose_g", "dose_q1_g", "dose_q3_g"},
    ),
    "longitudinal": (
        "clinical_longitudinal_summary.csv",
        {"group", "stratum_type", "stratum", "repeat_patients", "transitions", "median_patient_jaccard"},
    ),
    "comparisons": (
        "clinical_item_change_comparison.csv",
        {"combination_group", "combination_label", "single_group", "single_label", "stratum_type", "stratum", "change_type", "item_name", "combination_prevalence", "single_prevalence", "prevalence_difference", "combination_mean_transition_fraction", "single_mean_transition_fraction", "mean_transition_fraction_difference", "combination_dose_patients", "combination_median_dose_g", "combination_dose_q1_g", "combination_dose_q3_g", "single_dose_patients", "single_median_dose_g", "single_dose_q1_g", "single_dose_q3_g", "higher_frequency"},
    ),
    "year_summaries": (
        "clinical_year_summary.csv",
        {"group", "stratum_type", "stratum", "year", "patients", "repeat_patients", "visits", "transitions"},
    ),
    "year_items": (
        "clinical_year_item_prevalence.csv",
        {"group", "stratum_type", "stratum", "year", "item_name", "exposed_patients", "group_patients", "prevalence", "dose_patients", "median_dose_g", "dose_q1_g", "dose_q3_g"},
    ),
    "year_changes": (
        "clinical_year_item_change_tendency.csv",
        {"group", "stratum_type", "stratum", "year", "item_name", "change_type", "repeat_patients", "patients_with_change", "patient_prevalence", "mean_patient_transition_fraction", "dose_patients", "median_dose_g", "dose_q1_g", "dose_q3_g"},
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
    clinical_paths = [input_dir / filename for filename, _ in CLINICAL_TABLES.values()]
    if any(path.is_file() for path in clinical_paths) and not all(
        path.is_file() for path in clinical_paths
    ):
        raise DashboardError("Clinical dashboard tables are incomplete")
    clinical_mode = all(path.is_file() for path in clinical_paths)
    source_tables = [filename for filename, _ in TABLES.values()]
    if clinical_mode:
        clinical_loaded = {
            key: _read_rows(input_dir / filename, required)
            for key, (filename, required) in CLINICAL_TABLES.items()
        }
        groups = [
            {"code": row["group"], "label": row["group_label"], **row}
            for row in clinical_loaded["summaries"]
            if row["stratum_type"] == "overall"
        ]
        source_tables.extend(filename for filename, _ in CLINICAL_TABLES.values())
    else:
        labels = _group_labels(input_dir)
        groups = [
            {
                "code": row["group"],
                "label": labels.get(row["group"], _fallback_label(row["group"])),
                **row,
            }
            for row in loaded["cohorts"]
        ]
        clinical_loaded = {
            "summaries": groups,
            "items": loaded["items"],
            "combinations": loaded["combinations"],
            "changes": loaded["changes"],
            "longitudinal": loaded["longitudinal"],
            "comparisons": [],
            "year_summaries": [],
            "year_items": [],
            "year_changes": [],
        }
    if not groups:
        raise DashboardError("cohort_summary.csv has no reportable groups")

    payload = {
        "version": __version__,
        "clinicalMode": clinical_mode,
        "groups": groups,
        "summaries": clinical_loaded["summaries"],
        "items": clinical_loaded["items"],
        "combinations": clinical_loaded["combinations"],
        "changes": clinical_loaded["changes"],
        "longitudinal": clinical_loaded["longitudinal"],
        "comparisons": clinical_loaded["comparisons"],
        "yearSummaries": clinical_loaded["year_summaries"],
        "yearItems": clinical_loaded["year_items"],
        "yearChanges": clinical_loaded["year_changes"],
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
        "source_tables": source_tables,
        "clinical_mode": clinical_mode,
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
.group-nav{display:grid;gap:7px}.group-btn{width:100%;display:grid;grid-template-columns:8px 1fr auto;align-items:center;gap:10px;padding:11px 10px;border:1px solid transparent;border-radius:4px;background:transparent;text-align:left;cursor:pointer}.group-btn::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--rule)}.group-btn:hover{background:#fff}.group-btn[aria-pressed="true"]{border-color:#a9bdb4;background:var(--pine-soft)}.group-btn[aria-pressed="true"]::before{background:var(--pine);box-shadow:0 0 0 4px rgba(31,90,70,.12)}.group-btn small{color:var(--muted);font-size:10px}.group-name{display:grid;gap:3px}.group-kind{width:max-content;padding:2px 5px;background:var(--red-soft);color:#76372e;font:700 8px ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.08em}.rail-note{position:absolute;bottom:22px;left:20px;right:20px;padding-top:16px;border-top:1px solid var(--rule);color:var(--muted);font-size:11px;line-height:1.55}
.main{width:min(1280px,100%);margin:0 auto;padding:34px 42px 58px}.mast{display:flex;justify-content:space-between;gap:30px;align-items:flex-end;padding-bottom:22px;border-bottom:1px solid var(--ink)}.mast h2{margin:.35rem 0 0;font:600 clamp(30px,4vw,54px)/1 "STFangsong","FangSong",serif;letter-spacing:.02em}.mast-copy{max-width:420px;color:var(--muted);font-size:13px;line-height:1.7}.strata{display:flex;align-items:center;gap:8px;overflow-x:auto;padding:13px 0;border-bottom:1px solid var(--rule)}.strata-label{flex:0 0 auto;margin-right:4px;color:var(--muted);font-size:10px;font-weight:700}.stratum-btn{flex:0 0 auto;padding:6px 10px;border:1px solid transparent;border-radius:999px;background:transparent;color:var(--muted);font-size:11px;cursor:pointer}.stratum-btn[aria-pressed="true"]{border-color:#a9bdb4;background:var(--pine-soft);color:var(--ink)}.stats{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--rule)}.stat{padding:18px 18px 17px;border-right:1px solid var(--rule)}.stat:first-child{padding-left:0}.stat:last-child{border-right:0}.stat strong{display:block;font:600 25px/1 ui-monospace,SFMono-Regular,Consolas,monospace}.stat span{display:block;margin-top:7px;color:var(--muted);font-size:11px}.demographics{display:grid;grid-template-columns:1.1fr 1fr 1fr;gap:1px;margin-top:18px;border:1px solid var(--rule);background:var(--rule)}.demo-block{min-width:0;padding:15px 17px;background:rgba(251,252,249,.92)}.demo-block h4{margin:0 0 10px;font-size:11px}.age-median{font:600 23px ui-monospace,SFMono-Regular,Consolas,monospace}.age-median small{font:400 10px "Microsoft YaHei",sans-serif;color:var(--muted)}.demo-list{display:grid;gap:7px}.demo-row{display:grid;grid-template-columns:62px 1fr 38px;gap:8px;align-items:center;font-size:10px}.demo-meter{height:6px;background:#e5ebe8}.demo-meter i{display:block;height:100%;background:var(--pine)}.demo-row:nth-child(2n) .demo-meter i{background:var(--blue)}
.reference-shell{border:1px solid var(--rule);background:var(--paper);box-shadow:var(--shadow)}.reference-form{display:grid;grid-template-columns:minmax(190px,1.2fr) minmax(130px,.8fr) minmax(110px,.6fr) auto;gap:10px;align-items:end;padding:16px}.reference-form label{display:grid;gap:6px;color:var(--muted);font-size:10px}.reference-form select,.reference-form input{width:100%;min-width:0;padding:9px 11px;border:1px solid var(--rule);border-radius:3px;background:#fff;color:var(--ink)}.reference-action{padding:10px 14px;border:1px solid var(--pine);border-radius:3px;background:var(--pine);color:#fff;cursor:pointer}.reference-result{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;border-top:1px solid var(--rule);background:var(--rule)}.reference-card{min-width:0;padding:15px 16px;background:var(--paper)}.reference-card h4{margin:0 0 7px;font-size:11px}.reference-card p{margin:0;color:var(--muted);font-size:10px;line-height:1.6}.reference-items{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px;font-size:12px;font-weight:700;line-height:1.5}.reference-note{padding:0 16px 14px;color:var(--muted);font-size:10px;line-height:1.6}.dose-chip{display:inline-flex;gap:4px;align-items:center;padding:3px 6px;border:1px solid var(--rule);background:#fff}.dose-chip small{color:var(--muted);font:600 9px ui-monospace,SFMono-Regular,Consolas,monospace}
.section{padding:30px 0;border-bottom:1px solid var(--rule)}.section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:18px}.section-head h3{margin:0;font:600 23px/1.15 "STFangsong","FangSong",serif}.section-head p{margin:0;max-width:620px;color:var(--muted);font-size:12px;line-height:1.6}.trajectory-map{display:grid;grid-template-columns:1fr 1.15fr 1fr;gap:12px;margin-bottom:10px;font:700 10px ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.08em;text-align:center}.trajectory-map span{padding:7px 10px;border-bottom:2px solid}.trajectory-map .removal{color:var(--cinnabar)}.trajectory-map .core{color:var(--blue)}.trajectory-map .addition{color:var(--pine)}.trajectory{display:grid;grid-template-columns:1fr 1.15fr 1fr;grid-template-areas:"removal core addition";gap:12px;min-height:250px}.track{min-width:0;padding:18px 20px 20px;border:1px solid var(--rule);background:var(--paper)}.track-label{display:grid;grid-template-columns:34px minmax(0,1fr) auto;gap:10px;align-items:center;margin-bottom:16px}.track-sign{display:grid;width:32px;height:32px;place-items:center;border-radius:50%;font:700 20px/1 ui-monospace,SFMono-Regular,Consolas,monospace}.track-title{display:grid;gap:3px}.track-title strong{font-size:13px}.track-title small{color:var(--muted);font-size:9px;font-weight:400}.track-label em{font-style:normal;font:600 9px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted);text-align:right}.track.removal{grid-area:removal;border-top:6px solid var(--cinnabar);background:linear-gradient(180deg,rgba(166,75,60,.11),rgba(251,252,249,.96) 42%)}.track.removal .track-sign{background:var(--red-soft);color:var(--cinnabar)}.track.core{grid-area:core;transform:translateY(-7px);border-top:6px solid var(--blue);background:linear-gradient(180deg,rgba(45,95,136,.12),rgba(251,252,249,.98) 46%);box-shadow:0 16px 32px rgba(45,95,136,.12)}.track.core .track-sign{background:var(--blue-soft);color:var(--blue);font-size:13px}.track.addition{grid-area:addition;border-top:6px solid var(--pine);background:linear-gradient(180deg,rgba(31,90,70,.12),rgba(251,252,249,.96) 42%)}.track.addition .track-sign{background:var(--pine-soft);color:var(--pine)}.mini-list{display:grid;gap:6px}.mini-item{display:grid;grid-template-columns:24px minmax(0,1fr) auto;gap:9px;align-items:center;padding:8px 0;border-bottom:1px dotted var(--rule)}.mini-item:last-child{border-bottom:0}.mini-symbol{display:grid;width:22px;height:22px;place-items:center;border-radius:50%;font:700 13px/1 ui-monospace,SFMono-Regular,Consolas,monospace}.mini-item.removal .mini-symbol{background:var(--red-soft);color:var(--cinnabar)}.mini-item.core .mini-symbol{background:var(--blue-soft);color:var(--blue);font-size:8px}.mini-item.addition .mini-symbol{background:var(--pine-soft);color:var(--pine)}.mini-drug{display:grid;gap:2px;min-width:0}.mini-item b{font-size:14px}.mini-drug small{overflow:hidden;color:var(--muted);font:600 9px ui-monospace,SFMono-Regular,Consolas,monospace;text-overflow:ellipsis;white-space:nowrap}.mini-item .mini-value{font:700 11px ui-monospace,SFMono-Regular,Consolas,monospace}.mini-item.removal .mini-value{color:var(--cinnabar)}.mini-item.core .mini-value{color:var(--blue)}.mini-item.addition .mini-value{color:var(--pine)}.empty{padding:24px 0;color:var(--muted);font-size:12px;line-height:1.65}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center}.search{min-width:230px;padding:9px 12px;border:1px solid var(--rule);border-radius:3px;background:#fff;color:var(--ink)}.search:focus,.filter-btn:focus-visible,.annual-btn:focus-visible,.group-btn:focus-visible,select:focus{outline:3px solid rgba(45,95,136,.28);outline-offset:2px}.filter-btn,.annual-btn,select{padding:9px 12px;border:1px solid var(--rule);border-radius:3px;background:var(--paper);cursor:pointer}.filter-btn[aria-pressed="true"],.annual-btn[aria-pressed="true"]{border-color:var(--blue);background:var(--blue-soft);color:#173e5a}
.annual-controls{display:flex;flex-wrap:wrap;align-items:center;gap:8px;min-width:0}.annual-controls select{min-width:150px;max-width:220px}.annual-frame{position:relative;border:1px solid var(--rule);background:var(--paper);box-shadow:var(--shadow)}.annual-scale{display:flex;justify-content:space-between;padding:10px 14px 0;color:var(--muted);font:600 9px ui-monospace,SFMono-Regular,Consolas,monospace}.annual-chart{display:flex;align-items:flex-end;gap:9px;min-height:226px;padding:18px 16px 14px;overflow-x:auto}.annual-column{flex:1 0 62px;display:grid;grid-template-rows:20px 132px 18px 16px 16px;gap:4px;min-width:62px;text-align:center}.annual-value{align-self:end;font:700 10px ui-monospace,SFMono-Regular,Consolas,monospace}.annual-bar-area{display:flex;align-items:flex-end;justify-content:center;border-bottom:1px solid var(--rule);background:linear-gradient(to top,transparent 49.5%,rgba(203,211,207,.55) 50%,transparent 50.5%)}.annual-bar{width:min(28px,62%);min-height:2px;background:var(--blue);border-radius:2px 2px 0 0}.annual-bar.addition{background:var(--pine)}.annual-bar.removal{background:var(--cinnabar)}.annual-bar.missing{height:1px!important;min-height:1px;background:repeating-linear-gradient(90deg,var(--rule) 0 4px,transparent 4px 7px)}.annual-year{font:700 10px ui-monospace,SFMono-Regular,Consolas,monospace}.annual-n,.annual-dose{color:var(--muted);font-size:8px;white-space:nowrap}.annual-dose{color:var(--pine);font-weight:700}.annual-caption{padding:0 16px 14px;color:var(--muted);font-size:10px;line-height:1.6}
.content-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);gap:26px}.ledger{background:var(--paper);border:1px solid var(--rule)}.ledger-title{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid var(--rule);font-size:12px;font-weight:700}.rank-row{display:grid;grid-template-columns:30px minmax(150px,.8fr) minmax(180px,1fr);gap:12px;align-items:center;padding:13px 16px;border-bottom:1px solid #e2e7e4}.rank-row:last-child{border-bottom:0}.rank{font:600 11px ui-monospace,SFMono-Regular,Consolas,monospace;color:var(--muted)}.drug b{display:block;font-size:14px}.drug small{display:block;color:var(--muted);font-size:10px;line-height:1.5}.drug .dose-line{color:var(--pine);font-weight:700}.meter{position:relative;height:22px;background:#e8edeb;overflow:hidden}.meter i{position:absolute;inset:0 auto 0 0;background:var(--blue-soft);border-right:2px solid var(--blue)}.meter span{position:relative;z-index:1;display:block;padding:4px 8px;text-align:right;font:600 10px ui-monospace,SFMono-Regular,Consolas,monospace}.combos{display:grid;gap:10px}.combo{padding:15px 16px;border:1px solid var(--rule);background:var(--paper)}.combo-top{display:flex;justify-content:space-between;gap:12px;align-items:center}.combo-name{font-weight:700;line-height:1.5}.combo-dose{display:flex;flex-wrap:wrap;gap:5px;margin-top:9px}.combo-size{flex:0 0 auto;padding:3px 7px;background:var(--blue-soft);color:#194560;font:700 9px ui-monospace,SFMono-Regular,Consolas,monospace}.combo-meta{display:flex;flex-wrap:wrap;gap:9px 18px;margin-top:10px;color:var(--muted);font-size:10px}.combo-meta b{color:var(--ink)}
.change-columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.change-panel{border:1px solid var(--rule);background:var(--paper)}.change-panel.add{border-top:4px solid var(--pine)}.change-panel.remove{border-top:4px solid var(--cinnabar)}.change-row{padding:13px 15px;border-bottom:1px solid #e2e7e4}.change-row:last-child{border-bottom:0}.change-main{display:flex;justify-content:space-between;gap:12px}.change-main b{font-size:14px}.change-main span{font:600 11px ui-monospace,SFMono-Regular,Consolas,monospace}.change-sub{margin-top:5px;color:var(--muted);font-size:10px;line-height:1.55}.change-dose{color:var(--pine);font-weight:700}.comparison-control{display:flex;min-width:0;max-width:100%;align-items:center;gap:9px}.comparison-control select{min-width:0;max-width:100%}.comparison-columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.comparison-panel{border:1px solid var(--rule);background:var(--paper)}.comparison-panel.combo{border-top:4px solid var(--pine)}.comparison-panel.single{border-top:4px solid var(--blue)}.comparison-row{padding:13px 15px;border-bottom:1px solid #e2e7e4}.comparison-row:last-child{border-bottom:0}.comparison-main{display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center}.direction{padding:2px 5px;background:#e8edeb;color:var(--muted);font:700 8px ui-monospace,SFMono-Regular,Consolas,monospace}.comparison-main b{font-size:14px}.delta{font:700 12px ui-monospace,SFMono-Regular,Consolas,monospace}.delta.positive{color:var(--pine)}.delta.negative{color:var(--blue)}.comparison-sub{margin-top:6px;color:var(--muted);font-size:10px;line-height:1.55}.comparison-dose{color:var(--pine);font-weight:700}.evidence{margin-top:24px;border:1px solid var(--rule);background:rgba(251,252,249,.7)}.evidence summary{cursor:pointer;padding:15px 17px;font-weight:700;font-size:12px}.evidence-body{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;padding:0 17px 18px;color:var(--muted);font-size:11px;line-height:1.65}.evidence-body b{display:block;margin-bottom:4px;color:var(--ink)}
.footer{display:flex;justify-content:space-between;gap:20px;padding-top:24px;color:var(--muted);font-size:10px}.footer code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
@media(max-width:900px){.shell{width:100%;max-width:100%;grid-template-columns:minmax(0,1fr)}.rail,.main{width:100%;min-width:0}.rail{position:static;height:auto;padding:18px 20px;border-right:0;border-bottom:1px solid var(--rule)}.brand{margin-bottom:16px}.brand h1{font-size:24px}.group-nav{display:flex;max-width:100%;overflow-x:auto;overflow-y:hidden;padding-bottom:7px;scroll-snap-type:x proximity;scrollbar-width:thin;scrollbar-color:var(--pine) var(--pine-soft)}.group-btn{min-width:190px;scroll-snap-align:start}.rail-note{position:static;margin-top:14px}.main{padding:26px 20px 44px}.mast{align-items:flex-start;flex-direction:column}.mast>*,.mast-copy,.section-head>*{min-width:0;max-width:100%}.stats{grid-template-columns:1fr 1fr}.stat:nth-child(2){border-right:0}.demographics,.reference-result{grid-template-columns:1fr}.reference-form{grid-template-columns:1fr 1fr}.trajectory{grid-template-columns:minmax(0,1fr);grid-template-areas:"core" "removal" "addition";gap:10px}.trajectory-map{display:none}.track.core{transform:none}.content-grid{grid-template-columns:minmax(0,1fr)}.change-columns,.comparison-columns,.evidence-body{grid-template-columns:minmax(0,1fr)}.section-head{align-items:flex-start;flex-direction:column}.comparison-control,.annual-controls{width:100%}.comparison-control select{width:100%}.annual-controls select{flex:1;max-width:none}}
@media(max-width:520px){.safety{align-items:flex-start;justify-content:flex-start;gap:.4rem;padding:.45rem .85rem;line-height:1.45}.safety b{flex:0 0 auto}.main{padding-left:14px;padding-right:14px}.stats{grid-template-columns:1fr}.stat{padding-left:0;border-right:0}.reference-form{grid-template-columns:1fr}.rank-row{grid-template-columns:24px minmax(0,1fr)}.meter{grid-column:2}.controls{align-items:stretch}.search{min-width:100%;width:100%}.trajectory,.annual-frame,.reference-shell{box-shadow:none}.change-columns{grid-template-columns:minmax(0,1fr)}}
@media(prefers-reduced-motion:no-preference){.main{animation:enter .32s ease-out both}@keyframes enter{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}}
</style>
</head>
<body>
<div class="safety"><b>历史处方复盘</b><span>仅显示达到公开阈值的群体趋势和历史记录克数，不生成患者级处方、推荐剂量或疗效判断</span></div>
<div class="shell">
  <aside class="rail">
    <div class="brand"><div class="eyebrow">MingYiRx / local</div><h1>门诊处方复盘</h1><p>从真实门诊记录中回看常用骨架与复诊调整，不替代辨证、查体和临床判断。</p></div>
    <nav class="group-nav" id="group-nav" aria-label="选择记录标签病种"></nav>
    <div class="rail-note">本页面不含患者明细。所有药味、组合和变化方向均来自已通过隐私阈值的汇总表。</div>
  </aside>
  <main class="main">
    <header class="mast"><div><div class="eyebrow">Recorded-label cohort review</div><h2 id="group-title"></h2></div><div class="mast-copy">先看首诊处方骨架，再看复诊中的加减方向。排名表示本数据集中的记录频率，不表示疗效、必要性或个体患者适用性。</div></header>
    <div class="strata" id="strata" aria-label="选择性别或年龄分层"></div>
    <section class="stats" id="stats"></section>
    <section class="section" id="reference-section" hidden><div class="section-head"><div><h3>同类历史处方参照</h3><p>输入只在当前浏览器页面内使用。结果检索公开队列汇总并显示历史记录克数，不生成患者处方、推荐剂量或疗效预测。</p></div></div><div class="reference-shell"><form class="reference-form" id="reference-form"><label>记录标签诊断<select id="reference-diagnosis" required></select></label><label>性别（可选）<select id="reference-sex"><option value="">不限定</option></select></label><label>年龄（可选）<input id="reference-age" type="number" min="0" max="130" inputmode="numeric" placeholder="如 52"></label><button class="reference-action" type="submit">查看历史参照</button></form><div class="reference-note">性别和年龄分别调用一维公开分层；两者不会被合成联合预测。克数为对应分层的历史中位数，未达到公开人数门槛时显示不可用。</div><div class="reference-result" id="reference-result" aria-live="polite"></div></div></section>
    <section class="demographics" id="demographics" aria-label="公开人口学构成"></section>
    <section class="section" id="annual-section" hidden><div class="section-head"><div><h3>年度处方演变</h3><p>年度常用药每名患者每年只取首张合格处方；加减按后一次就诊年份归属，并先算患者年内频率和药味克数。</p></div><div class="annual-controls"><button class="annual-btn" data-annual="prevalence" aria-pressed="true">年度常用</button><button class="annual-btn" data-annual="addition" aria-pressed="false">年度加药</button><button class="annual-btn" data-annual="removal" aria-pressed="false">年度减药</button><select id="annual-item" aria-label="选择年度趋势药味"></select></div></div><div class="annual-frame"><div class="annual-scale"><span id="annual-scale"></span><span>缺失＝未公开或未达到门槛</span></div><div class="annual-chart" id="annual-chart"></div><div class="annual-caption" id="annual-caption"></div></div></section>
    <section class="section"><div class="section-head"><h3>处方演变轨迹</h3><p>以首诊常用药为基线，向左看复诊中减少的药味，向右看复诊中新加入的药味；药名下方为达到门槛的历史中位克数。</p></div><div class="trajectory-map" aria-hidden="true"><span class="removal">减味 ←</span><span class="core">首诊处方骨架</span><span class="addition">→ 加味</span></div><div class="trajectory" aria-label="首诊处方骨架及复诊减味、加味趋势"><div class="track removal"><div class="track-label"><span class="track-sign" aria-hidden="true">−</span><span class="track-title"><strong>复诊减味</strong><small>从首诊或前次处方中减少</small></span><em>发生患者占比</em></div><div class="mini-list" id="trajectory-removal"></div></div><div class="track core"><div class="track-label"><span class="track-sign" aria-hidden="true">◆</span><span class="track-title"><strong>首诊处方骨架</strong><small>每名患者首张合格处方</small></span><em>首诊患者覆盖率</em></div><div class="mini-list" id="trajectory-core"></div></div><div class="track addition"><div class="track-label"><span class="track-sign" aria-hidden="true">＋</span><span class="track-title"><strong>复诊加味</strong><small>较前次处方新加入</small></span><em>发生患者占比</em></div><div class="mini-list" id="trajectory-addition"></div></div></div></section>
    <section class="section" id="comparison-section" hidden><div class="section-head"><div><h3>合并病与单病种加减差</h3><p>按患者等权复诊频率差排序，同时保留发生患者比例；仅比较两侧都达到公开门槛的药味。</p></div><div class="comparison-control"><label for="comparison-target" class="eyebrow">比较对象</label><select id="comparison-target"></select></div></div><div id="comparison-caption" class="mast-copy"></div><div class="comparison-columns"><div class="comparison-panel combo"><div class="ledger-title"><span>合并病更常加减</span><span>复诊频率差</span></div><div id="comparison-combo"></div></div><div class="comparison-panel single"><div class="ledger-title"><span>单病种更常加减</span><span>复诊频率差</span></div><div id="comparison-single"></div></div></div></section>
    <section class="section"><div class="section-head"><div><h3>常用处方结构</h3><p>药味按首诊患者覆盖率排序并显示历史中位克数；组合中的克数来自同一分层各单味药的首诊汇总，不是组合专属剂量。</p></div><div class="controls"><label><span class="eyebrow">搜索药味</span><input class="search" id="search" type="search" placeholder="输入药名或组合" autocomplete="off"></label><button class="filter-btn" data-size="all" aria-pressed="true">全部组合</button><button class="filter-btn" data-size="2" aria-pressed="false">药对</button><button class="filter-btn" data-size="3" aria-pressed="false">三药</button><select id="limit" aria-label="显示数量"><option value="8">前8项</option><option value="12" selected>前12项</option><option value="20">前20项</option></select></div></div><div class="content-grid"><div class="ledger"><div class="ledger-title"><span>首诊常用药与历史克数</span><span>患者覆盖率</span></div><div id="item-list"></div></div><div><div class="ledger-title"><span>稳定处方组合</span><span>首诊支持度</span></div><div class="combos" id="combo-list"></div></div></div></section>
    <section class="section"><div class="section-head"><h3>复诊加减倾向</h3><p>先在每名患者内计算该药发生加/减的复诊比例和事件克数，再对患者等权汇总。未显示的方向不能当作零。</p></div><div class="change-columns"><div class="change-panel add"><div class="ledger-title"><span>常见加药</span><span>发生患者占比</span></div><div id="addition-list"></div></div><div class="change-panel remove"><div class="ledger-title"><span>常见减药</span><span>发生患者占比</span></div><div id="removal-list"></div></div></div><details class="evidence"><summary>查看计算依据与使用边界</summary><div class="evidence-body"><div><b>人群定义</b>合并病来自完整诊断历史中的目标疾病组合；性别取一致的源记录，年龄按首个合格处方计算。未知或低于门槛的分层不显示。</div><div><b>加药与减药</b>每个方向至少由公开阈值规定数量的复诊患者发生。患者占比回答“多少患者发生”，患者等权复诊频率回答“平均多常发生”。</div><div><b>历史克数</b>只汇总原始记录中明确为 g 的克数，不换算其他单位。首诊每名患者贡献一次；加减先取患者内中位数。可解析患者不足门槛时显示不可用。</div><div><b>不能回答</b>合并病与单病种差值未校正病情、证候、随访机会及其他混杂，历史克数不能作为个体开方、推荐剂量、禁忌或疗效判断。</div></div></details></section>
    <footer class="footer"><span>本地自包含页面 · 不连接外部服务</span><code id="version"></code></footer>
  </main>
</div>
<script id="dashboard-data" type="application/json">__PAYLOAD__</script>
<script>
const data=JSON.parse(document.getElementById('dashboard-data').textContent);
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const number=value=>{const parsed=Number(value);return Number.isFinite(parsed)?parsed:0};
const percent=value=>`${(number(value)*100).toFixed(1)}%`;
const percentagePoints=value=>`${number(value)>=0?'+':''}${(number(value)*100).toFixed(1)} pp`;
const hasDose=row=>row&&row.dose_patients!==undefined&&row.dose_patients!==null&&row.dose_patients!==''&&row.median_dose_g!==undefined&&row.median_dose_g!==null&&row.median_dose_g!=='';
const doseNumber=value=>Number(value).toLocaleString('zh-CN',{maximumFractionDigits:2});
const doseShort=row=>hasDose(row)?`${doseNumber(row.median_dose_g)}克`:'克数未公开';
const doseDetail=row=>hasDose(row)?`历史中位 ${doseNumber(row.median_dose_g)}克（IQR ${doseNumber(row.dose_q1_g)}–${doseNumber(row.dose_q3_g)}；n=${row.dose_patients}）`:'历史克数未达到公开门槛';
const prefixedDose=(row,prefix)=>({dose_patients:row[`${prefix}_dose_patients`],median_dose_g:row[`${prefix}_median_dose_g`],dose_q1_g:row[`${prefix}_dose_q1_g`],dose_q3_g:row[`${prefix}_dose_q3_g`]});
const translations={'Rheumatoid arthritis':'类风湿关节炎','Sjögren disease':'干燥综合征','Ankylosing spondylitis':'强直性脊柱炎'};
const groupLabel=value=>String(value??'').split(' + ').map(part=>translations[part]||part).join(' ＋ ');
let selected=data.groups[0].code,query='',comboSize='all',limit=12,stratumType='overall',stratum='all',comparisonKey='',annualMetric='prevalence',annualItem='';
const inStratum=row=>!data.clinicalMode||(row.stratum_type===stratumType&&row.stratum===stratum);
const forContext=(rows,group=selected)=>rows.filter(row=>row.group===group&&inStratum(row));
const sorted=(rows,key)=>[...rows].sort((a,b)=>number(b[key])-number(a[key]));
const empty=message=>`<div class="empty">${escapeHtml(message)}</div>`;

function availableSummaries(){return data.summaries.filter(row=>row.group===selected)}
function ensureStratum(){if(!data.clinicalMode)return;const available=availableSummaries().some(row=>row.stratum_type===stratumType&&row.stratum===stratum);if(!available){stratumType='overall';stratum='all'}}
function renderNav(){document.getElementById('group-nav').innerHTML=data.groups.map(group=>`<button class="group-btn" data-group="${escapeHtml(group.code)}" aria-pressed="${group.code===selected}"><span class="group-name"><span>${escapeHtml(groupLabel(group.label))}</span>${number(group.disease_count)>1?'<em class="group-kind">合并病</em>':''}</span><small>${escapeHtml(group.patients)}人</small></button>`).join('');document.querySelectorAll('.group-btn').forEach(button=>button.addEventListener('click',()=>{selected=button.dataset.group;comparisonKey='';annualItem='';ensureStratum();render();[...document.querySelectorAll('.group-btn')].find(item=>item.dataset.group===selected)?.focus()}))}
function renderStrata(){const target=document.getElementById('strata');if(!data.clinicalMode){target.hidden=true;return}target.hidden=false;target.innerHTML='<span class="strata-label">查看分层</span>'+availableSummaries().map(row=>`<button class="stratum-btn" data-type="${escapeHtml(row.stratum_type)}" data-stratum="${escapeHtml(row.stratum)}" aria-pressed="${row.stratum_type===stratumType&&row.stratum===stratum}">${escapeHtml(row.stratum_type==='overall'?'全部患者':row.stratum_label)} · ${escapeHtml(row.patients)}人</button>`).join('');document.querySelectorAll('.stratum-btn').forEach(button=>button.addEventListener('click',()=>{stratumType=button.dataset.type;stratum=button.dataset.stratum;comparisonKey='';annualItem='';render();[...document.querySelectorAll('.stratum-btn')].find(item=>item.dataset.type===stratumType&&item.dataset.stratum===stratum)?.focus()}))}
function currentSummary(){return availableSummaries().find(row=>row.stratum_type===stratumType&&row.stratum===stratum)||{}}
function publicValue(value){return value===undefined||value===null||value===''?'—':value}
function renderStats(){const group=data.groups.find(row=>row.code===selected);const summary=currentSummary();const longitudinal=forContext(data.longitudinal)[0]||{};document.getElementById('group-title').textContent=groupLabel(group.label);const stats=[['分析患者',summary.patients||summary.first_prescription_patients],['复诊患者',publicValue(summary.repeat_patients)],['相邻复诊',publicValue(summary.transitions)],['患者内连续性',longitudinal.median_patient_jaccard?percent(longitudinal.median_patient_jaccard):'—']];document.getElementById('stats').innerHTML=stats.map(([label,value])=>`<div class="stat"><strong>${escapeHtml(publicValue(value))}</strong><span>${escapeHtml(label)}</span></div>`).join('')}
function demoRows(rows,total){if(!rows.length)return empty('该构成未达到公开门槛。');return `<div class="demo-list">${rows.map(row=>{const share=number(row.patients)/Math.max(1,total);return `<div class="demo-row"><span>${escapeHtml(row.stratum_label)}</span><span class="demo-meter"><i style="width:${Math.min(100,share*100)}%"></i></span><b>${escapeHtml(row.patients)}</b></div>`}).join('')}</div>`}
function renderDemographics(){const target=document.getElementById('demographics');if(!data.clinicalMode){target.hidden=true;return}target.hidden=false;const rows=availableSummaries();const overall=rows.find(row=>row.stratum_type==='overall')||{};const ageText=overall.median_age?`${escapeHtml(overall.median_age)}岁 <small>IQR ${escapeHtml(overall.age_q1)}–${escapeHtml(overall.age_q3)}岁</small>`:'—';target.innerHTML=`<div class="demo-block"><h4>首个合格处方时年龄</h4><div class="age-median">${ageText}</div></div><div class="demo-block"><h4>公开性别构成</h4>${demoRows(rows.filter(row=>row.stratum_type==='sex'),number(overall.patients))}</div><div class="demo-block"><h4>公开年龄构成</h4>${demoRows(rows.filter(row=>row.stratum_type==='age_band'),number(overall.patients))}</div>`}
function referenceContextItems(group,type,value){return sorted(data.items.filter(row=>row.group===group&&row.stratum_type===type&&row.stratum===value),'prevalence').slice(0,6)}
function referenceContextCombinations(group,type,value){return sorted(data.combinations.filter(row=>row.group===group&&row.stratum_type===type&&row.stratum===value&&row.stable_core_combination==='True'),'support').slice(0,3)}
function referenceCard(title,summary){if(!summary)return `<article class="reference-card"><h4>${escapeHtml(title)}</h4><p>该分层未达到公开人数门槛，不能据此推断为没有记录。</p></article>`;const items=referenceContextItems(summary.group,summary.stratum_type,summary.stratum);const combinations=referenceContextCombinations(summary.group,summary.stratum_type,summary.stratum);return `<article class="reference-card"><h4>${escapeHtml(title)} · ${escapeHtml(summary.patients)}人</h4><p>历史常用药味（患者覆盖率排序；克数为历史中位）</p><div class="reference-items">${items.length?items.map(row=>`<span class="dose-chip">${escapeHtml(row.item_name)} <small>${escapeHtml(doseShort(row))}</small></span>`).join(''):'未公开'}</div><p>${combinations.length?`稳定组合：${combinations.map(row=>escapeHtml(row.combination.split(' | ').join('＋'))).join('；')}`:'稳定组合未公开。'}</p></article>`}
function populateReferenceSex(){const diagnosis=document.getElementById('reference-diagnosis').value;const select=document.getElementById('reference-sex');const previous=select.value;const definitions=new Map(data.summaries.filter(row=>row.stratum_type==='sex').map(row=>[row.stratum,row.stratum_label]));select.innerHTML='<option value="">不限定</option>'+[...definitions].map(([value,label])=>`<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`).join('');if([...select.options].some(option=>option.value===previous))select.value=previous;select.dataset.diagnosis=diagnosis}
function renderReferenceResult(){if(!data.clinicalMode)return;const group=document.getElementById('reference-diagnosis').value;const sex=document.getElementById('reference-sex').value;const ageText=document.getElementById('reference-age').value.trim();const age=ageText===''?null:Number(ageText);const summaries=data.summaries.filter(row=>row.group===group);const overall=summaries.find(row=>row.stratum_type==='overall');const cards=[referenceCard(`${groupLabel(overall?.group_label||group)}总体`,overall)];if(sex){const definition=data.summaries.find(row=>row.stratum_type==='sex'&&row.stratum===sex);cards.push(referenceCard(`${definition?.stratum_label||sex}分层`,summaries.find(row=>row.stratum_type==='sex'&&row.stratum===sex)))}if(age!==null&&Number.isFinite(age)&&age>=0&&age<=130){const band=data.summaries.find(row=>row.stratum_type==='age_band'&&age>=number(row.age_min)&&age<=number(row.age_max));cards.push(referenceCard(`${age}岁所在年龄层`,band? summaries.find(row=>row.stratum_type==='age_band'&&row.stratum===band.stratum):null))}document.getElementById('reference-result').innerHTML=cards.join('')}
function initializeReference(){const section=document.getElementById('reference-section');if(!data.clinicalMode){section.hidden=true;return}section.hidden=false;const diagnosis=document.getElementById('reference-diagnosis');diagnosis.innerHTML=data.groups.map(group=>`<option value="${escapeHtml(group.code)}">${escapeHtml(groupLabel(group.label))}</option>`).join('');diagnosis.addEventListener('change',()=>{populateReferenceSex();renderReferenceResult()});populateReferenceSex();document.getElementById('reference-form').addEventListener('submit',event=>{event.preventDefault();renderReferenceResult()});renderReferenceResult()}
function annualSourceRows(){return annualMetric==='prevalence'?forContext(data.yearItems):forContext(data.yearChanges).filter(row=>row.change_type===annualMetric)}
function renderAnnual(){const section=document.getElementById('annual-section');if(!data.clinicalMode){section.hidden=true;return}const summaries=forContext(data.yearSummaries).sort((a,b)=>number(a.year)-number(b.year));const rows=annualSourceRows();if(!summaries.length||!rows.length){section.hidden=true;return}section.hidden=false;const valueKey=annualMetric==='prevalence'?'prevalence':'mean_patient_transition_fraction';const items=[...new Set(rows.map(row=>row.item_name))].sort((left,right)=>Math.max(...rows.filter(row=>row.item_name===right).map(row=>number(row[valueKey])))-Math.max(...rows.filter(row=>row.item_name===left).map(row=>number(row[valueKey])))||left.localeCompare(right,'zh-CN'));if(!items.includes(annualItem))annualItem=items[0];const select=document.getElementById('annual-item');select.innerHTML=items.map(item=>`<option value="${escapeHtml(item)}" ${item===annualItem?'selected':''}>${escapeHtml(item)}</option>`).join('');document.querySelectorAll('.annual-btn').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.annual===annualMetric)));const selectedRows=new Map(rows.filter(row=>row.item_name===annualItem).map(row=>[row.year,row]));const values=[...selectedRows.values()].map(row=>number(row[valueKey]));const scaleMax=Math.max(.1,Math.ceil(Math.max(...values)*10)/10);document.getElementById('annual-scale').textContent=`图内上限 ${percent(scaleMax)}`;document.getElementById('annual-chart').innerHTML=summaries.map(summary=>{const row=selectedRows.get(summary.year);const value=row?number(row[valueKey]):null;const barHeight=value===null?0:Math.max(2,Math.min(100,value/scaleMax*100));const n=row?(annualMetric==='prevalence'?`${row.exposed_patients}/${row.group_patients}人`:`${row.patients_with_change}/${row.repeat_patients}人`):'未公开';const dose=row?doseShort(row):'克数未公开';return `<div class="annual-column"><span class="annual-value">${value===null?'—':percent(value)}</span><span class="annual-bar-area"><i class="annual-bar ${escapeHtml(annualMetric)} ${value===null?'missing':''}" style="height:${barHeight}%"></i></span><span class="annual-year">${escapeHtml(summary.year)}</span><span class="annual-n">${escapeHtml(n)}</span><span class="annual-dose">${escapeHtml(dose)}</span></div>`}).join('');const definition=annualMetric==='prevalence'?'每名患者该年首张合格处方的覆盖率和历史中位克数':`每名复诊患者在该年${annualMetric==='addition'?'加':'减'}用该药的转移比例，再对患者等权平均；克数同样先在患者年内取中位数`;document.getElementById('annual-caption').textContent=`${annualItem}：${definition}。纵轴按当前药味动态缩放，只用于比较该药不同年份；缺失点未补零。`}
function visibleItems(){return sorted(forContext(data.items).filter(row=>!query||row.item_name.toLowerCase().includes(query)), 'prevalence').slice(0,limit)}
function visibleChanges(type){return sorted(forContext(data.changes).filter(row=>row.change_type===type&&(!query||row.item_name.toLowerCase().includes(query))),'patient_prevalence').slice(0,limit)}
function mini(rows,type){if(!rows.length)return empty('未达到公开阈值，不能解释为没有发生。');const symbols={removal:'−',core:'◆',addition:'＋'};return rows.slice(0,5).map(row=>`<div class="mini-item ${type}"><span class="mini-symbol" aria-hidden="true">${symbols[type]}</span><span class="mini-drug"><b>${escapeHtml(row.item_name)}</b><small>${escapeHtml(doseShort(row))}</small></span><span class="mini-value">${type==='core'?percent(row.prevalence):percent(row.patient_prevalence)}</span></div>`).join('')}
function renderTrajectory(){document.getElementById('trajectory-core').innerHTML=mini(sorted(forContext(data.items),'prevalence'),'core');document.getElementById('trajectory-addition').innerHTML=mini(sorted(forContext(data.changes).filter(row=>row.change_type==='addition'),'patient_prevalence'),'addition');document.getElementById('trajectory-removal').innerHTML=mini(sorted(forContext(data.changes).filter(row=>row.change_type==='removal'),'patient_prevalence'),'removal')}
function renderItems(){const rows=visibleItems();document.getElementById('item-list').innerHTML=rows.length?rows.map((row,index)=>`<div class="rank-row"><span class="rank">${String(index+1).padStart(2,'0')}</span><span class="drug"><b>${escapeHtml(row.item_name)}</b><small>${escapeHtml(row.exposed_patients)} / ${escapeHtml(row.group_patients)}名首诊患者</small><small class="dose-line">${escapeHtml(doseDetail(row))}</small></span><span class="meter"><i style="width:${Math.min(100,number(row.prevalence)*100)}%"></i><span>${percent(row.prevalence)}</span></span></div>`).join(''):empty('没有符合当前搜索条件的公开药味。')}
function renderCombos(){const rows=sorted(forContext(data.combinations).filter(row=>(comboSize==='all'||row.combination_size===comboSize)&&(!query||row.combination.toLowerCase().includes(query))&&row.stable_core_combination==='True'),'support').slice(0,limit);const itemIndex=new Map(forContext(data.items).map(item=>[item.item_name,item]));document.getElementById('combo-list').innerHTML=rows.length?rows.map(row=>{const doseChips=row.combination.split(' | ').map(item=>`<span class="dose-chip">${escapeHtml(item)} <small>${escapeHtml(doseShort(itemIndex.get(item)))}</small></span>`).join('');return `<article class="combo"><div class="combo-top"><div class="combo-name">${escapeHtml(row.combination.split(' | ').join(' ＋ '))}</div><span class="combo-size">${row.combination_size==='2'?'PAIR':'TRIPLET'}</span></div><div class="combo-dose" aria-label="各药味历史首诊中位克数">${doseChips}</div><div class="combo-meta"><span><b>${percent(row.support)}</b> 首诊支持度</span><span><b>${escapeHtml(row.support_patients)}</b> 名患者</span><span><b>${percent(row.bootstrap_core_selection_probability)}</b> 重选概率</span></div></article>`}).join(''):empty('没有符合当前条件的稳定公开组合。')}
function renderChangeList(type,target){const rows=visibleChanges(type);document.getElementById(target).innerHTML=rows.length?rows.map(row=>`<div class="change-row"><div class="change-main"><b>${escapeHtml(row.item_name)}</b><span>${percent(row.patient_prevalence)}</span></div><div class="change-sub">${escapeHtml(row.patients_with_change)} / ${escapeHtml(row.repeat_patients)}名复诊患者；患者等权复诊频率 ${percent(row.mean_patient_transition_fraction)}<br><span class="change-dose">${escapeHtml(doseDetail(row))}</span></div></div>`).join(''):empty('没有达到公开患者数门槛的方向。缺失不能解释为零。')}
function comparisonPairs(){const keys=new Map();data.comparisons.filter(row=>row.stratum_type===stratumType&&row.stratum===stratum&&(row.combination_group===selected||row.single_group===selected)).forEach(row=>{const key=`${row.combination_group}|${row.single_group}`;keys.set(key,{key,combination:row.combination_group,combinationLabel:row.combination_label,single:row.single_group,singleLabel:row.single_label})});return [...keys.values()]}
function comparisonRow(row){const difference=number(row.mean_transition_fraction_difference);const combinationDose=doseShort(prefixedDose(row,'combination'));const singleDose=doseShort(prefixedDose(row,'single'));return `<div class="comparison-row"><div class="comparison-main"><span class="direction">${row.change_type==='addition'?'加':'减'}</span><b>${escapeHtml(row.item_name)}</b><span class="delta ${difference>=0?'positive':'negative'}">${escapeHtml(percentagePoints(difference))}</span></div><div class="comparison-sub">患者等权频率 ${percent(row.combination_mean_transition_fraction)} vs ${percent(row.single_mean_transition_fraction)}；发生患者 ${percent(row.combination_prevalence)} vs ${percent(row.single_prevalence)}<br><span class="comparison-dose">历史中位克数 ${escapeHtml(combinationDose)} vs ${escapeHtml(singleDose)}</span></div></div>`}
function renderComparisons(){const section=document.getElementById('comparison-section');if(!data.clinicalMode){section.hidden=true;return}const pairs=comparisonPairs();if(!pairs.length){section.hidden=true;return}section.hidden=false;if(!pairs.some(pair=>pair.key===comparisonKey))comparisonKey=pairs[0].key;const target=document.getElementById('comparison-target');target.innerHTML=pairs.map(pair=>`<option value="${escapeHtml(pair.key)}" ${pair.key===comparisonKey?'selected':''}>${escapeHtml(groupLabel(pair.combinationLabel))} ↔ ${escapeHtml(groupLabel(pair.singleLabel))}</option>`).join('');const pair=pairs.find(row=>row.key===comparisonKey);document.getElementById('comparison-caption').textContent=`${groupLabel(pair.combinationLabel)} 与 ${groupLabel(pair.singleLabel)}；差值＝合并病－单病种，当前分层为${currentSummary().stratum_type==='overall'?'全部患者':currentSummary().stratum_label}。`;const rows=data.comparisons.filter(row=>`${row.combination_group}|${row.single_group}`===comparisonKey&&row.stratum_type===stratumType&&row.stratum===stratum&&(!query||row.item_name.toLowerCase().includes(query)));const ordered=[...rows].sort((a,b)=>Math.abs(number(b.mean_transition_fraction_difference))-Math.abs(number(a.mean_transition_fraction_difference)));const combo=ordered.filter(row=>row.higher_frequency==='combination').slice(0,limit);const single=ordered.filter(row=>row.higher_frequency==='single').slice(0,limit);document.getElementById('comparison-combo').innerHTML=combo.length?combo.map(comparisonRow).join(''):empty('没有两侧均达到门槛且合并病频率更高的药味。');document.getElementById('comparison-single').innerHTML=single.length?single.map(comparisonRow).join(''):empty('没有两侧均达到门槛且单病种频率更高的药味。')}
function render(){ensureStratum();renderNav();renderStrata();renderStats();renderDemographics();renderAnnual();renderTrajectory();renderComparisons();renderItems();renderCombos();renderChangeList('addition','addition-list');renderChangeList('removal','removal-list');document.getElementById('version').textContent=`MingYiRx ${data.version}`}
document.getElementById('search').addEventListener('input',event=>{query=event.target.value.trim().toLowerCase();renderTrajectory();renderComparisons();renderItems();renderCombos();renderChangeList('addition','addition-list');renderChangeList('removal','removal-list')});document.querySelectorAll('.filter-btn').forEach(button=>button.addEventListener('click',()=>{comboSize=button.dataset.size;document.querySelectorAll('.filter-btn').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));renderCombos()}));document.querySelectorAll('.annual-btn').forEach(button=>button.addEventListener('click',()=>{annualMetric=button.dataset.annual;annualItem='';renderAnnual()}));document.getElementById('annual-item').addEventListener('change',event=>{annualItem=event.target.value;renderAnnual()});document.getElementById('limit').addEventListener('change',event=>{limit=Number(event.target.value);render()});document.getElementById('comparison-target').addEventListener('change',event=>{comparisonKey=event.target.value;renderComparisons()});initializeReference();render();
</script>
</body>
</html>
"""
