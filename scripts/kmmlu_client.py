#!/usr/bin/env python3
"""Run resumable zero-shot KMMLU evaluation against llama-server."""

import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

PROMPT = (
    "다음 객관식 문제의 정답 번호를 고르세요. "
    "설명 없이 숫자 하나(1, 2, 3, 4)만 답하세요.\n\n"
    "문제: {question}\n1. {A}\n2. {B}\n3. {C}\n4. {D}\n\n정답:"
)


def read_jsonl(path):
    with path.open(encoding="utf-8") as src:
        return [json.loads(line) for line in src if line.strip()]


def request(url, item):
    a, b, c, d = item["choices"]
    prompt = PROMPT.format(question=item["question"], A=a, B=b, C=c, D=d)
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 8,
        "seed": 42,
        "chat_template_kwargs": {"enable_thinking": False},
        "logprobs": True,
        "top_logprobs": 20,
    }, ensure_ascii=False).encode("utf-8")

    # Initial attempt plus three retries.
    for attempt in range(4):
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                return json.load(response)
        except (urllib.error.URLError, OSError) as error:
            if attempt == 3:
                raise RuntimeError(
                    f"{item['id']}: request failed after 4 attempts: {error}"
                ) from error
            print(
                f"{item['id']}: {error}; retry {attempt + 1}/3 in 5 s",
                file=sys.stderr, flush=True,
            )
            time.sleep(5)


def predict(response):
    choices = response.get("choices") if isinstance(response, dict) else None
    choice = choices[0] if isinstance(choices, list) and choices else {}
    if not isinstance(choice, dict):
        choice = {}

    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else ""
    if not isinstance(content, str):
        content = ""

    logprobs = choice.get("logprobs")
    tokens = logprobs.get("content") if isinstance(logprobs, dict) else None
    first = tokens[0] if isinstance(tokens, list) and tokens else {}
    top = first.get("top_logprobs") if isinstance(first, dict) else None

    best = None
    best_score = -math.inf
    for entry in top if isinstance(top, list) else []:
        if not isinstance(entry, dict):
            continue
        token, score = entry.get("token"), entry.get("logprob")
        if not isinstance(token, str) or token.strip() not in ("1", "2", "3", "4"):
            continue
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            continue
        if math.isfinite(score) and score > best_score:
            best, best_score = int(token.strip()), score

    if best is not None:
        return best, "logprob", content
    match = re.search(r"[1-4]", content)
    if match:
        return int(match.group()), "text", content
    return None, "none", content


def progress(label, rows, total):
    done = len(rows)
    correct = sum(row["correct"] is True for row in rows.values())
    seconds = sum(row["wall_s"] for row in rows.values())
    accuracy = correct / done if done else 0
    mean = seconds / done if done else 0
    print(
        f"{label} {done}/{total} accuracy={accuracy:.2%} "
        f"mean_s/question={mean:.3f}",
        flush=True,
    )


def summary(label, rows, total):
    progress(label, rows, total)
    counts, correct, sources = Counter(), Counter(), Counter()
    missing = 0
    for row in rows.values():
        category = row.get("category") or row["subject"]
        counts[category] += 1
        correct[category] += row["correct"] is True
        sources[row["pred_src"]] += 1
        missing += row["pred"] is None

    for category in sorted(counts):
        n, hits = counts[category], correct[category]
        print(f"{label} {category}: {hits}/{n} accuracy={hits / n:.2%}")
    print(
        f"{label} pred=None: {missing}; "
        f"logprob: {sources['logprob']}; text: {sources['text']}",
        flush=True,
    )


def main():
    if len(sys.argv) != 5:
        raise SystemExit(
            "Usage: kmmlu_client.py <sample.jsonl> <out.jsonl> <port> <label>"
        )
    sample_path, out_path = map(Path, sys.argv[1:3])
    port, label = sys.argv[3:]
    url = f"http://127.0.0.1:{int(port)}/v1/chat/completions"

    sample = read_jsonl(sample_path)
    ids = {item["id"] for item in sample}
    if len(ids) != len(sample):
        raise ValueError("Duplicate IDs in sample")

    existing = read_jsonl(out_path) if out_path.exists() else []
    rows = {row["id"]: row for row in existing if row["id"] in ids}
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve a valid final record even when it lacks a terminating newline.
    needs_newline = False
    if out_path.exists() and out_path.stat().st_size:
        with out_path.open("rb") as src:
            src.seek(-1, 2)
            needs_newline = src.read(1) != b"\n"

    with out_path.open("a", encoding="utf-8") as out:
        if needs_newline:
            out.write("\n")
            out.flush()

        for item in sample:
            if item["id"] in rows:
                continue
            started = time.monotonic()
            response = request(url, item)
            pred, source, content = predict(response)
            row = {
                "id": item["id"],
                "subject": item["subject"],
                "category": item.get("category") or item["subject"],
                "answer": item["answer"],
                "pred": pred,
                "pred_src": source,
                "correct": pred == item["answer"],
                "content": content,
                "wall_s": round(time.monotonic() - started, 6),
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            rows[row["id"]] = row
            if len(rows) % 50 == 0:
                progress(label, rows, len(sample))

    summary(label, rows, len(sample))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
