#!/bin/bash
# Ollama gemma4:12b under live conditions (npu-server up): same 6 prompts, greedy, 400 tok, no thinking
cd "$(dirname "$0")/.."
TEMP=$(grep -l x86_pkg_temp /sys/class/thermal/thermal_zone*/type | sed 's/type$/temp/')
t() { echo $(( $(cat $TEMP) / 1000 )); }
for i in $(seq 1 24); do [ $(t) -lt 60 ] && break; sleep 5; done
since=$(date '+%Y-%m-%d %H:%M:%S')
n=0
while IFS= read -r p; do
  n=$((n+1)); t0=$(t)
  python -I -c 'import json,sys;print(json.dumps({"model":"gemma4:12b","messages":[{"role":"user","content":sys.argv[1]}],"stream":False,"think":False,"options":{"num_predict":400,"temperature":0}}))' "$p" \
  | curl -s 127.0.0.1:11434/api/chat -d @- > results/v2-ollama-q$n.json
  python -I scripts/fmt_ollama.py results/v2-ollama-q$n.json $n $t0 $(t)
done < scripts/prompts_ko.txt
journalctl --user -u ollama --since "$since" --no-pager | grep -oE 'offloaded [0-9]+/49 layers|draft acceptance = [0-9.]+' | sort | uniq -c
