from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = REPO_ROOT / "data" / "sample"
METADATA_DIR = SAMPLE_DIR / "metadata_sample"
CSV_PATH = SAMPLE_DIR / "paper_dataset_sample.csv"
METADATA_PATH = METADATA_DIR / "SAMPLE_with_metadata.json"

CSV_COLUMNS = [
    "journal",
    "DI",
    "SO",
    "AU",
    "AUNUM",
    "PY",
    "VL",
    "IS",
    "cd_index",
    "n_total",
    "n_disruptive",
    "n_consolidating",
    "Mean",
    "Top5_Mean",
    "Skewness",
    "Frac_Below_Global_Q25",
    "Frac_Above_Global_Q75",
    "PP",
    "FIS",
    "IMEAN",
    "MMEAN",
    "RMEAN",
    "DMEAN",
    "ABMEAN",
    "TIMEAN",
    "JIF",
    "NR",
    "2024JIF",
    "EF",
]


def clamp(value: float, low: float = 0.03, high: float = 0.97) -> float:
    return max(low, min(high, value))


def make_rows(seed: int = 20260629, n: int = 80) -> list[dict[str, object]]:
    rng = random.Random(seed)
    journals = [
        ("SJOIS", "SYNTHETIC JOURNAL OF INFORMATION SCIENCE"),
        ("JDSR", "JOURNAL OF DEMO SCHOLARLY RESEARCH"),
        ("AIMR", "ARTIFICIAL INTELLIGENCE METHODS REVIEW"),
        ("KMR", "KNOWLEDGE MANAGEMENT RESEARCH"),
        ("LISQ", "LIBRARY AND INFORMATION SCIENCE QUARTERLY"),
    ]

    rows: list[dict[str, object]] = []
    papers_per_issue = 4
    for idx in range(n):
        issue_group = idx // papers_per_issue
        journal, source = journals[issue_group % len(journals)]
        year = 2018 + (issue_group % 8)
        volume = 10 + (issue_group // 4)
        issue = 1 + (issue_group % 4)
        authors = 1 + (idx % 5)
        pages = 8 + (idx % 17)
        references = 18 + (idx * 7) % 95
        n_total = 25 + (idx * 11) % 165

        base = 0.34 + 0.22 * math.sin(idx / 5.5) + rng.uniform(-0.06, 0.06)
        imean = clamp(base + rng.uniform(-0.08, 0.08))
        mmean = clamp(base + rng.uniform(-0.10, 0.06))
        rmean = clamp(base + rng.uniform(-0.06, 0.10))
        dmean = clamp(base + rng.uniform(-0.09, 0.09))
        mean = (imean + mmean + rmean + dmean) / 4
        top5 = clamp(mean + 0.07 + rng.uniform(-0.05, 0.05))
        abmean = clamp(mean + rng.uniform(-0.11, 0.08))
        timean = clamp(mean + rng.uniform(-0.08, 0.10))

        disruption_rate = clamp(0.18 + 0.36 * mean + rng.uniform(-0.08, 0.08), 0.05, 0.82)
        n_disruptive = max(1, min(n_total - 1, round(n_total * disruption_rate)))
        n_consolidating = n_total - n_disruptive

        rows.append(
            {
                "journal": journal,
                "DI": f"10.0000/zpaper.sample.{idx + 1:04d}",
                "SO": source,
                "AU": f"Synthetic Author {idx % 9 + 1}; Synthetic Author {(idx + 3) % 9 + 1}",
                "AUNUM": authors,
                "PY": year,
                "VL": volume,
                "IS": issue,
                "cd_index": round(disruption_rate - 0.5, 4),
                "n_total": n_total,
                "n_disruptive": n_disruptive,
                "n_consolidating": n_consolidating,
                "Mean": round(mean, 9),
                "Top5_Mean": round(top5, 9),
                "Skewness": round(rng.uniform(-0.8, 0.8), 9),
                "Frac_Below_Global_Q25": round(clamp(0.45 - mean / 3 + rng.uniform(-0.04, 0.04)), 9),
                "Frac_Above_Global_Q75": round(clamp(0.12 + mean / 2.4 + rng.uniform(-0.04, 0.04)), 9),
                "PP": pages,
                "FIS": round(0.2 + (idx % 6) * 0.11 + rng.uniform(-0.04, 0.04), 3),
                "IMEAN": round(imean, 9),
                "MMEAN": round(mmean, 9),
                "RMEAN": round(rmean, 9),
                "DMEAN": round(dmean, 9),
                "ABMEAN": round(abmean, 9),
                "TIMEAN": round(timean, 9),
                "JIF": round(1.2 + (idx % 7) * 0.42 + rng.uniform(-0.08, 0.08), 3),
                "NR": references,
                "2024JIF": round(1.4 + (idx % 8) * 0.39 + rng.uniform(-0.08, 0.08), 3),
                "EF": round(0.15 + (idx % 5) * 0.21 + rng.uniform(-0.03, 0.03), 3),
            }
        )
    return rows


def make_metadata() -> list[dict[str, object]]:
    return [
        {
            "INFO": "SYNTHETIC_SAMPLE",
            "note": "Generated demonstration records. No real titles, abstracts, authors, or DOIs are included.",
        },
        {
            "Title": "Synthetic Study of Search Interface Signals",
            "Introduction": "Examines how visible interface cues shape discovery behavior in a controlled demo setting.",
            "Methods": "Uses simulated paper-level indicators and deterministic random variation.",
            "Results": "Higher synthetic visibility scores are associated with a higher generated disruption share.",
            "Discussion": "This record exists only to document the metadata schema used by the project.",
            "TI": "Synthetic Study of Search Interface Signals",
            "AB": "Synthetic abstract written for repository testing and examples.",
            "SO": "SYNTHETIC JOURNAL OF INFORMATION SCIENCE",
            "AU": "Synthetic Author 1; Synthetic Author 2",
            "DT": "Article",
            "PY": 2024,
            "VL": 1,
            "IS": 1,
            "DI": "10.0000/zpaper.sample.metadata.0001",
        },
        {
            "Title": "Synthetic Paper on Knowledge Diffusion Metrics",
            "Introduction": "Introduces a toy problem for validating IMRAD-style extraction pipelines.",
            "Methods": "Combines fabricated structured fields with schema-compatible identifiers.",
            "Results": "The sample can exercise loaders without revealing the private corpus.",
            "Discussion": "Replace this file with properly licensed private or public metadata for real analysis.",
            "TI": "Synthetic Paper on Knowledge Diffusion Metrics",
            "AB": "Another synthetic abstract for code examples only.",
            "SO": "JOURNAL OF DEMO SCHOLARLY RESEARCH",
            "AU": "Synthetic Author 3",
            "DT": "Article",
            "PY": 2025,
            "VL": 1,
            "IS": 2,
            "DI": "10.0000/zpaper.sample.metadata.0002",
        },
    ]


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(make_rows())

    METADATA_PATH.write_text(json.dumps(make_metadata(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"csv": str(CSV_PATH), "metadata": str(METADATA_PATH)}, indent=2))


if __name__ == "__main__":
    main()
