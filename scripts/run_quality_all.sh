#!/bin/bash
# waits for the IQ4_XS speed run to finish (npu-server back up), then generates answers with npu-server UP
cd "$(dirname "$0")/.."
until grep -q NPU_RESTARTED logs/q36x.log 2>/dev/null || grep -qE 'DOWNLOAD_FAILED|SHA_MISMATCH' logs/q36x.log 2>/dev/null; do sleep 15; done
until ! pgrep -x llama-server >/dev/null; do sleep 5; done
curl -s 127.0.0.1:11434/api/generate -d '{"model":"gemma4:12b","keep_alive":0}' >/dev/null
O=${OLLAMA_BLOBS:-$HOME/.ollama/models/blobs}
S=scripts/gen_quality.sh
$S gemma4-12b $O/sha256-bb722270d54346adc198f213851dbe0207e87c3ecf2a0aff4d92262726215391 $O/sha256-7008a656050bed18f6741406a631e83fa75ee1a02308f2e4f40d978cfbb3ce4b
$S gemma4-26b-a4b models/gemma-4-26b-a4b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf models/gemma-4-26b-a4b/MTP/mtp-gemma-4-26B-A4B-it-Q8_0.gguf
X=models/qwen3.6-35b-a3b-mtp/Qwen3.6-35B-A3B-UD-IQ4_XS.gguf
[ -f $X ] && $S qwen3.6-35b-a3b-iq4xs $X || echo "qwen3.6 iq4xs missing, skipped"
$S qwen3.8-27b models/qwen3.8-27b/Qwen3.8-27B-UD-Q4_K_XL.gguf models/qwen3.8-27b/MTP/mtp-Qwen3.8-27B-Q4_0.gguf
echo QUALITY_ALL_DONE
