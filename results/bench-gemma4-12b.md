| model                          |       size |     params | backend    | ngl |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --: | --------------: | -------------------: |
| gemma4 ?B Q4_K - Medium        |   6.86 GiB |    11.91 B | Vulkan     |  99 |   1 |           pp512 |        102.68 ± 0.58 |
| gemma4 ?B Q4_K - Medium        |   6.86 GiB |    11.91 B | Vulkan     |  99 |   1 |           tg128 |         10.55 ± 0.08 |

build: d812350 (1)
