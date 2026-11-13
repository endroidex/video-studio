#!/usr/bin/env python3
"""
Ensambla el proyecto HyperFrames de Negocity a partir de:
  - src/shared.css            sistema de diseño (se inyecta en cada escena)
  - src/scenes/<id>.html      escenas (usan /*@CSS@*/, /*@T@*/ y {{icon:nombre}})
  - ../../projects/negocity/voice/lines.json   tiempos palabra por palabra de la voz
Escribe: compositions/*.html, index.html, timing.json
Uso: ../../.venv/bin/python tools/build.py
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
VOICE = HERE.parents[1] / "projects/negocity-lealtad/voice"
FPS = 30

# ── plan de montaje: (segmento de voz, pausa después en s). El video arranca con LEAD de imagen sola.
LEAD = 0.45
PLAN = [("0", 0.35), ("1", 0.35), ("2", 0.30), ("3", 0.30), ("4", 0.55), ("5", 0.30), ("6", 2.30)]
# ── escenas: id, primer segmento, último segmento
SCENES = [("s1-carton", "0", "0"), ("s2-revela", "1", "1"), ("s3-cartel", "2", "2"), ("s4-sello", "3", "3"),
          ("s5-premio", "4", "4"), ("s6-cierre", "5", "6")]

ICONS = {
    "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.600-7 10-7 10z"/>',
    "star": '<path d="M12 3.500l2.600 5.400 5.900.800-4.300 4.100 1.050 5.850L12 16.900l-5.250 2.750 1.050-5.850-4.300-4.100 5.900-.800z"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "users": '<circle cx="9" cy="8" r="3.500"/><path d="M2.500 20c.500-3.600 3.100-5.500 6.500-5.500s6 1.900 6.500 5.500"/><circle cx="17.500" cy="9" r="2.500"/><path d="M17.500 14.500c2.300.200 3.700 1.600 4 4"/>',
    "book": '<path d="M5 4h12a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2z"/><path d="M5 18a2 2 0 0 1 2-2h12"/><circle cx="12" cy="9" r="2"/><path d="M9 13.500c.500-1.200 1.600-1.800 3-1.800s2.500.600 3 1.800"/>',
    "receipt": '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
    "grid": '<rect x="4" y="4" width="6.500" height="6.500" rx="1.500"/><rect x="13.500" y="4" width="6.500" height="6.500" rx="1.500"/><rect x="4" y="13.500" width="6.500" height="6.500" rx="1.500"/><rect x="13.500" y="13.500" width="6.500" height="6.500" rx="1.500"/>',
    "gift": '<rect x="4" y="10" width="16" height="10" rx="2"/><path d="M3 7h18v3H3zM12 7v13"/><path d="M12 7c-1.500-3.500-5.500-3.500-5 0M12 7c1.500-3.500 5.500-3.500 5 0"/>',
    "check": '<path d="M5 12.500l4.500 4.500L19 7.500"/>',
    "phone": '<path d="M6 3h3l1.500 5-2 1.500a12 12 0 0 0 6 6l1.500-2 5 1.500v3a2 2 0 0 1-2 2A16 16 0 0 1 4 5a2 2 0 0 1 2-2z"/>',
    "chat": '<path d="M4 5h16v11H10l-5 4v-4H4z"/>',
    "search": '<circle cx="11" cy="11" r="6.500"/><path d="M16 16l5 5"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "cup": '<path d="M5 9h12v5a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5z"/><path d="M17 10h1.500a2.500 2.500 0 0 1 0 5H17M8 3v2.500M12 3v2.500"/>',
    "qr": '<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><path d="M14 14h2v2M20 14v6h-3M14 19v1"/>',
    "user": '<circle cx="12" cy="8.500" r="4"/><path d="M4 20.500c.800-4 4-6 8-6s7.200 2 8 6"/>',
    "refresh": '<path d="M20 12a8 8 0 1 1-2.600-5.900"/><path d="M20 4v5h-5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "clock": '<circle cx="12" cy="12" r="8.500"/><path d="M12 7v5l3.500 2"/>',
    "db": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.700 3.100 3 7 3s7-1.300 7-3V6M5 12v6c0 1.700 3.100 3 7 3s7-1.300 7-3v-6"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 3v2.500M12 18.500V21M3 12h2.500M18.500 12H21M5.600 5.600l1.800 1.800M16.600 16.600l1.800 1.800M5.600 18.400l1.800-1.800M16.600 7.400l1.800-1.800"/>',
    "bell": '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "cart": '<path d="M3 4h2.500l2.200 10h9.800l2-7H7"/><circle cx="9" cy="19" r="1.600"/><circle cx="17" cy="19" r="1.600"/>',
    "scissors": '<circle cx="6" cy="7" r="2.600"/><circle cx="6" cy="17" r="2.600"/><path d="M8.200 8.600L20 18M8.200 15.400L20 6"/>',
    "taco": '<path d="M2.500 17a9.500 9.500 0 0 1 19 0z"/><path d="M6.500 13.500l1.500-1M10.500 11.500l1.500-1M14.500 12.500l1.500-1"/>',
    "spark": '<path stroke="none" fill="currentColor" d="M12 1c.900 6.200 4.800 10.100 11 11-6.200.900-10.100 4.800-11 11-.900-6.200-4.800-10.100-11-11 6.200-.900 10.100-4.800 11-11z"/>',
}


def icon(name, extra=""):
    return f'<svg class="ico" viewBox="0 0 24 24" {extra}>{ICONS[name]}</svg>'


def load_lines():
    return json.loads((VOICE / "final.json").read_text())


def timing():
    segs = load_lines()
    t, out = LEAD, {}
    for key, gap in PLAN:
        s = segs[key]
        out[key] = {"s": round(t, 3), "e": round(t + s["dur"], 3), "text": s["text"],
                    "w": [{"t": w["text"], "s": round(t + w["start"], 3), "e": round(t + w["end"], 3)} for w in s["words"]]}
        t += s["dur"] + gap
    total = round(t * FPS) / FPS
    scenes = []
    for i, (sid, a, b) in enumerate(SCENES):
        start = 0.0 if i == 0 else scenes[-1]["end"]
        nxt = SCENES[i + 1][1] if i + 1 < len(SCENES) else None
        # la escena termina 0.12 s antes de la primera palabra de la siguiente (el cambio cae en la pausa)
        end = total if nxt is None else out[nxt]["s"] - 0.12
        scenes.append({"id": sid, "start": round(round(start * FPS) / FPS, 4), "end": round(round(end * FPS) / FPS, 4), "segs": [k for k, _ in PLAN if PLAN_INDEX[a] <= PLAN_INDEX[k] <= PLAN_INDEX[b]]})
    return {"total": total, "segs": out, "scenes": scenes, "fps": FPS}


PLAN_INDEX = {k: i for i, (k, _) in enumerate(PLAN)}


def caption_groups(T):
    groups = []
    for key, _ in PLAN:
        cur = []
        ws = T["segs"][key]["w"]
        if key == "6":   # la dirección web se muestra escrita, no deletreada
            ws = ws[:3] + [{"t": "negocity.com.mx", "s": ws[3]["s"], "e": ws[-1]["e"]}]
        for i, w in enumerate(ws):
            prev = ws[i - 1] if i else None
            if cur and (len(cur) >= 4 or w["s"] - prev["e"] >= 0.2 or re.search(r"[.!?…:,]$", prev["t"]) and len(cur) >= 2):
                groups.append(cur); cur = []
            cur.append(w)
        if cur:
            groups.append(cur)
    # no dejar una palabra sola si se puede unir al grupo anterior del mismo segmento
    return groups


def build_captions(T):
    groups = caption_groups(T)
    html, js = [], []
    for gi, g in enumerate(groups):
        start = max(0.1, g[0]["s"] - 0.10)
        end = g[-1]["e"] + 0.22
        if gi + 1 < len(groups):
            end = min(end, groups[gi + 1][0]["s"] - 0.10)
        words = "".join(f'<span class="cw" id="cw-{gi}-{wi}"><span class="cwb" id="cwb-{gi}-{wi}"></span><span class="cwt">{w["t"]}</span></span>' for wi, w in enumerate(g))
        html.append(f'      <div class="cg" id="cg-{gi}" style="opacity:0"><div class="cplate">{words}</div></div>')
        js.append(f'  G({gi}, {start:.3f}, {end:.3f}, {json.dumps([[round(w["s"],3), round(w["e"],3)] for w in g])});')
    tpl = (HERE / "src/captions.html").read_text()
    return tpl.replace("<!--@GROUPS@-->", "\n".join(html)).replace("/*@GROUPS@*/", "\n".join(js))


def main():
    T = timing()
    (HERE / "timing.json").write_text(json.dumps(T, ensure_ascii=False, indent=1))
    css = (HERE / "src/shared.css").read_text()
    qr = json.loads((HERE / "assets/qr-path.txt").read_text())
    comp = HERE / "compositions"
    comp.mkdir(exist_ok=True)
    hosts = []
    for z, sc in enumerate(T["scenes"], start=1):
        src = HERE / "src/scenes" / f'{sc["id"]}.html'
        dur = round(sc["end"] - sc["start"], 4)
        if not src.exists():
            continue
        h = src.read_text()
        helpers = (HERE / "src/helpers.js").read_text()
        helpers = ("      window.__QR_D = %s; const ICON_CHECK = %s, ICON_GIFT = %s;\n" % (json.dumps(qr["d"]), json.dumps(icon("check")), json.dumps(icon("gift")))) + helpers
        tjs = "const S0=%s, DUR=%s, SEG=%s, SEED=%d;\n" % (sc["start"], dur, json.dumps({k: T["segs"][k] for k in sc["segs"]}, ensure_ascii=False), sum(map(ord, sc["id"]))) + helpers
        h = h.replace("/*@CSS@*/", css).replace("/*@T@*/", tjs).replace("@DUR@", str(dur))
        h = h.replace("{{qr:d}}", qr["d"]).replace("{{qr:n}}", str(qr["n"]))
        h = re.sub(r"\{\{icon:([a-z]+)\}\}", lambda m: icon(m.group(1)), h)
        (comp / f'{sc["id"]}.html').write_text(h)
        hosts.append(f'      <div id="{sc["id"]}" data-composition-id="{sc["id"]}" data-composition-src="compositions/{sc["id"]}.html" data-start="{sc["start"]}" data-duration="{dur}" '
                     f'data-track-index="{z}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:{z}"></div>')
    total = T["total"]
    if (HERE / "src/captions.html").exists():
        (comp / "captions.html").write_text(build_captions(T).replace("/*@CSS@*/", css).replace("@DUR@", str(total)))
        hosts.append(f'      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{total}" '
                     f'data-track-index="20" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:20"></div>')
    audio = ""
    if (HERE / "assets/audio/mix.wav").exists():
        audio = f'      <audio id="mix" class="clip" src="assets/audio/mix.wav" data-start="0" data-duration="{total}" data-track-index="30" data-volume="1"></audio>'
    index = f'''<!doctype html>
<html lang="es" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Negocity · Haz que tus clientes vuelvan</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; }}
      #root-ground {{ position: absolute; inset: 0; background: #000; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
      <div id="root-ground"></div>
{chr(10).join(hosts)}
{audio}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
'''
    (HERE / "index.html").write_text(index)
    print(f"total {total:.2f}s ·", " · ".join(f'{s["id"]} {s["start"]:.2f}-{s["end"]:.2f}' for s in T["scenes"]))


if __name__ == "__main__":
    main()
