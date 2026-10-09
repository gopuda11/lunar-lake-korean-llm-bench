import json, sys
label, n, t0, t1, f = sys.argv[1:6]
d = json.load(sys.stdin); t = d.get("timings", {})
dn = t.get("draft_n") or 0; da = t.get("draft_n_accepted") or 0
acc = da / dn * 100 if dn else 0
print(f"{label} q{n} gen={t.get('predicted_n')} tps={t.get('predicted_per_second', 0):.2f} accept={acc:.0f}% temp={t0}->{t1}C gpu_mhz={f}")
