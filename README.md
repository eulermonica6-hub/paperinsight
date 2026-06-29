<<<<<<< HEAD
# paperinsight
AI as a scientific evaluator.
=======
# Zpaper Semantic Disruption Toolkit

This repository contains a sanitized, open-source wrapper for a research workflow that studies the relationship between semantic visibility signals and downstream citation-disruption indicators.

The public package includes reusable Python code, schema-compatible synthetic sample data, and documentation. The private corpus, manuscript drafts, target-journal PDFs, reviewer materials, and generated research outputs are intentionally excluded.

## What Is Included

- `src/zpaper/semantic_disruption.py`: regression pipeline for paper-level semantic and disruption indicators.
- `src/zpaper/make_sample_data.py`: deterministic generator for synthetic sample data.
- `data/sample/`: generated demo CSV and metadata JSON with no real papers or authors.
- `docs/`: data policy and project-structure notes for safe GitHub sharing.

## What Is Not Included

The original local project contains private research inputs and derived materials such as full metadata JSON files, article-level data, draft manuscripts, figures, rendered reports, and target-journal references. These are ignored by `.gitignore` and should not be uploaded.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m zpaper.make_sample_data
python -m zpaper.semantic_disruption
```

The demo run writes tables and a Markdown report to `outputs/demo_semantic_disruption/`. That output directory is ignored by Git.

## Run With Your Own Data

Prepare a CSV with the schema documented in `docs/DATA_POLICY.md`, then run:

```powershell
python -m zpaper.semantic_disruption --input data/private/your_dataset.csv --output-dir outputs/your_run
```

Keep private data under `data/private/` or pass an explicit private path. Do not place raw data in `data/sample/`.

## License

Code is released under the MIT License. The synthetic sample data is released for demonstration use only and does not represent empirical findings.
>>>>>>> 2547de4 (Add project files)
