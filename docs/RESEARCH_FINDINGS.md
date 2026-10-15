# Sanitized research findings

> This document records the current state of the research program without exposing the private corpus or article-level records. It is a research summary, not a claim that the synthetic demo reproduces the estimates below.

## 1. Research question

Does a paper's semantic position inside its publication issue predict two outcomes that are often treated as aligned: later scholarly visibility and citation-based disruption?

The working hypothesis is a trade-off:

> Issue-level semantic centrality can improve visibility while reducing the probability that a paper displaces the issue's prevailing knowledge structure.

The design uses text available at publication time and downstream citation outcomes measured over a later window. This temporal ordering supports early-prediction interpretation, but does not by itself establish causality.

## 2. Two connected research lines

### Semantic centrality and disruption

1. Extract Introduction, Methods, Results, and Discussion from abstracts with an LLM-assisted workflow.
2. Encode sections with sentence embeddings.
3. Compare each paper with the other papers in the same journal issue.
4. Compute section-level similarity (`IMEAN`, `MMEAN`, `RMEAN`, `DMEAN`).
5. Combine the section measures with entropy weights into `Mean`; use `Top5_Mean` as a local-neighborhood alternative.
6. Relate these predictors to later citation visibility and `cd_index`.

### Visibility quality measures

The companion line constructs `Q_Score`, `H_Score`, and `QWHI`, weighted h-index-like visibility measures, and compares them with journal impact factor and citation/disruption indicators. These measures are intended as alternative or quality-adjusted visibility outcomes, not as replacements for the primary disruption measure.

## 3. Current evidence map

The private working analysis covers a Web of Science information-science and library-science corpus from 2010–2020. Depending on the specification, usable observations range from approximately 24,763 after a minimum-citation restriction to approximately 30,140–30,700 in broader regression samples. Exact sample counts must therefore be reported with the model specification, missing-data rule, and citation window.

| Evidence | Current pattern | Interpretation |
| --- | --- | --- |
| `Mean` and later citations | Positive association in the main semantic-centrality specifications | Semantically central papers are more visible to later citing work |
| `Mean` and `cd_index` | Negative association in the main fixed-effect specifications | Centrality is associated with less disruptive citation patterns |
| IMRAD decomposition | `RMEAN` is the most stable negative component in the reported models | Similarity in Results language is a plausible mechanism candidate |
| Boundary conditions | Reference depth strengthens the integration pattern; large issue pools attenuate it; cross-disciplinary journals can reverse the direction | The association is context-dependent rather than universal |
| Tail outcomes | Negative patterns also appear for positive-disruption and top-decile specifications | The result concerns the type of influence, not only the average level |
| QWHI family and JIF | Overall Spearman correlations are positive: Q_Score 0.4362, H_Score 0.2121, QWHI 0.4693 | Quality-weighted visibility is related to conventional journal visibility, with substantial heterogeneity |

The strongest working narrative is therefore a **visibility–disruption trade-off**, with Results-section alignment as a mechanism candidate. The coefficients are intentionally not presented as universally transferable constants: they depend on the corpus, outcome window, controls, and fixed effects.

## 4. What has been learned

- A single raw citation count is not enough to represent visibility; QWHI-family measures provide a useful robustness direction.
- `cd_index` and disruptive-share outcomes are related but not interchangeable in estimation. The main analysis should choose `cd_index` and treat the share as a robustness outcome.
- Issue-level comparison pools operationalize a local knowledge field, but issue size (`PP`) is also a boundary condition and must be modeled.
- The synthetic demo can validate schema handling and execution only. Its coefficient signs must never be cited as empirical findings.
- The project is observational and initially concentrated in one broad field; causal and cross-field claims require additional tests.

## 5. Evidence and provenance

The findings were consolidated from the private working notes and outputs, including the local project synthesis, correlation summaries, regression diagnostics, variable definitions, and lagged-analysis work. Those files remain local and are intentionally not copied to GitHub. Public code exposes the calculation pattern and schema, not the private observations.
