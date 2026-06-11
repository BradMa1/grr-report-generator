# GRR Report Generator

量具重复性与再现性（Gauge R&R）分析工具，完全匹配 **COSMO 2.5.2e** 的输出格式与风格。

支持 CLI 命令行和桌面 GUI 两种使用方式，基于 ANOVA 方差分析生成专业级 PDF 报告。

## 功能特性

- **三种分析方法**：ANOVA（完整方差分析）、ANOVA Main Effect（主效应）、Range（极差法）
- **双模式使用**：CLI 命令行批量处理 + 桌面 GUI 交互式操作
- **COSMO 风格 PDF 报告**：汇总页 + 每项详情页，含 4 种图表（散点图 + 贡献图）
- **AIAG 标准支持**：Study Variation × 5.15，支持 P/T（%Tolerance）和 %TV（%Study Variation）两种输出
- **自动评级**：Excellent（≤10%）、Good（≤20%）、Marginal（≤30%）、Poor（>30%）
- **暖色纸纹 GUI**：类纸质界面，柔和护眼

## 快速开始

### 安装依赖

```bash
# 推荐使用 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### CLI 模式

```bash
python3 grr_report.py data.csv -o report.pdf
```

### GUI 桌面模式

```bash
python3 grr_gui.py
```

或直接运行启动脚本：

```bash
./run.sh
```

## CLI 使用详解

```
python3 grr_report.py <csv文件> [选项]
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `-o` / `--output` | 自动命名 | 输出 PDF 路径 |
| `--trials` | 4 | 每个 (操作员, 零件) 对的试验次数 |
| `--part-col` | 自动检测 | 零件/部件列名 |
| `--appraiser-col` | 自动检测 | 评价人/操作员列名 |
| `--method` | `ANOVA` | 分析方法：`ANOVA`、`ANOVA Main Effect`、`Range` |
| `--study-const` | `6.0` | 安全系数（AIAG 标准为 `5.15`） |
| `--output-format` | `tol` | 输出格式：`tol`（P/T %Tolerance）、`tv`（Study Variation %TV） |

### 示例

```bash
# COSMO 桌面模式（默认）
python3 grr_report.py measurement_data.csv

# AIAG 标准模式
python3 grr_report.py data.csv --study-const 5.15 --output-format tv

# 指定零件列和操作员列
python3 grr_report.py data.csv --part-col dut_id --appraiser-col operator_id

# 导出到指定路径，指定 5 次试验
python3 grr_report.py data.csv -o my_report.pdf --trials 5
```

## GUI 桌面应用

启动后进入 COSMO v2.5.2e 风格的 4 标签页界面：

| 标签页 | 功能 |
|--------|------|
| **Load** | 加载 CSV 文件，选择零件/评价人列，预览数据 |
| **Test Items** | 选择要分析的测量项 |
| **Analysis** | 设置分析方法、试验次数、选择单元和评价人 |
| **Results** | 查看分析结果（颜色编码表格），导出 PDF/CSV |

右侧面板始终可见，显示 Base Data / Selected Data 信息、方法选择和 Run/Export 按钮。

## 输入数据格式

### 必需列

| 列名 | 说明 | 示例 |
|------|------|------|
| `operator_id` | 评价人编号 | `1.0`, `2.0`, `3.0` |
| `dut_id` | 零件/部件编号 | `65130DLFS00001` |
| `run_index` | 试验次数（可选，自动分配） | `0`, `1`, `2` |

### 测量列

可以是 `hinge_measurement_*` 命名的列，或其他数值列。程序自动检测。

### COSMO 格式支持

直接支持 COSMO 2.5.2e 导出的 CSV 格式：第 2 行 UL 值、第 3 行 LL 值自动解析。

### 示例 CSV

```csv
operator_id,dut_id,run_index,hinge_measurement_length
1,65130DLFS00001,0,10.234
1,65130DLFS00001,1,10.256
1,65130DLFS00001,2,10.245
1,65130DLFS00002,0,9.876
...
```

## 输出说明

### PDF 报告结构

**第 1 页 — 汇总页**
- Cosmo GRR Report 蓝色标题
- 版本号/日期
- GRR Information：分析方法、评价人数、零件数
- 汇总表：所有测量项的 UL / LL / GRR / Repeat / Reprod / %GRR / 评级

**第 2+ 页 — 每项详情页**
- 测量项名称 + 规格限 (UL/LL)
- 2×2 图表布局：
  - Scatter by Part（按零件散点图）
  - Scatter by Appraiser（按评价人散点图）
  - Scatter by Part and Appraiser（交互散点图）
  - Contribution（方差贡献图）
- Results 表：完整方差分量
- Data 矩阵：原始数据排列

### 评级标准

| %GRR | 评级 |
|------|------|
| ≤ 10% | ✅ Excellent |
| ≤ 20% | ✅ Good |
| ≤ 30% | ⚠️ Marginal |
| > 30% | ❌ Poor |

## 项目结构

```
grr-reporter/
├── grr_core.py       # 核心分析引擎（ANOVA / Range）★
├── grr_gui.py        # COSMO 风格桌面 GUI ★
├── grr_pdf.py        # PDF 报告生成（reportlab + matplotlib）
├── grr_report.py     # CLI 命令行入口 ★
├── requirements.txt  # Python 依赖
└── run.sh           # macOS/Linux 启动脚本
```

## 依赖

- **Python** ≥ 3.10
- **pandas** — 数据处理
- **numpy** — 数值计算
- **scipy** — 方差分析
- **matplotlib** — 图表绘制
- **reportlab** — PDF 生成

## 许可证

[MIT](LICENSE)

---

*Built with ❤️ for measurement system analysis*
