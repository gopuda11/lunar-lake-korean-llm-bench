#!/bin/bash
# usage: mtp_run.sh <label> <model.gguf> <spec-type> [draft.gguf]
# starts llama-server, runs 2 Korean prompts (greedy, 300 tok), prints timings, stops server by PID
cd /mnt/data/ai/llm-bench
label=$1; model=$2; spec=$3; draft=$4
args=(-m "$model" -ngl 99 -fa on -c 4096 --port 18080 --host 127.0.0.1 -np 1 -lm none)
[ "$spec" != none ] && args+=(--spec-type "$spec")
[ -n "$draft" ] && args+=(-md "$draft" -ngld 99)
llama.cpp/build/bin/llama-server "${args[@]}" > logs/server-$label.log 2>&1 &
spid=$!
for i in $(seq 1 180); do curl -sf 127.0.0.1:18080/health >/dev/null && break; kill -0 $spid 2>/dev/null || { echo "$label SERVER_DIED"; tail -5 logs/server-$label.log; exit 1; }; sleep 1; done
sw0=$(awk '$1=="pswpin"{print $2}' /proc/vmstat)
for p in "리튬이온 배터리가 겨울에 성능이 떨어지는 이유를 고등학생이 이해할 수 있게 5문단으로 설명해 줘." "파이썬으로 CSV 파일에서 날짜별 매출 합계를 구하는 함수를 작성하고, 코드의 각 부분을 한국어로 설명해 줘."; do
  python -I -c 'import json,sys;print(json.dumps({"messages":[{"role":"user","content":sys.argv[1]}],"max_tokens":300,"temperature":0,"chat_template_kwargs":{"enable_thinking":False}}))' "$p" \
  | curl -s 127.0.0.1:18080/v1/chat/completions -H 'Content-Type: application/json' -d @- \
  | python -I -c 'import json,sys;d=json.load(sys.stdin);t=d.get("timings",{});print(sys.argv[1], "gen",t.get("predicted_n"),"tok",round(t.get("predicted_per_second",0),2),"t/s | prompt",round(t.get("prompt_per_second",0),1),"t/s | draft",t.get("draft_n"),"accepted",t.get("draft_n_accepted"))' "$label"
done
echo "$label swapin_pages=$(( $(awk '$1=="pswpin"{print $2}' /proc/vmstat) - sw0 ))"
kill $spid; wait $spid 2>/dev/null
grep -iE 'mtp|draft|spec' logs/server-$label.log | grep -iE 'error|fail|unsupported|not found' | head -3
