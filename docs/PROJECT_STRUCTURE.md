# Project Structure

The public repository is organized as a clean research-code package.

```text
.
├── src/zpaper/
│   ├── __init__.py
│   ├── make_sample_data.py
│   └── semantic_disruption.py
├── data/sample/
│   ├── paper_dataset_sample.csv
│   └── metadata_sample/
│       └── SAMPLE_with_metadata.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_POLICY.md
│   ├── EXPERIMENT_DESIGN.md
│   ├── RESEARCH_FINDINGS.md
│   └── PROJECT_STRUCTURE.md
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
└── .gitignore
```

The original local workspace also contains private analysis outputs, manuscript drafts, reference PDFs, and exploratory scripts. Those files are kept on disk for local continuity but are not part of the open-source release.

## Main Workflow

1. Generate or provide a schema-compatible paper-level CSV.
2. Run `zpaper.semantic_disruption`.
3. Review generated CSV tables and the Markdown report under `outputs/`.

The public sample is designed to verify code execution and schema handling. It should not be interpreted as an empirical result.

The research narrative and planned robustness sequence are documented separately from the executable package:

- [`RESEARCH_FINDINGS.md`](RESEARCH_FINDINGS.md) records the sanitized evidence map and interpretation guardrails.
- [`EXPERIMENT_DESIGN.md`](EXPERIMENT_DESIGN.md) records estimands, baseline models, data-quality gates, and follow-up experiments.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) explains the engineering layers, data boundary, and end-to-end workflow.
