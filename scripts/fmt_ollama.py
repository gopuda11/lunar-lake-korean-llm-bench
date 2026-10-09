import json, sys
path, n, t0, t1 = sys.argv[1:5]
d = json.load(open(path))
e = d["eval_count"]
print(f"ollama-g12 q{n} gen={e} tps={e / d['eval_duration'] * 1e9:.2f} accept=0% temp={t0}->{t1}C gpu_mhz=0")
