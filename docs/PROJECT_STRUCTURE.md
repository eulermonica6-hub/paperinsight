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
│   ├── DATA_POLICY.md
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
