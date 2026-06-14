# GRR 示例数据

## 文件列表

| 文件名 | 来源 | 说明 | 零件数 | 操作员 | 可用 trial | 推荐 n_trials |
|--------|------|------|:------:|:-----:|:---------:|:------------:|
| `SA-BUTTON#2-GRR.csv` | Mars 测试系统 | Button Tactile 按钮触感测试，含 29 项测量指标（力/行程/比率） | 2 | 3 | min=4 | **3** |
| `123.csv` | COSMO 输出 | SA-BUTTON 的 COSMO 参考结果（n_trials=3 时生成），用于比对验证 | — | — | — | — |
| `MCN5_FVN-N1F-H01_SA-AIRLK-VB_IN26A-01-2026-06-11.csv` | Mars 测试系统 | 气密性测试，含 cts_run_loadcell/VB 等测量列 | 3 | 3 | min=10 | **10** |

## 使用说明

### SA-BUTTON 按钮测试（29 项指标）

**源数据**: `SA-BUTTON#2-GRR.csv`
**COSMO 参考**: `123.csv`
**设置**: n_trials=3 | ANOVA | P/T | Sigma=6

数据包含 2 个零件 × 3 个操作员，每个格子实测有 4~8 次测量。
测试标准要求 3 次/格，所以 COSMO 使用 n=3。
加载 CSV 后把 Number of trials 改成 **3** 再跑，结果与 123.csv 完全一致。

### MCN5 气密性测试

**源数据**: `MCN5_FVN-N1F-H01_SA-AIRLK-VB_IN26A-01-2026-06-11.csv`
**设置**: n_trials=10 | ANOVA | P/T | Sigma=6

数据包含 3 个零件 × 3 个操作员，每个格子实测有 10~14 次测量。
测试标准要求 10 次/格，加载 CSV 后把 Number of trials 改成 **10** 再跑。

## 常见问题

**Q: 为什么 Number of trials 默认是 3？**
A: MSA 行业标准通常是 3 次测量/格，与 COSMO 默认值一致。如果测试标准不同，手动修改即可。

**Q: "可用: X" 是什么意思？**
A: 表示源数据中每个（零件×操作员）格子最少有 X 行数据。例如 "可用: 4" 意味着数据里有 4 次测量可用，但实际用几次取决于测试标准。
