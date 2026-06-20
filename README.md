# GRR Report Generator

量具重复性与再现性（Gauge R&R）分析工具，**完全匹配 COSMO 2.5.2e** 的输出格式与风格。

支持 **CLI 命令行** 和 **桌面 GUI** 两种使用方式，基于 **ANOVA 方差分析** 生成专业级 PDF 报告。

---

## 功能特性

### 分析引擎
- **三种分析方法**：
  - **ANOVA** — 完整方差分析（含零件×评价人交互作用），最推荐方法
  - **ANOVA Main Effect** — 主效应 ANOVA（不含交互作用，IV 合并入 EV）
  - **Range** — Xbar/R 极差法（经典方法，适用于小样本）
- **两种输出格式**：
  - **P/T (%Tolerance)** — 基于公差范围（默认，匹配 COSMO 桌面）
  - **Study Var (%TV)** — 基于总研究变差（AIAG 标准）
- **d2 查表** — 内置 AIAG MSA 4th d2 值表（2~10），超出范围自动线性近似
- **自动评级** — 按 AIAG 标准自动评级：Excellent / Good / Marginal / Poor

### 用户界面
- **CLI 命令行** — 批量处理，适合自动化流水线
- **桌面 GUI** — COSMO 风格 4 标签页交互界面，暖色纸纹主题
- **中/英双语** — 支持一键语言切换

### 报告输出
- **COSMO 风格 PDF 报告** — 汇总页 + 每项详情页，完整复刻 COSMO 2.5.2e 格式
- **CSV 导出** — 将 GRR 分析结果导出为 CSV
- **一致性报告** — 导出测量一致性分析 PDF
- **4 种图表** — 每项详情页含散点图（按零件/按评价人/交互）+ 方差贡献图
- **统一 Results 表** — grr/rr/%rr 合并为单个紧凑表格，左对齐+数值居中
- **自适应 Y 轴刻度** — 根据数据范围动态计算步进，避免刻度稀疏或缺失
- **深色图表配色** — 提高阅读对比度，坐标轴标题黑色更清晰

### 数据兼容性
- **自动列检测** — 自动识别 `operator_id`、`dut_id`、测量列
- **COSMO 格式支持** — 自动解析 COSMO 导出 CSV 前 3 行的 UL/LL 元数据
- **规格限导入/导出** — 支持从 JSON 导入导出规格限
- **任意试验次数** — 动态检测可用试验次数，用户可自定义

---

## 快速开始

### 1. 安装依赖

```bash
# 推荐使用 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. GUI 桌面模式（推荐）

```bash
# 直接启动
python3 grr_gui.py

# 或使用启动脚本
./run.sh
```

### 3. CLI 命令行模式

```bash
# 一键生成报告（COSMO 桌面风格，默认 3 次试验，P/T 格式）
python3 grr_report.py data.csv

# AIAG 标准模式
python3 grr_report.py data.csv --study-const 5.15 --output-format tv

# 指定试验次数和输出路径
python3 grr_report.py data.csv -o my_report.pdf --trials 5
```

---

## CLI 使用详解

### 基本用法

```bash
python3 grr_report.py <csv文件> [选项]
```

### 选项一览

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `csv` | — | 输入 CSV 数据文件路径（必填） |
| `-o` / `--output` | 自动命名 | 输出 PDF 路径，默认 `<输入文件名>-GRR-REPORT.pdf` |
| `--trials` | `3` | 每个 (操作员, 零件) 组合使用的试验次数（行业标准=3） |
| `--part-col` | 自动检测 | 零件/部件列名 |
| `--appraiser-col` | 自动检测 | 评价人/操作员列名 |
| `--method` | `ANOVA` | 分析方法：`ANOVA`、`ANOVA Main Effect`、`Range` |
| `--study-const` | `6.0` | 安全系数（COSMO 默认 6.0，AIAG 标准为 5.15） |
| `--output-format` | `tol` | 输出格式：`tol`（P/T %Tolerance）、`tv`（Study Var %TV） |

### 示例

```bash
# 使用所有可用试验次数（匹配 COSMO 行为）
python3 grr_report.py data.csv --trials 10

