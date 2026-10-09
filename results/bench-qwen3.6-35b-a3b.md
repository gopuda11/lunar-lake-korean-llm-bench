| model                          |       size |     params | backend    | ngl |  fa |         lm |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --: | ---------: | --------------: | -------------------: |
| qwen35moe 35B.A3B Q4_K - Medium |  21.10 GiB |    35.51 B | Vulkan     |  99 |   1 |       none |           pp512 |       248.64 ± 27.34 |
| qwen35moe 35B.A3B Q4_K - Medium |  21.10 GiB |    35.51 B | Vulkan     |  99 |   1 |       none |           tg128 |         21.85 ± 2.16 |

build: d812350 (1)
