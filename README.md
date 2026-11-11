# Video Studio: videos con motion graphics creados desde cero

Pipeline local que convierte un **guion en JSON** en un video vertical 1080×1920 listo para publicar:

```
guion.json ─► voz (Piper TTS / ElevenLabs) ─► subtítulos palabra a palabra (Whisper)
          ─► animación sincronizada (Remotion + React) ─► SFX + música sintetizados
          ─► mezcla con ducking a −14 LUFS ─► MP4 H.264
```

## Herramientas

| Pieza | Herramienta | Para qué |
|---|---|---|
| Animación / motion graphics | **Remotion 4** (React → video) | Escenas, tipografía cinética, widgets, personaje, cámara |
| Voz | **Piper TTS** (local, voces es_MX / es_ES) · opcional **ElevenLabs** | Locución |
| Subtítulos y sincronía | **faster-whisper** (modelo `small`) | Tiempos palabra a palabra para subtítulos y para que cada elemento aparezca justo cuando se nombra |
| Diseño sonoro | `scripts/audio_lib.py` (numpy/scipy) | Whoosh, pop, tick, ding, thud, riser, tecleo, caja registradora y música (lofi/upbeat/dark/ambient) |
| Mezcla / master | ffmpeg + pyloudnorm | EQ y compresión de voz, ducking de música, −14 LUFS |
| Render | Remotion + Chromium + ffmpeg | MP4 H.264, CRF 18 |

## Uso

```bash
./make.sh demo            # genera out/demo.mp4
./make.sh demo --preview  # render rápido a mitad de resolución
npx remotion studio src/index.ts   # editor visual en el navegador
```

## Formato del guion (`projects/<id>/script.json`)

```jsonc
{
  "title": "...",
  "voice": "es_MX-claude-high",   // también: es_MX-ald-medium, es_ES-davefx-medium, es_ES-sharvard-medium
  "speed": 1.08,
  "music": "lofi",                 // lofi | upbeat | dark | ambient | none
  "theme": { "accent": "#E5483B", "bg": "#ECE8E1" },   // opcional
  "character": true,
  "scenes": [
    {
      "tag": "paso 1 · necesidades",                 // etiqueta mono arriba
      "voice": "El *cincuenta* por ciento va a ...",  // *palabra* = acento (serif cursiva, color)
      "headline": "LO *ESENCIAL*",
      "badge": 1,
      "widget": {
        "type": "checklist",
        "items": [{ "label": "Renta", "at": "renta" }],   // "at": aparece cuando la voz dice esa palabra
        "stamp": "AUTOMÁTICO", "stampAt": "automático"   // sello rojo opcional
      },
      "sfx": [{ "at": "renta", "name": "cash" }]           // SFX extra opcionales
    }
  ]
}
```

**Widgets:** `checklist`, `stat` (contador con anillo), `donut`, `bars`, `steps`, `typing`,
`phone` (notificaciones), `compare` (antes/después), `chat`, `icon`.
Si hace falta algo nuevo, se agrega un componente en `src/widgets/`.

## Voces — ElevenLabs (solo con orden explícita)

**Regla:** ElevenLabs se usa únicamente cuando el usuario pide explícitamente un video con ElevenLabs (ver `CLAUDE.md`).
Las llamadas de pago están bloqueadas salvo con `ELEVEN_APPROVED=1`. Pruebas y demos: voz local. Música: nunca ElevenLabs.

La clave de API vive en el entorno como *network secret* (host `api.elevenlabs.io`, cabecera `xi-api-key`);
el proxy la inyecta sola, el código nunca la ve. Fuera de este entorno: variable `ELEVENLABS_API_KEY`.

- `scripts/eleven.py` — cliente; `scripts/tts_eleven.py` — voz + **tiempos exactos por palabra** (endpoint `with-timestamps`, sin Whisper).
- `voices.json` — voces elegidas (alias → id). `_default` es la que se usa si el guion no dice otra.
  Mexicanas ya agregadas: `marto`, `antonio` (masculinas), `angelica`, `azucena` (femeninas).
- Modelo: `eleven_v4`. Ritmo natural, sin acelerar. Pronunciaciones en `pronunciations.json` (Negocity → "Négocity").
- Plan Starter: 40 000 caracteres/mes. Un guion de 45–60 s gasta ~600–700.

```bash
.venv/bin/python scripts/tts_eleven.py uso        # caracteres usados
.venv/bin/python scripts/tts_eleven.py voces      # voces de la cuenta
.venv/bin/python scripts/tts_eleven.py di marto "Hola" salida.wav
.venv/bin/python scripts/sfx_eleven.py <nombre> "<descripción en inglés>" 1.0   # efecto → assets/sfx (se genera una vez y se reutiliza)
```

En el guion: `"tts": "elevenlabs"` + `"voice": "marto"` y ejecutar con `ELEVEN_APPROVED=1`. Sin `"tts"`, el motor es `chatterbox` (local).

Proyectos HyperFrames (p. ej. Negocity): `projects/<id>/voice_eleven.py <voz>` genera `voice/final_*.wav` + `final.json`;
Luego `tools/build.py` → `tools/audio.py` → `npx hyperframes render`.

## HyperFrames (segundo motor de animación)

`hf/` contiene proyectos de [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP → MP4, de HeyGen, Apache 2.0).
Las skills están en `.claude/skills/` (hyperframes, hyperframes-cli, hyperframes-registry, media-use).

- ~450 bloques listos: transiciones con shaders, captions animados (karaoke, highlight, kinetic slam…), mockups de iPhone/chat/notificaciones, gráficas, mapas, 3D, texto manuscrito.
- Renderiza ~4× más rápido que Remotion en este entorno.
- Flujo: `npx hyperframes init hf/<id> --resolution=portrait --skip-skills` → `npx hyperframes add <bloque>` → `npx hyperframes check` → `npx hyperframes render`.
- La voz, subtítulos, SFX y mezcla salen del mismo `scripts/build.py` (`public/projects/<id>/mix.wav` + `timeline.json`).

**Cuándo usar cuál:** Remotion para el estilo de personaje + widgets propio (ya probado);
HyperFrames cuando el video pide efectos que ya existen en su catálogo (shaders, 3D, mockups realistas, captions de TikTok).

## Referencias de estilo

Pon videos de ejemplo en `referencias/` y ejecuta:

```bash
.venv/bin/python scripts/analyze_ref.py
```

Genera en `referencias/_analisis/<video>/`: hojas de contacto (2 frames/s), eventos visuales (ritmo),
paleta dominante, transcripción con tiempos, palabras por minuto y loudness.
Zonas seguras de 9:16 (TikTok/Reels): nada importante arriba de 168 px ni debajo de 1330 px.
