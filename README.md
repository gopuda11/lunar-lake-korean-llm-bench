# Lunar Lake 노트북 로컬 LLM 한국어 벤치마크

Intel Lunar Lake 노트북(Core Ultra 5 228V, 32 GB 통합 메모리)에서 로컬 MoE 모델을 돌렸을 때
**한국어 품질 × 속도 × 메모리**가 어떤지 측정한 기록입니다.
같은 하드웨어의 공개 사례([MatheusSchneiderr/lunar-lake-local-llm](https://github.com/MatheusSchneiderr/lunar-lake-local-llm))는
영어 코딩만 다루고 있어서, 한국어 검증을 더하는 것이 목적입니다.

**결론: 이 노트북에서 평소 서비스(브라우저, 로컬 서버 등)와 함께 상시 운영한다면 gemma4:12b가 현실적인 최선입니다.**
Gemma-4-26B-A4B가 품질·KMMLU 모두 1위지만 차이는 작고, Q4 양자화(약 17 GB)를 GPU에 전부 올리면
긴 실행에서 메모리 부족(OOM)으로 두 번 죽었고 한 번은 노트북 전체가 멈췄습니다.

## 결과 요약

| 모델 | 실사용 tok/s | 한국어 품질 1위 횟수 /20 | 심사단 평균 (1-5) | 한국어 자연스러움 | KMMLU 900문항 (±95% CI) |
|---|---|---|---|---|---|
| Gemma-4-26B-A4B UD-Q4_K_XL | 22.5 (MTP) / 19.2 | 9.5 | 4.39 | 4.54 | **65.78%** ±3.1 |
| Qwen3.6-35B-A3B UD-IQ4_XS | 21.6 | 5.5 | 3.94 | 3.88 | 63.33% ±3.1 |
| gemma4:12b | 19.0 (MTP, llama.cpp) / 13.5 (Ollama) | 4.0 | 4.26 | 4.42 | 60.33% ±3.2 |
| Qwen3-30B-A3B Q4_K_M | 22.4 | 평가 안 함 | – | – | 56.11% ±3.2 |
| Qwen3.8-27B UD-Q4_K_XL (dense) | 4.3 (MTP) | 제외 (20개 중 16개만 생성) | – | – | 측정 안 함 |

- 1위 횟수는 작은 차이도 크게 보이게 합니다. 평균 점수로 보면 Gemma-4-26B와 gemma4:12b는 0.1점 남짓 차이입니다.
- KMMLU에서 26B와 Qwen3.6의 차이(2.4%p)는 신뢰구간 안입니다. 26B와 12b의 차이는 +5.4%p입니다.
- 관찰된 결함: Qwen3.6은 한자가 섞여 나옴(k02), gemma 12b/26b는 LaTeX `$\rightarrow$`가 섞여 나옴(k07).

자세한 표: [`results/FINAL-2026-10-08.md`](results/FINAL-2026-10-08.md), 속도: [`results/SUMMARY-v2-2026-10-08.md`](results/SUMMARY-v2-2026-10-08.md), [`results/SUMMARY-2026-10-08.md`](results/SUMMARY-2026-10-08.md).

## 환경

- CPU/GPU: Intel Core Ultra 5 228V, Arc 130V iGPU (전용 VRAM 없음, 시스템 메모리 공유), 사용 가능 메모리 약 30 GB, swap은 zram
- OS: CachyOS (Linux 7.2, GNOME 데스크톱)
- 추론: llama.cpp v0.6.0 (d812350) Vulkan 빌드, 비교용 Ollama 0.40.1
- **측정 조건: 깨끗한 시스템이 아닙니다.** 데스크톱, 브라우저, 다른 로컬 서비스(작은 LLM 서버, NPU 서버 등)가 켜진 상태였고,
  아무것도 안 해도 약 6 GB가 이미 쓰이고 있었습니다. 백그라운드를 최소화하면 메모리 결과는 달라질 수 있습니다.

모델 출처: Qwen/Qwen3-30B-A3B-GGUF (공식), unsloth의 Qwen3.6-35B-A3B(-MTP)-GGUF, Gemma-4-26B-A4B, Qwen3.8-27B GGUF (unsloth dynamic quant).
모든 파일은 Hugging Face의 SHA-256과 대조했습니다.

## 측정 방법

### 1. 속도
- 한국어 프롬프트 6개, greedy, 400 토큰, thinking 끔, 매 실행 전 60°C 이하로 식힘
- MTP(multi-token prediction) 투기적 디코딩 켬/끔 비교. 스크립트: `scripts/run_v2_all.sh`, `scripts/mtp_v2.sh`, `scripts/ollama_v2.sh`

### 2. 한국어 품질 (20문항)
- 직접 만든 20개 프롬프트 (`scripts/prompts_quality_ko.jsonl`): 설명, 요약, 글쓰기, 말투 변환, 맞춤법, 번역, 코딩, 추론, 한국 문화, 지시 이행, 사실 확인(k17 환각 함정), 창작, 조언
- 답변을 A/B/C로 가린 블라인드 평가. 정확성 / 한국어 자연스러움 / 지시 준수 각 1-5점
- **서로 다른 회사의 심사위원 5개**: JEV, Cloudflare Clef, Codex, Claude Sonnet, Gemini Flash.
  답변 순서를 정방향/역방향 두 번 돌려서, 두 번 다 같은 답을 고른 심사위원만 투표에 넣었습니다 (`scripts/aggregate_judges.py`)
- 심사위원끼리 의견이 갈린 4문항(k02/k07/k08/k15)은 사람(저장소 주인)이 블라인드로 직접 채점 (`results/quality/owner_grades.json`)

### 3. KMMLU
- [HAERAE-HUB/KMMLU](https://huggingface.co/datasets/HAERAE-HUB/KMMLU) rev `d61b3f19`, 45과목 × 20문항 층화 샘플 = 900문항
  (`scripts/kmmlu_sample.py`, 과목별 고정 시드). 사용한 문항 ID: `results/kmmlu/sample-ids.txt`
- zero-shot, temperature 0, 정답 = 첫 토큰의 1-4 중 logprob 최댓값. 4개 모델 모두 900문항 전부 파싱됨
- **KMMLU는 CC-BY-ND-4.0이라 문제 원문은 이 저장소에 넣지 않았습니다.** 결과 파일에는 ID, 과목, 예측, 정답 여부만 있습니다
- 메모리 때문에 일부 실행은 `--n-cpu-moe`로 전문가(expert) 레이어 일부를 CPU에 두었습니다 (같은 가중치).
  Gemma-4-26B 마지막 44문항(13), Qwen3.6 전체(19), Qwen3-30B 전체(21). Qwen3-30B는 198번에서 중단 후 이어서 실행(ID 중복 없음 확인)

## 메모리에서 배운 것 (Vulkan + 통합 메모리)

- `-ngl 99`로 17 GB급 모델을 전부 GPU에 올리면 약 17.7 GB가 GPU 몫으로 고정되고, 이 부분은 swap으로 못 뺍니다.
  swap이 zram이라 "남은 swap"도 실제로는 여유가 아닙니다
- `--n-cpu-moe N`만으로는 CPU 쪽 전문가 가중치가 여전히 Vulkan host buffer(고정 메모리)에 들어갑니다.
  **`--n-cpu-moe N --no-host --no-repack -lm mmap`**을 같이 줘야 회수 가능한 파일 페이지가 됩니다
  (load-mode auto는 Vulkan에서 mmap을 건너뜀)
- 배터리가 바닥나면 upowerd가 강제로 절전에 들어가며, `systemd-inhibit`로도 막을 수 없습니다. 긴 측정은 충전기를 꽂고 하세요

## 참고 저장소와의 차이

같은 노트북 급의 [MatheusSchneiderr/lunar-lake-local-llm](https://github.com/MatheusSchneiderr/lunar-lake-local-llm)은
최종적으로 **Qwen3.6-35B-A3B IQ1_M (약 10 GB)**를 **SYCL** 백엔드로 운영하고, NPU 모델과 GPU 모델이 동시에 뜨지 않게 막았습니다.
이 저장소는 Q4 계열(약 17 GB)을 Vulkan으로, 다른 서비스와 함께 돌렸습니다. "같은 노트북에서 35B가 돈다"는 말은
양자화 크기와 함께 띄우는 것에 따라 결과가 크게 달라집니다.

## 한계

- 사람 평가자 1명, 품질 문항 20개뿐
- AI 심사위원 편향: Gemini가 같은 회사의 Gemma를 심사함, Qwen 제작사(Alibaba) 계열 심사위원은 없음
- KMMLU는 zero-shot, 900문항 샘플 (전체 데이터셋 아님)
- 측정 시점의 백그라운드 부하가 기록되어 있지 않은 부분이 있음
- 다음 할 일: 10 GB 안팎으로 작게 줄인 양자화(IQ2급)에서 한국어 품질이 얼마나 떨어지는지 측정

## 재현

스크립트는 저장소 루트 기준 상대 경로로 동작합니다. llama-server는 `127.0.0.1:18082`, 비교용 Ollama는 `127.0.0.1:11434`를 씁니다 (Ollama 모델 위치가 다르면 `OLLAMA_BLOBS` 지정).
JEV/Clef 심사는 각각 `JEV_API_KEY`, `CF_ACCOUNT_ID`/`CF_API_TOKEN` 환경변수가 필요합니다.

```
python scripts/kmmlu_sample.py          # KMMLU를 data/kmmlu-d61b3f19 에 받아둔 뒤
scripts/run_kmmlu_all.sh                # 모델 목록은 스크립트 하단 heredoc
python scripts/aggregate_judges.py --reveal
```

## 라이선스

코드와 결과는 MIT. KMMLU 데이터는 포함하지 않으며 원 라이선스(CC-BY-ND-4.0)를 따릅니다.

측정한 모델(가중치는 이 저장소에 없음): Gemma 4 12B / 26B-A4B (Google, Apache-2.0), Qwen3-30B-A3B · Qwen3.6-35B-A3B · Qwen3.8-27B (Alibaba Qwen, Apache-2.0).
결과 파일의 모델 답변과 AI 심사위원 출력은 각 모델·서비스로 생성한 것입니다. 언급된 모델·서비스 이름은 각 회사의 상표이며, 이 저장소는 어느 회사와도 관련이 없습니다.
