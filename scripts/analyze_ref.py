#!/usr/bin/env python3
"""
Analiza videos de referencia para aprender su estilo.
Uso: .venv/bin/python scripts/analyze_ref.py referencias/*.mp4
Por cada video crea referencias/_analisis/<nombre>/ con:
  - hojas de contacto (1 frame cada 0.5 s) para estudiar layout, tipografía y color
  - cortes de escena detectados (ritmo de edición)
  - paleta de colores dominante
  - transcripción palabra por palabra (velocidad de voz, estructura del guion)
  - loudness del audio
  - resumen.json con todo lo anterior
"""
import json, os, re, subprocess, sys
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("HF_HOME", str(ROOT / "models/hf"))


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def analyze(video: Path):
    out = video.parent / "_analisis" / video.stem
    out.mkdir(parents=True, exist_ok=True)
    meta = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_type",
                           "-of", "json", str(video)]).stdout)
    dur = float(meta["format"]["duration"])
    vs = next(s for s in meta["streams"] if s["codec_type"] == "video")

    # hojas de contacto: 24 frames por hoja, 1 cada 0.5 s
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", "fps=2,scale=240:-1,tile=8x3", str(out / "hoja_%02d.png")])

    # cortes de escena
    # eventos visuales: picos de cambio entre frames (sirve también para motion graphics sobre fondo fijo)
    g = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", "fps=10,scale=54:96,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(g, dtype=np.uint8).reshape(-1, 96 * 54).astype(float)
    diff = np.abs(np.diff(fr, axis=0)).mean(1)
    thr = diff.mean() + 1.5 * diff.std()
    cuts, last = [], -1.0
    for i in range(1, len(diff) - 1):
        t = (i + 1) / 10
        if diff[i] > thr and diff[i] >= diff[i - 1] and diff[i] >= diff[i + 1] and t - last >= 0.4:
            cuts.append(round(t, 1))
            last = t

    # paleta: k-means simple sobre frames muestreados
    palette = []
    try:
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", "fps=1,scale=64:-1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True).stdout
        px = np.frombuffer(p, dtype=np.uint8).reshape(-1, 3).astype(float)
        px = px[np.random.default_rng(0).choice(len(px), min(20000, len(px)), replace=False)]
        cent = px[np.random.default_rng(1).choice(len(px), 8, replace=False)]
        for _ in range(15):
            lab = ((px[:, None] - cent[None]) ** 2).sum(-1).argmin(1)
            cent = np.array([px[lab == k].mean(0) if np.any(lab == k) else cent[k] for k in range(8)])
        counts = np.bincount(lab, minlength=8)
        palette = [{"hex": "#%02X%02X%02X" % tuple(int(v) for v in cent[k]), "share": round(counts[k] / len(px), 3)}
                   for k in np.argsort(-counts)]
    except Exception as e:  # noqa: BLE001
        palette = [{"error": str(e)}]

    # audio: transcripción + loudness
    words, lufs = [], None
    wav = out / "audio.wav"
    if run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)]).returncode == 0:
        a, _ = sf.read(wav, dtype="float32")
        from faster_whisper import WhisperModel
        m = WhisperModel("small", device="cpu", compute_type="int8")
        segs, info = m.transcribe(a, word_timestamps=True)
        words = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for s in segs for w in s.words]
        (out / "transcripcion.txt").write_text(" ".join(w["w"] for w in words), encoding="utf-8")
        ld = run(["ffmpeg", "-nostats", "-i", str(video), "-af", "ebur128", "-f", "null", "-"]).stderr
        mm = re.findall(r"I:\s+(-?[\d.]+) LUFS", ld)
        lufs = float(mm[-1]) if mm else None
        wav.unlink()

    speech = (words[-1]["e"] - words[0]["s"]) if words else 0
    summary = {
        "archivo": video.name, "duracion_s": round(dur, 2), "resolucion": f'{vs["width"]}x{vs["height"]}', "fps": vs["r_frame_rate"],
        "eventos_visuales_s": cuts, "num_eventos": len(cuts), "segundos_entre_eventos": round(dur / (len(cuts) + 1), 2),
        "palabras": len(words), "palabras_por_minuto": round(len(words) / speech * 60) if speech else None,
        "loudness_lufs": lufs, "paleta": palette, "palabras_con_tiempo": words,
    }
    (out / "resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{video.name}: {dur:.1f}s, {len(cuts)} eventos visuales (uno cada {summary["segundos_entre_eventos"]}s), "
          f"{summary['palabras_por_minuto']} ppm, {lufs} LUFS -> {out}")


if __name__ == "__main__":
    files = [Path(f) for f in sys.argv[1:]] or sorted((ROOT / "referencias").glob("*.mp4"))
    for f in files:
        analyze(f)
