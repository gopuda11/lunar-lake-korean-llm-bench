import re, sys, statistics as st
rows = {}
swap = {}
for line in open(sys.argv[1], encoding="utf-8"):
    m = re.match(r"(\S+) q(\d) gen=(\d+) tps=([\d.]+) accept=(\d+)% temp=(\d+)->(\d+)C gpu_mhz=(\d+)", line)
    if m:
        r = rows.setdefault(m[1], {"tps": [], "acc": [], "tmax": 0, "mhz": []})
        r["tps"].append(float(m[4])); r["acc"].append(int(m[5]))
        r["tmax"] = max(r["tmax"], int(m[7])); r["mhz"].append(int(m[8]))
    m = re.match(r"(\S+) swapin_MB=(\d+)", line)
    if m: swap[m[1]] = int(m[2])
print("| run | mean tok/s | min–max | MTP accept (mean) | max temp | mean GPU MHz | swap-in MB |")
print("|---|---|---|---|---|---|---|")
for k, r in rows.items():
    acc = f"{st.mean(r['acc']):.0f}%" if any(r["acc"]) else "–"
    print(f"| {k} | {st.mean(r['tps']):.2f} | {min(r['tps']):.1f}–{max(r['tps']):.1f} | {acc} | {r['tmax']}°C | {st.mean(r['mhz']):.0f} | {swap.get(k,'?')} |")
