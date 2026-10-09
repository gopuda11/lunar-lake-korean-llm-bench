#!/bin/bash
# llama-bench each model; record peak used RAM and swap-in/out pages during the run
cd "$(dirname "$0")/.."
BIN=llama.cpp/build/bin/llama-bench
declare -a MODELS=(
  "gemma-4-26b-a4b|models/gemma-4-26b-a4b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf"
  "qwen3.8-27b|models/qwen3.8-27b/Qwen3.8-27B-UD-Q4_K_XL.gguf"
  "qwen3-30b-a3b|models/qwen3-30b-a3b/Qwen3-30B-A3B-Q4_K_M.gguf"
  "qwen3.6-35b-a3b|models/qwen3.6-35b-a3b-mtp/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
)
vm() { awk -v k=$1 '$1==k{print $2}' /proc/vmstat; }
for e in "${MODELS[@]}"; do
  name=${e%%|*}; path=${e#*|}
  echo "=== $name $(date +%T)"
  in0=$(vm pswpin); out0=$(vm pswpout); peak=0
  $BIN -m "$path" -ngl 99 -fa 1 -lm none -p 512 -n 128 -r 3 -o md > results/bench-$name.md 2> logs/bench-$name.err &
  pid=$!
  while kill -0 $pid 2>/dev/null; do
    u=$(LC_ALL=C free -b | awk '/^Mem/{print $3}'); [ $u -gt $peak ] && peak=$u; sleep 1
  done
  wait $pid; rc=$?
  in1=$(vm pswpin); out1=$(vm pswpout)
  cat results/bench-$name.md
  echo "rc=$rc peak_used_GiB=$(awk -v p=$peak 'BEGIN{printf "%.1f",p/2^30}') swapin_pages=$((in1-in0)) swapout_pages=$((out1-out0))" | tee results/mem-$name.txt
  sleep 10
done
echo BENCH_DONE
