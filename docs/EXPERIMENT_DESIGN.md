# Experiment design

This document separates the estimand, public engineering workflow, and planned robustness work. It is designed to prevent the demo pipeline from being mistaken for the private empirical analysis.

## 1. Unit of analysis and timing

- **Unit:** paper.
- **Local comparison pool:** journal × year × volume × issue (`issue_id`).
- **Predictors:** semantic similarity features computed from text available at publication.
- **Primary outcomes:** later `cd_index` for disruption and a visibility outcome (log citations, with QWHI-family measures as robustness alternatives).
- **Controls:** issue size (`PP`), team size, references (`NR`), journal impact factor, year/journal effects, and cross-disciplinary status where available.
- **Clustering:** issue-level clustering is the default for the public linear-model implementation.

## 2. Core estimands

The primary estimands are the conditional associations of `Mean` and the IMRAD components with:

1. `cd_index = (n_disruptive - n_consolidating) / (n_disruptive + n_consolidating)`;
2. a log-transformed visibility outcome;
3. a quality-adjusted visibility outcome such as QWHI.

The same predictor set should be shown against the visibility and disruption outcomes in adjacent columns. This makes the proposed trade-off testable in one table rather than inferred from unrelated analyses.

## 3. Baseline specification

For a continuous outcome `Y`, estimate:

```text
Y_i = beta * semantic_i
    + gamma * controls_i
    + journal_FE + year_FE + error_i
```

Use issue-clustered standard errors and report the sample, missing-data rule, fixed effects, transformation, and weighting scheme for every model. The public implementation uses transparent NumPy/Pandas least squares so that the pipeline can run without a proprietary statistical package.

## 4. Required robustness sequence

### P0: close the visibility–disruption loop

- Add log citations, QWHI, H_Score, and Q_Score as alternative visibility outcomes.
- Report `cd_index` as the primary disruption outcome and disruptive share as a robustness outcome.
- Put both outcome families in one reproducible result table.

### P1: measurement and functional-form checks

- Compare entropy-weighted IMRAD with equal-weight IMRAD, `ABMEAN`, and `TIMEAN`.
- Compare MPNet with at least one scientific embedding model and a lexical baseline (TF-IDF or topic similarity).
- Use fractional logit or beta-binomial models for disruptive shares, including explicit handling of 0 and 1.
- Re-estimate across 2-, 5-, and 10-year citation windows.

### P2: external validity and falsification

- Replicate the same feature construction in at least one non-LIS field.
- Test additional disruption measures when licensing and data provenance permit.
- Permute issue assignments as a placebo for the local comparison pool.
- Report journal heterogeneity and meta-regression rather than presenting one pooled coefficient as universal.

### P3: mechanism and interpretation

- Pre-register or document selection rules for high-centrality/low-disruption and low-centrality/high-disruption cases.
- Add qualitative case summaries using only data cleared for public release.
- Distinguish global field centrality from local `Top5_Mean` neighborhood centrality.

## 5. Data-quality gates

Before a run is accepted:

1. Validate required columns and numeric ranges.
2. Record row counts before and after every filter.
3. Report missingness for outcomes, predictors, and controls.
4. Check whether `n_disruptive + n_consolidating` is zero.
5. Preserve a run manifest containing the input schema, code version, model formula, and output directory.
6. Confirm that no raw DOI, author string, abstract, manuscript text, or private path enters the public artifact.

## 6. Interpretation guardrails

- The public synthetic data is not an empirical replication.
- Association is not causation; publication selection, field composition, and citation practices may confound the relationship.
- Abstract-based IMRAD extraction is a measurement choice and may not represent full-text structure.
- Coefficients are specification- and corpus-dependent.
