# MingYiRx

MingYiRx 是一个本地运行、默认隐私安全的名老中医纵向处方分析项目。它把一次性论文脚本拆成可配置的数据入口和稳定的分析定义，用于描述：

- 不同记录标签表型的首次处方药味结构；
- 经过隐私阈值和患者重抽样稳定性筛选的首次处方药对与三药组合；
- 使用共享布局和预设阈值网格审计的稳定高频药味共现网络；
- 主网络中三病共享、两病共享和单病种药味/药对的成员模式及两两Jaccard；
- 同一患者相邻复诊处方的延续与加减；
- 患者等权的逐药加药与减药倾向；
- 单病种/合并病、性别和首诊年龄分层的公开临床复盘；
- 每名患者每年一次的年度处方构成，以及患者—年度等权的加减演变；
- 加药、减药、记录剂量改变和处方修改负担；
- 不同疾病组的处方分布重叠；
- 患者内相邻处方与匹配的不同患者处方背景之间的差值；
- 患者不重叠的前后时期稳定性。

它不分析疗效、安全性、处方合理性、机制或诊断性能。

当前版本为 `0.12.1`：除既有纵向、组合和网络分析外，支持严格主队列之外的精确单病种/合并病临床表型、性别与首诊年龄分层、合并病与相应单病种的患者等权加减差，以及患者—年度处方构成和加减演变。交互页面可用诊断、性别和年龄检索已公开历史分层；处方演变轨迹用明确的减味—首诊骨架—加味三态视觉编码，但不拟合或输出患者处方。随机分析使用预先定义的固定种子；组合与网络节点稳定性使用精确二项概率，不引入Monte Carlo误差。

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
python -m mingyirx dashboard `
  --input-dir outputs\demo `
  --output outputs\demo\clinical_review.html
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
12. 在 `network_analysis` 中预设主cosine阈值以及节点流行率/cosine敏感性网格；网络成员变化应与网络规模一起报告。
13. 跨病种比较只使用同一主阈值；“单病种成员”表示仅在该阈值下入选，不能写成该病专用或其他病种未使用。
14. 如需临床探索视图，配置 `clinical_phenotype_analysis`、一致的性别映射和不重叠年龄段；合并病来自完整诊断历史中的精确目标疾病组合，并单独排除配置的其他结缔组织病。

规范输入为一行一个处方药味，必需字段是：

```text
patient_id, visit_id, visit_date, diagnosis_text, item_name
```

可选字段是：

```text
dose, unit, physician_id, sex, birth_date
```

患者键只在内存中用于链接，不会写入公开结果。

重复表头、多文件重叠和逐文件溯源的完整约定见 [input-contract.md](docs/input-contract.md)。

陶庆文两份锁定的GB18030导出可使用 [tao_qingwen_gb18030.template.json](configs/tao_qingwen_gb18030.template.json)。模板只包含列位置、文件哈希、记录标签规则和饮片资格规则，不包含文件路径或患者数据。

## 输出

核心运行产生十八张科学汇总表、一个Markdown报告和一个运行清单。启用临床表型层时再增加九张公开汇总表：

- `cohort_summary.csv`
- `first_prescription_item_prevalence.csv`
- `frequent_item_combinations.csv`
- `network_nodes.csv`
- `network_edges.csv`
- `network_threshold_sensitivity.csv`
- `network_group_overlap.csv`
- `network_membership.csv`
- `longitudinal_summary.csv`
- `longitudinal_item_change_tendency.csv`
- `transition_mode_summary.csv`
- `cross_group_similarity.csv`
- `temporal_stability.csv`
- `temporal_cutpoint_sensitivity.csv`
- `matched_reference_summary.csv`
- `matched_reference_sensitivity.csv`
- `item_normalization_audit.csv`
- `dose_conflict_audit.csv`
- `clinical_phenotype_summary.csv`
- `clinical_first_prescription_item_prevalence.csv`
- `clinical_frequent_item_combinations.csv`
- `clinical_longitudinal_summary.csv`
- `clinical_item_change_tendency.csv`
- `clinical_item_change_comparison.csv`
- `clinical_year_summary.csv`
- `clinical_year_item_prevalence.csv`
- `clinical_year_item_change_tendency.csv`
- `report.md`
- `run_manifest.json`

