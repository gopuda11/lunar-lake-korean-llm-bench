| model                          |       size |     params | backend    | ngl |  fa |         lm |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --: | ---------: | --------------: | -------------------: |
| qwen35moe 35B.A3B IQ4_XS - 4.25 bpw |  16.95 GiB |    35.51 B | Vulkan     |  99 |   1 |       none |           pp512 |        203.49 ± 8.76 |
| qwen35moe 35B.A3B IQ4_XS - 4.25 bpw |  16.95 GiB |    35.51 B | Vulkan     |  99 |   1 |       none |           tg128 |         17.52 ± 3.53 |

build: d812350 (1)
