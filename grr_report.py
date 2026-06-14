#!/usr/bin/env python3
"""
GRR Report Generator — CLI 入口
================================
基于 COSMO 格式的 CSV 数据生成 GRR (Gauge R&R) 分析报告 PDF。

用法:
    python grr_report.py <csv文件> [-o 输出路径] [--trials N]
                          [--study-const K] [--output-format {tol,tv}]

示例:
    python grr_report.py data.csv                                          # COSMO 桌面模式
    python grr_report.py data.csv --study-const 5.15 --output-format tv    # AIAG 标准模式
    python grr_report.py data.csv -o my_report.pdf --trials 5
"""

import os
import sys
import argparse

# 设置 matplotlib 缓存路径
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl_grr")

# 确保能导入同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from grr_core import run_grr_analysis
from grr_pdf import generate_pdf


def main():
    parser = argparse.ArgumentParser(
        description="GRR Report Generator — 量具重复性与再现性分析报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s data.csv                                   # COSMO 桌面模式(P/T,6σ)
  %(prog)s data.csv -o report.pdf
  %(prog)s data.csv --trials 5
  %(prog)s data.csv --study-const 5.15 --output-format tv   # AIAG 标准模式

输出格式:
  tol: P/T = σ × study_const / Tolerance × 100  (匹配 COSMO 桌面, 默认)
  tv:  Study Variation = σ × study_const         (AIAG 标准)

数据格式要求:
  - CSV 必须包含: operator_id, dut_id
  - 测量列以 hinge_measurement_* 命名或为数值列
  - 程序会自动按 (DUT, 操作员) 分组分配试验次数
""")
    parser.add_argument("csv", help="输入 CSV 数据文件路径")
    parser.add_argument("-o", "--output", default=None,
                        help="输出 PDF 文件路径 (默认: 与输入同名的 .pdf)")
    parser.add_argument("--trials", type=int, default=3,
                        help="每个操作员-零件组合使用的试验次数 (默认: 3，行业标准)")
    parser.add_argument("--part-col", default=None,
                        help="Part/DUT 列名 (默认: 自动检测)")
    parser.add_argument("--appraiser-col", default=None,
                        help="Appraiser/Operator 列名 (默认: 自动检测)")
    parser.add_argument("--method", default="ANOVA",
                        choices=["ANOVA", "ANOVA Main Effect", "Range"],
                        help="分析方法: ANOVA (默认), ANOVA Main Effect, or Range")
    parser.add_argument("--study-const", type=float, default=6.0,
                        help="安全系数 (默认: 6.0 匹配 COSMO 桌面; AIAG 标准为 5.15)")
    parser.add_argument("--output-format", default="tol",
                        choices=["tol", "tv"],
                        help="输出格式: tol=P/T(%%Tolerance) 匹配 COSMO 桌面, tv=Study Variation(%%TV) AIAG 标准")

    args = parser.parse_args()

    # 校验输入文件
    if not os.path.isfile(args.csv):
        print(f"❌ 错误: 找不到文件 '{args.csv}'")
        sys.exit(1)

    # 输出路径
    if args.output is None:
        base = os.path.splitext(args.csv)[0]
        args.output = f"{base}-GRR-REPORT.pdf"

    output_desc = "P/T (%Tolerance)" if args.output_format == "tol" else "Study Var (%TV)"
    print(f"\n{'='*60}")
    print(f"  GRR Report Generator v1.0")
    print(f"  输入: {args.csv}")
    print(f"  输出: {args.output}")
    print(f"  试验次数: {args.trials}")
    print(f"  输出格式: {output_desc}  (study_const={args.study_const})")
    print(f"{'='*60}\n")

    # 运行分析
    print("📊 正在分析数据...")
    report = run_grr_analysis(
        args.csv,
        n_trials=args.trials,
        part_col=args.part_col,
        appraiser_col=args.appraiser_col,
        method=args.method,
        output_format=args.output_format,
        study_const=args.study_const,
    )

    # 生成 PDF
    print("\n📄 正在生成报告...")
    generate_pdf(report, args.output)

    # 汇总
    print(f"\n{'='*60}")
    print(f"  {len(report.results)} 个测量项")
    poor = sum(1 for r in report.results if r.rating == "Poor")
    marginal = sum(1 for r in report.results if r.rating == "Marginal")
    good = sum(1 for r in report.results if r.rating == "Good")
    excellent = sum(1 for r in report.results if r.rating == "Excellent")
    print(f"  Excellent: {excellent}  Good: {good}  Marginal: {marginal}  Poor: {poor}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
