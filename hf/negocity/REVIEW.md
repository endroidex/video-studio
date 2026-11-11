# Negocity · promo 9:16 — nota de entrega

- **Archivo:** `out/negocity.mp4` · 1080×1920 · 30 fps · 43.7 s · H.264 + AAC · −14.0 LUFS, pico −1.1 dBFS.
- **Estructura:** s1 caos (0–8.3) → s2 marca + celular (8.3–14.3) → s3 lealtad (14.3–20.7) → s4 datos (20.7–25.2) → s5 equipo/contactos (25.2–30.8) → s6 conectado (30.8–35.7) → s7 cierre (35.7–43.7).
- **Reconstruir:** `tools/build.py` (escenas + index + subtítulos desde `src/`), `tools/audio.py` (mezcla), `npx hyperframes render`. Voz: `projects/negocity/voice2.py`.

## Decisiones
- Logo oficial usado como PNG sin tocar (fondo negro propio sobre secciones negras; ícono verde como ícono de app).
- Paleta estricta: verde #09672C, crema #FFFEFA, negro, dorado solo en el premio, azul solo en destellos/indicadores.
- QR real que abre https://negocity.com.mx.
- Música y efectos sintetizados por código (propios, sin licencias de terceros), 106.3 BPM, impactos en 8.69 s y 35.79 s.

## Medido vs. solo visto
- Medido: duración, loudness, pico, palabras de la voz (Whisper 100 % por segmento), `hyperframes check` sin errores.
- Visto en capturas: las 7 escenas, los 6 cortes, vista de 360 px.
- **Nadie lo escuchó:** acento/naturalidad de la voz, gusto de la música y nivel de los efectos.

## Pendiente / más débil
- Sin tomas reales de negocios (no hay material; todo es motion graphics).
- La interfaz es ilustrativa: negocity.com.mx no era accesible desde este entorno, no se usaron pantallas reales.
- Datos de ejemplo inventados (Café Lupita, $18,450, 68 %).
- Avisos de `check` conservados: "¿Y los $470?" dura 1.0 s (ritmo del caos); solapamiento del premio sobre los puntos (intencional).
- Con más tiempo: s6 (diagrama) más grande; tercio inferior con más textura.
