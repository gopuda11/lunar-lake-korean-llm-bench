#!/bin/bash
# usage: gen_quality.sh <label> <model.gguf> [draft.gguf]
# answers the 20 Korean quality prompts (temp 0.3, top_p 0.9, seed 42, no thinking, max 1200 tok) with MTP on
cd /mnt/data/ai/llm-bench
label=$1; model=$2; draft=$3
out=results/quality/$label; mkdir -p $out
args=(-m "$model" -ngl 99 -fa on -c 8192 --port 18081 --host 127.0.0.1 -np 1 -lm none --spec-type draft-mtp)
[ -n "$draft" ] && args+=(-md "$draft" -ngld 99)
llama.cpp/build/bin/llama-server "${args[@]}" > logs/quality-server-$label.log 2>&1 &
spid=$!
for i in $(seq 1 300); do curl -sf 127.0.0.1:18081/health >/dev/null && break; kill -0 $spid 2>/dev/null || { echo "$label SERVER_DIED"; exit 1; }; sleep 1; done
python -I scripts/gen_quality_client.py scripts/prompts_quality_ko.jsonl $out 18081 "$label"
kill $spid; wait $spid 2>/dev/null
echo "$label GEN_DONE"
