# PaperInsight

**AI-assisted scientific evaluation and semantic disruption research toolkit**

PaperInsight is the sanitized, open-source engineering companion to a research program on how the semantic position of a paper within a journal issue relates to later scholarly visibility and citation disruption.

The public repository contains reusable code, a schema-compatible synthetic dataset, and a documented experimental design. It does **not** contain the private corpus, article-level metadata, manuscript drafts, target-journal materials, or empirical output files.

## Research in one paragraph

The project studies a possible **visibility–disruption trade-off**. A paper that is semantically central to its issue may be easier for later work to discover and cite, while being less likely to replace the issue's prevailing knowledge structure. Semantic centrality is estimated from abstract sections (IMRAD), encoded with sentence embeddings, and aggregated within an issue-level comparison pool. Citation disruption is treated as a downstream outcome, so the public package emphasizes reproducible engineering and transparent design rather than shipping private empirical claims.

## What is included

- `src/zpaper/semantic_disruption.py` — schema validation, feature preparation, entropy-weighted IMRAD construction, fixed-effect regression, and report generation.
- `src/zpaper/make_sample_data.py` — deterministic synthetic data generator.
- `data/sample/` — synthetic paper-level records and metadata with no real papers, authors, or DOIs.
- `docs/RESEARCH_FINDINGS.md` — sanitized stage-by-stage findings and evidence map.
- `docs/EXPERIMENT_DESIGN.md` — current design, estimands, robustness checks, and next experiments.
- `docs/DATA_POLICY.md` — public/private data boundary and release checklist.
- `docs/PROJECT_STRUCTURE.md` — repository layout and workflow.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m zpaper.make_sample_data
python -m zpaper.semantic_disruption
```

The demo writes tables and a Markdown report to `outputs/demo_semantic_disruption/`. That directory is ignored by Git. The demo verifies the pipeline only; it is not evidence for the research findings.

## Run with a private or approved dataset

Prepare a CSV following [`docs/DATA_POLICY.md`](docs/DATA_POLICY.md), then run:

```powershell
python -m zpaper.semantic_disruption `
  --input data/private/your_dataset.csv `
  --output-dir outputs/your_run
```

Keep private data under `data/private/` or outside the repository. Never place raw records, author names, real DOI lists, manuscript text, or derived empirical outputs in `data/sample/`.

## Current research status

The engineering package is reproducible on synthetic data. The empirical findings summarized in [`docs/RESEARCH_FINDINGS.md`](docs/RESEARCH_FINDINGS.md) are a sanitized research record derived from a private working corpus and are not recreated by the demo dataset. The project remains observational: reported associations should not be read as causal effects.

## License

Code is released under the MIT License. Synthetic data is released for demonstration and testing only.