# AIAG 标准模式（5.15σ + %TV）
python3 grr_report.py data.csv --study-const 5.15 --output-format tv

# 指定列名
python3 grr_report.py data.csv --part-col dut_id --appraiser-col operator_id

# 极差法分析
python3 grr_report.py data.csv --method Range

# 导出到指定路径
python3 grr_report.py data.csv -o /path/to/report.pdf
```

---

## GUI 桌面应用

### 启动

```bash
python3 grr_gui.py
```

启动后进入 COSMO v2.5.2e 风格的 4 标签页界面。**右侧面板始终可见**，显示基础信息、方法选择和操作按钮。

### 界面布局

```
┌──────────────────────────────────────────────────────┐
│  菜单: [Load] [Test Items] [Analysis] [Results]      │  ← 右侧面板: ┐
├──────────────────────────────────────────────────────┤  Base Data   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐│  Selected    │
│  │   Load   │  │Test Items│  │ Analysis │  │Res.. ││  Data        │
│  │          │  │          │  │          │  │      ││              │
│  │  加载CSV  │  │ 选择测项  │  │ 分析设置  │  │ 查看  ││ Method       │
│  │  配置列   │  │ 设置规格限│  │ 选择数据  │  │ 导出  ││ Output Format│
│  └──────────┘  └──────────┘  └──────────┘  └──────┘│ Study Const  │
├──────────────────────────────────────────────────────┤              │
│  状态栏: 显示当前操作信息                             │ [Run]        │
└──────────────────────────────────────────────────────┘ [导出PDF]    │
                                                         └─────────────┘
