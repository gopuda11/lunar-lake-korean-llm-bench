#!/bin/bash
# usage: mtp_v2.sh <label> <model.gguf> <none|draft-mtp> [draft.gguf]
# cool down, start llama-server, run 6 Korean prompts (greedy, 400 tok, no thinking),
# log tok/s, MTP acceptance, package temp, mean GPU freq, swap-in; stop server by PID.
cd /mnt/data/ai/llm-bench
label=$1; model=$2; spec=$3; draft=$4
FREQ=$(ls /sys/class/drm/card*/device/tile0/gt0/freq0/act_freq | head -1)
TEMP=$(grep -l x86_pkg_temp /sys/class/thermal/thermal_zone*/type | sed 's/type$/temp/')
t() { echo $(( $(cat $TEMP) / 1000 )); }
for i in $(seq 1 24); do [ $(t) -lt 60 ] && break; sleep 5; done   # cool to <60C, max 120 s
args=(-m "$model" -ngl 99 -fa on -c 4096 --port 18080 --host 127.0.0.1 -np 1 -lm none)
[ "$spec" != none ] && args+=(--spec-type "$spec")
[ -n "$draft" ] && args+=(-md "$draft" -ngld 99)
llama.cpp/build/bin/llama-server "${args[@]}" > logs/v2-server-$label.log 2>&1 &
spid=$!
for i in $(seq 1 240); do curl -sf 127.0.0.1:18080/health >/dev/null && break; kill -0 $spid 2>/dev/null || { echo "$label SERVER_DIED"; grep -iE 'error|fail' logs/v2-server-$label.log | tail -3; exit 1; }; sleep 1; done
sw0=$(awk '$1=="pswpin"{print $2}' /proc/vmstat)
n=0
while IFS= read -r p; do
  n=$((n+1)); t0=$(t)
  ( while :; do cat $FREQ; sleep 0.5; done ) > /tmp/claude-1000/freq.$$ & fpid=$!
  r=$(python -I -c 'import json,sys;print(json.dumps({"messages":[{"role":"user","content":sys.argv[1]}],"max_tokens":400,"temperature":0,"chat_template_kwargs":{"enable_thinking":False}}))' "$p" \
      | curl -s 127.0.0.1:18080/v1/chat/completions -H 'Content-Type: application/json' -d @-)
  kill $fpid; f=$(awk '{s+=$1;c++} END{printf "%d", s/c}' /tmp/claude-1000/freq.$$)
  echo "$r" | python -I /mnt/data/ai/llm-bench/scripts/fmt_v2.py "$label" $n $t0 $(t) $f
  echo "$r" > results/v2-$label-q$n.json
done < scripts/prompts_ko.txt
echo "$label swapin_MB=$(( ($(awk '$1=="pswpin"{print $2}' /proc/vmstat) - sw0) * 4 / 1024 ))"
kill $spid; wait $spid 2>/dev/null
rm -f /tmp/claude-1000/freq.$$
