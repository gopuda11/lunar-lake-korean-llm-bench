import json, sys, time, urllib.request
prompts, out, port, label = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
for line in open(prompts, encoding="utf-8"):
    p = json.loads(line)
    body = {"messages": [{"role": "user", "content": p["prompt"]}], "max_tokens": 1200,
            "temperature": 0.3, "top_p": 0.9, "seed": 42,
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    d = json.load(urllib.request.urlopen(req, timeout=3600))
    msg = d["choices"][0]["message"]
    rec = {"id": p["id"], "category": p["category"], "prompt": p["prompt"], "model": label,
           "answer": msg.get("content") or "", "reasoning": msg.get("reasoning_content") or "",
           "finish_reason": d["choices"][0].get("finish_reason"), "timings": d.get("timings"),
           "wall_s": round(time.time() - t0, 1)}
    json.dump(rec, open(f"{out}/{p['id']}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(label, p["id"], rec["finish_reason"], len(rec["answer"]), "chars", flush=True)
