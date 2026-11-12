# Video Studio — reglas del dueño (leer antes de trabajar)

## ElevenLabs: SOLO con orden explícita
- Usar ElevenLabs **únicamente** cuando el usuario pida explícitamente crear un video con ElevenLabs.
- **Nunca** para pruebas, demos, muestras ni comparaciones: gasta sus créditos (plan Starter, 40 000 caracteres/mes).
- Las llamadas de pago están bloqueadas en `scripts/eleven.py`; se habilitan con `ELEVEN_APPROVED=1` solo en el comando
  del video pedido. Consultas gratuitas (uso, lista de voces) sí se permiten.
- **Música: nunca con ElevenLabs.** Se genera con `scripts/audio_lib.py` / `tools/audio.py`.
- Para pruebas y borradores: voz local (`chatterbox` por defecto, `kokoro`, `piper`).

## Voz
- Voz elegida para ElevenLabs: `marto` (`voices.json` → `_default`). **Decisión final del usuario:** probó `victor`
  (más grave) y prefirió volver a `marto`. No cambiar de voz sin que lo pida.
- Ritmo: **un poco más rápido que el natural** → tempo 1.10 con rubberband (el modelo `eleven_v4` ignora `speed`).
  El natural le pareció lento. Si el video dura más de lo pedido, no importa.
- Negocity: las tomas de `marto` a ritmo natural ya existen en el commit `17a86c8` (`projects/negocity/voice/`);
  se pueden recuperar con `git show` y acelerar a 1.10 **sin gastar créditos**. El proyecto quedó montado con `victor`.
- Pronunciación: `pronunciations.json` (p. ej. "Negocity" se dice **Négocity**, acento en "Ne"; en pantalla siempre "Negocity").
- Para elegir voces sin gastar créditos: descargar las muestras gratuitas (`preview_url`) y medir el tono.

## Flujo
- Estilo de referencia: `referencias/estilos/ejemplo_02_dark_premium.md`. Motores: HyperFrames (`hf/`) y Remotion (`src/`).
- No generar videos ni demos sin que el usuario lo pida.
- Detalles técnicos: `README.md`. Instalación en una sesión nueva: `bash setup.sh`.
