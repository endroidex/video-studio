#!/usr/bin/env python3
"""Resume `hyperframes check --json` (stdout limpio). Uso: python3 tools/chk.py"""
import json, subprocess, sys, collections
r = subprocess.run(["npx", "hyperframes", "check", "--json"], capture_output=True, text=True)
raw = r.stdout; i = raw.find("{")
d = json.loads(raw[i:])
print({k: v for k, v in d.items() if not isinstance(v, (list, dict))})
seen = collections.Counter(); out = []
def walk(o):
    if isinstance(o, dict):
        if ("message" in o) and ("rule" in o or "code" in o or "kind" in o):
            key = (o.get("severity") or o.get("level"), o.get("rule") or o.get("code") or o.get("kind"))
            seen[key] += 1
            if seen[key] <= int(sys.argv[1]) if len(sys.argv) > 1 else seen[key] <= 3:
                out.append(f' - {key[0]} {key[1]} | {str(o.get("message"))[:260]} | {o.get("file","")} {o.get("selector","")} t={o.get("time", o.get("atSec",""))} {str(o.get("fix") or o.get("hint") or "")[:160]}')
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(d)
print("\n".join(out)); print(dict(seen))
