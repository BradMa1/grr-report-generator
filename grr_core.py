"""
GRR 分析核心模块 — ANOVA / Range 方法
======================================
实现 Gauge Repeatability & Reproducibility (量具重复性与再现性) 分析，
完全匹配 COSMO 软件的输出格式，支持三种方法：

  - ANOVA        : 完整方差分析（含交互作用）
  - ANOVA Main   : 主效应 ANOVA（不含交互作用，IV 合并入 EV）
  - Range        : Xbar/R 极差法

输入数据格式（CSV）：
  - operator_id: 评价人编号 (1.0, 2.0, 3.0)
  - dut_id: 零件编号 (e.g. 65130DLFS00001)
  - run_index: 试验次数 (0, 1, 2)
  - 测量列: hinge_measurement_* 命名的数值列
"""

import math
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional


# ── 评级阈值（基于 P/T %Tolerance） ──────────────────────
# COSMO 使用 P/T = (σ_GRR × 5.15) / (UL - LL) × 100
GRR_RATING_THRESHOLDS = [
    (10, "Excellent"),
    (20, "Good"),
    (30, "Marginal"),
    (float("inf"), "Poor"),
]


def rate_grr(pct_grr: float) -> str:
    """根据 %GRR 返回评级"""
    for threshold, rating in GRR_RATING_THRESHOLDS:
        if pct_grr <= threshold:
            return rating
    return "Poor"


# ── d2 值查表 (AIAG MSA 4th) ─────────────────────────────
D2_TABLE = {
    2: 1.128,
    3: 1.693,
    4: 2.059,
    5: 2.326,
    6: 2.534,
    7: 2.704,
    8: 2.847,
    9: 2.970,
    10: 3.078,
}


def _d2(n: int) -> float:
    """根据样本数 n 查 d2 值（超出范围用近似值）"""
    if n in D2_TABLE:
        return D2_TABLE[n]
    # 近似: d2 ≈ 0.304 * n + 0.8 (线性近似)
    return min(0.304 * n + 0.8, 4.0)


# ══════════════════════════════════════════════════════════
#  GRR 计算结果数据结构
# ══════════════════════════════════════════════════════════

@dataclass
class GrrResult:
    """单个测量项的 GRR 分析结果 — 匹配 COSMO 输出"""
    name: str
    method: str = "ANOVA"
    ul: float = float('inf')
    ll: float = float('-inf')

    # 第一行结果 (study variation, 默认 ×0.3 缩放)
    grr_study: float = 0.0     # 汇总表/第一行的 grr
    repeat_study: float = 0.0  # 汇总表/第一行的 repeatability
    reprod_study: float = 0.0  # 汇总表/第一行的 reproducibility

    # 标准差分量 (匹配 COSMO 第二行: rr ev av iv pv tv)
    rr: float = 0.0      # GRR 标准差 = sqrt(EV² + AV² + IV²)
    ev: float = 0.0      # Equipment Variation 标准差
    av: float = 0.0      # Appraiser Variation 标准差
    iv: float = 0.0      # Interaction Variation 标准差
    pv: float = 0.0      # Part Variation 标准差
    tv: float = 0.0      # Total Variation 标准差

    # %Contribution (方差占比 × 100) — 匹配 COSMO 桌面
    pct_rr: float = 0.0  # %GRR = σ²_GRR / σ²_TV × 100
    pct_ev: float = 0.0  # %EV = σ²_EV / σ²_TV × 100
    pct_av: float = 0.0  # %AV = σ²_AV / σ²_TV × 100
    pct_iv: float = 0.0  # %IV = σ²_IV / σ²_TV × 100
    pct_pv: float = 0.0  # %PV = σ²_PV / σ²_TV × 100

    # P/T 比率 (Precision-to-Tolerance) = σ × 5.15 / Tolerance × 100
    # 这是 COSMO 用于评级的标准
    pct_tol: float = 0.0     # %GRR P/T
    pct_tol_ev: float = 0.0  # %EV P/T
    pct_tol_av: float = 0.0  # %AV P/T
    pct_tol_iv: float = 0.0  # %IV P/T
    pct_tol_pv: float = 0.0  # %PV P/T

    # 数据矩阵 (用于详情页)
    data_matrix: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def _has_spec_limits(self) -> bool:
        """是否有有效规格限"""
        return self.ul != float('inf') and self.ll != float('-inf') and self.ul > self.ll

    @property
    def rating(self) -> str:
        """评级：有规格限时用 P/T (%Tolerance)，否则用 %GRR (%Study Variation)"""
        if self._has_spec_limits:
            return rate_grr(self.pct_tol)
        else:
            return rate_grr(self.pct_rr)

    @property
    def tolerance(self) -> float:
        return self.ul - self.ll

    def to_summary_row(self) -> dict:
        row = {
            "Item": self.name,
            "GRR": round(self.grr_study, 3),
            "Repeat": round(self.repeat_study, 3),
            "Reprod": round(self.reprod_study, 3),
            "pct_rr": round(self.pct_rr, 3),
            "Result": self.rating,
        }
        if self._has_spec_limits:
            row["pct_tol"] = round(self.pct_tol, 3)
        else:
            row["pct_tol"] = None  # 无规格限
        return row