```

### 标签页说明

| 标签页 | 功能 |
|--------|------|
| **Load** | 加载 CSV 文件，选择零件列/评价人列/排序列，预览数据。支持 COSMO 行格式解析（前 3 行 UL/LL） |
| **Test Items** | 从加载的数据中选择要分析的测量项。支持筛选、添加/移除测项、设置每项规格限（UL/LL） |
| **Analysis** | 设置分析方法（ANOVA/Range）、GRR 方法、试验次数、自动分箱参数。选择参与分析的 Units 和 Appraisers |
| **Results** | 查看分析结果表格（颜色编码：绿/黄/橙/红对应评级），切换 %Variance / %Tolerance 显示，导出 PDF/CSV |

### 右侧面板

| 区域 | 内容 |
|------|------|
| **Base Data** | 显示加载数据的基本信息：Units 数、Appraisers 数、Trials 数、列数 |
| **Selected Data** | 显示当前选择的分析范围：选择的 Units、Appraisers、Trials、Test Items 数 |
| **Method** | 选择分析方法（ANOVA / ANOVA Main Effect / Range） |
| **Output Format** | 选择输出格式：P/T (%Tol) 或 Study Var (%TV) |
| **Study Const** | 选择安全系数：6.0 (COSMO) 或 5.15 (AIAG) |
### 操作按钮

| 按钮 | 功能 |
|------|------|
| **Run** | 运行 GRR 分析 |
| **Export as CSV** | 导出分析结果为 CSV |
| **Export as PDF** | 生成并保存 COSMO 风格 PDF 报告 |
| **Export Consistency Report PDF** | 生成并保存一致性分析 PDF 报告 |

### 语言切换

点击右上角面板的 **"🌐 中文"** / **"🌐 EN"** 按钮，可在中英文界面之间一键切换。

### 参数说明

#### Output Format（输出格式）

| 选项 | 公式 | 说明 |
|------|------|------|
| **P/T (%Tol)** | `σ × K ÷ Tolerance × 100%` | 基于公差范围，需要设置规格限（UL/LL）。COSMO 桌面默认模式 |
| **Study Var (%TV)** | `σ × K` | 基于总研究变差，无需规格限。AIAG MSA 标准输出 |

#### Study Const（研究常数 / 安全系数 K）

| 选项 | 覆盖率 | 说明 |
|------|--------|------|
| **6.0 (COSMO)** | 99.73% (±3σ) | COSMO 软件默认，覆盖 ±3 个标准差 |
| **5.15 (AIAG)** | 99% | AIAG MSA 手册标准，覆盖 ±2.575 个标准差（约 5.15σ 范围） |

---

## 输入数据格式

### 文件格式
- **格式**：CSV（逗号分隔）
- **编码**：UTF-8（推荐），也支持 GBK 编码自动检测
- **表头**：第一行为列名

### 必需列

| 列名 | 说明 | 示例值 |
|------|------|--------|
| `operator_id` | 评价人（Appraiser）编号 | `1.0`, `2.0`, `3.0` |
| `dut_id` | 零件（Part/Unit）编号 | `65130DLFS00001` |
| `run_index` | 试验次数索引（可选，自动分配） | `0`, `1`, `2` |

### 测量列

可以是 `hinge_measurement_*` 命名的列，或其他数值列。程序会自动检测数值列作为候选测量项。

### COSMO 格式支持

直接支持 COSMO 2.5.2e 导出的 CSV 格式：
- **第 2 行**：各列的规格上限（UL）值
- **第 3 行**：各列的规格下限（LL）值
- 程序自动识别并提取

### 示例 CSV

```csv
operator_id,dut_id,run_index,hinge_measurement_length
1,65130DLFS00001,0,10.234
1,65130DLFS00001,1,10.256
1,65130DLFS00001,2,10.245
1,65130DLFS00002,0,9.876
1,65130DLFS00002,1,9.892
1,65130DLFS00002,2,9.888
2,65130DLFS00001,0,10.198
2,65130DLFS00001,1,10.212
2,65130DLFS00001,2,10.203
...
```

### 数据要求
- 每个 `(operator_id, dut_id)` 组合必须有 **相同数量的测量值**（完整的交叉设计）
- 至少需要 **2 个评价人 × 2 个零件 × 2 次试验** = 8 个数据点
- 推荐：10 个零件 × 3 个评价人 × 3 次试验 = 90 个数据点（AIAG 标准）

---

## 输出格式说明

### P/T (%Tolerance) — 百分比公差

$$P/T = \frac{\sigma_{GRR} \times K}{USL - LSL} \times 100\%$$

- **分母** = 公差范围（规格上限 − 规格下限）
- **含义**：测量系统的变差占产品公差带的比例
- **应用**：判断测量系统是否足以控制规格限内的产品质量
- **默认模式**：匹配 COSMO 桌面软件

### Study Var (%TV) — 百分比研究变差

$$\%TV = \frac{\sigma_{GRR} \times K}{Total\ Variation} \times 100\%$$

- **分母** = 总研究变差（包含零件间变差 + 测量系统变差）
- **含义**：测量系统的变差占总过程变差的比例
- **应用**：判断测量系统对整体过程波动的影响程度
- **AIAG 标准**：常与 Study Const = 5.15 搭配使用

### 安全系数（Study Const）

| 值 | 对应标准 | 说明 |
|----|---------|------|
| `6.0` | COSMO 桌面 | 6σ 范围，覆盖 99.73% 的测量值 |
| `5.15` | AIAG MSA 4th | 5.15σ 范围，覆盖 99% 的测量值 |

### 评级标准（AIAG）

基于 %GRR 值自动评级（适用于 P/T 和 %TV 两种格式）：

| %GRR 范围 | 评级 | 颜色 | 含义 |
|-----------|------|------|------|
| ≤ 10% | **Excellent** | 🟢 绿色 | 测量系统可接受 |
| 10% ~ 20% | **Good** | 🔵 蓝色 | 测量系统合格 |
| 20% ~ 30% | **Marginal** | 🟠 橙色 | 有条件接受，需改进 |
| > 30% | **Poor** | 🔴 红色 | 不可接受，必须改进 |

---

## PDF 报告结构

### 第 1 页 — 汇总页（Summary）

- **Cosmo GRR Report** 蓝色大标题
- 版本号 / 生成日期
- **GRR Information** 区域：分析方法、评价人数、零件数
- **汇总表**：所有测量项的完整结果，包括：
  - UL / LL（规格上下限）
  - GRR / Repeat / Reprod（研究变差）
  - %GRR / %EV / %AV / %IV / %PV（百分比）
  - **评级**（颜色标注：绿/蓝/橙/红）

### 第 2 ~ N 页 — 每项详情页（Detail）

每页对应一个测量项，包含：

- **标题行**：测量项名称 + 规格限 (UL / LL)
- **2×2 图表布局**：
  - **Scatter by Part** — 按零件分组的测量值散点图
  - **Scatter by Appraiser** — 按评价人分组的测量值散点图
  - **Scatter by Part and Appraiser** — 交互作用散点图
  - **Contribution** — 方差分量贡献百分比柱状图
- **Results 表**：完整方差分量数据（合并统一表，grr/rr/%rr 三合一紧凑布局）
- **Data 矩阵**：原始测量数据排列（Units × Trials × Appraisers，自适应字体与小数位）
- **页码**：Page X / Y

---

## 项目结构

```
grr-reporter/
├── grr_core.py         # 核心分析引擎（ANOVA / Range）★
├── grr_gui.py          # COSMO 风格桌面 GUI ★
├── grr_pdf.py          # PDF 报告生成模块（reportlab + matplotlib）
├── grr_report.py       # CLI 命令行入口 ★
├── requirements.txt    # Python 依赖列表
├── run.sh              # macOS/Linux 一键启动脚本
├── LICENSE             # MIT 许可证
├── .gitignore          # Git 忽略规则
└── samples/            # 示例数据
    ├── 123.csv
    ├── SA-BUTTON#2-GRR.csv
    └── README.md
