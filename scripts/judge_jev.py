"""Judge the blind answers with JEV (typesafe systemone API) or, with --clef, Cloudflare Clef.

For each question: two calls, answers in forward and reversed order (position-bias check).
Questions per call: `best` (choice over labels) and, per answer, acc/ko/follow (score, 5 levels).
Raw responses go to results/quality/judge_jev/<qid>-<fwd|rev>.json. Credentials come from
~/.config/decision-gateway/env and ~/.config/jev/env and are never printed.
usage: judge_jev.py [--clef] <grading-data.json> [qid ...]
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

env = {}
for f in (".config/decision-gateway/env", ".config/jev/env"):
    for line in open(Path.home() / f, encoding="utf-8"):
        line = line.strip().removeprefix("export ")
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
JUDGE = "clef" if "--clef" in sys.argv else "jev"
if JUDGE == "jev":
    URL = env.get("JEV_URL") or "https://api.typesafe.ai/v1/systemone"
    MODEL = env.get("JEV_MODEL") or "jev-1.13.0"
    KEY = env["JEV_API_KEY"]
else:  # Cloudflare Workers AI clef model, same {model, state, questions} wire format wrapped in {result}
    MODEL = env.get("CLEF_MODEL") or "clef-flash"
    URL = env.get("CLEF_URL") or f"https://api.cloudflare.com/client/v4/accounts/{env['CF_ACCOUNT_ID']}/ai/run/@cf/cloudflare/{MODEL}"
    KEY = env["CF_API_TOKEN"]
OUT = ROOT / f"results/quality/judge_{JUDGE}"
OUT.mkdir(parents=True, exist_ok=True)

LEVELS = ["1 매우 나쁨", "2 나쁨", "3 보통", "4 좋음", "5 매우 좋음"]
CRIT = {
    "acc": "답안 {l}의 내용이 사실과 맞고 질문에 맞는 답인가? (틀린 사실, 지어낸 내용이 있으면 낮게)",
    "ko": "답안 {l}의 한국어가 자연스러운가? (번역투, 어색한 어휘, 문법 오류가 있으면 낮게)",
    "follow": "답안 {l}이 질문의 형식, 분량, 조건을 지켰는가?",
}


def build(q, order):
    parts = [f"한국어 질문에 대한 AI 답안 {len(order)}개를 채점한다. 답안 순서는 품질과 무관하다.",
             "", "[질문]", q["prompt"], ""]
    for a in order:
        parts += [f"[답안 {a['label']}]", a["text"], ""]
    questions = {"best": {"type": "choice",
                          "instructions": "정확성, 한국어 자연스러움, 지시 이행을 모두 고려할 때 가장 좋은 답안은?",
                          "criteria": {a["label"]: f"답안 {a['label']}" for a in order}}}
    for a in order:
        for k, text in CRIT.items():
            questions[f"{k}_{a['label']}"] = {"type": "score", "instructions": text.format(l=a["label"]), "criteria": LEVELS}
    return "\n".join(parts), questions


def call(state, questions):
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}, ensure_ascii=False).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.load(r)
    if JUDGE == "clef":
        if res.get("success") is False or "result" not in res:
            raise ValueError("clef_error")
        res = res["result"]
    return res


args = [a for a in sys.argv[1:] if a != "--clef"]
data = json.load(open(args[0], encoding="utf-8"))
want = set(args[1:])
for q in data["questions"]:
    if want and q["id"] not in want:
        continue
    for tag, order in (("fwd", q["answers"]), ("rev", list(reversed(q["answers"])))):
        path = OUT / f"{q['id']}-{tag}.json"
        if path.exists():
            continue
        state, questions = build(q, order)
        for attempt in range(3):
            try:
                res = call(state, questions)
                break
            except Exception as e:  # network/rate limit: back off, never print the request
                err = type(e).__name__ + (f" {e.code}" if hasattr(e, "code") else "")
                time.sleep(5 * (attempt + 1))
        else:
            print(q["id"], tag, "FAILED", err, flush=True)
            continue
        json.dump({"qid": q["id"], "order": [a["label"] for a in order], "state_bytes": len(state.encode()), "response": res},
                  open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(q["id"], tag, "ok", flush=True)
