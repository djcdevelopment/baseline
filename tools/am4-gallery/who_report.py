"""Summarize gallery access from Caddy's JSON access log (read on stdin).

Counts page views (requests for "/" and the index.json fetch), ignoring the
thousands of thumb/img asset hits. Usage: who_report.py [recent|summary]
"""
import sys, json, datetime
from collections import defaultdict

mode = sys.argv[1] if len(sys.argv) > 1 else "recent"


def browser(ua):
    ua = ua or ""
    plat = "Mobile" if any(x in ua for x in ("Android", "iPhone", "iPad", "Mobile")) else "Desktop"
    for tag, name in (("Edg", "Edge"), ("OPR", "Opera"), ("Chrome", "Chrome"),
                      ("Firefox", "Firefox"), ("Safari", "Safari")):
        if tag in ua:
            return f"{name} / {plat}"
    return f"other / {plat}"


views = []   # successful page opens (GET / -> 200)
fails = 0    # 401s on / that never carried a valid user (wrong pw / bare challenge)
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        e = json.loads(line)
    except ValueError:
        continue
    req = e.get("request", {})
    if req.get("uri", "") != "/":
        continue  # the page open; ignore assets and the index.json fetch
    status = e.get("status", 0)
    if status == 401:
        fails += 1
        continue
    if status != 200:
        continue
    ts = datetime.datetime.fromtimestamp(e.get("ts", 0)).strftime("%Y-%m-%d %H:%M:%S")
    user = e.get("user_id") or "-"
    hdr = req.get("headers", {}) or {}
    ua = (hdr.get("User-Agent") or [""])[0]
    ip = req.get("client_ip") or req.get("remote_ip", "")
    views.append((ts, user, ip, browser(ua)))

if mode == "summary":
    agg = defaultdict(lambda: {"n": 0, "first": None, "last": None, "ips": set(), "br": set()})
    for ts, user, ip, br in views:
        a = agg[user]; a["n"] += 1; a["ips"].add(ip); a["br"].add(br)
        a["first"] = a["first"] or ts; a["last"] = ts
    if not agg:
        print("no page views logged yet"); sys.exit()
    print(f"{'user':14}{'visits':>7}  {'first seen':19}  {'last seen':19}  browser(s) | ip(s)")
    for u, a in sorted(agg.items()):
        print(f"{u:14}{a['n']:7}  {a['first']:19}  {a['last']:19}  "
              f"{', '.join(sorted(a['br']))} | {', '.join(sorted(a['ips']))}")
    print(f"\n(failed / challenge 401s on the page: {fails})")
else:
    if not views:
        print("no page views logged yet"); sys.exit()
    print(f"{'when':19}  {'user':12} {'ip':39} browser")
    for ts, user, ip, br in views[-60:]:
        print(f"{ts}  {user:12} {ip:39} {br}")
    print(f"\n(failed / challenge 401s on the page: {fails})")
