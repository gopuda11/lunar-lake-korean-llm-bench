#!/bin/bash
cd "$(dirname "$0")/.."
trap 'systemctl --user start npu-server; echo NPU_RESTARTED $(systemctl --user is-active npu-server)' EXIT
systemctl --user stop npu-server
curl -s 127.0.0.1:11434/api/generate -d '{"model":"gemma4:12b","keep_alive":0}' >/dev/null
O=${OLLAMA_BLOBS:-$HOME/.ollama/models/blobs}
G12=$O/sha256-bb722270d54346adc198f213851dbe0207e87c3ecf2a0aff4d92262726215391
G12D=$O/sha256-7008a656050bed18f6741406a631e83fa75ee1a02308f2e4f40d978cfbb3ce4b
G4=models/gemma-4-26b-a4b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf; G4D=models/gemma-4-26b-a4b/MTP/mtp-gemma-4-26B-A4B-it-Q8_0.gguf
Q36=models/qwen3.6-35b-a3b-mtp/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
Q38=models/qwen3.8-27b/Qwen3.8-27B-UD-Q4_K_XL.gguf; Q38D=models/qwen3.8-27b/MTP/mtp-Qwen3.8-27B-Q4_0.gguf
Q30=models/qwen3-30b-a3b/Qwen3-30B-A3B-Q4_K_M.gguf
S=scripts/mtp_v2.sh
$S g12-off $G12 none;  $S g12-mtp $G12 draft-mtp $G12D
$S g4-off  $G4 none;   $S g4-mtp  $G4 draft-mtp $G4D
$S q36-off $Q36 none;  $S q36-mtp $Q36 draft-mtp
$S q30-off $Q30 none
$S q38-off $Q38 none;  $S q38-mtp $Q38 draft-mtp $Q38D
echo V2_DONE