```

### 核心模块说明

| 文件 | 功能 |
|------|------|
| `grr_core.py` | GRR 分析核心引擎，实现 ANOVA / ANOVA Main Effect / Range 三种方法，包含 d2 查表、方差分量计算、评级判断 |
| `grr_gui.py` | 基于 tkinter 的桌面 GUI 应用，4 标签页交互界面，中英双语，暖色纸纹主题 |
| `grr_pdf.py` | 基于 reportlab + matplotlib 的 PDF 报告生成，COSMO 风格格式，含 4 种图表 |
| `grr_report.py` | CLI 命令行入口，解析参数、调用分析引擎、生成报告 |

---

## 依赖

| 包 | 用途 | 最低版本 |
|----|------|---------|
| **pandas** | 数据加载与处理 | ≥ 2.0 |
| **numpy** | 数值计算 | ≥ 1.24 |
| **scipy** | 方差分析（ANOVA） | ≥ 1.10 |
| **matplotlib** | 图表绘制 | ≥ 3.7 |
| **reportlab** | PDF 报告生成 | ≥ 4.0 |

> Python 版本要求：**≥ 3.10**

---

## 常见问题

### Q: 结果与 COSMO 软件不一致？

**A**: 最常见的原因是试验次数（Number of Trials）不一致。COSMO 默认使用所有可用的试验次数，而本工具默认使用 3 次。可以通过 `--trials` 参数或 GUI 中的 Number of trials 设置为所需的试验次数。

### Q: 支持哪些 CSV 编码？

**A**: 支持 UTF-8 和 GBK 编码，程序会自动检测。

### Q: 如何添加新的规格限？

**A**: 在 GUI 的 Test Items 标签页中，可以手动输入每项的 UL 和 LL 值，也可以从 JSON 文件导入。

### Q: 第二次导出 PDF 时卡住了怎么办？

**A**: 这是 matplotlib 全局状态在多次调用后未清理导致的。已修复：每次导出 PDF 后自动清理 matplotlib 内部缓存和图形对象。如果仍遇到卡顿，请确保 `matplotlib.use("Agg")` 模式启用（GUI 导出已内置此设置）。

**A**: 支持 Python 3.10+ 的所有平台。GUI 基于 tkinter（Python 标准库），无需额外安装。

### Q: 支持 Mac/Windows/Linux 吗？

---

## 许可证

[MIT](LICENSE)

---

*Built with ❤️ for measurement system analysis*
