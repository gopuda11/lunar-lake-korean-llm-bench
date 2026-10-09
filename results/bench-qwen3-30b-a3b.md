| model                          |       size |     params | backend    | ngl |  fa |         lm |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --: | ---------: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  99 |   1 |       none |           pp512 |       251.28 ± 11.02 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  99 |   1 |       none |           tg128 |         31.66 ± 0.94 |

build: d812350 (1)
