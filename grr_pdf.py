"""
GRR PDF 报告生成模块 — COSMO 2.5.2e 风格
========================================
完全复刻 COSMO 2.5.2e 的 PDF 报告格式：

第1页 — 汇总页
  Cosmo GRR Report（蓝色大标题）
  Version / Date
  GRR Information: 方法、评价人、零件（浅蓝背景标题）
  汇总表（浅蓝表头 + 绿色 Result 底色 + 交替行色）

第2~N页 — 每个测量项详情页
  测量名 + (UL:xxx  LL:xxx)
  4 图表 2×2 布局：
    - Scatter by Part
    - Scatter by Appraiser
    - Scatter by Part and Appraiser
    - Contribution
  Results 表
  Data 矩阵 (Unit x Trial x Appraiser)
  Page X/Y
"""

import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, PageBreak, Paragraph, Spacer,
    Table, TableStyle, Image,
)

from grr_core import GrrReport, GrrResult

# ── COSMO 配色 (ReportLab 用) ──
C_TITLE     = colors.HexColor("#1a5276")   # 标题深蓝
C_HEADER_BG = colors.HexColor("#3498db")   # 表头/信息头浅蓝背景
C_HEADER_FG = colors.white                 # 表头文字白色
C_ROW_ALT   = colors.HexColor("#f2f6fa")   # 交替行色
C_ROW_WHITE = colors.white
C_EXCELLENT = colors.HexColor("#2ecc71")   # Excellent 绿色
C_GOOD      = colors.HexColor("#3498db")   # Good 蓝色
C_MARGINAL  = colors.HexColor("#f39c12")   # Marginal 橙色
C_POOR      = colors.HexColor("#e74c3c")   # Poor 红色
C_GRAY      = colors.HexColor("#7f8c8d")
C_LIGHT_GRAY = colors.HexColor("#bdc3c7")
C_GRID      = colors.HexColor("#d5dbdb")

# ── Matplotlib 配色 (十六进制字符串) ──
MPL_TITLE     = "#1a5276"
MPL_HEADER_BG = "#3498db"
MPL_RED       = "#e74c3c"
MPL_GREEN     = "#2ecc71"
MPL_BLUE      = "#2980b9"
MPL_ORANGE    = "#f39c12"

# ── 图表配色 ──
CHART_COLORS = ["#2980b9", "#e74c3c", "#2ecc71", "#f39c12", "#8e44ad", "#1abc9c"]
CONTRIB_COLORS = ["#3498db", "#2ecc71", "#f39c12", "#e74c3c"]  # Equipment, Appraiser, Interaction, Part


def _rating_color(rating: str):
    return {"Excellent": C_EXCELLENT, "Good": C_GOOD,
            "Marginal": C_MARGINAL, "Poor": C_POOR}.get(rating, C_GRAY)


def _rating_bg(rating: str):
    """Result 列背景色"""
    return {"Excellent": colors.HexColor("#d5f5e3"),
            "Good": colors.HexColor("#d6eaf8"),
            "Marginal": colors.HexColor("#fdebd0"),
            "Poor": colors.HexColor("#fadbd8")}.get(rating, colors.white)


def _op_sort_key(x):
    """Operator 排序键：数字按数值排，文本按字符串排（数值优先）"""
    try:
        return (0, float(x), str(x))
    except (ValueError, TypeError):
        return (1, 0, str(x))


# ══════════════════════════════════════════════════════════════════
# 第1页：汇总页
# ══════════════════════════════════════════════════════════════════