@dataclass
class GrrReport:
    """完整的 GRR 报告"""
    version: str = "1.0.0"
    report_date: str = ""
    method: str = "ANOVA"
    num_appraisers: int = 0
    appraisers: List[str] = field(default_factory=list)
    num_units: int = 0
    unit_serials: List[str] = field(default_factory=list)
    num_trials: int = 0
    results: List[GrrResult] = field(default_factory=list)


# ══════════════════════════════════════════════════════════
#  ANOVA 方法（完整 + 主效应）
# ══════════════════════════════════════════════════════════

def compute_grr_anova(
    data: pd.DataFrame,
    operator_col: str = "operator_id",
    part_col: str = "dut_id",
    trial_col: str = "trial",
    measurement_col: str = "measurement",
    ul: float = float('inf'),
    ll: float = float('-inf'),
    main_effect: bool = False,
    output_format: str = "tol",
    study_const: float = 6.0,
) -> GrrResult:
    """
    对单个测量列执行 ANOVA GRR 分析。

    main_effect=True 时使用主效应模型（不含交互作用），
    IV 合并入 EV（Equipment Variation）。

    output_format:
      - "tol": P/T = σ × study_const / Tolerance × 100（匹配 COSMO 桌面）
      - "tv":  Study Variation = σ × study_const（AIAG 标准）
    """
    df = data[[operator_col, part_col, trial_col, measurement_col]].copy()
    df.columns = ["operator", "part", "trial", "value"]
    df = df.dropna(subset=["value"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # 构建数据矩阵
    matrix = df.pivot_table(
        index="part",
        columns=["operator", "trial"],
        values="value",
        aggfunc="first",
    )
    matrix.columns = [f"{int(float(op))}.{int(float(tr))}" for op, tr in matrix.columns]

    values = df["value"].values
    operators = df["operator"].values
    parts = df["part"].values

    unique_ops = np.unique(operators)
    unique_parts = np.unique(parts)
    n_ops = len(unique_ops)
    n_parts = len(unique_parts)
    n = len(values) // (n_ops * n_parts)  # trials per cell

    grand_mean = np.mean(values)

    # SS_operator (评价人)
    ss_operator = 0.0
    for op in unique_ops:
        mask = operators == op
        group_mean = np.mean(values[mask])
        ss_operator += len(values[mask]) * (group_mean - grand_mean) ** 2

    # SS_part (零件)
    ss_part = 0.0
    for part in unique_parts:
        mask = parts == part
        group_mean = np.mean(values[mask])
        ss_part += len(values[mask]) * (group_mean - grand_mean) ** 2

    # SS_operator_part (交互作用) + SS_within (组内误差)
    ss_interaction = 0.0
    ss_within = 0.0
    for op in unique_ops:
        op_mean = np.mean(values[operators == op])
        for part in unique_parts:
            part_mean = np.mean(values[parts == part])
            mask = (operators == op) & (parts == part)
            cell_values = values[mask]
            if len(cell_values) == 0:
                continue
            cell_mean = np.mean(cell_values)
            ss_interaction += len(cell_values) * (
                cell_mean - op_mean - part_mean + grand_mean
            ) ** 2
            ss_within += np.sum((cell_values - cell_mean) ** 2)

    # 自由度
    df_operator = n_ops - 1
    df_part = n_parts - 1
    df_interaction = (n_ops - 1) * (n_parts - 1)
    df_within = n_ops * n_parts * (n - 1)
    df_total = n_ops * n_parts * n - 1

    # 均方
    ms_operator = ss_operator / df_operator if df_operator > 0 else 0
    ms_part = ss_part / df_part if df_part > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_within = ss_within / df_within if df_within > 0 else 0

    # ── 方差分量 ──
    if main_effect:
        # 主效应模型：IV 合并入 EV，且 EV 使用 pooled error（匹配 COSMO）
        # var_ev = (SS_Within + SS_Interaction) / (df_Within + df_Interaction)
        var_ev = (ss_within + ss_interaction) / (df_within + df_interaction)

        # σ²_AV = (MS_Operator - var_ev) / (n_parts × n)
        var_av = max((ms_operator - var_ev) / (n_parts * n), 0)

        # σ²_PV = (MS_Part - var_ev) / (n_ops × n)
        var_pv = max((ms_part - var_ev) / (n_ops * n), 0)

        # IV = 0（合并入 EV）
        var_iv = 0.0
    else:
        # 完整模型（匹配 COSMO 桌面表现）：
        #   - var_ev = ms_within（始终，不做 pooling）
        #   - var_av/var_pv 始终以 ms_interaction 为基准
        #   - IV 仅当 ms_interaction > ms_within 时非零
        #   - 当 ms_part < ms_interaction 时，降级使用 ms_within 为基准
        #     以匹配 COSMO 对 Part 分量更宽容的处理方式
        var_ev = ms_within
        var_iv = max((ms_interaction - ms_within) / n, 0) if ms_interaction > ms_within else 0.0
        var_av = max((ms_operator - ms_interaction) / (n_parts * n), 0)
        var_pv_full = (ms_part - ms_interaction) / (n_ops * n)
        var_pv_fallback = max((ms_part - ms_within) / (n_ops * n), 0) if ms_part > ms_within else 0.0
        var_pv = max(var_pv_full, 0) if var_pv_full > 0 else var_pv_fallback

    # 标准差
    ev = np.sqrt(var_ev)
    iv = np.sqrt(var_iv)
    av = np.sqrt(var_av)
    pv = np.sqrt(var_pv)

    # GRR 标准差 = sqrt(EV² + AV² + IV²)
    rr = np.sqrt(ev**2 + av**2 + iv**2)

    # 总变异标准差 = sqrt(GRR² + PV²)
    tv = np.sqrt(rr**2 + pv**2)

    # %Study Variation = (σ²分量 / σ²总变异) × 100 — 方差占比 (匹配 COSMO)
    tv2 = tv**2 if tv > 0 else 1
    pct_rr = (rr**2 / tv2 * 100) if tv > 0 else 0
    pct_ev = (ev**2 / tv2 * 100) if tv > 0 else 0
    pct_av = (av**2 / tv2 * 100) if tv > 0 else 0
    pct_iv = (iv**2 / tv2 * 100) if tv > 0 else 0
    pct_pv = (pv**2 / tv2 * 100) if tv > 0 else 0

    # P/T 比率 (Precision-to-Tolerance)
    # 使用参数化的 study_const（默认 6.0 匹配 COSMO 桌面）
    tol = ul - ll
    pct_tol     = (rr * study_const / tol * 100) if tol != 0 else 0
    pct_tol_ev  = (ev * study_const / tol * 100) if tol != 0 else 0
    pct_tol_av  = (av * study_const / tol * 100) if tol != 0 else 0
    pct_tol_iv  = (iv * study_const / tol * 100) if tol != 0 else 0
    pct_tol_pv  = (pv * study_const / tol * 100) if tol != 0 else 0

    # 第一行（汇总表数值）— 根据 output_format 选择口径
    if output_format == "tol" and tol != 0:
        # P/T 比率 = σ × study_const / Tolerance × 100（匹配 COSMO 桌面）
        grr_study = rr * study_const / tol * 100
        repeat_study = ev * study_const / tol * 100
        # COSMO 桌面 reproducibility 列 = AV P/T（不含 IV）
        reprod_study = av * study_const / tol * 100
    else:
        # Study Variation = σ × study_const（AIAG 标准）
        grr_study = rr * study_const
        repeat_study = ev * study_const
        # COSMO 桌面 reproducibility 列 = AV Study Variation（不含 IV）
        reprod_study = av * study_const

    method_name = "ANOVA Main Effect" if main_effect else "ANOVA"

    return GrrResult(
        name=measurement_col,
        method=method_name,
        ul=ul, ll=ll,
        grr_study=round(grr_study, 6),
        repeat_study=round(repeat_study, 6),
        reprod_study=round(reprod_study, 6),
        rr=round(rr, 6),
        ev=round(ev, 6),
        av=round(av, 6),
        iv=round(iv, 6),
        pv=round(pv, 6),
        tv=round(tv, 6),
        pct_rr=round(pct_rr, 4),
        pct_ev=round(pct_ev, 4),
        pct_av=round(pct_av, 4),
        pct_iv=round(pct_iv, 4),
        pct_pv=round(pct_pv, 4),
        pct_tol=round(pct_tol, 4),
        pct_tol_ev=round(pct_tol_ev, 4),
        pct_tol_av=round(pct_tol_av, 4),
        pct_tol_iv=round(pct_tol_iv, 4),
        pct_tol_pv=round(pct_tol_pv, 4),
        data_matrix=matrix,
    )


# ══════════════════════════════════════════════════════════
#  Range 方法（Xbar/R）
# ══════════════════════════════════════════════════════════

def compute_grr_range(
    data: pd.DataFrame,
    operator_col: str = "operator_id",
    part_col: str = "dut_id",
    trial_col: str = "trial",
    measurement_col: str = "measurement",
    ul: float = float('inf'),
    ll: float = float('-inf'),
    output_format: str = "tol",
    study_const: float = 6.0,
) -> GrrResult:
    """
    Xbar/R 极差法 GRR 分析。

    基于 AIAG MSA 第4版，使用平均极差和均值极差计算方差分量。
    注意：Range 方法不单独计算交互作用 (IV = 0)。

    output_format:
      - "tol": P/T = σ × study_const / Tolerance × 100（匹配 COSMO 桌面）
      - "tv":  Study Variation = σ × study_const（AIAG 标准）
    """
    df = data[[operator_col, part_col, trial_col, measurement_col]].copy()
    df.columns = ["operator", "part", "trial", "value"]
    df = df.dropna(subset=["value"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # 构建数据矩阵
    matrix = df.pivot_table(
        index="part",
        columns=["operator", "trial"],
        values="value",
        aggfunc="first",
    )
    matrix.columns = [f"{int(float(op))}.{int(float(tr))}" for op, tr in matrix.columns]

    values = df["value"].values
    unique_ops = np.unique(df["operator"].values)
    unique_parts = np.unique(df["part"].values)
    n_ops = len(unique_ops)
    n_parts = len(unique_parts)
    n_trials = len(values) // (n_ops * n_parts)

    # ── 1. Equipment Variation (EV) ──
    # 对每个 (operator, part) 单元格计算极差 R
    cell_stats = df.groupby(["operator", "part"])["value"].agg(["min", "max", "mean"])
    cell_stats["range"] = cell_stats["max"] - cell_stats["min"]
    r_bar = cell_stats["range"].mean()  # 平均极差

    k1 = 1.0 / _d2(n_trials)
    ev = r_bar * k1

    # ── 2. Appraiser Variation (AV) ──
    # 每个评价人的均值
    op_means = df.groupby("operator")["value"].mean()
    x_bar_diff = op_means.max() - op_means.min()

    k2 = 1.0 / _d2(n_ops)
    av_raw = x_bar_diff * k2
    av_sq = av_raw**2 - (ev**2 / (n_parts * n_trials))
    av = math.sqrt(max(av_sq, 0))

    # ── 3. Part Variation (PV) ──
    part_means = df.groupby("part")["value"].mean()
    r_part = part_means.max() - part_means.min()

    k3 = 1.0 / _d2(n_parts)
    pv = r_part * k3

    # ── 4. GRR & Total ──
    iv = 0.0  # Range 方法不计算交互作用
    rr = math.sqrt(ev**2 + av**2)
    tv = math.sqrt(rr**2 + pv**2)

    # %Contribution (方差占比 × 100) — 匹配 COSMO 桌面
    tv2 = tv**2 if tv > 0 else 1
    pct_rr = (rr**2 / tv2 * 100) if tv > 0 else 0
    pct_ev = (ev**2 / tv2 * 100) if tv > 0 else 0
    pct_av = (av**2 / tv2 * 100) if tv > 0 else 0
    pct_iv = 0.0
    pct_pv = (pv**2 / tv2 * 100) if tv > 0 else 0

    # P/T 比率 (Precision-to-Tolerance)
    tol = ul - ll
    pct_tol     = (rr * study_const / tol * 100) if tol != 0 else 0
    pct_tol_ev  = (ev * study_const / tol * 100) if tol != 0 else 0
    pct_tol_av  = (av * study_const / tol * 100) if tol != 0 else 0
    pct_tol_iv  = 0.0
    pct_tol_pv  = (pv * study_const / tol * 100) if tol != 0 else 0

    # 第一行（汇总表数值）— 根据 output_format 选择口径
    if output_format == "tol" and tol != 0:
        grr_study = rr * study_const / tol * 100
        repeat_study = ev * study_const / tol * 100
        reprod_study = av * study_const / tol * 100
    else:
        grr_study = rr * study_const
        repeat_study = ev * study_const
        reprod_study = av * study_const

    return GrrResult(
        name=measurement_col,
        method="Range",
        ul=ul, ll=ll,
        grr_study=round(grr_study, 6),
        repeat_study=round(repeat_study, 6),
        reprod_study=round(reprod_study, 6),
        rr=round(rr, 6),
        ev=round(ev, 6),
        av=round(av, 6),
        iv=round(iv, 6),
        pv=round(pv, 6),
        tv=round(tv, 6),
        pct_rr=round(pct_rr, 4),
        pct_ev=round(pct_ev, 4),
        pct_av=round(pct_av, 4),
        pct_iv=round(pct_iv, 4),
        pct_pv=round(pct_pv, 4),
        pct_tol=round(pct_tol, 4),
        pct_tol_ev=round(pct_tol_ev, 4),
        pct_tol_av=round(pct_tol_av, 4),
        pct_tol_iv=round(pct_tol_iv, 4),
        pct_tol_pv=round(pct_tol_pv, 4),
        data_matrix=matrix,
    )


# ══════════════════════════════════════════════════════════
#  公共入口
# ══════════════════════════════════════════════════════════

def parse_cosmo_csv(
    csv_path: str,
    n_trials: int = 3,
    part_col: Optional[str] = None,
    appraiser_col: Optional[str] = None,
) -> tuple:
    """
    读取 COSMO 格式 CSV，自动分配 trial 编号.
    返回 (df_with_trials, measure_cols, actual_part_col, actual_appraiser_col, spec_limits)

    spec_limits = { "measure_col": (ul, ll), ... }
    从 COSMO 行格式提取 (第1行=UL, 第2行=LL, 0-indexed 取第1~2行).
    """
    df = pd.read_csv(csv_path, low_memory=False)

    # 自动检测 part/appraiser 列名
    if part_col is None:
        for candidate in ["dut_id", "part", "unit", "serial", "part_id", "unit_id"]:
            if candidate in df.columns:
                part_col = candidate
                break
        if part_col is None:
            raise ValueError("无法自动检测 Part 列，请在界面中手动选择")

    if appraiser_col is None:
        for candidate in ["operator_id", "appraiser", "operator", "evaluator", "inspector"]:
            if candidate in df.columns:
                appraiser_col = candidate
                break
        if appraiser_col is None:
            raise ValueError("无法自动检测 Appraiser 列，请在界面中手动选择")

    # ── 提取 COSMO 行格式 UL/LL ──
    # COSMO CSV: 第0行=列名, 第1行=名称/描述(空), 第2行=UL, 第3行=LL, 第4行起=数据
    # 在 pandas 中 df 的第0~2行对应 CSV 的 1~3行
    spec_limits = {}
    # 查找 UL/LL 行：关键列为空的行即元数据行
    meta_rows = df[df[part_col].isna() & df[appraiser_col].isna()]
    if len(meta_rows) >= 2:
        ul_row = meta_rows.iloc[0]  # 第一条元数据行 = UL
        ll_row = meta_rows.iloc[1]  # 第二条元数据行 = LL
        for col in df.columns:
            ul_val = ul_row[col]
            ll_val = ll_row[col]
            if pd.notna(ul_val) and pd.notna(ll_val):
                try:
                    ul = float(ul_val)
                    ll = float(ll_val)
                    # 不过滤，让用户在 Test Items 标签页中手动筛选
                    spec_limits[col] = (ul, ll)
                except (ValueError, TypeError):
                    pass

    # 过滤掉元数据行 (所有关键列为空)
    df = df.dropna(subset=[part_col, appraiser_col])

    # 按 (part, appraiser) 分组分配 trial 编号
    df = df.copy()
    df["trial"] = df.groupby([part_col, appraiser_col]).cumcount()
    # 只保留前 n_trials 次测量
    df = df[df["trial"] < n_trials].copy()

    # 自动识别测量列
    skip_cols = {part_col, appraiser_col, "trial", "run_index",
                 "slot", "station_id", "outcome", "start_time",
                 "end_time", "total_test_time", "framework",
                 "msa_id", "spec_version", "test_asset_name", "test_description",
                 "test_version", "project", "test_name", "line_type",
                 "line_id", "test_mode", "fail_stop",
                 "sfc_check_out_result", "device_config", "build_phase",
                 "sub_build_phase", "scof_on", "start_time_millis",
                 "cof_on", "retest_policy", "check_in_time_ms",
                 "final_run", "work_order", "retest_state",
                 "campaign_codes", "logger_mode", "dut_index",
                 "failure_code"}

    # 收集所有数值列中看起来像测量的列
    candidate_cols = set()
    for c in df.columns:
        if c in skip_cols:
            continue
        if not pd.api.types.is_numeric_dtype(df[c]):
            continue
        # 排除常量列（全相同值）
        if df[c].nunique() <= 1:
            continue
        # 排除 _status 结尾的状态列
        if c.endswith("_status"):
            continue
        # 排除测试时间列 (sample_total_time)
        if "sample_total_time" in c or c.endswith("_total_time"):
            continue
        candidate_cols.add(c)

    # 测量列 = 有 UL/LL 的列 + 其他候选列（去重）
    # spec_limits 中的列一定算测量列
    from_spec = {c for c in candidate_cols if c in spec_limits}
    other = candidate_cols - from_spec
    measure_cols = sorted(from_spec) + sorted(other)
    # 同时支持 hinge_measurement_ 前缀（处理其他 CSV 格式）
    hinge_cols = [c for c in df.columns if c.startswith("hinge_measurement_")
                  and c not in measure_cols]
    measure_cols = measure_cols + hinge_cols

    if not measure_cols:
        raise ValueError("未找到测量列")

    print(f"  发现 {len(measure_cols)} 个测量项")
    print(f"  UL/LL 规格限: {len(spec_limits)} 个有效列")
    return df, measure_cols, part_col, appraiser_col, spec_limits


def run_grr_analysis(
    csv_path: str,
    n_trials: int = 3,
    spec_limits: Optional[dict] = None,
    part_col: Optional[str] = None,
    appraiser_col: Optional[str] = None,
    method: str = "ANOVA",
    output_format: str = "tol",
    study_const: float = 6.0,
) -> GrrReport:
    """
    对 CSV 文件运行完整 GRR 分析。

    method 支持: "ANOVA", "ANOVA Main Effect", "Range"
    output_format:
      - "tol": P/T = σ × study_const / Tolerance × 100（匹配 COSMO 桌面）
      - "tv":  Study Variation = σ × study_const（AIAG 标准）
    """
    import datetime

    df, measure_cols, part_col, appraiser_col, csv_spec_limits = parse_cosmo_csv(
        csv_path, n_trials, part_col, appraiser_col
    )

    # 合并 CSV 提取的 UL/LL 与用户传入的 spec_limits
    # 用户传入优先（覆盖 CSV 中提取的值）
    if spec_limits is None:
        spec_limits = {}
    for col, (ul, ll) in csv_spec_limits.items():
        if col not in spec_limits:
            spec_limits[col] = (ul, ll)

    appraisers = sorted(df[appraiser_col].dropna().unique())
    unit_serials = sorted(df[part_col].dropna().unique())
    n_t = df["trial"].nunique()

    report = GrrReport(
        report_date=datetime.datetime.now().strftime("%Y-%m-%d"),
        method=method,
        num_appraisers=len(appraisers),
        appraisers=[str(a) for a in appraisers],
        num_units=len(unit_serials),
        unit_serials=[str(u) for u in unit_serials],
        num_trials=n_t,
    )

    print(f"  Method: {method}")
    print(f"  Appraisers: {len(appraisers)}, Parts: {len(unit_serials)}, Trials: {n_t}")
    print(f"  数据点: {len(df)}")

    print(f"  Output Format: {output_format}, Study Const: {study_const}")

    # 选择计算方法
    if method.lower().startswith("anova main"):
        compute_fn = lambda d, oc, pc, tc, mc, ul, ll: compute_grr_anova(
            d, oc, pc, tc, mc, ul, ll, main_effect=True,
            output_format=output_format, study_const=study_const)
    elif method.lower() == "range":
        compute_fn = lambda d, oc, pc, tc, mc, ul, ll: compute_grr_range(
            d, oc, pc, tc, mc, ul, ll,
            output_format=output_format, study_const=study_const)
    else:
        compute_fn = lambda d, oc, pc, tc, mc, ul, ll: compute_grr_anova(
            d, oc, pc, tc, mc, ul, ll, main_effect=False,
            output_format=output_format, study_const=study_const)

    for col in measure_cols:
        col_data = df[col].dropna()
        if col in spec_limits:
            ul, ll = spec_limits[col]
        else:
            # 无规格限时保留 inf/-inf（不擅自填充假值）
            ul = float('inf')
            ll = float('-inf')

        result = compute_fn(df, appraiser_col, part_col, "trial", col, ul, ll)
        report.results.append(result)

        print(f"    {col[:40]:40s} %GRR={result.pct_rr:5.1f}%  {result.rating}")

    return report
