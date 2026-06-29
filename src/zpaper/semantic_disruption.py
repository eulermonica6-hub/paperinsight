from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "data" / "sample" / "paper_dataset_sample.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "demo_semantic_disruption"

KEY_VARS = [
    "Mean",
    "Top5_Mean",
    "Equal_IMRAD",
    "IMEAN",
    "MMEAN",
    "RMEAN",
    "DMEAN",
    "ABMEAN",
    "TIMEAN",
]

RAW_CONTROLS = ["PP", "AUNUM", "JIF", "NR", "2024JIF", "EF"]
LOG_CONTROL_MAP = {
    "PP": "ln_PP",
    "AUNUM": "ln_AUNUM",
    "JIF": "ln_JIF",
    "NR": "ln_NR",
    "2024JIF": "ln_2024JIF",
}
CONTROL_VARS = ["ln_PP", "ln_AUNUM", "ln_JIF", "ln_NR", "ln_2024JIF", "EF"]


def normal_pvalue(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return math.erfc(abs(float(z)) / math.sqrt(2.0))


def stars(p: float) -> str:
    if not np.isfinite(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def format_coef(coef: float, se: float, p: float) -> str:
    if not np.isfinite(coef):
        return ""
    return f"{coef:.4f}{stars(p)} ({se:.4f})"


def winsorize(s: pd.Series, low: float = 0.01, high: float = 0.99) -> pd.Series:
    lo, hi = s.quantile([low, high])
    return s.clip(lo, hi)


def entropy_weights(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    x = frame[cols].copy()
    shifted = pd.DataFrame(index=x.index)
    for col in cols:
        min_val = x[col].min()
        max_val = x[col].max()
        denom = max_val - min_val
        if denom == 0 or not np.isfinite(denom):
            shifted[col] = 1.0
        else:
            shifted[col] = (x[col] - min_val) / denom + 1e-12
    p = shifted.div(shifted.sum(axis=0), axis=1)
    logp = np.log(p.replace(0, np.nan))
    entropy = -(p * logp).sum(axis=0) / math.log(len(p))
    diversity = 1 - entropy
    weights = diversity / diversity.sum()
    return weights


def prepare_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.copy()
    df["Y"] = df["n_disruptive"] / df["n_total"]
    df["issue_id"] = (
        df["journal"].astype(str)
        + "_"
        + df["PY"].astype(str)
        + "_"
        + df["VL"].astype(str)
        + "_"
        + df["IS"].astype(str)
    )
    imrad_cols = ["IMEAN", "MMEAN", "RMEAN", "DMEAN"]
    df["Equal_IMRAD"] = df[imrad_cols].mean(axis=1, skipna=False)
    complete = df[imrad_cols].dropna()
    weights = entropy_weights(complete, imrad_cols)
    df["Recalc_Entropy_IMRAD"] = np.nan
    df.loc[complete.index, "Recalc_Entropy_IMRAD"] = (complete * weights).sum(axis=1)
    for src, dst in LOG_CONTROL_MAP.items():
        df[dst] = np.log1p(df[src])
    for col in ["n_total", "n_disruptive", "n_consolidating"]:
        df[f"w_{col}"] = winsorize(df[col]) if col in df else np.nan
    df["Y_winsor"] = winsorize(df["Y"].dropna()).reindex(df.index)
    return df


def design_matrix(df: pd.DataFrame, variables: list[str], fixed_effects: bool) -> tuple[np.ndarray, list[str]]:
    parts = [pd.Series(1.0, index=df.index, name="Intercept")]
    for var in variables:
        parts.append(df[var].astype(float).rename(var))
    if fixed_effects:
        journal_dummies = pd.get_dummies(df["journal"].astype(str), prefix="journal", drop_first=True, dtype=float)
        year_dummies = pd.get_dummies(df["PY"].astype(str), prefix="year", drop_first=True, dtype=float)
        parts.extend([journal_dummies, year_dummies])
    x = pd.concat(parts, axis=1)
    return x.to_numpy(dtype=float), list(x.columns)


def fit_linear_model(
    frame: pd.DataFrame,
    y_var: str,
    variables: list[str],
    fixed_effects: bool = True,
    cluster_var: str = "issue_id",
    weight_var: str | None = None,
    extra_required: list[str] | None = None,
) -> dict:
    required = [y_var, cluster_var, "journal", "PY", *variables]
    if extra_required:
        required.extend(extra_required)
    if weight_var:
        required.append(weight_var)
    data = frame[required].dropna().copy()
    if weight_var:
        data = data[data[weight_var] > 0].copy()
    y = data[y_var].to_numpy(dtype=float)
    x, names = design_matrix(data, variables, fixed_effects=fixed_effects)
    if weight_var:
        weights = data[weight_var].to_numpy(dtype=float)
        weights = weights / np.nanmean(weights)
    else:
        weights = np.ones(len(data), dtype=float)
    sw = np.sqrt(weights)
    xw = x * sw[:, None]
    yw = y * sw
    beta, _, rank, _ = np.linalg.lstsq(xw, yw, rcond=None)
    fitted = x @ beta
    resid = y - fitted
    resid_w = yw - xw @ beta
    xtx_inv = np.linalg.pinv(xw.T @ xw)
    groups = data[cluster_var].astype(str).to_numpy()
    unique_groups = pd.unique(groups)
    meat = np.zeros((x.shape[1], x.shape[1]), dtype=float)
    for group in unique_groups:
        idx = groups == group
        score = xw[idx].T @ resid_w[idx]
        meat += np.outer(score, score)
    n = len(data)
    k = rank
    g = len(unique_groups)
    if g > 1 and n > k:
        meat *= (g / (g - 1)) * ((n - 1) / (n - k))
    cov = xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = beta / se
    pvals = np.array([normal_pvalue(value) for value in z])
    sse = float(np.sum(weights * resid**2))
    ybar = float(np.average(y, weights=weights))
    tss = float(np.sum(weights * (y - ybar) ** 2))
    r2 = 1 - sse / tss if tss > 0 else np.nan
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - k) if n > k and np.isfinite(r2) else np.nan
    result = pd.DataFrame(
        {
            "term": names,
            "coef": beta,
            "se_cluster_issue": se,
            "z": z,
            "p": pvals,
        }
    )
    return {
        "n": int(n),
        "rank": int(rank),
        "clusters": int(g),
        "r2": r2,
        "adj_r2": adj_r2,
        "fixed_effects": fixed_effects,
        "weight_var": weight_var or "",
        "terms": result,
    }


def fit_within_model(
    frame: pd.DataFrame,
    y_var: str,
    variables: list[str],
    fixed_effect_var: str = "issue_id",
    cluster_var: str = "issue_id",
    weight_var: str | None = None,
) -> dict:
    required = list(dict.fromkeys([y_var, fixed_effect_var, cluster_var, *variables]))
    if weight_var:
        required.append(weight_var)
    data = frame[required].dropna().copy()
    if weight_var:
        data = data[data[weight_var] > 0].copy()
        weights = data[weight_var].to_numpy(dtype=float)
        weights = weights / np.nanmean(weights)
    else:
        weights = np.ones(len(data), dtype=float)

    names = variables
    y = data[y_var].astype(float)
    x = data[variables].astype(float)
    groups = data[fixed_effect_var].astype(str)

    if weight_var:
        wy = y * weights
        wx = x.mul(weights, axis=0)
        denom = pd.Series(weights, index=data.index).groupby(groups).transform("sum")
        y_mean = wy.groupby(groups).transform("sum") / denom
        x_mean = wx.groupby(groups).transform("sum").div(denom, axis=0)
    else:
        y_mean = y.groupby(groups).transform("mean")
        x_mean = x.groupby(groups).transform("mean")

    y_dm = (y - y_mean).to_numpy(dtype=float)
    x_dm = (x - x_mean).to_numpy(dtype=float)
    keep = np.linalg.norm(x_dm, axis=0) > 1e-12
    x_dm = x_dm[:, keep]
    names = [name for name, is_kept in zip(names, keep) if is_kept]

    sw = np.sqrt(weights)
    xw = x_dm * sw[:, None]
    yw = y_dm * sw
    beta, _, rank, _ = np.linalg.lstsq(xw, yw, rcond=None)
    resid_w = yw - xw @ beta
    xtx_inv = np.linalg.pinv(xw.T @ xw)

    cluster_groups = data[cluster_var].astype(str).to_numpy()
    unique_groups = pd.unique(cluster_groups)
    meat = np.zeros((x_dm.shape[1], x_dm.shape[1]), dtype=float)
    for group in unique_groups:
        idx = cluster_groups == group
        score = xw[idx].T @ resid_w[idx]
        meat += np.outer(score, score)
    n = len(data)
    g = len(unique_groups)
    absorbed = data[fixed_effect_var].nunique()
    k = rank + absorbed - 1
    if g > 1 and n > k:
        meat *= (g / (g - 1)) * ((n - 1) / (n - k))
    cov = xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    z = beta / se
    pvals = np.array([normal_pvalue(value) for value in z])

    resid = y_dm - x_dm @ beta
    sse = float(np.sum(weights * resid**2))
    tss = float(np.sum(weights * y_dm**2))
    r2_within = 1 - sse / tss if tss > 0 else np.nan
    adj_r2 = 1 - (1 - r2_within) * (n - 1) / (n - k) if n > k and np.isfinite(r2_within) else np.nan
    result = pd.DataFrame(
        {
            "term": names,
            "coef": beta,
            "se_cluster_issue": se,
            "z": z,
            "p": pvals,
        }
    )
    return {
        "n": int(n),
        "rank": int(rank),
        "clusters": int(g),
        "r2": r2_within,
        "adj_r2": adj_r2,
        "fixed_effects": f"{fixed_effect_var}",
        "weight_var": weight_var or "",
        "terms": result,
    }


def collect_terms(model_name: str, result: dict, terms: Iterable[str]) -> list[dict]:
    records = []
    table = result["terms"].set_index("term")
    for term in terms:
        if term not in table.index:
            continue
        row = table.loc[term]
        records.append(
            {
                "model": model_name,
                "term": term,
                "coef": row["coef"],
                "se_cluster_issue": row["se_cluster_issue"],
                "z": row["z"],
                "p": row["p"],
                "stars": stars(row["p"]),
                "coef_se": format_coef(row["coef"], row["se_cluster_issue"], row["p"]),
                "n": result["n"],
                "clusters": result["clusters"],
                "r2": result["r2"],
                "adj_r2": result["adj_r2"],
                "weight_var": result["weight_var"],
        "fixed_effects": result["fixed_effects"],
            }
        )
    return records


def model_summary(term_rows: pd.DataFrame, baseline_model: str | None = None) -> pd.DataFrame:
    summary = (
        term_rows.groupby("model", as_index=False)
        .agg(
            n=("n", "first"),
            clusters=("clusters", "first"),
            r2=("r2", "first"),
            adj_r2=("adj_r2", "first"),
            weight_var=("weight_var", "first"),
            fixed_effects=("fixed_effects", "first"),
        )
        .sort_values("model")
    )
    if baseline_model and baseline_model in set(summary["model"]):
        baseline = float(summary.loc[summary["model"] == baseline_model, "adj_r2"].iloc[0])
        summary["delta_adj_r2_vs_baseline"] = summary["adj_r2"] - baseline
    return summary


def binned_mean_table(df: pd.DataFrame) -> pd.DataFrame:
    data = df[["Y", "Mean", "n_total"]].dropna().copy()
    data["Mean_decile"] = pd.qcut(data["Mean"], q=10, labels=False, duplicates="drop") + 1
    grouped = []
    for decile, group in data.groupby("Mean_decile"):
        grouped.append(
            {
                "Mean_decile": int(decile),
                "n": len(group),
                "Mean_min": group["Mean"].min(),
                "Mean_max": group["Mean"].max(),
                "Mean_avg": group["Mean"].mean(),
                "Y_avg": group["Y"].mean(),
                "Y_median": group["Y"].median(),
                "Y_weighted_by_n_total": np.average(group["Y"], weights=group["n_total"]),
                "n_total_avg": group["n_total"].mean(),
            }
        )
    return pd.DataFrame(grouped)


def summarize_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_vars = [
        "Y",
        "Mean",
        "Top5_Mean",
        "Equal_IMRAD",
        "IMEAN",
        "MMEAN",
        "RMEAN",
        "DMEAN",
        "ABMEAN",
        "TIMEAN",
        "PP",
        "AUNUM",
        "PY",
        "JIF",
        "2024JIF",
        "NR",
        "EF",
        "n_total",
    ]
    desc = df[summary_vars].describe(percentiles=[0.25, 0.5, 0.75]).T
    desc = desc.rename(columns={"50%": "median"})
    missing = df[summary_vars].isna().mean().rename("missing_rate").to_frame()
    corr_vars = ["Y", "Mean", "Top5_Mean", "Equal_IMRAD", "IMEAN", "MMEAN", "RMEAN", "DMEAN", "ABMEAN", "TIMEAN"]
    corr = df[corr_vars].corr()
    return desc, missing, corr


def make_wide_model_table(term_rows: pd.DataFrame, model_order: list[str], terms: list[str]) -> pd.DataFrame:
    rows = []
    labels = {
        "Mean": "期内语义中心性 Mean",
        "Top5_Mean": "替代中心性 Top5_Mean",
        "Equal_IMRAD": "IMRAD 等权均值",
        "Recalc_Entropy_IMRAD": "脚本重算 IMRAD 熵权值",
        "IMEAN": "Introduction 相似度",
        "MMEAN": "Methods 相似度",
        "RMEAN": "Results 相似度",
        "DMEAN": "Discussion 相似度",
        "ABMEAN": "摘要相似度",
        "TIMEAN": "标题相似度",
        "ln_PP": "ln(期号文献规模+1)",
        "ln_AUNUM": "ln(团队规模+1)",
        "ln_JIF": "ln(发表年 JIF+1)",
        "ln_NR": "ln(参考文献数+1)",
        "ln_2024JIF": "ln(2024 JIF+1)",
        "EF": "跨学科期刊",
    }
    for term in terms:
        row = {"term": labels.get(term, term)}
        for model in model_order:
            matched = term_rows[(term_rows["model"] == model) & (term_rows["term"] == term)]
            row[model] = matched["coef_se"].iloc[0] if not matched.empty else ""
        rows.append(row)
    for stat in ["n", "clusters", "adj_r2"]:
        row = {"term": stat}
        for model in model_order:
            matched = term_rows[term_rows["model"] == model]
            if matched.empty:
                row[model] = ""
            elif stat == "adj_r2":
                row[model] = f"{matched[stat].iloc[0]:.4f}"
            else:
                row[model] = f"{int(matched[stat].iloc[0])}"
        rows.append(row)
    return pd.DataFrame(rows)


def write_markdown_report(
    path: Path,
    desc: pd.DataFrame,
    missing: pd.DataFrame,
    corr: pd.DataFrame,
    main_table: pd.DataFrame,
    robust_table: pd.DataFrame,
    within_table: pd.DataFrame,
    entropy_table: pd.DataFrame,
    model_summary_table: pd.DataFrame,
    binned_table: pd.DataFrame,
    entropy_info: dict,
) -> None:
    def md_table(frame: pd.DataFrame, max_rows: int | None = None) -> str:
        out = frame.copy()
        if max_rows:
            out = out.head(max_rows)
        out = out.fillna("")
        headers = [str(col) for col in out.columns]
        rows = [[str(value) for value in row] for row in out.to_numpy()]
        widths = [
            max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
            for i in range(len(headers))
        ]

        def fmt_row(values: list[str]) -> str:
            return "| " + " | ".join(values[i].ljust(widths[i]) for i in range(len(values))) + " |"

        lines = [fmt_row(headers), "| " + " | ".join("-" * width for width in widths) + " |"]
        lines.extend(fmt_row(row) for row in rows)
        return "\n".join(lines)

    lines = []
    lines.append("# 期内语义相似度与文献颠覆性实证分析\n")
    lines.append("## 实验设计\n")
    lines.append(
        "- 因变量：`Y = n_disruptive / n_total`，表示文献后续引用组合中颠覆性引用占比。\n"
        "- 核心解释变量：`Mean`，即 IMRAD 四结构期内语义相似度的信息熵加权中心性。\n"
        "- 替代解释变量：`Top5_Mean`；对照解释变量：`ABMEAN`、`TIMEAN`；IMRAD 分解变量：`IMEAN`、`MMEAN`、`RMEAN`、`DMEAN`。\n"
        "- 控制变量：期号文献规模、团队规模、发表年 JIF、2024JIF、参考文献数、跨学科期刊，并使用期刊与年份固定效应。\n"
        "- 标准误：按 `journal-PY-VL-IS` 构造期号聚类，报告聚类稳健标准误。\n"
        "- 稳健性：以 `n_total` 为权重进行加权回归，检验引用样本规模差异对结果的影响。\n"
    )
    lines.append("## 描述统计\n")
    desc_view = desc.reset_index().rename(columns={"index": "variable"})
    keep_cols = ["variable", "count", "mean", "std", "min", "25%", "median", "75%", "max"]
    lines.append(md_table(desc_view[keep_cols].round(4), max_rows=18))
    lines.append("\n## 缺失率\n")
    missing_view = missing.reset_index().rename(columns={"index": "variable"})
    lines.append(md_table(missing_view.round(4), max_rows=18))
    lines.append("\n## 主要变量相关性\n")
    corr_view = corr.round(3).reset_index().rename(columns={"index": "variable"})
    lines.append(md_table(corr_view))
    lines.append("\n## 主回归结果\n")
    lines.append("括号内为期号聚类稳健标准误；*, **, *** 分别表示 10%、5%、1% 显著性。")
    lines.append(md_table(main_table))
    lines.append("\n## 模型解释力比较\n")
    lines.append(md_table(model_summary_table.round(6)))
    lines.append("\n## 加权稳健性结果\n")
    lines.append("权重为 `n_total`，用于降低低引用窗口文献比例型因变量的噪声影响。")
    lines.append(md_table(robust_table))
    lines.append("\n## 期号固定效应组内结果\n")
    lines.append("该组模型比较同一期号内文献的语义中心性差异；`PP` 及期刊/年份等期号层面常量由期号固定效应吸收。")
    lines.append(md_table(within_table))
    lines.append("\n## 熵权 vs 等权同样本比较\n")
    lines.append("该组模型均限制在四个 IMRAD 结构完整的样本上。")
    lines.append(md_table(entropy_table))
    lines.append("\n## Mean 十分位原始关系\n")
    lines.append("该表用于直观看原始分组关系，不控制期刊、年份和其他协变量。")
    lines.append(md_table(binned_table.round(4)))
    lines.append("\n## 熵权与等权说明\n")
    lines.append(
        f"基于 IMRAD 完整样本重新计算的熵权为：IMEAN={entropy_info['weights']['IMEAN']:.4f}, "
        f"MMEAN={entropy_info['weights']['MMEAN']:.4f}, RMEAN={entropy_info['weights']['RMEAN']:.4f}, "
        f"DMEAN={entropy_info['weights']['DMEAN']:.4f}。"
    )
    lines.append(
        f"`Mean` 与四结构等权均值在完整样本中的相关系数为 {entropy_info['corr_mean_equal']:.4f}；"
        f"`Mean` 与本脚本重算熵权值的相关系数为 {entropy_info['corr_mean_recalc_entropy']:.4f}。"
    )
    path.write_text("\n\n".join(lines), encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run semantic visibility/disruption regressions on a prepared paper-level CSV."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to the prepared CSV. Defaults to the synthetic open-source sample.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated tables and the Markdown report.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {input_path}. "
            "Generate sample data with `python -m zpaper.make_sample_data` "
            "or pass your private dataset with `--input`."
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    df = prepare_data(input_path)
    desc, missing, corr = summarize_data(df)

    imrad_cols = ["IMEAN", "MMEAN", "RMEAN", "DMEAN"]
    complete = df[imrad_cols].dropna()
    entropy_info = {
        "weights": entropy_weights(complete, imrad_cols).to_dict(),
        "corr_mean_equal": float(df[["Mean", "Equal_IMRAD"]].dropna().corr().iloc[0, 1]),
        "corr_mean_recalc_entropy": float(df[["Mean", "Recalc_Entropy_IMRAD"]].dropna().corr().iloc[0, 1]),
    }

    model_specs = {
        "M0_controls": CONTROL_VARS,
        "M1_Mean": ["Mean", *CONTROL_VARS],
        "M2_Top5": ["Top5_Mean", *CONTROL_VARS],
        "M3_EqualIMRAD": ["Equal_IMRAD", *CONTROL_VARS],
        "M4_IMRAD_parts": [*imrad_cols, *CONTROL_VARS],
        "M5_Abstract": ["ABMEAN", *CONTROL_VARS],
        "M6_Title": ["TIMEAN", *CONTROL_VARS],
        "M7_All_semantics": ["Mean", "ABMEAN", "TIMEAN", *CONTROL_VARS],
    }

    term_order = [
        "Mean",
        "Top5_Mean",
        "Equal_IMRAD",
        "IMEAN",
        "MMEAN",
        "RMEAN",
        "DMEAN",
        "ABMEAN",
        "TIMEAN",
        "Recalc_Entropy_IMRAD",
        *CONTROL_VARS,
    ]

    all_rows = []
    full_terms = {}
    for name, variables in model_specs.items():
        result = fit_linear_model(df, "Y", variables, fixed_effects=True, cluster_var="issue_id")
        full_terms[name] = result["terms"]
        all_rows.extend(collect_terms(name, result, term_order))
    term_rows = pd.DataFrame(all_rows)

    weighted_rows = []
    weighted_full_terms = {}
    for name, variables in {
        "W1_Mean": ["Mean", *CONTROL_VARS],
        "W2_Top5": ["Top5_Mean", *CONTROL_VARS],
        "W3_EqualIMRAD": ["Equal_IMRAD", *CONTROL_VARS],
        "W4_IMRAD_parts": [*imrad_cols, *CONTROL_VARS],
        "W5_All_semantics": ["Mean", "ABMEAN", "TIMEAN", *CONTROL_VARS],
    }.items():
        result = fit_linear_model(
            df,
            "Y",
            variables,
            fixed_effects=True,
            cluster_var="issue_id",
            weight_var="n_total",
        )
        weighted_full_terms[name] = result["terms"]
        weighted_rows.extend(collect_terms(name, result, term_order))
    weighted_term_rows = pd.DataFrame(weighted_rows)

    within_rows = []
    within_specs = {
        "I1_Mean_issueFE": ["Mean", *CONTROL_VARS],
        "I2_Top5_issueFE": ["Top5_Mean", *CONTROL_VARS],
        "I3_Abstract_issueFE": ["ABMEAN", *CONTROL_VARS],
        "I4_Title_issueFE": ["TIMEAN", *CONTROL_VARS],
        "I5_All_semantics_issueFE": ["Mean", "ABMEAN", "TIMEAN", *CONTROL_VARS],
        "I6_IMRAD_parts_issueFE": [*imrad_cols, *CONTROL_VARS],
    }
    for name, variables in within_specs.items():
        result = fit_within_model(df, "Y", variables, fixed_effect_var="issue_id", cluster_var="issue_id")
        within_rows.extend(collect_terms(name, result, term_order))
    within_term_rows = pd.DataFrame(within_rows)

    entropy_rows = []
    entropy_specs = {
        "E1_Mean_complete": (["Mean", *CONTROL_VARS], ["Equal_IMRAD"]),
        "E2_EqualIMRAD": (["Equal_IMRAD", *CONTROL_VARS], []),
        "E3_RecalcEntropy": (["Recalc_Entropy_IMRAD", *CONTROL_VARS], []),
    }
    for name, (variables, extra_required) in entropy_specs.items():
        result = fit_linear_model(
            df,
            "Y",
            variables,
            fixed_effects=True,
            cluster_var="issue_id",
            extra_required=extra_required,
        )
        entropy_rows.extend(collect_terms(name, result, term_order))
    entropy_term_rows = pd.DataFrame(entropy_rows)

    main_table = make_wide_model_table(
        term_rows,
        ["M0_controls", "M1_Mean", "M2_Top5", "M3_EqualIMRAD", "M4_IMRAD_parts", "M5_Abstract", "M6_Title", "M7_All_semantics"],
        term_order,
    )
    robust_table = make_wide_model_table(
        weighted_term_rows,
        ["W1_Mean", "W2_Top5", "W3_EqualIMRAD", "W4_IMRAD_parts", "W5_All_semantics"],
        term_order,
    )
    within_table = make_wide_model_table(
        within_term_rows,
        [
            "I1_Mean_issueFE",
            "I2_Top5_issueFE",
            "I3_Abstract_issueFE",
            "I4_Title_issueFE",
            "I5_All_semantics_issueFE",
            "I6_IMRAD_parts_issueFE",
        ],
        term_order,
    )
    entropy_table = make_wide_model_table(
        entropy_term_rows,
        ["E1_Mean_complete", "E2_EqualIMRAD", "E3_RecalcEntropy"],
        term_order,
    )
    summary_table = model_summary(term_rows, baseline_model="M0_controls")
    weighted_summary_table = model_summary(weighted_term_rows)
    binned_table = binned_mean_table(df)

    desc.to_csv(output_dir / "descriptive_statistics.csv", encoding="utf-8-sig")
    missing.to_csv(output_dir / "missing_rates.csv", encoding="utf-8-sig")
    corr.to_csv(output_dir / "correlations.csv", encoding="utf-8-sig")
    term_rows.to_csv(output_dir / "regression_terms_main.csv", index=False, encoding="utf-8-sig")
    weighted_term_rows.to_csv(output_dir / "regression_terms_weighted.csv", index=False, encoding="utf-8-sig")
    within_term_rows.to_csv(output_dir / "regression_terms_issue_fixed_effects.csv", index=False, encoding="utf-8-sig")
    entropy_term_rows.to_csv(output_dir / "regression_terms_entropy_comparison.csv", index=False, encoding="utf-8-sig")
    main_table.to_csv(output_dir / "regression_table_main.csv", index=False, encoding="utf-8-sig")
    robust_table.to_csv(output_dir / "regression_table_weighted.csv", index=False, encoding="utf-8-sig")
    within_table.to_csv(output_dir / "regression_table_issue_fixed_effects.csv", index=False, encoding="utf-8-sig")
    entropy_table.to_csv(output_dir / "regression_table_entropy_comparison.csv", index=False, encoding="utf-8-sig")
    summary_table.to_csv(output_dir / "model_summary_main.csv", index=False, encoding="utf-8-sig")
    weighted_summary_table.to_csv(output_dir / "model_summary_weighted.csv", index=False, encoding="utf-8-sig")
    binned_table.to_csv(output_dir / "binned_mean_deciles.csv", index=False, encoding="utf-8-sig")
    for name, terms in full_terms.items():
        terms.to_csv(output_dir / f"full_terms_{name}.csv", index=False, encoding="utf-8-sig")
    for name, terms in weighted_full_terms.items():
        terms.to_csv(output_dir / f"full_terms_{name}.csv", index=False, encoding="utf-8-sig")
    (output_dir / "entropy_weights.json").write_text(json.dumps(entropy_info, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(
        output_dir / "semantic_disruption_report.md",
        desc,
        missing,
        corr,
        main_table,
        robust_table,
        within_table,
        entropy_table,
        summary_table,
        binned_table,
        entropy_info,
    )

    print(json.dumps(
        {
            "rows": len(df),
            "output_dir": str(output_dir.resolve()),
            "main_sample_n": int(term_rows[term_rows["model"] == "M1_Mean"]["n"].iloc[0]),
            "imrad_sample_n": int(term_rows[term_rows["model"] == "M4_IMRAD_parts"]["n"].iloc[0]),
            "weighted_sample_n": int(weighted_term_rows[weighted_term_rows["model"] == "W1_Mean"]["n"].iloc[0]),
            "mean_coef": float(term_rows[(term_rows["model"] == "M1_Mean") & (term_rows["term"] == "Mean")]["coef"].iloc[0]),
            "mean_p": float(term_rows[(term_rows["model"] == "M1_Mean") & (term_rows["term"] == "Mean")]["p"].iloc[0]),
            "weighted_mean_coef": float(weighted_term_rows[(weighted_term_rows["model"] == "W1_Mean") & (weighted_term_rows["term"] == "Mean")]["coef"].iloc[0]),
            "weighted_mean_p": float(weighted_term_rows[(weighted_term_rows["model"] == "W1_Mean") & (weighted_term_rows["term"] == "Mean")]["p"].iloc[0]),
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