def _build_summary(report: GrrReport) -> list:
    els = []

    # ── 标题 (COSMO 风格: 蓝色大标题居中) ──
    els.append(Paragraph(
        "Cosmo GRR Report",
        ParagraphStyle("T", fontSize=24, textColor=C_TITLE,
                       spaceAfter=2, leading=30, alignment=1)))  # 居中
    els.append(Paragraph(
        f"Report Date: {report.report_date}",
        ParagraphStyle("D", fontSize=10, textColor=C_TITLE,
                       spaceAfter=6, leading=14, alignment=1)))
    els.append(Spacer(1, 4 * mm))

    # ── GRR Information 区块 ──
    els.append(Paragraph(
        "GRR Information:",
        ParagraphStyle("GI", fontSize=11, textColor=C_TITLE,
                       fontName="Helvetica-Bold", spaceAfter=3, leading=16)))
    info_lines = [
        f"* GRR Method: {report.method}",
        f"* Number of Appraisers: {report.num_appraisers}",
        f"* Appraisers: {','.join(report.appraisers)}",
        f"* Number of Units: {report.num_units}",
        f"* Unit Serials: {','.join(report.unit_serials)}",
    ]
    for line in info_lines:
        els.append(Paragraph(
            line,
            ParagraphStyle("IL", fontSize=9, textColor=colors.black,
                           spaceAfter=1, leading=14)))
    els.append(Spacer(1, 6 * mm))

    # ── 汇总表 ──
    # COSMO 格式: # | Item | GRR | Repeat | Reprod | Result (6 列)
    header = ["#", "Item", "GRR", "Repeat", "Reprod", "Result"]
    rows = [header]
    for i, r in enumerate(report.results, 1):
        if r is None:
            continue
        try:
            row = r.to_summary_row()
            grr_s = f"{row.get('GRR', 0):.3f}" if row.get('GRR', 0) is not None else "---"
            repeat_s = f"{row.get('Repeat', 0):.3f}" if row.get('Repeat', 0) is not None else "---"
            reprod_s = f"{row.get('Reprod', 0):.3f}" if row.get('Reprod', 0) is not None else "---"
            result_s = str(row.get('Result', 'N/A'))
            rows.append([
                str(i),
                str(row.get('Item', r.name)),
                grr_s, repeat_s, reprod_s, result_s,
            ])
        except Exception as e:
            print(f"[PDF SUMMARY] 第 {i} 行错误: {e}")
            rows.append([str(i), str(getattr(r, 'name', '?')), "---", "---", "---", "Error"])

    # 列宽: # | Item | GRR | Repeat | Reprod | Result
    # 总量 = 186mm (A4 - 12mm×2 margin)
    cw = [10 * mm, 86 * mm, 22 * mm, 22 * mm, 22 * mm, 24 * mm]
    sum_table = Table(rows, colWidths=cw, repeatRows=1)

    cmds = [
        # 表头 — 白字蓝底
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), C_HEADER_BG),
        # 数据行 — 黑字
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),          # # 列居中
        ("ALIGN", (2, 0), (4, -1), "CENTER"),           # GRR/Repeat/Reprod 居中
        ("ALIGN", (5, 0), (5, -1), "CENTER"),           # Result 居中
        ("ALIGN", (1, 0), (1, -1), "LEFT"),             # Item 列左对齐
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]

    # 交替行背景色（# ～ GRR/Repeat/Reprod 列，Result 列单独处理）
    for i in range(1, len(rows)):
        bg = C_ROW_ALT if i % 2 == 0 else C_ROW_WHITE
        cmds.append(("BACKGROUND", (0, i), (4, i), bg))

    # Result 列背景色 + 字体颜色 (第5列，index 5)
    for i, r in enumerate(report.results, 1):
        bg = _rating_bg(r.rating)
        fg = _rating_color(r.rating)
        cmds.append(("BACKGROUND", (5, i), (5, i), bg))
        cmds.append(("TEXTCOLOR", (5, i), (5, i), fg))
        cmds.append(("FONTNAME", (5, i), (5, i), "Helvetica-Bold"))

    # GRR 列 (第2列，index 2) 颜色显示逻辑：进入 Marginal (GRR>20) 才标
    for i, r in enumerate(report.results, 1):
        grr_val = r.grr_study
        if grr_val > 30:
            # Poor — 红色背景 + 红字加粗
            cmds.append(("BACKGROUND", (2, i), (2, i), colors.HexColor("#fadbd8")))
            cmds.append(("TEXTCOLOR", (2, i), (2, i), C_POOR))
            cmds.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))
        elif grr_val > 20:
            # Marginal — 橙色背景 + 橙字加粗
            cmds.append(("BACKGROUND", (2, i), (2, i), colors.HexColor("#fdebd0")))
            cmds.append(("TEXTCOLOR", (2, i), (2, i), C_MARGINAL))
            cmds.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))

    sum_table.setStyle(TableStyle(cmds))
    els.append(sum_table)

    return els


