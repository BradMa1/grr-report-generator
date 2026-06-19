#!/usr/bin/env python3
"""
COSMO GRR GUI — v2.5.2e 使用 COSMO 原生后端
使用 tkinter + ttk.Notebook 实现 Load / Test Items / Analysis / Results 四个视图
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import json
import csv
import glob
import re
import datetime
import pandas as pd
import numpy as np

# 新 GRR 引擎
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
from grr_core import compute_grr_anova, compute_grr_range, GrrResult, GrrReport

# ════════════════════════════════════════════════════════════════
#  暖色纸纹主题 — 仿纸质界面，柔和护眼
# ════════════════════════════════════════════════════════════════
# 主背景 — 暖木色（仿桌面/写字板）
BG_MAIN     = "#C8BCAA"
# 面板/卡片 — 暖白纸色
BG_PANEL    = "#F7F2EA"
# 侧栏 — 深暖褐色
BG_SIDEBAR  = "#B8AC98"
# 标题/强调色 — 暖棕
C_TITLE     = "#5C3D1E"
# 主文字色 — 暖黑棕
FG_DARK     = "#2A2218"
# 辅助文字色
FG_MUTED    = "#7A6A52"
# 按钮基础色
BTN_BG      = "#DED4C2"
BTN_ACTIVE  = "#CEC2AE"
# 输入框背景
ENTRY_BG    = "#FAF7F0"
# 列表背景
LISTBOX_BG  = "#FAF7F0"
# 选中高亮色
HIGHLIGHT   = "#3A6CA5"
# 边框色
BORDER_CLR  = "#B8AA90"

# 结果表格标签色（按用户规范）
# ≤10% → 绿色   10-20% → 黄色   20-30% → 橙色   >30% → 红色
TAG_EXCELLENT = "#ABEBC6"  # 中绿底 + 深绿字  (≤10%)
TAG_GOOD      = "#F9E79F"  # 中黄底 + 暗黄字  (10-20%)
TAG_MARGINAL  = "#F5CBA7"  # 中橙底 + 深橙字  (20-30%)
TAG_POOR      = "#F1948A"  # 中红底 + 深红字  (>30%)

# 字体
FONT_UI    = ("Segoe UI", 10)
FONT_LABEL = ("Segoe UI", 10)
FONT_BTN   = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 10, "bold")
FONT_MONO  = ("Consolas", 9)

# ════════════════════════════════════════════════════════════════
#  语言翻译表 — English → 简体中文
# ════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    # 菜单
    "Load": "加载CSV",
    "Test Items": "测试项目",
    "Analysis": "分析设置",
    "Results": "分析结果",

    # 右侧面板
    "Method:": "分析方法：",
    "Output Format:": "输出格式：",
    "P/T (%Tol)": "P/T (%公差)",
    "Study Var (%TV)": "Study Var (%TV)",
    "Study Const:": "Study Const：",
    "6.0 (COSMO)": "6.0 (COSMO)",
    "5.15 (AIAG)": "5.15 (AIAG)",
    "Run": "运行分析",
    "Export as CSV": "导出CSV",
    "Export as PDF": "导出PDF",
    "Consistency:": "一致性：",
    "Export Consistency\nReport PDF": "导出一致性\n报告PDF",

    # Load 标签页
    "CSV Path:": "CSV路径：",
    "Load CSV": "加载CSV",
    "Part Column": "零件列",
    "Appraiser Column(s)": "检验员列",
    "Order by": "排序",
    "Apply Filter": "应用筛选",
    "Auto Bin\nAppraisers": "自动分箱\n检验员",
    "Data Preview": "数据预览",
    "Use current settings": "使用当前设置",
    "Load Limits from CSV": "从CSV加载规格限",
    "COSMO row format (UL/LL in first 3 rows)": "COSMO格式（前三行UL/LL）",
    "Outcome Settings": "结果项设置",
    "JSON to CSV": "JSON转CSV",
    "Dashboard Connection": "仪表盘连接",
    "Import Settings": "导入设置",
    "Export Settings": "导出设置",
    "Import Limits": "导入规格限",
    "Export Limits": "导出规格限",

    # Test Items 标签页
    "Filter:": "筛选：",
    "Clear Filter": "清除筛选",
    "原始数据": "Source",
    "已选测项": "Loaded",
    "Source": "原始数据",
    "Loaded": "已选测项",
    "Item": "项目",
    "UL": "上限",
    "LL": "下限",
    "UL_new": "上限(新)",
    "LL_new": "下限(新)",
    "全部添加": "Add All",
    "添加 >>>": "Add >>>",
    "<<< 移除": "<<< Remove",
    "全部移除": "Remove All",
    "Add All": "全部添加",
    "Add >>>": "添加 >>>",
    "<<< Remove": "<<< 移除",
    "Remove All": "全部移除",

    # Analysis 标签页
    "(+) Add": "(+) 添加",
    "Select All": "全选",
    "Clear": "清除",
    "Apply Selection": "应用选择",
    "Clear Selection": "清除选择",
    "Select Data for Analysis": "选择分析数据",
    "GRR Method": "GRR方法",
    "Autobin Settings": "自动分箱设置",
    "Number of units:": "Units数量：",
    "Number of appraisers:": "Appraiser数量：",
    "Number of trials:": "Trials数量：",
    "GRR Settings": "GRR设置",
    "Sigma:": "Sigma：",
    "Apply All Settings": "应用所有设置",
    "GRR": "GRR",

    # Results 标签页
    "Export as CSV": "导出CSV",
    "Export as PDF": "导出PDF",
    "Show %Variance": "显示%方差",
    "Show %Tolerance": "显示%公差",
    "#": "#",
    "%rr": "%rr",
    "%ev": "%ev",
    "%av": "%av",
    "%iv": "%iv",
    "%pv": "%pv",
    "rr": "rr",
    "ev": "ev",
    "av": "av",
    "iv": "iv",
    "pv": "pv",
    "tv": "tv",
    "repeat_study": "repeat(P/T)",
    "reprod_study": "reprod(P/T)",
    "grr_study": "GRR(P/T)",
    "ndc": "ndc",
    "pct_rr": "%rr",
    "pct_ev": "%ev",
    "pct_av": "%av",
    "pct_iv": "%iv",
    "pct_pv": "%pv",

    # 弹出对话框
    "Load GRR State": "加载GRR状态",
    "Save GRR State": "保存GRR状态",
    "State files (*.json)": "状态文件 (*.json)",

    # 状态信息
    "No CSV": "未选择CSV",
    "No Results": "无结果",
    "Save CSV": "保存CSV",
    "CSV": "CSV",

    # Appraiser column 候选
    "operator_id": "检验员ID",
    "appraiser_id": "检验员ID",

    # 语言切换
    "🌐 Language": "🌐 语言",
    "English": "English",
    "简体中文": "简体中文",
    "Language": "语言",
    "Select Language": "选择语言",

    # Part column 候选
    "dut_id": "零件ID",
    "part_id": "零件ID",

    # ═══ 专用翻译（不重复定义已在上面出现的条目）
    "Base Data": "基础数据",
    "Selected Data": "选中数据",
    "Units:": "Units：",
    "Appraisers:": "Appraisers：",
    "Trials:": "Trials：",
    "Columns:": "列数：",
    "Test Items:": "测试项：",
    "Select Units": "选择Units",
    "Select Appraisers": "选择Appraisers",
    "Settings applied.": "设置已应用。",
    "GRR complete (ANOVA):": "GRR完成 (ANOVA)：",
    "GRR complete (Range):": "GRR完成 (Range)：",
    "Please run GRR analysis first.": "请先运行GRR分析。",
    "Please load a CSV file first.": "请先加载CSV文件。",
    "No data after filtering.": "筛选后无数据。",
    "Filter applied:": "筛选已应用：",
    "Loaded:": "已加载：",
    "Running GRR analysis (": "正在运行GRR分析 (",
    "Generating PDF...": "正在生成PDF...",
    "Generating Consistency Report PDF...": "正在生成一致性报告PDF...",
    "OK": "确定",
    "Cancel": "取消",
    "Done": "完成",
    "Error": "错误",
    "Warning": "警告",
    "Information": "信息",
    "Save": "保存",
    "Open": "打开",
    "Dashboard connection setting": "仪表盘连接设置",
    "bigbird ip:": "bigbird IP：",
    "bigbird port:": "bigbird 端口：",
    "Product Family:": "产品系列：",
    "Product Type:": "产品类型：",
    "Input Product:": "输入产品：",
    "grr": "GRR",
    "repeatability": "重复性",
    "reproducibility": "再现性",
}

# 反向翻译表（中文→英文），自动生成
TRANSLATIONS_REV = {v: k for k, v in TRANSLATIONS.items()}

class _TkStyle:
    """工厂方法 — 统一创建带配色的小部件"""

    @staticmethod
    def label(parent, text="", **kw):
        defaults = dict(bg=BG_PANEL, fg=FG_DARK, font=FONT_LABEL, anchor=tk.W)
        defaults.update(kw)
        return tk.Label(parent, text=text, **defaults)

    @staticmethod
    def button(parent, text="", **kw):
        defaults = dict(bg=BTN_BG, fg=FG_DARK, font=FONT_BTN,
                         relief=tk.RAISED, bd=1, padx=8, pady=2,
                         activebackground=BTN_ACTIVE, activeforeground=FG_DARK)
        defaults.update(kw)
        return tk.Button(parent, text=text, **defaults)

    @staticmethod
    def frame(parent, **kw):
        defaults = dict(bg=BG_PANEL)
        defaults.update(kw)
        return tk.Frame(parent, **defaults)

    @staticmethod
    def entry(parent, **kw):
        defaults = dict(bg=ENTRY_BG, fg=FG_DARK, font=FONT_UI,
                         relief=tk.SUNKEN, bd=1, insertbackground=FG_DARK)
        defaults.update(kw)
        return tk.Entry(parent, **defaults)

    @staticmethod
    def listbox(parent, **kw):
        defaults = dict(bg=LISTBOX_BG, fg=FG_DARK, font=FONT_UI,
                         relief=tk.SUNKEN, bd=1, selectmode=tk.BROWSE,
                         exportselection=False, selectbackground=HIGHLIGHT,
                         selectforeground="white")
        defaults.update(kw)
        return tk.Listbox(parent, **defaults)

    @staticmethod
    def checkbutton(parent, text="", **kw):
        defaults = dict(bg=BG_PANEL, fg=FG_DARK, font=FONT_LABEL,
                         activebackground=BG_PANEL, activeforeground=FG_DARK,
                         selectcolor=BG_PANEL)
        defaults.update(kw)
        return tk.Checkbutton(parent, text=text, **defaults)

    @staticmethod
    def radiobutton(parent, text="", **kw):
        defaults = dict(bg=BG_PANEL, fg=FG_DARK, font=FONT_LABEL,
                         activebackground=BG_PANEL, activeforeground=FG_DARK,
                         selectcolor=BG_PANEL)
        defaults.update(kw)
        return tk.Radiobutton(parent, text=text, **defaults)

    @staticmethod
    def separator(parent):
        return tk.Frame(parent, bg=BORDER_CLR, height=1)


# ── 工作目录 ─────────────────────────────────────────
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)


# ═══════════════════════════════════════════════════════
#  主窗口
# ═══════════════════════════════════════════════════════
class CosmoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cosmo v2.5.2e")
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)
        self.geometry("1200x720")
        self.minsize(960, 560)

        # ── 共享状态 ──
        self._csv_path        = tk.StringVar()
        self._use_current     = tk.BooleanVar(value=False)
        self._load_limits     = tk.BooleanVar(value=True)
        self._auto_bin        = tk.BooleanVar(value=False)
        self._cosmo_row_format = tk.BooleanVar(value=False)  # COSMO 行格式（UL/LL 作为前3行元数据）
        self._method_var      = tk.StringVar(value="ANOVA")
        self._grr_method_var  = tk.StringVar(value="ANOVA")
        self._sigma_var       = tk.StringVar(value="")
        self._show_mode       = tk.StringVar(value="%Variance")
        self._output_format_var = tk.StringVar(value="tol")
        self._study_const_var   = tk.StringVar(value="6.0")
        self._report          = None
        self._df              = None
        self._part_col        = None
        self._appr_col        = None
        self._selected_items  = []
        self._all_items       = []
        self._sel_units       = []
        self._sel_appraisers  = []
        self._item_limits     = {}   # {item_name: (ul, ll)}
        self._ti_loaded_data  = []   # [(item_name, ul, ll)] 已选测项数据（不受筛选影响）
        self._ul_filter_active = False
        self._ll_filter_active = False
        self._lang            = "en"  # 当前语言
        self._lang_btn        = None  # 语言切换按钮引用

        self._build_menu()
        self._build_right_panel()
        self._build_notebook()

    # ══════════════════════════════════════════════════
    #  语言切换
    # ══════════════════════════════════════════════════
    def _tr(self, text):
        """翻译文本。英文直接返回，中文查表"""
        if self._lang == "en":
            return text
        return TRANSLATIONS.get(text, text)

    def _toggle_language(self):
        """切换语言并刷新所有控件文字"""
        self._lang = "zh" if self._lang == "en" else "en"
        self._refresh_language()

    def _refresh_language(self):
        """递归遍历所有子控件并更新文字"""
        def _walk(w):
            try:
                # 更新 Label / Button / Checkbutton / Radiobutton / Menu
                current = w.cget("text") if hasattr(w, "cget") and w.winfo_exists() else None
            except Exception:
                current = None

            if current is not None and isinstance(current, str) and current.strip():
                # 决定方向：中文→英文 或 英文→中文
                if self._lang == "zh":
                    new_text = TRANSLATIONS.get(current, current)
                else:
                    new_text = TRANSLATIONS_REV.get(current, current)
                if new_text != current:
                    try:
                        w.configure(text=new_text)
                    except Exception:
                        pass

            # ttk.Treeview headings
            if isinstance(w, ttk.Treeview):
                try:
                    for col in w["columns"]:
                        h = w.heading(col, "text")
                        if self._lang == "zh":
                            nh = TRANSLATIONS.get(h, h)
                        else:
                            nh = TRANSLATIONS_REV.get(h, h)
                        if nh != h:
                            w.heading(col, text=nh)
                except Exception:
                    pass

            # 递归子控件
            try:
                for child in w.winfo_children():
                    _walk(child)
            except Exception:
                pass

        _walk(self)

        # 更新 Notebook 标签
        tabs = {
            "Load": "加载CSV", "Test Items": "测试项目",
            "Analysis": "分析设置", "Results": "分析结果",
        }
        tabs_rev = {v: k for k, v in tabs.items()}
        for i in range(self._notebook.index("end")):
            cur = self._notebook.tab(i, "text")
            if self._lang == "zh":
                nt = tabs.get(cur, cur)
            else:
                nt = tabs_rev.get(cur, cur)
            if nt != cur:
                self._notebook.tab(i, text=nt)

        # 更新菜单标签
        try:
            mb = self.cget("menu")
            if mb:
                menu_map = {
                    "Load": "加载CSV", "Test Items": "测试项目",
                    "Analysis": "分析设置", "Results": "分析结果",
                }
                menu_rev = {v: k for k, v in menu_map.items()}
                last = mb.index("end")
                for i in range(last + 1 if last is not None else 0):
                    try:
                        cur = mb.entrycget(i, "label")
                        if self._lang == "zh":
                            nt = menu_map.get(cur, cur)
                        else:
                            nt = menu_rev.get(cur, cur)
                        if nt != cur:
                            mb.entryconfigure(i, label=nt)
                    except Exception:
                        pass
        except Exception:
            pass

        # 更新语言按钮文字
        if self._lang_btn:
            self._lang_btn.configure(text="🌐 EN" if self._lang == "zh" else "🌐 中文")

    # ══════════════════════════════════════════════════
    #  菜单栏
    # ══════════════════════════════════════════════════
    def _build_menu(self):
        mb = tk.Menu(self, font=FONT_UI, bg=BG_PANEL, fg=FG_DARK,
                     activebackground=HIGHLIGHT, activeforeground="white")
        mb.add_cascade(label="Load",       command=lambda: self._select_tab(0))
        mb.add_cascade(label="Test Items", command=lambda: self._select_tab(1))
        mb.add_cascade(label="Analysis",   command=lambda: self._select_tab(2))
        mb.add_cascade(label="Results",    command=lambda: self._select_tab(3))
        self.config(menu=mb)

    # ══════════════════════════════════════════════════
    #  右侧固定面板
    # ══════════════════════════════════════════════════
    def _build_right_panel(self):
        panel = _TkStyle.frame(self, bg=BG_SIDEBAR, width=160, relief=tk.RIDGE, bd=1)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)
        self._right_panel = panel

        # 语言切换按钮 — 放在顶部
        self._lang_btn = tk.Button(panel, text="🌐 中文",
                                   bg=BG_SIDEBAR, fg=C_TITLE, font=FONT_LABEL,
                                   relief=tk.FLAT, bd=0, padx=6, pady=2,
                                   activebackground=BTN_ACTIVE,
                                   activeforeground=FG_DARK,
                                   highlightthickness=0,
                                   command=self._toggle_language)
        self._lang_btn.pack(fill=tk.X, padx=6, pady=(6, 2))
        _TkStyle.separator(panel).pack(fill=tk.X, padx=6, pady=2)

        def sep():
            _TkStyle.separator(panel).pack(fill=tk.X, padx=6, pady=3)

        def sec(text):
            lbl = tk.Label(panel, text=text, bg=BG_SIDEBAR, fg=C_TITLE,
                           font=FONT_TITLE, anchor=tk.CENTER)
            lbl.pack(fill=tk.X, padx=6, pady=(8, 2))

        def row(label, attr):
            f = _TkStyle.frame(panel, bg=BG_SIDEBAR)
            f.pack(fill=tk.X, padx=6, pady=1)
            l = tk.Label(f, text=label, bg=BG_SIDEBAR, fg=FG_DARK,
                         font=FONT_LABEL, width=12, anchor=tk.W)
            l.pack(side=tk.LEFT)
            v = tk.Label(f, text="", bg=ENTRY_BG, fg=FG_DARK, font=FONT_LABEL,
                         width=6, anchor=tk.W, relief=tk.SUNKEN, bd=1)
            v.pack(side=tk.LEFT, fill=tk.X, expand=True)
            setattr(self, attr, v)

        sec("Base Data")
        row("Units:",       "_lbl_base_units")
        row("Appraisers:",  "_lbl_base_appraisers")
        row("Trials:",      "_lbl_base_trials")
        row("Columns:",     "_lbl_base_columns")

        sep()
        sec("Selected Data")
        row("Units:",       "_lbl_sel_units")
        row("Appraisers:",  "_lbl_sel_appraisers")
        row("Trials:",      "_lbl_sel_trials")
        row("Test Items:",  "_lbl_sel_test_items")

        sep()
        l = tk.Label(panel, text="Method:", bg=BG_SIDEBAR, fg=FG_DARK,
                     font=FONT_LABEL, anchor=tk.W)
        l.pack(fill=tk.X, padx=6, pady=(6, 0))
        self._method_combo = ttk.Combobox(panel, textvariable=self._method_var,
                                          values=["ANOVA", "ANOVA Main Effect", "Range"],
                                          state="readonly", width=14)
        self._method_combo.pack(fill=tk.X, padx=6, pady=2)
        # 同步右侧 combo 到左侧 radio
        self._method_var.trace_add("write",
            lambda *a: self._grr_method_var.set(self._method_var.get()))

        sep()
        l = tk.Label(panel, text="Output Format:", bg=BG_SIDEBAR, fg=FG_DARK,
                     font=FONT_LABEL, anchor=tk.W)
        l.pack(fill=tk.X, padx=6, pady=(6, 0))
        fmt_frame = _TkStyle.frame(panel, bg=BG_SIDEBAR)
        fmt_frame.pack(fill=tk.X, padx=6, pady=1)
        _TkStyle.radiobutton(fmt_frame, text="P/T (%Tol)", 
                             variable=self._output_format_var, value="tol").pack(anchor=tk.W)
        _TkStyle.radiobutton(fmt_frame, text="Study Var (%TV)",
                             variable=self._output_format_var, value="tv").pack(anchor=tk.W)
        _TkStyle.label(panel, text="Study Const:", font=FONT_LABEL).pack(fill=tk.X, padx=6, pady=(4, 0))
        sc_frame = _TkStyle.frame(panel, bg=BG_SIDEBAR)
        sc_frame.pack(fill=tk.X, padx=6, pady=1)
        _TkStyle.radiobutton(sc_frame, text="6.0 (COSMO)", 
                             variable=self._study_const_var, value="6.0").pack(anchor=tk.W)
        _TkStyle.radiobutton(sc_frame, text="5.15 (AIAG)",
                             variable=self._study_const_var, value="5.15").pack(anchor=tk.W)

        sep()
        for txt, cmd in [("Run",                    self._run_grr),
                          ("Export as CSV",          self._export_csv),
                          ("Export as PDF",          self._export_pdf),
                          ("Export Consistency",     self._export_consistency_pdf)]:
            _TkStyle.button(panel, text=txt, command=cmd,
                            width=16).pack(fill=tk.X, padx=6, pady=2)

        # ══════════════════════════════════════════════════
    #  Notebook — 4 个标签页
    # ══════════════════════════════════════════════════
    def _build_notebook(self):
        style = ttk.Style(self)
        style.theme_use("default")

        # 标签整体样式
        style.configure("Cosmo.TNotebook", background=BG_MAIN, borderwidth=0)
        # 标签页（卡片）样式
        style.configure("Cosmo.TNotebook.Tab",
                        background=BTN_BG, foreground=FG_DARK,
                        font=FONT_UI, padding=[8, 4],
                        borderwidth=1)
        style.map("Cosmo.TNotebook.Tab",
                  background=[("selected", BG_PANEL)],
                  foreground=[("selected", C_TITLE)],
                  font=[("selected", FONT_TITLE)])
        style.configure("Cosmo.TFrame", background=BG_MAIN)

        self._notebook = ttk.Notebook(self, style="Cosmo.TNotebook")
        self._notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 0))

        self._build_load_tab()
        self._build_test_items_tab()
        self._build_analysis_tab()
        self._build_results_tab()

    def _select_tab(self, idx):
        self._notebook.select(idx)

    # ─────────────────────────────────────────────────
    #  公用辅助 — 快速创建卡片容器
    # ─────────────────────────────────────────────────
    def _card_frame(self, parent, **kw):
        """带边框的卡片容器"""
        f = tk.Frame(parent, bg=BG_PANEL, relief=tk.RIDGE, bd=1, **kw)
        return f

    # ══════════════════════════════════════════════════
    #  Tab 1: Load
    # ══════════════════════════════════════════════════
    def _build_load_tab(self):
        self._load_frame = f = ttk.Frame(self._notebook, style="Cosmo.TFrame")
        self._notebook.add(f, text="Load")

        # ── CSV Path 卡片 ──
        card1 = self._card_frame(f)
        card1.pack(fill=tk.X, padx=8, pady=(6, 4))

        row1 = _TkStyle.frame(card1)
        row1.pack(fill=tk.X, padx=6, pady=4)

        _TkStyle.label(row1, text="CSV Path:").pack(side=tk.LEFT)
        _TkStyle.entry(row1, textvariable=self._csv_path
                       ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 6))
        _TkStyle.button(row1, text="Load CSV", command=self._load_csv,
                        padx=12).pack(side=tk.RIGHT)

        # ── 工具栏卡片 ──
        card2 = self._card_frame(f)
        card2.pack(fill=tk.X, padx=8, pady=2)

        row2 = _TkStyle.frame(card2)
        row2.pack(fill=tk.X, padx=6, pady=3)

        # 第一行按钮组
        btn_row_a = _TkStyle.frame(row2)
        btn_row_a.pack(fill=tk.X, pady=1)
        for txt, cmd in [
            ("Outcome Settings", self._show_outcome_settings),
            ("JSON to CSV", self._json_to_csv),
            ("Dashboard Connection", self._show_dashboard_connection),
        ]:
            _TkStyle.button(btn_row_a, text=txt, command=cmd,
                            padx=8).pack(side=tk.LEFT, padx=(0, 6))

        # 第二行: 设置导入导出 + 限制导入导出
        btn_row_b = _TkStyle.frame(row2)
        btn_row_b.pack(fill=tk.X, pady=1)
        for txt, cmd in [
            ("Import Settings", self._import_settings),
            ("Export Settings", self._export_settings),
            ("Import Limits", self._import_limits),
            ("Export Limits", self._export_limits),
        ]:
            _TkStyle.button(btn_row_b, text=txt, command=cmd,
                            padx=8).pack(side=tk.LEFT, padx=(0, 6))

        # 第三行: 复选框
        btn_row_c = _TkStyle.frame(row2)
        btn_row_c.pack(fill=tk.X, pady=1)
        _TkStyle.checkbutton(btn_row_c, text="Use current settings",
                             variable=self._use_current).pack(side=tk.LEFT, padx=(0, 12))
        _TkStyle.checkbutton(btn_row_c, text="Load Limits from CSV",
                             variable=self._load_limits).pack(side=tk.LEFT, padx=(0, 12))
        _TkStyle.checkbutton(btn_row_c, text="COSMO row format (UL/LL in first 3 rows)",
                             variable=self._cosmo_row_format).pack(side=tk.LEFT)

        # ── 三列 + Apply Filter 卡片 ──
        card4 = self._card_frame(f)
        card4.pack(fill=tk.X, padx=8, pady=4)

        cols_frame = _TkStyle.frame(card4)
        cols_frame.pack(fill=tk.X, padx=6, pady=4)

        self._part_lb  = self._make_lb_col(cols_frame, "Part Column")
        self._appr_lb  = self._make_lb_col(cols_frame, "Appraiser Column(s)")
        self._order_lb = self._make_lb_col(cols_frame, "Order by")
        # 实时刷新：选中 Part/Appraiser 列变更时自动更新 Units/Appraisers 列表
        self._part_lb.bind("<<ListboxSelect>>", lambda e: self._on_column_selection_changed())
        self._appr_lb.bind("<<ListboxSelect>>", lambda e: self._on_column_selection_changed())

        right_col = _TkStyle.frame(cols_frame)
        right_col.pack(side=tk.LEFT, padx=(8, 0), fill=tk.Y)
        _TkStyle.button(right_col, text="Apply Filter", command=self._apply_filter,
                        width=12, height=2).pack(pady=(0, 6))
        _TkStyle.checkbutton(right_col, text="Auto Bin\nAppraisers",
                             variable=self._auto_bin).pack()

        # ── Data Preview ──
        _TkStyle.label(f, text="Data Preview", font=FONT_TITLE).pack(fill=tk.X, padx=8, pady=(4, 0))
        pf = self._card_frame(f)
        pf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))
        # Treeview 表格 + 滚动条
        tree_frame = tk.Frame(pf, bg=BG_PANEL)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self._preview_tree = ttk.Treeview(tree_frame, show="headings", selectmode="browse")
        vsb = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._preview_tree.yview)
        hsb = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self._preview_tree.xview)
        self._preview_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 保留旧引用兼容（不再使用）
        self._preview = None

    def _make_lb_col(self, parent, label):
        f = _TkStyle.frame(parent)
        f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        _TkStyle.label(f, text=label, font=FONT_TITLE).pack(fill=tk.X)
        inner = _TkStyle.frame(f)
        inner.pack(fill=tk.BOTH, expand=True)
        lb = _TkStyle.listbox(inner, height=5)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── 自定义滚动条 + 悬停箭头按钮 ──
        sb_frame = _TkStyle.frame(inner)
        sb_frame.pack(side=tk.RIGHT, fill=tk.Y)

        arrow_font = ("Segoe UI", 5)
        arrow_cfg = dict(
            bg=BG_PANEL, fg=FG_MUTED, font=arrow_font,
            relief=tk.FLAT, bd=0, width=1, height=0,
            padx=0, pady=0,
            activebackground=BTN_ACTIVE, activeforeground=FG_DARK,
            highlightthickness=0,
        )

        up_btn = tk.Button(sb_frame, text="▲", **arrow_cfg,
                           command=lambda l=lb: l.yview_scroll(-1, "units"))
        up_btn.pack(fill=tk.X, ipady=0)

        sb = tk.Scrollbar(sb_frame, orient=tk.VERTICAL, command=lb.yview,
                          width=10, bg=BG_PANEL, troughcolor=BG_PANEL,
                          highlightthickness=0, bd=0)
        sb.pack(fill=tk.BOTH, expand=True)
        lb.config(yscrollcommand=sb.set)

        down_btn = tk.Button(sb_frame, text="▼", **arrow_cfg,
                             command=lambda l=lb: l.yview_scroll(1, "units"))
        down_btn.pack(fill=tk.X, ipady=0)

        # Hover highlight
        def _on_enter(_event, u=up_btn, d=down_btn):
            u.config(fg=FG_DARK, bg=BTN_BG)
            d.config(fg=FG_DARK, bg=BTN_BG)

        def _on_leave(_event, u=up_btn, d=down_btn):
            u.config(fg=FG_MUTED, bg=BG_PANEL)
            d.config(fg=FG_MUTED, bg=BG_PANEL)

        sb_frame.bind("<Enter>", _on_enter)
        sb_frame.bind("<Leave>", _on_leave)

        return lb

    # ══════════════════════════════════════════════════
    #  Tab 2: Test Items
    # ══════════════════════════════════════════════════
    def _build_test_items_tab(self):
        self._ti_frame = f = ttk.Frame(self._notebook, style="Cosmo.TFrame")
        self._notebook.add(f, text="Test Items")

        # ── Filter 行 ──
        card_filter = self._card_frame(f)
        card_filter.pack(fill=tk.X, padx=8, pady=(6, 4))

        filter_row = _TkStyle.frame(card_filter)
        filter_row.pack(fill=tk.X, padx=6, pady=4)

        _TkStyle.label(filter_row, text="Filter:").pack(side=tk.LEFT)
        self._ti_filter_var = tk.StringVar()
        filter_entry = _TkStyle.entry(filter_row, textvariable=self._ti_filter_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 6))
        self._ti_filter_var.trace_add("write", lambda *a: self._ti_apply_filter())
        _TkStyle.button(filter_row, text="Apply Filter",
                        command=self._ti_apply_filter, padx=8).pack(side=tk.LEFT, padx=(0, 4))
        _TkStyle.button(filter_row, text="Clear Filter",
                        command=self._ti_clear_filter, padx=8).pack(side=tk.LEFT)

        # ── 主体: 原始数据（左）| 中间按钮 | 已选测项（右）──
        body = _TkStyle.frame(f)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # 原始数据列表（左侧 — 可用测项）
        src_frame = _TkStyle.frame(body)
        src_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        _TkStyle.label(src_frame, text="Source",
                       font=FONT_TITLE).pack(fill=tk.X)
        src_inner = _TkStyle.frame(src_frame)
        src_inner.pack(fill=tk.BOTH, expand=True)
        self._ti_src_lb = _TkStyle.listbox(src_inner, selectmode=tk.EXTENDED)
        src_vsb = tk.Scrollbar(src_inner, orient=tk.VERTICAL, command=self._ti_src_lb.yview)
        src_hsb = tk.Scrollbar(src_frame, orient=tk.HORIZONTAL, command=self._ti_src_lb.xview)
        self._ti_src_lb.config(yscrollcommand=src_vsb.set, xscrollcommand=src_hsb.set)
        src_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._ti_src_lb.pack(fill=tk.BOTH, expand=True)
        src_hsb.pack(fill=tk.X)

        # 中间按钮列
        mid = _TkStyle.frame(body, width=100)
        mid.pack(side=tk.LEFT, padx=8, fill=tk.Y)
        mid.pack_propagate(False)
        spacer = _TkStyle.frame(mid)
        spacer.pack(fill=tk.Y, expand=True)
        for txt, cmd in [("Add All",       self._ti_add_all),
                          ("Add >>>",       self._ti_add_sel),
                          ("<<< Remove",    self._ti_remove_sel),
                          ("Remove All",    self._ti_remove_all)]:
            _TkStyle.button(mid, text=txt, command=cmd,
                            width=12).pack(pady=3)
        _TkStyle.frame(mid).pack(fill=tk.Y, expand=True)

        # 已选测项（右侧 — 用户选择的测项 + UL/LL）
        loaded_frame = _TkStyle.frame(body)
        loaded_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        _TkStyle.label(loaded_frame, text="Loaded",
                       font=FONT_TITLE).pack(fill=tk.X)

        cols = ("Item", "UL", "LL")
        self._ti_loaded_tree = ttk.Treeview(loaded_frame, columns=cols,
                                            show="headings", height=15)
        self._ti_loaded_tree.heading("Item", text="Item")
        self._ti_loaded_tree.heading("UL",   text="UL",
                                     command=self._ti_toggle_ul_filter)
        self._ti_loaded_tree.heading("LL",   text="LL",
                                     command=self._ti_toggle_ll_filter)
        self._ti_loaded_tree.column("Item", width=350, anchor=tk.W)
        self._ti_loaded_tree.column("UL",   width=80,  anchor=tk.CENTER)
        self._ti_loaded_tree.column("LL",   width=80,  anchor=tk.CENTER)

        # Treeview 配色
        tree_style = ttk.Style(self)
        tree_style.theme_use("default")
        tree_style.configure("Treeview", background=LISTBOX_BG, foreground=FG_DARK,
                             rowheight=22, fieldbackground=LISTBOX_BG,
                             font=FONT_UI, borderwidth=0)
        tree_style.map("Treeview", background=[("selected", HIGHLIGHT)])
        tree_style.configure("Treeview.Heading", background=BG_SIDEBAR,
                             foreground=FG_DARK, font=FONT_TITLE,
                             relief="flat", borderwidth=1)

        vsb = tk.Scrollbar(loaded_frame, orient=tk.VERTICAL, command=self._ti_loaded_tree.yview)
        hsb = tk.Scrollbar(loaded_frame, orient=tk.HORIZONTAL, command=self._ti_loaded_tree.xview)
        self._ti_loaded_tree.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._ti_loaded_tree.pack(fill=tk.BOTH, expand=True)

        # 支持双击编辑 UL/LL
        self._ti_loaded_tree.bind("<Double-1>", self._ti_edit_cell)

    def _ti_edit_cell(self, event):
        """双击编辑 UL/LL 列"""
        col = self._ti_loaded_tree.identify_column(event.x)
        col_idx = int(col.replace("#", "")) - 1 if col else -1
        # UL=1, LL=2
        if col_idx < 1 or col_idx > 2:
            return
        row_id = self._ti_loaded_tree.identify_row(event.y)
        if not row_id:
            return
        item = self._ti_loaded_tree.item(row_id, "values")
        old_val = item[col_idx]

        x, y, w, h = self._ti_loaded_tree.bbox(row_id, col)
        entry = tk.Entry(self._ti_loaded_tree, bg="white", fg=FG_DARK,
                         font=FONT_UI, relief=tk.SUNKEN, bd=1)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, old_val)
        entry.focus_set()
        entry.selection_range(0, tk.END)

        def save_edit():
            try:
                new_val = float(entry.get().strip())
                vals = list(item)
                vals[col_idx] = f"{new_val:.3f}"
                self._ti_loaded_tree.item(row_id, values=tuple(vals))
                # 更新 item_limits
                item_name = vals[0]
                ul = float(vals[1])
                ll = float(vals[2])
                self._item_limits[item_name] = (ul, ll)
                # 同步更新 _ti_loaded_data
                for i, (name, u, l) in enumerate(self._ti_loaded_data):
                    if name == item_name:
                        self._ti_loaded_data[i] = (name, ul, ll)
                        break
            except ValueError:
                pass
            finally:
                entry.destroy()

        entry.bind("<Return>", lambda e: save_edit())
        entry.bind("<FocusOut>", lambda e: save_edit())
        entry.bind("<Escape>", lambda e: entry.destroy())

    # ── Test Items 操作 ──
    def _ti_apply_filter(self):
        keyword = self._ti_filter_var.get().lower()
        self._ti_src_lb.delete(0, tk.END)
        loaded = set(self._get_loaded_items())
        for item in self._all_items:
            if keyword in item.lower() and item not in loaded:
                self._ti_src_lb.insert(tk.END, item)

    def _ti_clear_filter(self):
        self._ti_filter_var.set("")
        self._ti_refresh_src()

    def _get_loaded_items(self):
        return [t[0] for t in self._ti_loaded_data]

    def _ti_refresh_src(self):
        loaded = set(self._get_loaded_items())
        self._ti_src_lb.delete(0, tk.END)
        for item in self._all_items:
            if item not in loaded:
                self._ti_src_lb.insert(tk.END, item)

    @staticmethod
    def _fmt_limit(val: float) -> str:
        """格式化规格限：+/-999999 显示为 "∞"，正常值保留3位小数"""
        if val is None or (isinstance(val, float) and (val == 999999.0 or val == -999999.0 or val != val)):
            return "∞"
        return f"{val:.3f}"

    def _add_to_loaded(self, item_name):
        ul, ll = self._item_limits.get(item_name, (999999.0, -999999.0))
        self._ti_loaded_data.append((item_name, ul, ll))
        self._ti_refresh_loaded()

    def _ti_refresh_loaded(self):
        """刷新右侧已选测项 Treeview，UL/LL 筛选时排序（有值在前）"""
        for row_id in self._ti_loaded_tree.get_children():
            self._ti_loaded_tree.delete(row_id)

        data = list(self._ti_loaded_data)
        # 排序：有实际值的排前面，满足任一筛选条件就优先
        if self._ul_filter_active and self._ll_filter_active:
            data.sort(key=lambda t: (0 if t[1] != 999999.0 and t[2] != -999999.0 else 1))
        elif self._ul_filter_active:
            data.sort(key=lambda t: (0 if t[1] != 999999.0 else 1))
        elif self._ll_filter_active:
            data.sort(key=lambda t: (0 if t[2] != -999999.0 else 1))

        for item_name, ul, ll in data:
            self._ti_loaded_tree.insert("", tk.END, values=(item_name,
                                            self._fmt_limit(ul), self._fmt_limit(ll)))
        # 更新列头文字，显示筛选状态
        ul_txt = "UL ▼" if self._ul_filter_active else "UL"
        ll_txt = "LL ▼" if self._ll_filter_active else "LL"
        self._ti_loaded_tree.heading("UL", text=ul_txt)
        self._ti_loaded_tree.heading("LL", text=ll_txt)

    def _ti_toggle_ul_filter(self):
        """点击 UL 列头：将有实际 UL 值的测项排在前面"""
        self._ul_filter_active = not self._ul_filter_active
        self._ti_refresh_loaded()

    def _ti_toggle_ll_filter(self):
        """点击 LL 列头：将有实际 LL 值的测项排在前面"""
        self._ll_filter_active = not self._ll_filter_active
        self._ti_refresh_loaded()

    def _ti_add_all(self):
        for item in self._all_items:
            if item not in self._get_loaded_items():
                self._add_to_loaded(item)
        self._ti_refresh_src()
        self._update_selected_items()

    def _ti_add_sel(self):
        for i in reversed(self._ti_src_lb.curselection()):
            item = self._ti_src_lb.get(i)
            if item not in self._get_loaded_items():
                self._add_to_loaded(item)
            self._ti_src_lb.delete(i)
        self._update_selected_items()

    def _ti_remove_sel(self):
        sel_items = set()
        for row_id in self._ti_loaded_tree.selection():
            item = self._ti_loaded_tree.item(row_id, "values")[0]
            sel_items.add(item)
        self._ti_loaded_data = [t for t in self._ti_loaded_data
                                if t[0] not in sel_items]
        for item in sel_items:
            self._ti_src_lb.insert(tk.END, item)
        self._ti_refresh_loaded()
        self._update_selected_items()

    def _ti_remove_all(self):
        removed = [t[0] for t in self._ti_loaded_data]
        self._ti_loaded_data.clear()
        for item in removed:
            self._ti_src_lb.insert(tk.END, item)
        self._ti_refresh_loaded()
        self._update_selected_items()

    def _update_selected_items(self):
        self._selected_items = self._get_loaded_items()
        self._set_label(self._lbl_sel_test_items, str(len(self._selected_items)))

    # ══════════════════════════════════════════════════
    #  Tab 3: Analysis > GRR
    # ══════════════════════════════════════════════════
    def _build_analysis_tab(self):
        self._an_frame = f = ttk.Frame(self._notebook, style="Cosmo.TFrame")
        self._notebook.add(f, text="Analysis")

        # 内容区域
        body = _TkStyle.frame(f)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # ── 左侧设置面板 ──
        left = _TkStyle.frame(body, width=220, relief=tk.GROOVE, bd=1)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left.pack_propagate(False)

        def section_title(parent, text):
            """分区标题"""
            lbl = tk.Label(parent, text=text, bg=BG_SIDEBAR, fg=C_TITLE,
                           font=FONT_TITLE, anchor=tk.W)
            lbl.pack(fill=tk.X, padx=6, pady=(6, 2))

        # Autobin Settings
        section_title(left, "Autobin Settings")

        def ab_row(label, attr):
            row = _TkStyle.frame(left)
            row.pack(fill=tk.X, padx=6, pady=1)
            _TkStyle.label(row, text=label, width=22, anchor=tk.E).pack(side=tk.LEFT)
            var = tk.StringVar()
            _TkStyle.entry(row, textvariable=var, width=6).pack(side=tk.LEFT, padx=(2, 0))
            setattr(self, attr, var)

        ab_row("Number of units:",       "_ab_units_var")
        ab_row("Number of appraisers:",  "_ab_appraisers_var")
        ab_row("Number of trials:",      "_ab_trials_var")
        # 可用 trial 提示
        hint_row = _TkStyle.frame(left)
        hint_row.pack(fill=tk.X, padx=6, pady=(0, 4))
        self._lbl_avail_trials = tk.Label(hint_row, text="", bg=BG_SIDEBAR, fg="#6B5B4F",
                                          font=("Segoe UI", 9), anchor=tk.E)
        self._lbl_avail_trials.pack(side=tk.RIGHT)

        # GRR Settings
        section_title(left, "GRR Settings")
        sigma_row = _TkStyle.frame(left)
        sigma_row.pack(fill=tk.X, padx=6, pady=(6, 0))
        _TkStyle.label(sigma_row, text="Sigma:", width=12,
                       anchor=tk.E).pack(side=tk.LEFT)
        _TkStyle.entry(sigma_row, textvariable=self._sigma_var,
                       width=6).pack(side=tk.LEFT, padx=(2, 0))

        _TkStyle.button(left, text="Apply All Settings",
                        command=self._apply_all_settings,
                        width=18).pack(fill=tk.X, padx=6, pady=(12, 4))

        # ── 右侧选择区 ──
        right_area = _TkStyle.frame(body, relief=tk.GROOVE, bd=1)
        right_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._analysis_right = right_area  # 保存引用

        # 标题行
        header_bar = _TkStyle.frame(right_area)
        header_bar.pack(fill=tk.X, padx=6, pady=(4, 2))
        _TkStyle.label(header_bar, text="Select Data for Analysis",
                       font=FONT_TITLE).pack(side=tk.LEFT)
        _TkStyle.button(header_bar, text="Apply Selection",
                        command=self._apply_selection,
                        padx=6).pack(side=tk.RIGHT, padx=(2, 0))

        # Select Units / Select Appraisers 列表（左右各一列，按钮在各自列内）
        lb_row = _TkStyle.frame(right_area)
        lb_row.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        def make_an_lb(parent, label, attr):
            col = _TkStyle.frame(parent)
            col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
            # 列标题 + 按钮行
            hdr = _TkStyle.frame(col)
            hdr.pack(fill=tk.X)
            _TkStyle.label(hdr, text=label, font=FONT_TITLE).pack(side=tk.LEFT)
            select_all_id = f"_an_{attr}_select_all"
            setattr(self, select_all_id,
                    _TkStyle.button(hdr, text="Select All",
                                    command=lambda a=attr: self._sel_all(getattr(self, a)),
                                    padx=6))
            getattr(self, select_all_id).pack(side=tk.RIGHT)
            clear_id = f"_an_{attr}_clear"
            setattr(self, clear_id,
                    _TkStyle.button(hdr, text="Clear",
                                    command=lambda a=attr: self._sel_clear(getattr(self, a)),
                                    padx=6))
            getattr(self, clear_id).pack(side=tk.RIGHT, padx=(2, 0))

            inner = _TkStyle.frame(col)
            inner.pack(fill=tk.BOTH, expand=True)
            lb = _TkStyle.listbox(inner, selectmode=tk.EXTENDED, height=15)
            # ── 自定义滚动条 + 悬停箭头按钮 ──
            sb_frame = _TkStyle.frame(inner)
            sb_frame.pack(side=tk.RIGHT, fill=tk.Y)

            arrow_font = ("Segoe UI", 5)
            arrow_cfg = dict(
                bg=BG_PANEL, fg=FG_MUTED, font=arrow_font,
                relief=tk.FLAT, bd=0, width=1, height=0,
                padx=0, pady=0,
                activebackground=BTN_ACTIVE, activeforeground=FG_DARK,
                highlightthickness=0,
            )
            up_btn = tk.Button(sb_frame, text="▲", **arrow_cfg,
                               command=lambda l=lb: l.yview_scroll(-1, "units"))
            up_btn.pack(fill=tk.X, ipady=0)
            vsb = tk.Scrollbar(sb_frame, orient=tk.VERTICAL, command=lb.yview,
                               width=10, bg=BG_PANEL, troughcolor=BG_PANEL,
                               highlightthickness=0, bd=0)
            vsb.pack(fill=tk.BOTH, expand=True)
            lb.config(yscrollcommand=vsb.set)
            down_btn = tk.Button(sb_frame, text="▼", **arrow_cfg,
                                 command=lambda l=lb: l.yview_scroll(1, "units"))
            down_btn.pack(fill=tk.X, ipady=0)

            # Hover highlight
            def _on_enter(_event, u=up_btn, d=down_btn):
                u.config(fg=FG_DARK, bg=BTN_BG)
                d.config(fg=FG_DARK, bg=BTN_BG)
            def _on_leave(_event, u=up_btn, d=down_btn):
                u.config(fg=FG_MUTED, bg=BG_PANEL)
                d.config(fg=FG_MUTED, bg=BG_PANEL)
            sb_frame.bind("<Enter>", _on_enter)
            sb_frame.bind("<Leave>", _on_leave)

            hsb = tk.Scrollbar(col, orient=tk.HORIZONTAL, command=lb.xview)
            lb.config(xscrollcommand=hsb.set)
            lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            hsb.pack(fill=tk.X)
            setattr(self, attr, lb)

        make_an_lb(lb_row, "Select Units",      "_an_units_lb")
        make_an_lb(lb_row, "Select Appraisers", "_an_appr_lb")

    def _sel_all(self, lb):
        lb.select_set(0, tk.END)

    def _sel_clear(self, lb):
        lb.selection_clear(0, tk.END)

    def _apply_all_settings(self):
        self._status("Settings applied.")

    def _apply_selection(self):
        sel_units   = [self._an_units_lb.get(i)  for i in self._an_units_lb.curselection()]
        sel_appraisers = [self._an_appr_lb.get(i) for i in self._an_appr_lb.curselection()]
        self._sel_units      = sel_units
        self._sel_appraisers = sel_appraisers
        self._set_label(self._lbl_sel_units,      str(len(sel_units)))
        self._set_label(self._lbl_sel_appraisers, str(len(sel_appraisers)))
        self._status(f"Selection applied: {len(sel_units)} units, {len(sel_appraisers)} appraisers.")

    # ══════════════════════════════════════════════════
    #  Tab 4: Results
    # ══════════════════════════════════════════════════
    def _build_results_tab(self):
        self._res_frame = f = ttk.Frame(self._notebook, style="Cosmo.TFrame")
        self._notebook.add(f, text="Results")

        # 顶栏卡片
        top_card = self._card_frame(f)
        top_card.pack(fill=tk.X, padx=8, pady=(6, 4))

        top = _TkStyle.frame(top_card)
        top.pack(fill=tk.X, padx=6, pady=4)

        _TkStyle.label(top, text="Results", font=("Segoe UI", 11, "bold"),
                       fg=C_TITLE).pack(side=tk.LEFT)

        right_top = _TkStyle.frame(top)
        right_top.pack(side=tk.RIGHT)

        for val in ["%Variance", "%Tolerance"]:
            _TkStyle.radiobutton(right_top, text=f"Show {val}",
                                 variable=self._show_mode, value=val,
                                 command=self._refresh_results_view
                                 ).pack(side=tk.LEFT, padx=(0, 6))

        # 结果表格 — 初始列用 %Variance 列定义
        res_frame = self._card_frame(f)
        res_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # %Variance 列: #, Item, %rr, %ev, %av, %iv, %pv, ev, av, iv, pv, tv
        cols_init = ("#", "Item", "%rr", "%ev", "%av", "%iv", "%pv",
                     "ev", "av", "iv", "pv", "tv")

        self._res_tree = ttk.Treeview(res_frame, columns=cols_init,
                                      show="headings", height=20)
        for c in cols_init:
            self._res_tree.heading(c, text=c)
            if c == "#":
                self._res_tree.column(c, width=30, anchor=tk.CENTER)
            elif c == "Item":
                self._res_tree.column(c, width=280, anchor=tk.W)
            else:
                self._res_tree.column(c, width=80, anchor=tk.CENTER)

        vsb = tk.Scrollbar(res_frame, orient=tk.VERTICAL, command=self._res_tree.yview)
        hsb = tk.Scrollbar(res_frame, orient=tk.HORIZONTAL, command=self._res_tree.xview)
        self._res_tree.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._res_tree.pack(fill=tk.BOTH, expand=True)

        # 配置标签颜色（按用户规范：≤10%绿/10-20%黄/20-30%橙/>30%红）
        self._res_tree.tag_configure("excellent",
            background=TAG_EXCELLENT, foreground="#0E6251")   # 深绿字
        self._res_tree.tag_configure("good",
            background=TAG_GOOD, foreground="#7D6608")        # 暗黄字
        self._res_tree.tag_configure("marginal",
            background=TAG_MARGINAL, foreground="#7E5109")    # 深橙字
        self._res_tree.tag_configure("poor",
            background=TAG_POOR, foreground="#7B241C")        # 深红字

    def _get_row_tag(self, pct_val):
        """
        AIAG MSA 标准颜色规则：
          绿 ≤10%  |  黄 10-20%  |  橙 20-30%  |  红 >30%
        """
        if pct_val <= 10:
            return "excellent"
        elif pct_val <= 20:
            return "good"
        elif pct_val <= 30:
            return "marginal"
        else:
            return "poor"

    def _refresh_results_view(self):
        if not self._report:
            return

        for item in self._res_tree.get_children():
            self._res_tree.delete(item)

        mode = self._show_mode.get()

        if mode == "%Variance":
            # 列: #, Item, %rr, %ev, %av, %iv, %pv, ev, av, iv, pv, tv
            cols = ("#", "Item", "%rr", "%ev", "%av", "%iv", "%pv",
                    "ev", "av", "iv", "pv", "tv")
        else:
            # %Tolerance 列: #, Item, grr, repeatability, reproducibility, ev, av, iv, pv, tv
            cols = ("#", "Item", "grr", "repeatability", "reproducibility",
                    "ev", "av", "iv", "pv", "tv")

        self._res_tree["columns"] = cols
        for c in cols:
            self._res_tree.heading(c, text=c)
            if c == "#":
                self._res_tree.column(c, width=30, anchor=tk.CENTER)
            elif c == "Item":
                self._res_tree.column(c, width=260, anchor=tk.W)
            elif c in ("grr", "repeatability", "reproducibility"):
                self._res_tree.column(c, width=100, anchor=tk.CENTER)
            else:
                self._res_tree.column(c, width=80, anchor=tk.CENTER)

        for i, r in enumerate(self._report.results, 1):
            if mode == "%Variance":
                # 颜色基于 %rr (方差贡献率)
                tag = self._get_row_tag(r.pct_rr)
                vals = (
                    i,
                    r.name,
                    f"{r.pct_rr:.4f}",
                    f"{r.pct_ev:.4f}",
                    f"{r.pct_av:.4f}",
                    f"{r.pct_iv:.4f}",
                    f"{r.pct_pv:.4f}",
                    f"{r.ev:.6f}",
                    f"{r.av:.6f}",
                    f"{r.iv:.6f}",
                    f"{r.pv:.6f}",
                    f"{r.tv:.6f}",
                )
            else:
                # %Tolerance 模式：有规格限时显示 %P/T 百分比和 Tolerance 分数
                # 颜色基于 pct_tol (P/T 比率)
                SC = float(self._study_const_var.get())
                has_spec = r._has_spec_limits
                tag = self._get_row_tag(r.pct_tol)
                if has_spec:
                    # ev/av/pv/tv 显示为 Tolerance 分数 (= study variation / tolerance)
                    tol_frac = lambda pct: pct / 100.0
                    vals = (
                        i,
                        r.name,
                        f"{r.pct_tol:.4f}",          # grr = %P/T
                        f"{r.pct_tol_ev:.4f}",       # repeatability = %EV/T
                        f"{r.pct_tol_av:.4f}",       # reproducibility = %AV/T
                        f"{tol_frac(r.pct_tol_ev):.6f}",  # ev = EV_study / tolerance
                        f"{tol_frac(r.pct_tol_av):.6f}",  # av = AV_study / tolerance
                        f"{tol_frac(r.pct_tol_iv):.6f}",  # iv = IV_study / tolerance
                        f"{tol_frac(r.pct_tol_pv):.6f}",  # pv = PV_study / tolerance
                        f"{tol_frac(r.pct_tol):.6f}",     # tv = TV_study / tolerance
                    )
                else:
                    # 无规格限时显示原始 study variation 值
                    vals = (
                        i,
                        r.name,
                        f"{r.grr_study:.6f}",
                        f"{r.repeat_study:.6f}",
                        f"{r.reprod_study:.6f}",
                        f"{r.ev * SC:.6f}",
                        f"{r.av * SC:.6f}",
                        f"{r.iv * SC:.6f}",
                        f"{r.pv * SC:.6f}",
                        f"{r.tv * SC:.6f}",
                    )

            self._res_tree.insert("", tk.END, values=vals, tags=(tag,))

    # ══════════════════════════════════════════════════
    #  弹出对话框
    # ══════════════════════════════════════════════════
    def _show_outcome_settings(self):
        win = tk.Toplevel(self)
        win.title("Outcome Selection")
        win.configure(bg=BG_PANEL)
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)
        win.geometry("240x260")

        panel = _TkStyle.frame(win, relief=tk.GROOVE, bd=1, padx=12, pady=12)
        panel.pack(padx=10, pady=(12, 8), fill=tk.BOTH, expand=True)

        _TkStyle.label(panel, text="Outcome Selection",
                       font=("Segoe UI", 11, "bold"), fg=C_TITLE).pack(pady=(0, 8))

        outcomes = ["PASS", "FAIL", "ERROR", "TIMEOUT", "FAIL_STOP", "SCOF_PASS"]
        self._outcome_vars = {}
        defaults = {"PASS": True, "FAIL": True, "ERROR": False,
                    "TIMEOUT": False, "FAIL_STOP": False, "SCOF_PASS": False}

        for o in outcomes:
            var = tk.BooleanVar(value=defaults.get(o, False))
            self._outcome_vars[o] = var
            _TkStyle.checkbutton(panel, text=o, variable=var,
                                 anchor=tk.W).pack(fill=tk.X, padx=12, pady=1)

        def on_ok():
            selected = [k for k, v in self._outcome_vars.items() if v.get()]
            self._status(f"Outcomes: {', '.join(selected)}")
            win.destroy()

        _TkStyle.button(panel, text="OK", command=on_ok,
                        width=10).pack(pady=(10, 4))

    def _show_dashboard_connection(self):
        win = tk.Toplevel(self)
        win.title("Cosmo v2.5.2e")
        win.configure(bg=BG_MAIN)
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)
        win.geometry("400x340")

        panel = _TkStyle.frame(win, relief=tk.GROOVE, bd=1, padx=14, pady=14)
        panel.pack(padx=10, pady=(14, 10), fill=tk.BOTH, expand=True)

        _TkStyle.label(panel, text="Dashboard connection setting",
                       font=("Segoe UI", 11, "bold"), fg=C_TITLE).pack(anchor=tk.W, pady=(0, 10))

        db_var = tk.StringVar(value="google")
        self._db_mode_var = db_var
        radio_row = _TkStyle.frame(panel)
        radio_row.pack(fill=tk.X, pady=(0, 4))
        for val in ["google", "bigbird"]:
            _TkStyle.radiobutton(radio_row, text=val, variable=db_var,
                                 value=val).pack(side=tk.LEFT, padx=(0, 14))

        fields = [("bigbird ip:", "_db_ip"),
                  ("bigbird port:", "_db_port"),
                  ("Product Family:", "_db_family"),
                  ("Product Type:", "_db_type"),
                  ("Input Product:", "_db_product")]

        for label, attr in fields:
            row = _TkStyle.frame(panel)
            row.pack(fill=tk.X, pady=2)
            _TkStyle.label(row, text=label, width=14, anchor=tk.E).pack(side=tk.LEFT)
            var = tk.StringVar()
            setattr(self, attr + "_var", var)
            _TkStyle.entry(row, textvariable=var, width=20).pack(side=tk.LEFT, padx=(4, 0))

        btn_row1 = _TkStyle.frame(panel)
        btn_row1.pack(fill=tk.X, pady=(6, 2))
        self._db_station_var = tk.StringVar()
        cb = ttk.Combobox(btn_row1, textvariable=self._db_station_var,
                          values=[], state="readonly", width=14)
        cb.pack(side=tk.LEFT)

        # ══════════════════════════════════════════════════
    #  核心功能
    # ══════════════════════════════════════════════════

    # ── Settings 导入/导出 ──
    def _export_settings(self):
        """导出当前设置到 JSON 文件"""
        if not self._df is None:
            data = {
                "part_col": self._part_col,
                "appr_col": self._appr_col,
                "items": self._selected_items,
                "limits": {k: list(v) for k, v in self._item_limits.items()},
                "method": self._method_var.get(),
                "grr_method": self._grr_method_var.get(),
            }
            path = filedialog.asksaveasfilename(
                title="Export Settings", defaultextension=".json",
                filetypes=[("JSON", "*.json")])
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Done", f"Settings saved:\n{path}")
        else:
            messagebox.showwarning("No Data", "Load a CSV first.")

    def _import_settings(self):
        """从 JSON 文件导入设置"""
        path = filedialog.askopenfilename(
            title="Import Settings", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if self._df is not None:
                self._part_col = data.get("part_col")
                self._appr_col = data.get("appr_col")
                self._item_limits = {k: tuple(v) for k, v in data.get("limits", {}).items()}
                self._method_var.set(data.get("method", "ANOVA"))
                self._grr_method_var.set(data.get("grr_method", "ANOVA"))
                # 恢复 Test Items
                loaded_items = data.get("items", [])
                for row_id in self._ti_loaded_tree.get_children():
                    self._ti_loaded_tree.delete(row_id)
                for item in loaded_items:
                    ul, ll = self._item_limits.get(item, (999999.0, -999999.0))
                    self._ti_loaded_tree.insert("", tk.END, values=(item,
                                        self._fmt_limit(ul), self._fmt_limit(ll)))
                self._selected_items = loaded_items
                self._update_selected_items()
                self._apply_filter()
                self._status("Settings imported.")
            else:
                messagebox.showwarning("No Data", "Load a CSV file first, then import settings.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import settings:\n{e}")

    # ── Limits 导入/导出 ──
    def _export_limits(self):
        """导出规格限制到 JSON"""
        if not self._item_limits:
            messagebox.showwarning("No Limits", "No limits to export.")
            return
        data = {k: list(v) for k, v in self._item_limits.items()}
        path = filedialog.asksaveasfilename(
            title="Export Limits", defaultextension=".json",
            filetypes=[("JSON", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Done", f"Limits saved:\n{path}")

    def _import_limits(self):
        """从 JSON 文件导入规格限制"""
        path = filedialog.askopenfilename(
            title="Import Limits", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._item_limits = {k: tuple(v) for k, v in data.items()}
            # 刷新 Test Items tree
            for row_id in self._ti_loaded_tree.get_children():
                item = self._ti_loaded_tree.item(row_id, "values")[0]
                ul, ll = self._item_limits.get(item, (999999.0, -999999.0))
                self._ti_loaded_tree.item(row_id, values=(item, self._fmt_limit(ul), self._fmt_limit(ll)))
            self._status(f"Imported {len(self._item_limits)} limits.")
            messagebox.showinfo("Done", f"Imported {len(self._item_limits)} limits.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import limits:\n{e}")

    def _load_csv(self):
        path = filedialog.askopenfilename(
            title="Select GRR Data File",
            filetypes=[("CSV / Excel Files", "*.csv *.xlsx *.xls"),
                       ("CSV Files", "*.csv"),
                       ("Excel Files", "*.xlsx *.xls"),
                       ("All Files", "*.*")]
        )
        if not path:
            return
        self._csv_path.set(path)
        self._do_load_csv(path)
        self._select_tab(0)

    def _do_load_csv(self, path):
        # 加载新数据 → 清除上一次的分析结果
        self._report = None
        for item in self._res_tree.get_children():
            self._res_tree.delete(item)

        try:
            ext = os.path.splitext(path)[1].lower()

            cosmo_limits = None

            # ── 读取 CSV/Excel ──
            if ext not in (".xlsx", ".xls"):
                df = pd.read_csv(path, low_memory=False)
            else:
                df = pd.read_excel(path, engine="openpyxl")

            # ── 提取 UL/LL 规格限（COSMO 行格式） ──
            # COSMO CSV: 第1行=header, 第2行=UL, 第3行=LL, 第4行起=数据
            # 在 pandas 中，尝试通过"元数据行"检测（关键列为空）
            # 先尝试检测 part/appraiser 列名
            _detect_candidates = lambda keywords: next(
                (c for c in df.columns if any(k in c.lower() for k in keywords)), None)
            _part_candidates = ["dut_id", "part", "unit", "serial", "part_id", "unit_id", "dut", "sn", "s/n"]
            _appr_candidates = ["operator_id", "op_id", "appraiser", "operator", "evaluator", "inspector", "tester", "tech", "station_id"]
            guess_part = _detect_candidates(_part_candidates)
            guess_appr = _detect_candidates(_appr_candidates)
            if guess_part and guess_appr:
                meta_rows = df[df[guess_part].isna() & df[guess_appr].isna()]
                if len(meta_rows) >= 2:
                    ul_row = meta_rows.iloc[0]
                    ll_row = meta_rows.iloc[1]
                    limits_data = []
                    limits_index = []
                    for col in df.columns:
                        ul_val = ul_row[col]
                        ll_val = ll_row[col]
                        if pd.notna(ul_val) or pd.notna(ll_val):
                            try:
                                limits_index.append(col)
                                limits_data.append({
                                    'UL': float(ul_val) if pd.notna(ul_val) else float('nan'),
                                    'LL': float(ll_val) if pd.notna(ll_val) else float('nan'),
                                })
                            except (ValueError, TypeError):
                                pass
                    if limits_data:
                        cosmo_limits = pd.DataFrame(limits_data, index=limits_index)
                        print(f"[LOAD] COSMO 行格式: {len(cosmo_limits)} 个测项有 limits")
                # 过滤掉元数据行
                df = df.dropna(subset=[guess_part, guess_appr])

            self._df = df
            
            # 智能数值转换：只转换本身就是数值的列，不破坏文本列（如 slot, operator_id）
            for c in df.columns:
                try:
                    # 先看看这列是不是基本都是数字
                    sample = df[c].dropna().head(20)
                    if len(sample) == 0:
                        continue
                    # 计算可转换的比例
                    numeric_count = 0
                    for v in sample:
                        try:
                            float(v)
                            numeric_count += 1
                        except (ValueError, TypeError):
                            pass
                    # 如果超过 90% 的值可以转数值，才转（保留文本列）
                    if numeric_count / len(sample) >= 0.9:
                        df[c] = pd.to_numeric(df[c], errors='coerce')
                except Exception:
                    pass
            
            self._set_label(self._lbl_base_columns, str(df.shape[1]))
            # Units 会在列检测后按 part 列唯一值更新，这里先不显示误导性的行数
            self._set_label(self._lbl_base_units, "-")
            
            cols = list(df.columns)
            for lb in [self._part_lb, self._appr_lb, self._order_lb]:
                lb.delete(0, tk.END)
                for c in cols:
                    lb.insert(tk.END, c)
            
            # 自动检测列 — Part（增强关键词 + 低基数启发式）
            self._part_col = None
            self._appr_col = None
            self._order_col = None
            part_found = appr_found = order_found = False
            
            # Part 列检测关键词（按优先级排列）
            part_keywords = [
                "dut", "dut_id", "part", "part_no", "unit", "unit_no",
                "sample", "sn", "serial", "s/n", "device", "uut",
                "board", "specimen", "item_no", "item_id", "lot"
            ]
            # Appraiser 列检测关键词
            appr_keywords = [
                "operator_id", "op_id", "operator", "appraiser", "evaluator",
                "inspector", "tech", "tester", "person", "staff",
            ]
            
            # ── Part 优先：先扫描 exact match dut_id / part_id ──
            for i, c in enumerate(cols):
                cl = c.lower().strip()
                if cl in ("dut_id", "part_id"):
                    self._part_col = c
                    self._part_lb.selection_set(i)
                    self._part_lb.see(i)
                    part_found = True
                    break
            
            # ── Appraiser 优先：先扫描 exact match operator_id / op_id ──
            for i, c in enumerate(cols):
                cl = c.lower().strip()
                if cl in ("operator_id", "op_id"):
                    self._appr_col = c
                    self._appr_lb.selection_set(i)
                    self._appr_lb.see(i)
                    appr_found = True
                    break

            for i, c in enumerate(cols):
                cl = c.lower().strip()

                # Part 列（未命中 exact match 时走关键词）
                if not part_found and any(x in cl for x in part_keywords):
                    self._part_col = c
                    self._part_lb.selection_set(i)
                    self._part_lb.see(i)
                    part_found = True
                    continue  # 避免同一个列被重复检测

                # Appraiser 列（未命中 exact match 时走关键词）
                if not appr_found and any(x in cl for x in appr_keywords):
                    self._appr_col = c
                    self._appr_lb.selection_set(i)
                    self._appr_lb.see(i)
                    appr_found = True
                    continue

                # Order 列
                if not order_found and "time" in cl:
                    self._order_col = c
                    self._order_lb.selection_set(i)
                    self._order_lb.see(i)
                    order_found = True
            
            # ── 启发式 Part 列检测：如果关键词未命中，用低基数非时间列推断 ──
            if not part_found:
                best_col = None
                best_ratio = 1.0
                for c in cols:
                    if c == self._appr_col:
                        continue
                    cl = c.lower()
                    # 排除明显的时间/元数据列
                    if any(x in cl for x in ("time", "date", "timestamp", "index", "id_")):
                        continue
                    n = df[c].dropna().nunique()
                    rows = len(df[c].dropna())
                    if rows > 0 and n > 0 and n / rows < best_ratio and n / rows < 0.5:
                        best_ratio = n / rows
                        best_col = c
                if best_col is not None:
                    self._part_col = best_col
                    for i, c in enumerate(cols):
                        if c == best_col:
                            self._part_lb.selection_set(i)
                            self._part_lb.see(i)
                            break
                    part_found = True
                    print(f"[自动检测] Part列: '{best_col}' (低基数启发式, ratio={best_ratio:.3f})")
            
            # ── Fallback: 完全不检测到 Part 列时，添加合成 "Row_Index" 列 ──
            if not part_found and self._df is not None and len(self._df) > 0:
                synth_col = "Row_Index"
                count = 1
                while synth_col in cols:
                    synth_col = f"Row_Index_{count}"
                    count += 1
                self._df[synth_col] = range(len(self._df))
                self._part_col = synth_col
                cols = list(self._df.columns)  # 更新 cols 列表
                self._part_lb.insert(tk.END, synth_col)
                last_idx = self._part_lb.size() - 1
                if last_idx >= 0:
                    self._part_lb.selection_set(last_idx)
                    self._part_lb.see(last_idx)
                part_found = True
                print(f"[自动检测] 添加合成 Part 列: '{synth_col}' (行索引)")
            
            # 识别测量列
            skip_lower = {"slot", "station_id", "outcome", "start_time", "end_time",
                    "total_test_time", "framework", "msa_id", "run_index",
                    "spec_version", "test_asset_name", "test_description",
                    "test_version", "project", "test_name", "line_type",
                    "line_id", "test_mode", "fail_stop",
                    "sfc_check_out_result", "device_config", "build_phase",
                    "sub_build_phase", "scof_on", "start_time_millis",
                    "cof_on", "retest_policy", "check_in_time_ms",
                    "final_run", "work_order", "retest_state",
                    "campaign_codes", "logger_mode"}
            skip_patterns = ["_index", "_id", "_fixture", "_serial", "_sn", 
                            "batch", "lot", "timestamp", "_date", "_time",
                            "operator", "appraiser", "evaluator", "dut",
                            "part_no", "part_no.", "unit_no", "unit_no.",
                            "note", "comment", "status", "result", "pass_fail",
                            "setup", "config",
                            "limit_", "reference", "nominal", "spec_",
                            "(digital)", "(reference)", "(nominal)",
                            "_type"]
            def _is_skip_col(col_name):
                cl = col_name.lower().strip()
                if cl in skip_lower: return True
                for pat in skip_patterns:
                    if pat in cl: return True
                return False
            
            hing_meas = [c for c in cols if c.startswith("hinge_measurement_")]
            ul_ll_kw = ["_ul", "_ll", "_usl", "_lsl", "_upper", "_lower", "_spec_max", "_spec_min",
                        "limit_top", "top_limit", "limit_upper", "upper_limit",
                        "limit_bottom", "bottom_limit", "limit_lower", "lower_limit"]
            meas_cols = [c for c in hing_meas if not any(x in c.lower() for x in ul_ll_kw)]
            if not meas_cols:
                meas_cols = [c for c in cols if (pd.api.types.is_numeric_dtype(df[c]) and not _is_skip_col(c))]
            
            # Data Preview
            key_cols = []
            if self._part_col and self._part_col in df.columns:
                key_cols.append(self._part_col)
            if self._appr_col and self._appr_col in df.columns:
                key_cols.append(self._appr_col)
            other_cols = [c for c in df.columns if c not in key_cols]
            show_cols = key_cols + other_cols
            show_cols = [c for c in show_cols if c in df.columns]
            preview_df = df[show_cols].head(50) if show_cols else df.head(50)
            self._update_preview_treeview(preview_df)
            self._all_items = meas_cols
            
            # ── UL/LL 检测：COSMO 行格式 → 列匹配 → 全局列 → 无规格限 ──
            # 必须在此处完成检测，再填充 Test Items 树，否则全部显示 ∞
            self._item_limits = {}
            spec_from_rowfmt = spec_from_col = spec_from_global = spec_failed = 0
            ulll_diag = []
            
            # ── 规范化 limits 索引：去 BOM、去空格，构建快速查找映射 ──
            _limits_lookup = {}
            if cosmo_limits is not None and not cosmo_limits.empty:
                for idx in cosmo_limits.index:
                    key = str(idx).lstrip('\ufeff').strip()
                    _limits_lookup[key] = (cosmo_limits.loc[idx, 'UL'], cosmo_limits.loc[idx, 'LL'])
                print(f"[SPEC] cosmo_limits 索引 ({len(_limits_lookup)} 项): {list(_limits_lookup.keys())[:10]}...")
            else:
                print("[SPEC] cosmo_limits 为空/None，将使用列匹配/全局匹配")
            
            for c in meas_cols:
                ul_val = 999999.0
                ll_val = -999999.0
                found_via = "未找到"
                
                # 方式0: COSMO 行格式 — 使用规范化 key 查找
                norm_c = str(c).lstrip('\ufeff').strip()
                if norm_c in _limits_lookup:
                    ul_raw, ll_raw = _limits_lookup[norm_c]
                    # 处理 NaN / None 值（COSMO 标记为无规格限）
                    if pd.notna(ul_raw):
                        ul_val = float(ul_raw)
                        found_via = "行格式"
                        spec_from_rowfmt += 1
                    if pd.notna(ll_raw):
                        ll_val = float(ll_raw)
                        if found_via == "未找到":
                            found_via = "行格式"
                            spec_from_rowfmt += 1  # LL 也算找到
                    if pd.notna(ul_raw) or pd.notna(ll_raw):
                        if len(ulll_diag) < 5:
                            print(f"[SPEC] 行格式 ✓ {c} → UL={ul_val}, LL={ll_val}")
                else:
                    # 方式1: 列匹配（子串 → token重叠）
                    # 适用：1) cosmo limits 为空（标准 CSV）或 2) 此列不在 limits 中
                    if len(ulll_diag) < 3:
                        if _limits_lookup:
                            print(f"[SPEC] 行格式 ✗ {c} 不在 limits 中 (keys:{list(_limits_lookup.keys())[:5]})")
                        else:
                            print(f"[SPEC] 无 cosmo limits，对 {c} 使用列匹配")
                    c_ul_col = c_ll_col = None
                    tf_ul = ["_ul", "_usl", "_upper", "_spec_max"]
                    tf_ll = ["_ll", "_lsl", "_lower", "_spec_min"]
                    for df_col in df.columns:
                        if c in df_col and any(x in df_col.lower() for x in tf_ul):
                            c_ul_col = df_col
                        if c in df_col and any(x in df_col.lower() for x in tf_ll):
                            c_ll_col = df_col
                    
                    if c_ul_col is None or c_ll_col is None:
                        def _tokens(name):
                            clean = ''.join(ch if ch.isalpha() else '_' for ch in name.lower())
                            return set(t for t in clean.split('_') if t and len(t) > 1)
                        c_tokens = _tokens(c)
                        for noise in ('delta','angle','measure','measurement','free','open','test','hinge','sub','and'):
                            c_tokens.discard(noise)
                        bu, bl = 0, 0
                        for df_col in df.columns:
                            if df_col == c: continue
                            overlap = c_tokens & _tokens(df_col)
                            if not overlap: continue
                            score = len(overlap)
                            if c_ul_col is None and any(x in df_col.lower() for x in tf_ul) and score > bu:
                                bu = score; c_ul_col = df_col
                            if c_ll_col is None and any(x in df_col.lower() for x in tf_ll) and score > bl:
                                bl = score; c_ll_col = df_col
                    
                    if c_ul_col and c_ul_col in df.columns:
                        nn = df[c_ul_col].dropna()
                        if len(nn) > 0:
                            ul_val = float(nn.iloc[0]); found_via = f"列匹配({c_ul_col})"; spec_from_col += 1
                    if c_ll_col and c_ll_col in df.columns:
                        nn = df[c_ll_col].dropna()
                        if len(nn) > 0:
                            ll_val = float(nn.iloc[0])
                            if found_via == "未找到": found_via = f"列匹配({c_ll_col})"
                    
                    # 方式2: 全局列
                    if ul_val == 999999.0:
                        for dc in cols:
                            if any(x in dc.lower() for x in ["_ul","_usl","_upper","_spec_max","limit_top","top_limit","limit_upper","upper_limit"]):
                                if not any(mc in dc for mc in meas_cols):
                                    nn = df[dc].dropna()
                                    if len(nn) > 0:
                                        ul_val = float(nn.iloc[0]); found_via = f"全局({dc})"; spec_from_global += 1
                                    break
                    if ll_val == -999999.0:
                        for dc in cols:
                            if any(x in dc.lower() for x in ["_ll","_lsl","_lower","_spec_min","limit_bottom","bottom_limit","limit_lower","lower_limit"]):
                                if not any(mc in dc for mc in meas_cols):
                                    nn = df[dc].dropna()
                                    if len(nn) > 0:
                                        ll_val = float(nn.iloc[0])
                                        if found_via == "未找到": found_via = f"全局({dc})"
                                    break
                    
                    if ul_val == 999999.0 and ll_val == -999999.0:
                        spec_failed += 1; found_via = "无规格限"
                
                self._item_limits[c] = (ul_val, ll_val)
                ulll_diag.append((c, ul_val, ll_val, found_via))
            
            # ── 填充 Test Items（UL/LL 已就绪）──
            # 全部放入左侧原始数据区，右侧已选测项为空，用户手动添加
            self._ti_src_lb.delete(0, tk.END)
            for row_id in self._ti_loaded_tree.get_children():
                self._ti_loaded_tree.delete(row_id)
            self._ti_loaded_data.clear()
            for c in meas_cols:
                self._ti_src_lb.insert(tk.END, c)
            self._ti_refresh_loaded()
            self._update_selected_items()
            
            # 状态栏 — 增强诊断
            diag_parts = []
            if spec_from_rowfmt > 0: diag_parts.append(f"行格式:{spec_from_rowfmt}")
            if spec_from_col > 0: diag_parts.append(f"列匹配:{spec_from_col}")
            if spec_from_global > 0: diag_parts.append(f"全局:{spec_from_global}")
            if spec_failed > 0: diag_parts.append(f"无规格限:{spec_failed}")
            diag_str = " | ".join(diag_parts) if diag_parts else "⚠️ 未检测到任何规格值"
            
            # 详细日志：每个测项及其 spec 来源
            print(f"[SPEC] ====== Spec 检测结果 ({len(meas_cols)} 测项) ======")
            for item, ul, ll, via in ulll_diag:
                ul_s = f"{ul:.2f}" if ul != 999999.0 else "∞"
                ll_s = f"{ll:.2f}" if ll != -999999.0 else "∞"
                print(f"[SPEC]   {item:40s} UL={ul_s:>8s}  LL={ll_s:>8s}  [{via}]")
            print(f"[SPEC] 总计: 行格式={spec_from_rowfmt}, 列匹配={spec_from_col}, 全局={spec_from_global}, 未找到={spec_failed}")
            
            self._status(f"Loaded: {os.path.basename(path)} ({df.shape[0]} rows × {df.shape[1]} cols, {len(meas_cols)} items) | Spec: {diag_str}")
            
            # 更新 Analysis 列表 + 自动 Apply
            self._an_units_lb.delete(0, tk.END)
            self._an_appr_lb.delete(0, tk.END)
            self._apply_filter()
            
        except Exception as e:
            import traceback
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}\n{traceback.format_exc()}")

    def _on_column_selection_changed(self):
        """用户切换 Part/Appraiser 列选择时自动刷新 Units/Appraisers 列表"""
        if self._df is None:
            return
        part_sel = self._part_lb.curselection()
        appr_sel = self._appr_lb.curselection()
        if part_sel:
            self._part_col = self._part_lb.get(part_sel[0])
        if appr_sel:
            self._appr_col = self._appr_lb.get(appr_sel[0])

        # 刷新 Units
        self._an_units_lb.delete(0, tk.END)
        if self._part_col and self._part_col in self._df.columns:
            n = self._df[self._part_col].dropna().nunique()
            self._set_label(self._lbl_base_units, str(n))
            self._set_label(self._lbl_sel_units, str(n))
            for v in sorted(self._df[self._part_col].dropna().unique()):
                self._an_units_lb.insert(tk.END, str(v))
            self._an_units_lb.select_set(0, tk.END)
            self._ab_units_var.set(str(n))
        else:
            self._set_label(self._lbl_base_units, "0")
            self._set_label(self._lbl_sel_units, "0")
            self._ab_units_var.set("0")

        # 刷新 Appraisers
        self._an_appr_lb.delete(0, tk.END)
        if self._appr_col and self._appr_col in self._df.columns:
            n = self._df[self._appr_col].dropna().nunique()
            self._set_label(self._lbl_base_appraisers, str(n))
            self._set_label(self._lbl_sel_appraisers, str(n))
            for v in sorted(self._df[self._appr_col].dropna().unique()):
                self._an_appr_lb.insert(tk.END, str(v))
            self._an_appr_lb.select_set(0, tk.END)
            self._ab_appraisers_var.set(str(n))
        else:
            self._set_label(self._lbl_base_appraisers, "0")
            self._set_label(self._lbl_sel_appraisers, "0")
            self._ab_appraisers_var.set("0")

        # 刷新 Trials
        if (self._part_col and self._appr_col
                and self._part_col in self._df.columns
                and self._appr_col in self._df.columns):
            grp = self._df.dropna(subset=[self._part_col, self._appr_col])
            trials = grp.groupby([self._part_col, self._appr_col]).size()
            t_min = int(trials.min()) if len(trials) > 0 else 0
            t_use = 3  # 默认 3（行业标准），用户可根据测试计划手动修改
            self._set_label(self._lbl_base_trials, str(t_min))
            self._set_label(self._lbl_sel_trials, str(t_use))
            self._ab_trials_var.set(str(t_use))
            self._refresh_avail_trials_hint(t_min)

        # 刷新 Test Items
        n_items = len(self._selected_items) if self._selected_items else len(self._all_items)
        self._set_label(self._lbl_sel_test_items, str(n_items))

        # 同时刷新 Data Preview
        self._refresh_data_preview()

    def _refresh_data_preview(self):
        """Refresh the Data Preview treeview with selected columns"""
        if self._df is None:
            return
        df = self._df
        preview_cols = []
        if self._part_col and self._part_col in df.columns:
            preview_cols.append(self._part_col)
        if self._appr_col and self._appr_col in df.columns:
            preview_cols.append(self._appr_col)
        for c in df.columns:
            if c not in preview_cols:
                preview_cols.append(c)
        preview_df = df[preview_cols].head(50) if preview_cols else df.head(50)
        self._update_preview_treeview(preview_df)

    def _apply_filter(self):
        if self._df is None:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return
        df = self._df

        # 从 listbox 读取用户当前选中的列名
        part_sel = self._part_lb.curselection()
        appr_sel = self._appr_lb.curselection()
        if part_sel:
            self._part_col = self._part_lb.get(part_sel[0])
        if appr_sel:
            self._appr_col = self._appr_lb.get(appr_sel[0])

        # 刷新 Data Preview — 显示所有列（不限制数量）
        preview_cols = []
        if self._part_col and self._part_col in df.columns:
            preview_cols.append(self._part_col)
        if self._appr_col and self._appr_col in df.columns:
            preview_cols.append(self._appr_col)
        # 补充其余列（保留原有顺序）
        for c in df.columns:
            if c not in preview_cols:
                preview_cols.append(c)
        preview_df = df[preview_cols].head(50) if preview_cols else df.head(50)
        self._update_preview_treeview(preview_df)

        if self._part_col and self._part_col in df.columns:
            n = df[self._part_col].dropna().nunique()
            self._set_label(self._lbl_base_units, str(n))
            self._set_label(self._lbl_sel_units,  str(n))
            self._an_units_lb.delete(0, tk.END)
            for v in sorted(df[self._part_col].dropna().unique()):
                self._an_units_lb.insert(tk.END, str(v))
            self._an_units_lb.select_set(0, tk.END)
            self._ab_units_var.set(str(n))

        if self._appr_col and self._appr_col in df.columns:
            n = df[self._appr_col].dropna().nunique()
            self._set_label(self._lbl_base_appraisers, str(n))
            self._set_label(self._lbl_sel_appraisers,  str(n))
            self._an_appr_lb.delete(0, tk.END)
            for v in sorted(df[self._appr_col].dropna().unique()):
                self._an_appr_lb.insert(tk.END, str(v))
            self._an_appr_lb.select_set(0, tk.END)
            self._ab_appraisers_var.set(str(n))

        if self._part_col and self._appr_col and self._part_col in df.columns and self._appr_col in df.columns:
            grp = df.dropna(subset=[self._part_col, self._appr_col])
            trials = grp.groupby([self._part_col, self._appr_col]).size()
            t_min = int(trials.min()) if len(trials) > 0 else 0
            t_use = 3  # 默认 3（行业标准），用户可根据测试计划手动修改
            self._set_label(self._lbl_base_trials, str(t_min))
            self._set_label(self._lbl_sel_trials,  str(t_use))
            self._ab_trials_var.set(str(t_use))
            self._refresh_avail_trials_hint(t_min)

        n_items = len(self._selected_items) if self._selected_items else len(self._all_items)
        self._set_label(self._lbl_sel_test_items,  str(n_items))
        self._status(f"Filter applied: part={self._part_col}, appraiser={self._appr_col}")

    def _run_grr(self):
        csv_path = self._csv_path.get()
        if not csv_path:
            messagebox.showwarning("No CSV", "Please load a CSV file first.")
            return
        items = self._selected_items if self._selected_items else self._all_items
        method = self._grr_method_var.get()
        output_format = self._output_format_var.get()
        study_const = float(self._study_const_var.get())

        def _worker():
            try:
                self._status(f"Running GRR analysis ({method})...")

                # 生成 trial 编号列（按 (part, appraiser) 分组累加计数）
                self._df["_trial_no"] = self._df.groupby(
                    [self._part_col, self._appr_col], sort=False
                ).cumcount()

                # 读取用户选择的 trial 数（默认 3 匹配 COSMO）
                try:
                    num_trial = int(self._ab_trials_var.get())
                except (ValueError, TypeError):
                    num_trial = 3

                # 过滤数据
                filter_units = list(self._sel_units) if self._sel_units else (
                    list(self._df[self._part_col].dropna().unique()) if self._part_col else [])
                filter_appraisers = list(self._sel_appraisers) if self._sel_appraisers else (
                    list(self._df[self._appr_col].dropna().unique()) if self._appr_col else [])

                # 单 Unit 警告
                if len(filter_units) <= 1:
                    self.after(0, lambda: messagebox.showwarning(
                        "单 Unit 警告",
                        f"当前选中的 Unit (零件) 数量仅为 {len(filter_units)}。\n\n"
                        "GRR 分析需要至少 2 个不同的零件才能计算零件变异 (PV)。\n"
                        "当只有 1 个零件时，PV = 0，%GRR 会显示为 100%。\n\n"
                        "请检查：\n"
                        "1. Load 标签页中的 Part 列是否选错（如 dut_index 而不是 dut_id）\n"
                        "2. Analysis 标签页中是否只勾选了 1 个 Unit"
                    ))

                # 过滤 DataFrame
                df_f = self._df.copy()
                if filter_units:
                    units_set = set(str(u) for u in filter_units if u is not None)
                    if units_set:
                        df_f = df_f[df_f[self._part_col].astype(str).isin(units_set)]
                if filter_appraisers:
                    apprs_set = set(str(a) for a in filter_appraisers if a is not None)
                    if apprs_set:
                        df_f = df_f[df_f[self._appr_col].astype(str).isin(apprs_set)]
                df_f = df_f[df_f["_trial_no"] < num_trial]

                if len(df_f) == 0:
                    self.after(0, lambda: messagebox.showerror("No Data", "No data after filtering."))
                    return

                results_list = []
                for item in items:
                    if item not in df_f.columns:
                        continue
                    ul, ll = self._item_limits.get(item, (999999.0, -999999.0))

                    # 选择计算方法
                    main_effect = (method == "ANOVA Main Effect")
                    if method.lower() == "range":
                        r = compute_grr_range(
                            df_f,
                            operator_col=self._appr_col,
                            part_col=self._part_col,
                            trial_col="_trial_no",
                            measurement_col=item,
                            ul=ul, ll=ll,
                            output_format=output_format,
                            study_const=study_const,
                        )
                    else:
                        r = compute_grr_anova(
                            df_f,
                            operator_col=self._appr_col,
                            part_col=self._part_col,
                            trial_col="_trial_no",
                            measurement_col=item,
                            ul=ul, ll=ll,
                            main_effect=main_effect,
                            output_format=output_format,
                            study_const=study_const,
                        )
                    results_list.append(r)

                if items:
                    results_list = [r for r in results_list if r.name in items]

                # 构建 data_matrix
                for grr_res in results_list:
                    item = grr_res.name
                    try:
                        cols_needed = [self._part_col, self._appr_col, item]
                        missing = [c for c in cols_needed if c not in df_f.columns]
                        if missing:
                            print(f"[DATA_MATRIX] {item}: missing columns {missing}")
                            continue

                        df_item = df_f[cols_needed + ["_trial_no"]].dropna(subset=[item])
                        if len(df_item) == 0:
                            continue

                        df_item = df_item.copy()
                        df_item["_col"] = (df_item[self._appr_col].astype(str).str.strip()
                                           + "." + df_item["_trial_no"].astype(int).astype(str))

                        dm = df_item.pivot_table(
                            index=self._part_col,
                            columns="_col",
                            values=item,
                            aggfunc="first"
                        )
                        if dm.empty:
                            continue
                        # 排序列：按 operator + trial
                        def _sort_key(x):
                            parts = x.rsplit('.', 1)
                            op_str = parts[0]
                            trial_str = parts[1] if len(parts) > 1 else "0"
                            try:
                                op_tuple = (0, float(op_str), op_str)
                            except (ValueError, TypeError):
                                op_tuple = (1, 0, op_str)
                            try:
                                t = int(float(trial_str))
                            except (ValueError, TypeError):
                                t = 0
                            return op_tuple + (t,)
                        dm = dm.reindex(sorted(dm.columns, key=_sort_key), axis=1)
                        grr_res.data_matrix = dm
                    except Exception as e:
                        print(f"[DATA_MATRIX] {item}: {e}")

                num_units = len(filter_units)
                num_appraisers = len(filter_appraisers)
                appraisers = [str(a) for a in filter_appraisers] if filter_appraisers else []
                unit_serials = [str(u) for u in filter_units] if filter_units else []

                import datetime
                report = GrrReport(
                    report_date=datetime.datetime.now().strftime("%Y-%m-%d"),
                    method=method,
                    results=results_list,
                    num_units=num_units,
                    num_appraisers=num_appraisers,
                    num_trials=num_trial,
                    appraisers=appraisers,
                    unit_serials=unit_serials,
                )
                self._report = report

                self.after(0, lambda: self._set_label(self._lbl_sel_units,      str(num_units)))
                self.after(0, lambda: self._set_label(self._lbl_sel_appraisers, str(num_appraisers)))
                self.after(0, lambda: self._set_label(self._lbl_sel_trials,     str(num_trial)))
                self.after(0, lambda: self._set_label(self._lbl_sel_test_items, str(len(results_list))))
                self.after(0, lambda: self._status(f"GRR complete ({method}): {len(results_list)} items."))
                self.after(0, self._refresh_results_view)
                self.after(0, lambda: self._select_tab(3))
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                self.after(0, lambda: messagebox.showerror("GRR Error", tb))
                self.after(0, lambda: self._status(f"Error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _export_csv(self):
        if not self._report:
            messagebox.showwarning("No Results", "Please run GRR analysis first.")
            return
        path = filedialog.asksaveasfilename(title="Save CSV", defaultextension=".csv",
                                             filetypes=[("CSV", "*.csv")])
        if not path:
            return
        import csv as csv_mod
        mode = self._show_mode.get()
        with open(path, "w", newline="", encoding="utf-8") as f:
            if mode == "%Variance":
                headers = ["#", "Item", "%rr", "%ev", "%av", "%iv", "%pv", "ev", "av", "iv", "pv", "tv", "Rating"]
                w = csv_mod.writer(f)
                w.writerow(headers)
                for i, r in enumerate(self._report.results, 1):
                    w.writerow([i, r.name, r.pct_rr, r.pct_ev, r.pct_av, r.pct_iv, r.pct_pv,
                                r.ev, r.av, r.iv, r.pv, r.tv, r.rating])
            else:
                headers = ["#", "Item", "Tolerance", "%rr/Tol", "%ev/Tol", "%av/Tol", "%iv/Tol", "%pv/Tol", "Rating"]
                w = csv_mod.writer(f)
                w.writerow(headers)
                for i, r in enumerate(self._report.results, 1):
                    tol = r.tolerance
                    # 使用已存储的 pct_tol 值（已按用户选择的 study_const 计算）
                    pct_rr_t = f"{r.pct_tol:.4f}" if r.pct_tol else ""
                    pct_ev_t = f"{r.pct_tol_ev:.4f}" if r.pct_tol_ev else ""
                    pct_av_t = f"{r.pct_tol_av:.4f}" if r.pct_tol_av else ""
                    pct_iv_t = f"{r.pct_tol_iv:.4f}" if r.pct_tol_iv else ""
                    pct_pv_t = f"{r.pct_tol_pv:.4f}" if r.pct_tol_pv else ""
                    w.writerow([i, r.name, tol, pct_rr_t, pct_ev_t, pct_av_t, pct_iv_t, pct_pv_t, r.rating])
        messagebox.showinfo("Saved", f"CSV saved:\n{path}")

    def _export_pdf(self):
        if not self._report:
            messagebox.showwarning("No Results", "Please run GRR analysis first.")
            return
        path = filedialog.asksaveasfilename(title="Save PDF", defaultextension=".pdf",
                                             filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        def _worker():
            try:
                import os
                import matplotlib
                os.environ["MPLCONFIGDIR"] = "/tmp/mpl_grr"
                matplotlib.use("Agg")
                from grr_pdf import generate_pdf
                self._status("Generating PDF...")
                generate_pdf(self._report, path)
                # 清理 matplotlib 全局状态，避免第二次运行卡住
                matplotlib.pyplot.close("all")
                import gc
                gc.collect()
                self.after(0, lambda: self._status("PDF report generated successfully!"))
                self.after(0, lambda: messagebox.showinfo("Done", f"PDF report generated successfully!\n\n{path}"))
            except Exception as e:
                import traceback
                import matplotlib
                matplotlib.pyplot.close("all")
                self.after(0, lambda: messagebox.showerror("PDF Error", traceback.format_exc()))
        threading.Thread(target=_worker, daemon=True).start()

    def _export_consistency_pdf(self):
        if not self._report:
            messagebox.showwarning("No Results", "Please run GRR analysis first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save Consistency Report PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        def _worker():
            try:
                import os
                import matplotlib
                os.environ["MPLCONFIGDIR"] = "/tmp/mpl_grr"
                matplotlib.use("Agg")
                from grr_pdf import generate_consistency_pdf
                self._status("Generating Consistency Report PDF...")
                generate_consistency_pdf(self._report, path)
                matplotlib.pyplot.close("all")
                import gc
                gc.collect()
                self.after(0, lambda: self._status("Consistency report generated successfully!"))
                self.after(0, lambda: messagebox.showinfo("Done", f"Consistency report generated successfully!\n\n{path}"))
            except Exception as e:
                import traceback
                import matplotlib
                matplotlib.pyplot.close("all")
                self.after(0, lambda: messagebox.showerror("PDF Error", traceback.format_exc()))
        threading.Thread(target=_worker, daemon=True).start()

    def _json_to_csv(self):
        """将 JSON 文件转换为 COSMO 行格式 CSV（选择文件夹，自动合并所有 .json）"""
        # 选择包含 JSON 文件的文件夹
        folder = filedialog.askdirectory(title="Select Folder with JSON Files")
        if not folder:
            return

        # 递归扫描文件夹内所有 .json 文件（包括子文件夹）
        srcs = sorted(glob.glob(os.path.join(folder, "**", "*.json"), recursive=True))
        if not srcs:
            messagebox.showwarning("No JSON Files", f"No .json files found in:\n{folder}")
            return

        # 保存目标 CSV（检查文件名冲突）
        folder_name = os.path.basename(folder) or "grr_data"
        base_name = folder_name
        safe_name = base_name
        counter = 1
        parent_dir = os.path.dirname(folder)
        while os.path.exists(os.path.join(parent_dir, f"{safe_name}.csv")):
            safe_name = f"{base_name}_{counter}"
            counter += 1
        dst = filedialog.asksaveasfilename(
            title=f"Save combined CSV ({len(srcs)} JSON files)",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"{safe_name}.csv")
        if not dst:
            return

        try:
            all_measurements = {}   # {col_name: [values]}
            all_limits = {}         # {col_name: (ul, ll)}
            max_rows = 0
            header_names = []       # 保存列的顺序
            file_names = []         # 记录每个数据来自哪个文件

            for src_idx, src in enumerate(srcs):
                with open(src, encoding="utf-8") as f:
                    raw = json.load(f)

                base = os.path.splitext(os.path.basename(src))[0]

                # ── ① 检测生产测试站 JSON 格式 (phases[].measurements[]) ──
                # 每个文件代表一个 DUT，包含多项测量，所有文件合并为一行一条记录
                if isinstance(raw, dict) and "phases" in raw:
                    # ── 动态提取所有顶层标量字段（排除列表/对象类型）──
                    skip_top_keys = {"phases", "log_records", "attachments", "metadata"}
                    meta_fields = []
                    for k, v in raw.items():
                        if k in skip_top_keys:
                            continue
                        # 处理时间戳：start_time_millis / end_time_millis 转为可读时间
                        if k.endswith("_time_millis") and isinstance(v, str) and v.isdigit():
                            try:
                                dt = datetime.datetime.fromtimestamp(int(v) / 1000.0)
                                meta_fields.append((k.replace("_millis", ""), dt.strftime("%Y-%m-%d %H:%M:%S")))
                                continue
                            except (ValueError, OSError):
                                pass
                        if not isinstance(v, (str, int, float, bool)):
                            continue
                        meta_fields.append((k, str(v)))

                    # ── 展平 metadata 对象 ──
                    md = raw.get("metadata", {})
                    if isinstance(md, dict):
                        for mk, mv in md.items():
                            if isinstance(mv, list):
                                mv = ", ".join(str(x) for x in mv)
                            if not isinstance(mv, (str, int, float, bool)):
                                continue
                            meta_fields.append((f"metadata_{mk}", str(mv)))

                    # 将元数据列合并到全局列（放在测量列前面）
                    # 延迟对齐：等所有文件处理完后再统一填充空值
                    for meta_name, meta_val in meta_fields:
                        if meta_name not in all_measurements:
                            header_names.append(meta_name)
                            all_measurements[meta_name] = []
                            all_limits[meta_name] = (None, None)
                        # 用当前已处理文件数做对齐
                        while len(all_measurements[meta_name]) < len(file_names):
                            all_measurements[meta_name].append("")
                        all_measurements[meta_name].append(str(meta_val))

                    # ── 提取 phases 中的数值测量项 ──
                    for phase in raw.get("phases", []):
                        for m in phase.get("measurements", []):
                            m_name = m.get("name", "")
                            if not m_name:
                                continue
                            m_value = m.get("measured_value", "")
                            # 跳过非数值测量（如字符串类型的 SN、版本号等）
                            try:
                                m_val = float(m_value.strip('"'))
                            except (ValueError, TypeError):
                                continue

                            # 从 validators 解析 UL/LL，如 "-1000.0 <= x <= 1000.0"
                            ul, ll = None, None
                            for v_str in m.get("validators", []):
                                match = re.match(
                                    r'\s*([\d.-]+)\s*<=\s*x\s*<=\s*([\d.-]+)\s*',
                                    v_str.strip()
                                )
                                if match:
                                    ll = float(match.group(1))
                                    ul = float(match.group(2))
                                    break

                            # 合并到全局列
                            if m_name not in all_measurements:
                                header_names.append(m_name)
                                all_measurements[m_name] = []
                                # 用第一个文件的 UL/LL 作为整列的规格限
                                all_limits[m_name] = (ul, ll)
                            # 确保对齐前面的元数据行数
                            while len(all_measurements[m_name]) < len(file_names):
                                all_measurements[m_name].append("")
                            all_measurements[m_name].append(m_val)
                    file_names.append(base)
                    continue  # 跳过旧格式解析

                # ── ② 旧格式解析（兼容已有 JSON 结构）──
                items = None
                if isinstance(raw, list):
                    items = raw
                elif isinstance(raw, dict):
                    for key in ("items", "data", "records", "results", "measurements", "values"):
                        candidate = raw.get(key)
                        if isinstance(candidate, list) and len(candidate) > 0:
                            items = candidate
                            break
                    if items is None:
                        for key in ("data", "result", "dashboard"):
                            inner = raw.get(key)
                            if isinstance(inner, dict):
                                for k2 in ("items", "records", "results", "measurements"):
                                    candidate = inner.get(k2)
                                    if isinstance(candidate, list) and len(candidate) > 0:
                                        items = candidate
                                        break
                            if items:
                                break
                    if items is None:
                        items = [raw]

                if not items:
                    print(f"[WARN] {src}: 无法提取数据项")
                    continue

                for item_idx, item in enumerate(items):
                    if not isinstance(item, dict):
                        continue

                    # 提取 measurement name
                    name = None
                    for nk in ("name", "test_name", "item", "id", "measurement", "test", "label", "key", "parameter"):
                        v = item.get(nk)
                        if v is not None and v != "":
                            name = str(v).strip()
                            break
                    if name is None or name == "":
                        name = f"{base}_{item_idx}"

                    # 提取 UL/LL
                    ul = None
                    ll = None
                    for uk in ("ul", "usl", "upper_limit", "upper_spec", "spec_max", "upper", "max_value", "high_limit"):
                        v = item.get(uk)
                        if v is not None and v != "":
                            try:
                                ul = float(v)
                                break
                            except (ValueError, TypeError):
                                pass
                    for lk in ("ll", "lsl", "lower_limit", "lower_spec", "spec_min", "lower", "min_value", "low_limit"):
                        v = item.get(lk)
                        if v is not None and v != "":
                            try:
                                ll = float(v)
                                break
                            except (ValueError, TypeError):
                                pass

                    # 提取测量数据 —— 查找数组类型的字段
                    meas_values = []
                    for dk in ("measurements", "values", "data", "readings", "samples", "results"):
                        v = item.get(dk)
                        if isinstance(v, list) and len(v) > 0:
                            for mv in v:
                                try:
                                    meas_values.append(float(mv))
                                except (ValueError, TypeError):
                                    pass
                            break

                    # 如果没找到数组，尝试将数值字段收集为数据
                    if not meas_values:
                        for vk, vv in item.items():
                            if vk in ("name", "test_name", "item", "id", "measurement", "test", "label", "key", "parameter",
                                      "ul", "usl", "upper_limit", "upper_spec", "spec_max", "upper", "max_value", "high_limit",
                                      "ll", "lsl", "lower_limit", "lower_spec", "spec_min", "lower", "min_value", "low_limit",
                                      "measurements", "values", "data", "readings", "samples", "results"):
                                continue
                            try:
                                meas_values.append(float(vv))
                            except (ValueError, TypeError):
                                pass

                    # 使用文件后缀区分同名测量项
                    if name in all_measurements:
                        suffix = 1
                        while f"{name}_{suffix}" in all_measurements:
                            suffix += 1
                        name = f"{name}_{suffix}"

                    header_names.append(name)
                    all_measurements[name] = meas_values
                    actual_ul = ul if (ul is not None and ul != 999) else None
                    actual_ll = ll if (ll is not None and ll != 999) else None
                    all_limits[name] = (actual_ul, actual_ll)
                    if len(meas_values) > max_rows:
                        max_rows = len(meas_values)
                    file_names.append(base)

            # 更新 max_rows（phases 格式下由所有文件合并后的列长度决定）
            if header_names:
                max_rows = max((len(v) for v in all_measurements.values()), default=0)

            if not all_measurements:
                messagebox.showerror("Error", "No measurement data found in JSON files.")
                return

            # ── 构建 COSMO 行格式 CSV ──
            # pandoc COSMO 格式期望:
            #   第1行: 列名（测量项名称，pd.read_csv 自动用作 header）
            #   第2行: UL 值（parse_formatted_df 取 df.iloc[0]，即 header 后的第一行）
            #   第3行: LL 值（parse_formatted_df 取 df.iloc[1]，即 header 后的第二行）
            #   第4行起: 数据（parse_formatted_df 取 df.iloc[2:]）
            # 旧版有 name row 但 COSMO 原生 parse_formatted_df 不支持，已移除。
            
            cols = header_names
            with open(dst, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                
                # 第1行: 列名 (= 测量项名称, pd.read_csv 自动当作 header)
                writer.writerow(cols)
                
                # 第2行: UL 行（None 输出空字符串 → COSMO parse_formatted_df 会转 NaN）
                ul_row = []
                for c in cols:
                    ul_val = all_limits[c][0]
                    if ul_val is None:
                        ul_row.append("")
                    else:
                        ul_row.append(f"{ul_val:.0f}" if ul_val == int(ul_val) else f"{ul_val}")
                writer.writerow(ul_row)
                
                # 第3行: LL 行（None 输出空字符串 → COSMO parse_formatted_df 会转 NaN）
                ll_row = []
                for c in cols:
                    ll_val = all_limits[c][1]
                    if ll_val is None:
                        ll_row.append("")
                    else:
                        ll_row.append(f"{ll_val:.0f}" if ll_val == int(ll_val) else f"{ll_val}")
                writer.writerow(ll_row)
                
                # 第4行起: 数据
                for row_idx in range(max_rows):
                    data_row = []
                    for c in cols:
                        vals = all_measurements[c]
                        if row_idx < len(vals):
                            v = vals[row_idx]
                            data_row.append(f"{v}" if not pd.isna(v) else "")
                        else:
                            data_row.append("")
                    writer.writerow(data_row)

            msg = f"✅ JSON to CSV conversion successful!\n\nFolder: {os.path.basename(folder)}\nCombined {len(srcs)} JSON files → {os.path.basename(dst)}\n{len(cols)} items, {max_rows} data rows"
            messagebox.showinfo("Conversion Complete", msg)
            self._status(msg)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to convert JSON:\n{e}")

    # ── 辅助 ──
    def _set_label(self, lbl, text):
        lbl.config(text=text)

    def _refresh_avail_trials_hint(self, t_min):
        """更新 trials 输入框下方的可用 trial 提示"""
        if hasattr(self, '_lbl_avail_trials') and self._lbl_avail_trials:
            self._lbl_avail_trials.config(text=f"可用: {t_min}")

    def _update_preview_treeview(self, df):
        """用 Treeview 显示 DataFrame 预览，支持水平滚动"""
        tree = self._preview_tree
        # 清除旧列和数据
        tree.delete(*tree.get_children())
        for col in tree["columns"]:
            tree.heading(col, text="")
        tree["columns"] = ()
        if df is None or df.empty:
            return
        cols = list(df.columns)
        tree["columns"] = cols
        for c in cols:
            tree.heading(c, text=c)
            # 根据列名长度估算宽度，长列名放宽上限，短列收紧
            header_w = len(str(c)) * 8 + 24
            # 同时看看数据内容的典型长度
            sample_vals = [str(v) for v in df[c].dropna().head(5).values]
            content_w = max((len(v) * 7 + 16 for v in sample_vals), default=0)
            col_w = min(max(header_w, content_w, 50), 350)
            tree.column(c, width=int(col_w), anchor="center", stretch=False)
        # 插入数据（前50行）
        for _, row in df.iterrows():
            vals = [str(v) if pd.notna(v) else "" for v in row.values]
            tree.insert("", tk.END, values=vals)

    def _set_preview_text(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)

    def _status(self, msg):
        self.title(f"Cosmo v2.5.2e - {msg}")


# ── 入口 ──────────────────────────────────────────────
def main():
    app = CosmoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
