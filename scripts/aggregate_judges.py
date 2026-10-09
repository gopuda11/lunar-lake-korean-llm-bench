"""Combine the judge panel (forward + reversed order each) into per-question verdicts.

Judges: jev, clef (systemone probability API, results/quality/judge_<name>/<qid>-<fwd|rev>.json)
and codex, claude, gemini (JSON verdict files results/quality/judge_<name>_<fwd|rev>.json).
Per judge and question: mean scores over the two orders (1-5) and a best label that counts as a
vote only if both orders agree. A question is decided when one label gets a strict majority of
the judges that answered (>= 3 of 5), or when a unique plurality (>= 2 votes) matches the label
with the highest panel-mean total score; otherwise it goes to the owner.
Writes results/quality/judge_summary.json; prints labels only unless --reveal is given.
"""
import json
import sys
from collections import Counter
from pathlib import Path

Q = Path("/mnt/data/ai/llm-bench/results/quality")
reveal = "--reveal" in sys.argv
data = json.load(open(Q / "grading_data.json", encoding="utf-8"))
blind = json.load(open(Q / "blind_map.json", encoding="utf-8"))
CRIT = ("acc", "ko", "follow")
PROB_JUDGES = ("jev", "clef")
JSON_JUDGES = ("codex", "claude", "gemini")


def prob_runs(name, qid):
    runs = []
    for tag in ("fwd", "rev"):
        p = Q / f"judge_{name}" / f"{qid}-{tag}.json"
        if not p.exists():
            return None
        a = json.load(open(p, encoding="utf-8"))["response"]["answers"]
        labels = list(a["best"]["probabilities"])
        runs.append({"best": a["best"]["choice"],
                     "scores": {l: {c: a[f"{c}_{l}"]["score"] + 1 for c in CRIT} for l in labels}})
    return runs


def json_runs(name, qid):
    runs = []
    for tag in ("fwd", "rev"):
        p = Q / f"judge_{name}_{tag}.json"
        if not p.exists():
            return None
        v = json.load(open(p, encoding="utf-8")).get(qid)
        if not v:
            return None
        runs.append({"best": v["best"], "scores": {l: {c: float(s[c]) for c in CRIT} for l, s in v["scores"].items()}})
    return runs


def merge(runs):
    if not runs:
        return None
    labels = runs[0]["scores"].keys()
    mean = {l: {c: round(sum(r["scores"][l][c] for r in runs) / len(runs), 2) for c in CRIT} for l in labels}
    bests = [r["best"] for r in runs]
    return {"best": bests[0] if len(set(bests)) == 1 else None, "bests": bests, "scores": mean}


judges = {n: (lambda q, n=n: prob_runs(n, q)) for n in PROB_JUDGES}
judges.update({n: (lambda q, n=n: json_runs(n, q)) for n in JSON_JUDGES})

summary, disputed, consistency = {}, [], Counter()
for q in data["questions"]:
    qid = q["id"]
    per = {n: merge(f(qid)) for n, f in judges.items()}
    present = {n: v for n, v in per.items() if v}
    votes = Counter(v["best"] for v in present.values() if v["best"])
    for n, v in present.items():
        consistency[n] += v["best"] is not None
    top, n_top = votes.most_common(1)[0] if votes else (None, 0)
    totals = {}
    for v in present.values():
        for l, sc in v["scores"].items():
            totals.setdefault(l, []).append(sum(sc.values()))
    panel = {l: round(sum(x) / len(x), 2) for l, x in totals.items()}
    score_top = max(panel, key=panel.get) if panel else None
    unique_plurality = n_top >= 2 and list(votes.values()).count(n_top) == 1
    decided = n_top * 2 > len(present) or (unique_plurality and top == score_top)
    summary[qid] = {"judges": per, "votes": dict(votes), "n_judges": len(present), "panel_mean": panel,
                    "final_best": top if decided else None}
    if not decided:
        disputed.append(qid)

json.dump(summary, open(Q / "judge_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for qid, s in summary.items():
    print(qid, f"best={s['final_best'] or 'DISPUTED'}", "votes", s["votes"], f"({s['n_judges']} judges)")
print("order-consistent best per judge (of 20):", dict(consistency))
print("disputed:", disputed)

if reveal:
    models = sorted({m for v in blind.values() for m in v.values()})
    print("\nmodel | wins | " + " | ".join(f"{n} acc/ko/follow" for n in judges))
    for m in models:
        wins = sum(1 for qid, s in summary.items() if s["final_best"] and blind[qid][s["final_best"]] == m)
        cols = []
        for n in judges:
            vals = [s["judges"][n]["scores"][l] for qid, s in summary.items() if s["judges"].get(n)
                    for l, mm in blind[qid].items() if mm == m]
            cols.append("/".join(f"{sum(v[c] for v in vals) / len(vals):.2f}" for c in CRIT) if vals else "-")
        print(m, "|", wins, "|", " | ".join(cols))