`outputs/`、`work/` 和真实数据目录默认被Git忽略。

## 本地临床复盘界面

`dashboard` 命令把已经通过隐私扫描的公开汇总CSV打包为一个自包含HTML，不启动服务器，也不读取原始处方、患者键或 `run_manifest.json`。用浏览器打开生成的 `clinical_review.html` 后，可以：

- 切换记录标签病种，查看首次处方常用药味；
- 查看单病种与合并病表型、公开性别/年龄构成及一维分层；
- 按药味切换年度常用、年度加药和年度减药轨迹；
- 输入诊断、性别和年龄，在本地检索总体、性别和年龄的一维历史处方参照；
- 搜索药味或组合，并筛选药对、三药组合和显示数量；
- 对照首诊处方骨架，查看复诊中常见的逐药加药与减药方向；
- 展开计算依据，核对患者数、相邻复诊数、公开阈值后的分母和解释限制。

页面用于医师回顾自己的历史群体处方模式。诊断、性别和年龄输入只存在于当前浏览器页面，用来检索已经公开的聚合分层；不保存、不传输，也不会把性别与年龄合成未经估计的联合模型。页面不生成个体处方、剂量、禁忌或疗效建议。某一药味的“常加”或“常减”只表示在本数据集复诊患者中的记录频率，不能直接用于当前患者。

网络图是可选下游步骤，只读取已通过隐私扫描的汇总CSV。当前机器使用独立的CNSPlots环境：

```powershell
& 'C:\Users\glah1\.codex\tools\cnsplots\.venv\Scripts\python.exe' `
  scripts\plot_networks.py `
  --input-dir outputs\demo `
  --output-dir outputs\demo\figures `
  --groups ra sjd as
```

脚本生成三套紧凑PNG预览和可编辑SVG：三病种网络使用相同视觉编码和固定随机种子的独立布局，阈值热图显示具体边集合相对主分析的Jaccard，跨病种图则直接展示共享层级计数和节点/药对两两Jaccard。不同网络面板中的坐标位置不作跨病种解释。

## 论文分析的推荐顺序

1. 队列流程、缺失和记录质量。
2. 患者等权的首次处方药味结构。
3. 患者内相邻处方变化。
4. 患者等权的逐药加药/减药倾向。
5. 同医师不同患者背景参考及患者级bootstrap区间。
6. 患者不重叠的主时期比较和预设切点压力测试。
7. 用预设支持度和精确重抽样概率筛选稳定药对/三药组合。
8. 用预设节点/cosine阈值网格审计网络成员稳定性，并保持探索性解释。
9. 在同一主阈值下比较节点与药对成员重叠，区分共享药味与重新组合形成的病种差异。

具体边界见 [analysis-contract.md](docs/analysis-contract.md)，从公开汇总结果到论文段落/图表/代码证据的对应关系见 [data-to-paper-workflow.md](docs/data-to-paper-workflow.md)，原陶庆文研究到通用模块的映射见 [migration-map.md](docs/migration-map.md)。

## 自动验证

`.github/workflows/ci.yml` 在GitHub的push和pull request上使用Python 3.11与3.14运行编译、全部单元测试、只读验证和合成数据端到端分析。CI不安装绘图依赖，不读取真实数据、本地私有路径或任何凭据；真实分析仍只能在受控本地环境运行。

## Git发布边界

可以提交：代码、配置模板、合成数据、测试、分析契约和非敏感文档。

禁止提交：真实临床CSV/Excel、患者或就诊键、HMAC密钥、患者级中间表、精确日期、包含低频单元格的结果、伦理文件原件和任何凭据。
