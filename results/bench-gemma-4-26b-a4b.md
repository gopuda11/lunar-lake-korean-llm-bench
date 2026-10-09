| model                          |       size |     params | backend    | ngl |  fa |         lm |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --: | ---------: | --------------: | -------------------: |
| gemma4 26B.A4B Q4_K - Medium   |  15.83 GiB |    25.23 B | Vulkan     |  99 |   1 |       none |           pp512 |       222.13 ± 12.37 |
| gemma4 26B.A4B Q4_K - Medium   |  15.83 GiB |    25.23 B | Vulkan     |  99 |   1 |       none |           tg128 |         21.03 ± 0.71 |

build: d812350 (1)