# ══════════════════════════════════════════════════════════════════
# 详情页 — 4 图表
# ══════════════════════════════════════════════════════════════════

def _make_detail_charts(result: GrrResult, dm: pd.DataFrame):
    """生成 COSMO 风格 4 图表 (2×2 布局)"""
    # 从 data_matrix 重建原始数据
    records = []
    for part in dm.index:
        for col in dm.columns:
            val = dm.loc[part, col]
            if pd.notna(val) and "." in str(col):
                # 使用 rsplit 从右侧分割，防止 appraiser 值含点 (如 "7.0.0" → ["7.0", "0"])
                parts = col.rsplit(".", 1)
                op_str, trial_str = parts[0], parts[1]
                # trial 总是数字；operator 可能是文本（如 station_id="STN-A1"）或数字
                try:
                    trial_int = int(float(trial_str))
                except (ValueError, TypeError):
                    trial_int = 0
                try:
                    op_repr = int(float(op_str))  # 数字型 operator
                except (ValueError, TypeError):
                    op_repr = op_str  # 文本型 operator — 保持原样
                records.append({
                    "operator": str(op_repr),        # 统一为字符串避免 int/str 混用
                    "operator_display": str(op_repr),
                    "part": str(part),
                    "trial": trial_int,
                    "value": float(val),
                })
    raw = pd.DataFrame(records)

    # 没有有效数据 → 返回 None，调用方跳过图表
    if len(raw) == 0:
        print(f"[CHART] WARNING: No records rebuilt for {result.name}")
        print(f"         dm.shape={dm.shape}, columns={list(dm.columns)[:5]}...")
        print(f"         NaN count={dm.isna().sum().sum()}")
        return None

    operators = sorted(raw["operator"].unique(), key=lambda x: str(x))
    parts_list = sorted(raw["part"].unique(), key=lambda x: str(x))
    n_ops = len(operators)
    n_parts = len(parts_list)

    # 零件标签：优先显示完整 SN，过长时再截取
    short_labels = []
    for p in parts_list:
        s = str(p)
        if len(s) > 30:
            short_labels.append(s[:15] + ".." + s[-13:])
        elif len(s) > 24:
            short_labels.append(s[:12] + ".." + s[-10:])
        else:
            short_labels.append(s)  # 优先显示完整 SN

    # 计算所有数据的 y 范围，为散点图统一添加 20% 边距（匹配 COSMO 风格）
    all_vals = raw["value"].values
    y_min, y_max = all_vals.min(), all_vals.max()
    y_range = y_max - y_min
    y_pad = y_range * 0.2 if y_range > 0 else 0.02
    y_lo = y_min - y_pad
    y_hi = y_max + y_pad

    try:
        fig, axes = plt.subplots(2, 2, figsize=(9, 7.8))
        fig.subplots_adjust(hspace=0.55, wspace=0.35, left=0.09, right=0.96, top=0.92, bottom=0.20)

        # ── 1. Scatter by Part (左上) ──
        ax = axes[0, 0]
        for pi, part in enumerate(parts_list):
            vals = raw[raw["part"] == part]["value"].values
            if len(vals) == 0:
                continue
            x_jitter = np.random.uniform(-0.2, 0.2, len(vals)) if len(vals) > 1 else [0]
            ax.scatter([pi] * len(vals) + x_jitter, vals,
                       alpha=0.6, s=18, color=CHART_COLORS[0], edgecolors="white", linewidth=0.3)

        # 每个零件的均值线
        part_means = [raw[raw["part"] == p]["value"].mean() for p in parts_list]
        ax.plot(range(n_parts), part_means, color="#e74c3c", linewidth=2, marker="s",
                markersize=5, markerfacecolor="white", markeredgecolor="#e74c3c",
                markeredgewidth=1.2, zorder=5, label="Mean")

        ax.set_title("Scatter by Part", fontsize=8, fontweight="bold", color=MPL_TITLE, pad=3)
        ax.set_ylabel(result.name, fontsize=6.5, color=MPL_TITLE)  # 测项名称
        ax.set_ylim(y_lo, y_hi)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(5))  # 刻度间距=5
        ax.set_xticks(range(n_parts))
        ax.set_xticklabels(short_labels, fontsize=6, rotation=0, ha="center")
        ax.tick_params(axis="y", labelsize=6.5)
        # 自动格式：根据数据范围自动选择小数位数（修复小数值显示 0.00 的问题）
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.get_major_formatter().set_useOffset(False)
        ax.legend(fontsize=5.5, loc="upper right", framealpha=0.8)
        ax.set_xlabel("Part", fontsize=6.5, color=MPL_TITLE)
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.set_axisbelow(True)

        # ── 2. Scatter by Appraiser (右上) ──
        ax = axes[0, 1]
        for oi, op in enumerate(operators):
            vals = raw[raw["operator"] == op]["value"].values
            if len(vals) == 0:
                continue
            x_jitter = np.random.uniform(-0.2, 0.2, len(vals)) if len(vals) > 1 else [0]
            ax.scatter([oi] * len(vals) + x_jitter, vals,
                       alpha=0.6, s=18, color=CHART_COLORS[oi % len(CHART_COLORS)],
                       edgecolors="white", linewidth=0.3)

        op_means = [raw[raw["operator"] == o]["value"].mean() for o in operators]
        ax.plot(range(n_ops), op_means, color="#e74c3c", linewidth=2, marker="s",
                markersize=5, markerfacecolor="white", markeredgecolor="#e74c3c",
                markeredgewidth=1.2, zorder=5, label="Mean")

        ax.set_title("Scatter by Appraiser", fontsize=8, fontweight="bold", color=MPL_TITLE, pad=3)
        ax.set_ylabel(result.name, fontsize=6.5, color=MPL_TITLE)  # 测项名称
        ax.set_ylim(y_lo, y_hi)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(5))  # 刻度间距=5
        ax.set_xticks(range(n_ops))
        ax.set_xticklabels([str(o) for o in operators], fontsize=6.5)
        ax.tick_params(axis="y", labelsize=6.5)
        # 自动格式：根据数据范围自动选择小数位数
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.get_major_formatter().set_useOffset(False)
        ax.legend(fontsize=5.5, loc="upper right", framealpha=0.8)
        ax.set_xlabel("Appraiser", fontsize=6.5, color=MPL_TITLE)
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.set_axisbelow(True)

        # ── 3. Scatter by Part and Appraiser (左下) ──
        ax = axes[1, 0]
        for oi, op in enumerate(operators):
            line_vals = []
            for part in parts_list:
                cell = raw[(raw["part"] == part) & (raw["operator"] == op)]["value"]
                line_vals.append(cell.mean() if len(cell) > 0 else np.nan)
            ax.plot(range(n_parts), line_vals,
                    marker="o", markersize=4, linewidth=1.5,
                    color=CHART_COLORS[oi % len(CHART_COLORS)], label=str(op),
                    markerfacecolor="white", markeredgecolor=CHART_COLORS[oi % len(CHART_COLORS)],
                    markeredgewidth=1)

        ax.set_title("Scatter by Part and Appraiser", fontsize=8, fontweight="bold",
                     color=MPL_TITLE, pad=3)
        ax.set_ylabel(result.name, fontsize=6.5, color=MPL_TITLE)  # 测项名称
        ax.set_ylim(y_lo, y_hi)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(5))  # 刻度间距=5
        ax.set_xticks(range(n_parts))
        ax.set_xticklabels(short_labels, fontsize=6, rotation=0, ha="center")
        ax.tick_params(axis="y", labelsize=6.5)
        # 自动格式：根据数据范围自动选择小数位数
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.get_major_formatter().set_useOffset(False)
        ax.legend(fontsize=5.5, loc="upper right", framealpha=0.8, ncol=2)
        ax.set_xlabel("Part", fontsize=6.5, color=MPL_TITLE)
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.set_axisbelow(True)

        # ── 4. Contribution (右下) ──
        ax = axes[1, 1]
        labels = ["Equipment", "Appraiser", "Interaction", "Part", "NdR"]
        raw_values = [result.pct_ev, result.pct_av, result.pct_iv, result.pct_pv, result.pct_rr]
        # 显示时 clamp 负值到 0（COSMO 风格：负方差分量不显示）
        values = [max(v, 0) for v in raw_values]

        y_pos = range(len(labels))
        bars = ax.barh(y_pos, values, color="#3498db", height=0.55,  # 统一蓝色（匹配 COSMO 原版）
                       edgecolor="white", linewidth=0.5)

        # 在条形图右侧标注百分比（始终显示，包括 0 值）
        for i, (v, bar) in enumerate(zip(values, bars)):
            ax.text(max(v, 0) + max(values) * 0.02 + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"{v:.2f}%", va="center", fontsize=6.5, fontweight="bold",
                    color=MPL_TITLE)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=6.5)
        ax.set_title("Contribution", fontsize=8, fontweight="bold", color=MPL_TITLE, pad=3)
        ax.set_xlabel("% of Total Variance", fontsize=6.5)
        ax.xaxis.set_major_locator(mticker.MultipleLocator(10))  # 刻度间距=10（匹配 COSMO 原版）
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
        ax.tick_params(axis="x", labelsize=6)
        ax.invert_yaxis()
        ax.set_xlim(0, max(max(values) * 1.15, 105))
        ax.grid(True, axis="x", alpha=0.25, linestyle="--")
        ax.set_axisbelow(True)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf

    except Exception as e:
        print(f"[CHART] ERROR generating charts for {result.name}: {e}")
        import traceback
        traceback.print_exc()
        plt.close("all")
        return None


