#!/bin/bash
# download Qwen3.6 UD-IQ4_XS (MTP), verify, then llama-bench + v2 off/MTP runs with npu-server stopped
cd /mnt/data/ai/llm-bench
R=unsloth/Qwen3.6-35B-A3B-MTP-GGUF; F=Qwen3.6-35B-A3B-UD-IQ4_XS.gguf; D=models/qwen3.6-35b-a3b-mtp
~/.local/bin/uvx --from "huggingface_hub[hf_xet]" hf download $R $F --local-dir $D > logs/download-iq4xs.log 2>&1 || { echo DOWNLOAD_FAILED; exit 1; }
want=$(curl -s "https://huggingface.co/api/models/$R/paths-info/main" -d "paths=$F" | python -I -c 'import json,sys;print(json.load(sys.stdin)[0]["lfs"]["oid"])')
got=$(sha256sum $D/$F | cut -d' ' -f1)
[ "$want" = "$got" ] && echo "SHA_OK $F" || { echo "SHA_MISMATCH $F"; exit 1; }
trap 'systemctl --user start npu-server; echo NPU_RESTARTED $(systemctl --user is-active npu-server)' EXIT
systemctl --user stop npu-server
curl -s 127.0.0.1:11434/api/generate -d '{"model":"gemma4:12b","keep_alive":0}' >/dev/null
TEMP=$(grep -l x86_pkg_temp /sys/class/thermal/thermal_zone*/type | sed 's/type$/temp/')
for i in $(seq 1 24); do [ $(( $(cat $TEMP)/1000 )) -lt 60 ] && break; sleep 5; done
llama.cpp/build/bin/llama-bench -m $D/$F -ngl 99 -fa 1 -lm none -p 512 -n 128 -r 3 -o md 2>logs/bench-q36-iq4xs.err | tee results/bench-q36-iq4xs.md
scripts/mtp_v2.sh q36x-off $D/$F none
scripts/mtp_v2.sh q36x-mtp $D/$F draft-mtp
echo Q36X_DONE
