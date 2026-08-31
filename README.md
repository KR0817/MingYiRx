# MingYiRx

MingYiRx 是一个本地运行、默认隐私安全的名老中医纵向处方分析项目。它把一次性论文脚本拆成可配置的数据入口和稳定的分析定义，用于描述：

- 不同记录标签表型的首次处方药味结构；
- 经过隐私阈值和患者重抽样稳定性筛选的首次处方药对与三药组合；
- 同一患者相邻复诊处方的延续与加减；
- 加药、减药、记录剂量改变和处方修改负担；
- 不同疾病组的处方分布重叠；
- 患者内相邻处方与匹配的不同患者处方背景之间的差值；
- 患者不重叠的前后时期稳定性。

它不分析疗效、安全性、处方合理性、机制或诊断性能。

当前版本为 `0.7.0`：除多文件GB18030入口和资格门控外，已支持同医师不同患者匹配参照、患者级bootstrap区间、匹配与时间切点敏感性分析、版本化药名字典、剂量冲突汇总审计，以及患者等权的稳定药对/三药组合。随机分析使用预先定义的固定种子；组合稳定性使用精确二项概率，不引入Monte Carlo误差。

## 为什么不是直接整理原论文脚本

原脚本同时包含陶主任专属文件路径、疾病规则、期刊图表和投稿逻辑。直接公开会难以复用，也容易把敏感数据边界与分析代码混在一起。MingYiRx只保留可泛化的分析核心；论文、网络图和期刊打包属于下游模块。

## 快速开始

要求 Python 3.11 或更高版本，不需要第三方依赖或包安装。

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
python -m mingyirx validate `
  --config configs\example.json `
  --input data\synthetic\prescriptions.csv
python -m mingyirx run `
  --config configs\example.json `
  --input data\synthetic\prescriptions.csv `
  --output outputs\demo
```

也可以直接运行封装好的演示脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_demo.ps1
```

`pyproject.toml` 允许在已有 `setuptools` 或可联网获取构建工具时执行 `python -m pip install -e .`，但这不是运行分析的前提。

## 接入一位新的名老中医数据

1. 将真实数据放在仓库之外，并保持原文件只读；多份文件分别使用一个 `--input`。
2. 复制 `configs/example.json`，填写新的 `project_id`、`dataset_id` 和 `cohort_version`。
3. 修改 `columns`，把本地源表字段映射到规范字段；普通表头使用名称，重复表头使用从0开始的列位置。
4. 用完整诊断历史定义 `groups` 的正则表达式；不要根据用药反推疾病。
5. 将 `synthetic_mode` 设为 `false`，真实研究的 `min_public_n` 保持至少10。
6. 先运行 `validate`，核对患者数、重叠组、未匹配患者、日期和剂量警告。
7. 多文件时明确选择 `append` 或 `max_multiplicity`，冻结配置和输入哈希后再运行 `run`。
8. 启用匹配参照时映射 `physician_id`；单医师历史数据缺少该列时，只有在来源已确认后才设置 `assume_single_physician=true`。
9. 预先填写 `early_end_year` 和包含该年份的升序 `temporal_cutpoints`；不要根据结果寻找“最佳”分界点。
10. 如有药师确认的药名字典，在 `item_normalization` 中记录版本、相对/绝对路径和SHA-256；真实数据无权威文件时保持显式的 `source-string` 模式。
11. 在 `combination_analysis` 中预设组合阶数和稳定性概率阈值；不要根据结果事后调整 `core_prevalence`。

规范输入为一行一个处方药味，必需字段是：

```text
patient_id, visit_id, visit_date, diagnosis_text, item_name
```

可选字段是：

```text
dose, unit, physician_id
```

患者键只在内存中用于链接，不会写入公开结果。

重复表头、多文件重叠和逐文件溯源的完整约定见 [input-contract.md](docs/input-contract.md)。

陶庆文两份锁定的GB18030导出可使用 [tao_qingwen_gb18030.template.json](configs/tao_qingwen_gb18030.template.json)。模板只包含列位置、文件哈希、记录标签规则和饮片资格规则，不包含文件路径或患者数据。

## 输出

运行后产生十二张汇总表、一个Markdown报告和一个运行清单：

- `cohort_summary.csv`
- `first_prescription_item_prevalence.csv`
- `frequent_item_combinations.csv`
- `longitudinal_summary.csv`
- `transition_mode_summary.csv`
- `cross_group_similarity.csv`
- `temporal_stability.csv`
- `temporal_cutpoint_sensitivity.csv`
- `matched_reference_summary.csv`
- `matched_reference_sensitivity.csv`
- `item_normalization_audit.csv`
- `dose_conflict_audit.csv`
- `report.md`
- `run_manifest.json`

`outputs/`、`work/` 和真实数据目录默认被Git忽略。

## 论文分析的推荐顺序

1. 队列流程、缺失和记录质量。
2. 患者等权的首次处方药味结构。
3. 患者内相邻处方变化。
4. 同医师不同患者背景参考及患者级bootstrap区间。
5. 患者不重叠的主时期比较和预设切点压力测试。
6. 用预设支持度和精确重抽样概率筛选稳定药对/三药组合。
7. 最后才考虑网络和聚类，并保持探索性解释。

具体边界见 [analysis-contract.md](docs/analysis-contract.md)，原陶庆文研究到通用模块的映射见 [migration-map.md](docs/migration-map.md)。

## Git发布边界

可以提交：代码、配置模板、合成数据、测试、分析契约和非敏感文档。

禁止提交：真实临床CSV/Excel、患者或就诊键、HMAC密钥、患者级中间表、精确日期、包含低频单元格的结果、伦理文件原件和任何凭据。