# ══════════════════════════════════════════════════════════════════
# 详情页 — 构建整页内容
# ══════════════════════════════════════════════════════════════════

def _build_detail(report: GrrReport, result: GrrResult, idx: int) -> list:
    els = []

    dm = result.data_matrix
    if dm.empty:
        return els

    # ── 页面总可用宽度 (A4 - 左右边距 12mm×2 = 186mm) ──
    PAGE_W = 186 * mm

    # ── 标题行 ──
    ul_str = f"{result.ul:.3f}" if result.ul != float('inf') else "---"
    ll_str = f"{result.ll:.3f}" if result.ll != float('-inf') else "---"
    els.append(Paragraph(
        f"{result.name}  (UL:{ul_str}  LL:{ll_str})",
        ParagraphStyle("IT", fontSize=10, textColor=colors.black,
                       fontName="Helvetica-Bold", spaceAfter=6, leading=14)))
    els.append(Spacer(1, 2 * mm))

    # ── 4 图表 (2×2) — 保持原比例，宽度填满页面 ──
    chart_buf = _make_detail_charts(result, dm)
    if chart_buf:
        # figsize=(9,7.2) → 宽高比 = 4:5
        chart_h = PAGE_W * (7.2 / 9.0)
        els.append(Image(chart_buf, width=PAGE_W, height=chart_h))
        els.append(Spacer(1, 5 * mm))
    else:
        # 图表生成失败时显示提示信息
        els.append(Paragraph(
            "<i>Charts could not be generated for this item. "
            "Check console output for details.</i>",
            ParagraphStyle("NC", fontSize=8, textColor=C_GRAY,
                           spaceAfter=4, leading=12)))
        els.append(Spacer(1, 3 * mm))

    # ── Results 区块 (COSMO 风格: 三个独立紧凑表格) ──
    els.append(Paragraph(
        "Results:", ParagraphStyle("RL", fontSize=9, fontName="Helvetica-Bold",
                                   textColor=colors.black, spaceAfter=3, leading=13)))

    # 共享样式：紧凑网格表格
    _grid_style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]

    # Table 1: grr | repeatability | reproducibility
    t1_data = [
        ["grr", "repeatability", "reproducibility"],
        [f"{result.grr_study:.3f}", f"{result.repeat_study:.3f}", f"{result.reprod_study:.3f}"],
    ]
    t1_w = (PAGE_W - 14 * mm) / 3
    t1 = Table(t1_data, colWidths=[t1_w] * 3)
    t1s = list(_grid_style)
    t1s += [("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t1.setStyle(TableStyle(t1s))
    els.append(t1)
    els.append(Spacer(1, 3 * mm))

    # Table 2: rr | ev | av | iv | pv | tv
    t2_data = [
        ["rr", "ev", "av", "iv", "pv", "tv"],
        [f"{result.rr:.3f}", f"{result.ev:.3f}", f"{result.av:.3f}",
         f"{result.iv:.3f}", f"{result.pv:.3f}", f"{result.tv:.3f}"],
    ]
    t2_w = (PAGE_W - 14 * mm) / 6
    t2 = Table(t2_data, colWidths=[t2_w] * 6)
    t2s = list(_grid_style)
    t2s += [("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t2.setStyle(TableStyle(t2s))
    els.append(t2)
    els.append(Spacer(1, 3 * mm))

    # Table 3: %rr | %ev | %av | %iv | %pv
    t3_data = [
        ["%rr", "%ev", "%av", "%iv", "%pv"],
        [f"{result.pct_rr:.3f}", f"{result.pct_ev:.3f}",
         f"{result.pct_av:.3f}", f"{result.pct_iv:.3f}",
         f"{result.pct_pv:.3f}"],
    ]
    t3_w = (PAGE_W - 14 * mm) / 5
    t3 = Table(t3_data, colWidths=[t3_w] * 5)
    t3s = list(_grid_style)
    t3s += [("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t3.setStyle(TableStyle(t3s))
    els.append(t3)
    els.append(Spacer(1, 5 * mm))

    # ── Data 矩阵 ──
    # 格式: Unit | Op1 Op1 Op1 | Op2 Op2 Op2 ...
    #             T0  T1  T2    T0  T1  T2
    operators = sorted(set(c.rsplit(".", 1)[0] for c in dm.columns),
                       key=_op_sort_key)
    trials_per_op = []
    for op in operators:
        cols = sorted([c for c in dm.columns if c.startswith(f"{op}.")],
                      key=lambda x: int(x.rsplit(".", 1)[1]))
        trials_per_op.append([c.rsplit(".", 1)[1] for c in cols])

    # 计算数据列总数
    n_data_cols = sum(len(t) for t in trials_per_op)
    # Unit 列宽根据内容长度动态计算
    # 最长 Unit 名一般在 10~18 字符，按 3mm/字符估算，最小 35mm 最大 70mm
    max_unit_len = max((len(str(p)) for p in dm.index), default=10)
    unit_col_w = min(max(max_unit_len * 2.2 * mm, 35 * mm), 70 * mm)
    # 剩余宽度均分给数据列
    data_col_w = (PAGE_W - unit_col_w) / n_data_cols if n_data_cols > 0 else 15 * mm

    # 第一行: Unit + Operator 标签 (合并相同 op 的格)
    op_row = ["Unit"]
    for op, trials in zip(operators, trials_per_op):
        op_row.extend([op] * len(trials))

    # 第二行: 空白 + Trial 编号
    trial_row = [""]
    for trials in trials_per_op:
        trial_row.extend(trials)

    # 数据行
    data_rows = []
    for part_name, row_data in dm.iterrows():
        vals = []
        for col_name in dm.columns:
            v = row_data[col_name]
            vals.append(f"{v:.4f}" if pd.notna(v) else "")
        data_rows.append([str(part_name)] + vals)

    matrix_rows = [op_row, trial_row] + data_rows
    m_cw = [unit_col_w] + [data_col_w] * n_data_cols

    # Operator 列合并 SPAN
    op_spans = []
    col_idx = 1
    for op, trials in zip(operators, trials_per_op):
        n_t = len(trials)
        if n_t > 1:
            op_spans.append(("SPAN", (col_idx, 0), (col_idx + n_t - 1, 0)))
        col_idx += n_t

    # ── "Data:" 标签 ──
    els.append(Paragraph(
        "Data:", ParagraphStyle("DL", fontSize=9, fontName="Helvetica-Bold",
                                textColor=colors.black, spaceAfter=3, leading=13)))

    mtable = Table(matrix_rows, colWidths=m_cw)
    m_style = [
        # 表头行 — 黑字白底，加粗
        ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        # 数据行
        ("FONTNAME", (0, 2), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    # 添加 Operator SPAN
    m_style.extend(op_spans)
    mtable.setStyle(TableStyle(m_style))
    els.append(mtable)

    return els


# ══════════════════════════════════════════════════════════════════
# 一致性报告 PDF
# ══════════════════════════════════════════════════════════════════

def generate_consistency_pdf(report: GrrReport, output_path: str):
    """生成一致性报告 PDF — 展示每个评价人对每个零件的测量一致性（极差）"""
    from reportlab.platypus import KeepTogether

    total_pages = 1 + len(report.results)

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.black)
        page_w, page_h = A4
        x = page_w - 12 * mm
        y = 8 * mm
        canvas.drawRightString(x, y,
            f"Page {canvas.getPageNumber()}/{total_pages}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=12 * mm, bottomMargin=18 * mm,
        leftMargin=12 * mm, rightMargin=12 * mm,
    )
    all_els = []

    # ── 标题 ──
    all_els.append(Paragraph(
        "Cosmo Consistency Report",
        ParagraphStyle("CT", fontSize=22, textColor=C_TITLE,
                       spaceAfter=2, leading=28, alignment=1)))
    all_els.append(Paragraph(
        f"Method: {report.method}  |  Appraisers: {report.num_appraisers}  |  Units: {report.num_units}  |  Trials: {report.num_trials}",
        ParagraphStyle("CS", fontSize=9, textColor=C_TITLE,
                       spaceAfter=2, leading=14, alignment=1)))
    all_els.append(Paragraph(
        f"Report Date: {report.report_date}",
        ParagraphStyle("CD", fontSize=9, textColor=colors.black,
                       spaceAfter=6, leading=14, alignment=1)))
    all_els.append(Spacer(1, 3 * mm))

    # ── 每个测量项的一致性表格 ──
    for ri, result in enumerate(report.results, 1):
        dm = result.data_matrix
        if dm.empty:
            continue

        # 标题
        all_els.append(Paragraph(
            f"{ri}. {result.name}",
            ParagraphStyle("CI", fontSize=11, textColor=C_TITLE,
                           fontName="Helvetica-Bold", spaceAfter=4, leading=16)))

        # 从 data_matrix 的列名解析 operator.trial 格式
        cols = list(dm.columns)
        ops = sorted(set(str(c).split(".")[0] for c in cols), key=_op_sort_key)
        parts = list(dm.index)
        n_trials = len(cols) // len(ops) if ops else 0

        # 表头: Part | Op1 Range | Op1 Consistency | Op2 Range | Op2 Consistency | ...
        header = ["Part"]
        for op in ops:
            header.extend([f"Op {op}", "Status"])

        rows = [header]
        status_counts = {"OK": 0, "Inconsistent": 0}

        for part in parts:
            row = [str(part)]
            for op in ops:
                # 提取该 operator 的所有 trial 值
                op_cols = [c for c in cols if str(c).startswith(f"{op}.")]
                vals = []
                for c in op_cols:
                    v = dm.loc[part, c]
                    if pd.notna(v):
                        try:
                            vals.append(float(v))
                        except (ValueError, TypeError):
                            pass
                if vals:
                    r = max(vals) - min(vals)
                    # 一致性阈值: 极差 <= 0.1 * tolerance 或极差 <= 10% of mean
                    tol = result.tolerance if result._has_spec_limits else None
                    if tol and tol > 0:
                        threshold = tol * 0.1
                        ok = r <= threshold
                    else:
                        mean_v = sum(vals) / len(vals)
                        threshold = abs(mean_v) * 0.1 if mean_v != 0 else 0.1
                        ok = r <= threshold
                    status = "OK" if ok else "Inconsistent"
                    status_counts[status] = status_counts.get(status, 0) + 1
                else:
                    r = None
                    status = "N/A"

                r_s = f"{r:.4f}" if r is not None else "---"
                row.extend([r_s, status])
            rows.append(row)

        # 列宽
        n_op_cols = len(ops) * 2
        part_w = max(30 * mm, 186 * mm / (n_op_cols + 1) * 1.5)
        op_w = (186 * mm - part_w) / n_op_cols
        cw = [part_w] + [op_w] * n_op_cols

        ctable = Table(rows, colWidths=cw, repeatRows=1)
        c_cmds = [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 0), (-1, 0), C_HEADER_BG),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("LEADING", (0, 0), (-1, -1), 11),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]

        # 交替行 + Status 列颜色
        for i in range(1, len(rows)):
            bg = C_ROW_ALT if i % 2 == 0 else C_ROW_WHITE
            c_cmds.append(("BACKGROUND", (0, i), (0, i), bg))
            for j, op in enumerate(ops):
                col_idx = j * 2 + 1
                status_col = col_idx + 1
                status_val = rows[i][status_col]
                c_cmds.append(("BACKGROUND", (col_idx, i), (col_idx, i), bg))
                if status_val == "OK":
                    c_cmds.append(("BACKGROUND", (status_col, i), (status_col, i),
                                   colors.HexColor("#d5f5e3")))
                    c_cmds.append(("TEXTCOLOR", (status_col, i), (status_col, i), C_EXCELLENT))
                    c_cmds.append(("FONTNAME", (status_col, i), (status_col, i), "Helvetica-Bold"))
                elif status_val == "Inconsistent":
                    c_cmds.append(("BACKGROUND", (status_col, i), (status_col, i),
                                   colors.HexColor("#fadbd8")))
                    c_cmds.append(("TEXTCOLOR", (status_col, i), (status_col, i), C_POOR))
                    c_cmds.append(("FONTNAME", (status_col, i), (status_col, i), "Helvetica-Bold"))
                else:
                    c_cmds.append(("BACKGROUND", (status_col, i), (status_col, i), bg))

        ctable.setStyle(TableStyle(c_cmds))
        all_els.append(ctable)

        # 统计摘要
        total = status_counts["OK"] + status_counts["Inconsistent"]
        ok_pct = (status_counts["OK"] / total * 100) if total > 0 else 0
        all_els.append(Paragraph(
            f"Summary: <b>{status_counts['OK']}</b> OK  |  <b>{status_counts['Inconsistent']}</b> Inconsistent  (Consistency Rate: {ok_pct:.1f}%)",
            ParagraphStyle("CSU", fontSize=8, textColor=colors.black,
                           spaceAfter=8, leading=14)))

        if ri < len(report.results):
            all_els.append(Spacer(1, 2 * mm))

    doc.build(all_els, onFirstPage=_footer, onLaterPages=_footer)
    print(f"\n  Consistency Report generated: {output_path}")


# ══════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════

def generate_pdf(report: GrrReport, output_path: str):
    total_pages = 1 + len(report.results)

    def _footer(canvas, doc):
        """在每页底部绘制页脚"""
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.black)
        page_w, page_h = A4
        x = page_w - 12 * mm   # 右对齐
        y = 8 * mm             # 距离底部8mm
        canvas.drawRightString(x, y,
            f"Page {canvas.getPageNumber()}/{total_pages}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=12 * mm, bottomMargin=18 * mm,  # 底部预留页脚空间
        leftMargin=12 * mm, rightMargin=12 * mm,
    )
    all_els = []

    # ── 汇总页 ──
    all_els.extend(_build_summary(report))

    # ── 每个测量项一页 ──
    for i, result in enumerate(report.results, 2):
        all_els.append(PageBreak())
        try:
            detail_els = _build_detail(report, result, i)
            if not detail_els:
                # 无内容（data_matrix 为空）→ 显示提示
                detail_els.append(Paragraph(
                    f"<b>{result.name}</b><br/>No data matrix available for detail view.",
                    ParagraphStyle("ED", fontSize=9, textColor=C_GRAY, spaceAfter=4, leading=14)))
            all_els.extend(detail_els)
        except Exception as e:
            import traceback
            print(f"[PDF DETAIL] {result.name} 详情页错误: {e}")
            traceback.print_exc()
            all_els.append(Paragraph(
                f"<b>{result.name}</b><br/><font color='red'>Error generating detail page: {e}</font>",
                ParagraphStyle("EE", fontSize=9, textColor=C_GRAY, spaceAfter=4, leading=14)))

    doc.build(all_els, onFirstPage=_footer, onLaterPages=_footer)
    print(f"\n  Report generated: {output_path}")
    print(f"  Total {total_pages} pages ({len(report.results)} measurement items)")
