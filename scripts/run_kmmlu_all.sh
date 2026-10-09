#!/usr/bin/env bash
# Run KMMLU sequentially, stopping only the server PID started here.
# Run 6 (2026-10-09): only qwen3-30b left (resumes at 199/900); --n-cpu-moe keeps the first N layers' experts in mmap (reclaimable) RAM so GPU-pinned memory stays ~11 GB (full offload OOM-froze the laptop).
# --no-host --no-repack -lm mmap: otherwise the CPU-side experts land in pinned Vulkan host buffers or anon memory (auto load mode skips mmap on Vulkan), not reclaimable mmap pages.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
mkdir -p logs results/kmmlu || exit 1
sample=results/kmmlu/sample-20x45.jsonl
[[ -f "$sample" ]] || { printf 'Missing sample: %s\n' "$sample" >&2; exit 1; }

server=llama.cpp/build/bin/llama-server
spid=""
overall_rc=0

stop_server() {
    [[ -n "$spid" ]] || return 0
    kill "$spid" 2>/dev/null || :
    local deadline=$((SECONDS + 30))
    while kill -0 "$spid" 2>/dev/null && ((SECONDS < deadline)); do
        sleep 1
    done
    if kill -0 "$spid" 2>/dev/null; then
        kill -9 "$spid" 2>/dev/null || :
    fi
    wait "$spid" 2>/dev/null || :
    spid=""
}

trap stop_server EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

while IFS='|' read -r label gguf ncmoe; do
    curl -s --connect-timeout 2 --max-time 30 \
        127.0.0.1:11434/api/generate \
        -H 'Content-Type: application/json' \
        -d '{"model":"gemma4:12b","keep_alive":0}' >/dev/null || :

    "$server" -m "$gguf" -ngl 99 -fa on -c 4096 --n-cpu-moe "${ncmoe:-0}" --no-host --no-repack -lm mmap \
        --port 18082 --host 127.0.0.1 -np 1 \
        >"logs/kmmlu-server-$label.log" 2>&1 &
    spid=$!

    ready=0
    deadline=$((SECONDS + 300))
    while ((SECONDS < deadline)); do
        kill -0 "$spid" 2>/dev/null || break
        remaining=$((deadline - SECONDS))
        timeout=2
        ((remaining < timeout)) && timeout=$remaining
        if curl -sf --connect-timeout "$timeout" --max-time "$timeout" \
            127.0.0.1:18082/health >/dev/null; then
            ready=1
            break
        fi
        ((SECONDS < deadline)) && sleep 1
    done

    if ! kill -0 "$spid" 2>/dev/null; then
        printf '%s SERVER_DIED\n' "$label"
        overall_rc=1
        stop_server
        continue
    fi
    if ((ready == 0)); then
        printf '%s SERVER_TIMEOUT\n' "$label"
        overall_rc=1
        stop_server
        continue
    fi

    if python -I scripts/kmmlu_client.py \
        "$sample" "results/kmmlu/$label.jsonl" 18082 "$label"; then
        client_rc=0
    else
        client_rc=$?
        overall_rc=1
        printf '%s CLIENT_FAILED exit=%s\n' "$label" "$client_rc" >&2
    fi

    stop_server
    printf '%s KMMLU_DONE\n' "$label"
done <<'MODELS'
qwen3-30b-a3b|models/qwen3-30b-a3b/Qwen3-30B-A3B-Q4_K_M.gguf|21
MODELS

printf 'KMMLU_ALL_DONE\n'
exit "$overall_rc"
