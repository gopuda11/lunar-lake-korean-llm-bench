#!/usr/bin/env python3
"""Create a deterministic, stratified KMMLU sample."""

import csv
import json
import random
from collections import Counter
from pathlib import Path

DATA = Path("/mnt/data/ai/llm-bench/data/kmmlu-d61b3f19")
OUT = Path("results/kmmlu/sample-20x45.jsonl")


def main():
    files = sorted(DATA.glob("*-test.csv"))
    if not files:
        raise SystemExit(f"No test CSV files found in {DATA}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    total = 0

    with OUT.open("w", encoding="utf-8") as out:
        for path in files:
            subject = path.name.removesuffix("-test.csv")
            with path.open(encoding="utf-8-sig", newline="") as src:
                rows = list(csv.DictReader(src))

            rng = random.Random(f"kmmlu-{subject}-42")
            indices = sorted(rng.sample(range(len(rows)), min(20, len(rows))))
            for index in indices:
                row = rows[index]
                category = (row.get("Category") or "").strip() or subject
                item = {
                    "id": f"{subject}-{index}",  # Zero-based CSV data-row index.
                    "subject": subject,
                    "category": category,
                    "question": row["question"],
                    "choices": [row[key] for key in "ABCD"],
                    "answer": int(row["answer"]),
                }
                if item["answer"] not in (1, 2, 3, 4):
                    raise ValueError(f"Invalid answer: {item['id']}")
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
                counts[category] += 1
                total += 1

    print(f"Total: {total} -> {OUT}")
    for category, count in sorted(counts.items()):
        print(f"{category}: {count}")


if __name__ == "__main__":
    main()
