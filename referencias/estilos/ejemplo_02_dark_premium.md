# Estilo "Dark Premium" — aprendido de referencias/ejemplo_02.mp4

Valoración del usuario: le gustan las animaciones, tipografía, ritmo, transiciones, voz,
y el alto nivel de detalle y variedad de elementos gráficos. Usar como estilo por defecto
cuando pida "como el ejemplo" o un video de alta calidad.

## Métricas medidas
- 1080×1920, 30 fps, 47 s. Voz a **~170 palabras/min** (rápida pero clara). Audio −16 LUFS (yo masterizo a −14).
- 1 cambio visual grande cada ~4 s; micro-animaciones constantes entre medias (nunca hay un frame quieto).
- Estructura: gancho (0–7 s) → 4 pasos (~8 s c/u) → cierre/CTA con perfil (~8 s).

## Paleta
- Fondo casi negro cálido `#181818` / `#161616`, tarjetas `#21222B`–`#232323`.
- Acento único coral/naranja `#E07A5F` aprox. (botones, palabras clave, check, líneas).
- Blanco `#FFFFFF` para titulares; gris `#8A8A8A` para texto secundario/futuro.
- Toque de luz: **aurora/gradiente violeta-verde difuminado** en la esquina superior derecha, muy sutil (luz ambiental).
- Rejilla fina (grid) apenas visible sobre el fondo + viñeta oscura.

## Tipografía
- Titulares: **Anton** (condensada, mayúsculas), 2 líneas: línea 1 blanca, línea 2 en acento.
- Texto UI y subtítulos: **Poppins** (semibold).
- Código / prompts: monoespaciada (JetBrains Mono) con sintaxis coloreada (claves en acento).
- Kicker en píldora: "• PASO 01" (punto de acento + mayúsculas espaciadas, fondo gris oscuro redondeado).
- **Número gigante de contorno** ("01", "02"…) detrás del titular, outline gris muy tenue (decoración de profundidad).

## Sistema de layout
- Arriba: barra de progreso segmentada "PASO 1 DE 4" (4 segmentos, los completados en acento), centrada.
- Titular alineado a la izquierda, margen ~60 px.
- Centro: el "diagrama" de la escena (tarjetas, iconos, flujo).
- Subtítulos: **una frase corta centrada en ~y=1140**, Poppins, palabra activa con **fondo píldora coral** (karaoke),
  palabras ya dichas en blanco, futuras en gris; la píldora salta palabra a palabra.
- Tercio inferior libre (zona de UI de TikTok).

## Biblioteca de elementos (variedad = clave)
- Tarjetas con glassmorphism oscuro: esquinas 20–24 px, borde 1 px rgba blanco 6%, sombra suave.
- Iconos en "app tiles" redondeados con glow del color de la marca (Claude naranja, Remotion azul).
- **Conectores animados**: línea punteada curva que se dibuja entre dos nodos + check circular que aparece en medio.
- Editor de código con escritura carácter a carácter y cursor, luego flecha → reproductor MP4 con barra de progreso.
- Ventana "prompt.md" con traffic lights (● ● ●), líneas que se escriben y **checks ✓ que aparecen al final de cada línea**.
- Panel de "marca": swatches de color que aparecen en cascada, muestras de fuente (ANTON / Poppins), chips de estilo (Premium seleccionado).
- Diagrama radial: icono central (bombilla) con anillos de pulso + 3 nodos (Historia, Público, Objetivo) conectados con curvas.
- **Sellos** rotados con borde en acento ("100 % TUYO", "EN MINUTOS") con líneas de impacto alrededor (burst).
- Terminal de Claude Code: input, "[Pasted text +42 lines]", checklist de progreso y barra de render con %.
- Mockup de "Remotion Studio": preview + timeline con pistas (escenas, voz con forma de onda, SFX como puntos, subtítulos) y playhead.
- Tarjeta de perfil de TikTok con avatar, botón "Seguir" → "✓ Siguiendo" pulsado por un **cursor de mano animado**.
- Fila con candado que se abre (masterclass bloqueada → desbloqueada).

## Movimiento
- Titulares: escritura con cursor tipo máquina (gancho) o entrada por máscara/slide-up rápida con easing expo-out.
- Elementos entran con escala 0.9→1 + fade + leve blur, stagger 60–120 ms.
- **Transiciones entre pasos**: desenfoque de movimiento + desplazamiento lateral/zoom del bloque saliente (whip blur), el
  siguiente entra limpio; la píldora "PASO 0X" y el número de contorno cambian.
- Cámara: punch-in suave sobre el elemento que se nombra; en el cierre, zoom-out que revela el proyecto dentro de un mockup (meta).
- Cada sustantivo importante de la voz dispara algo en pantalla (sincronía voz→visual muy estricta).
- Nada estático: pulsos en iconos, glow que respira, cursores parpadeando.

## Sonido / voz
- Voz masculina natural, cercana, ritmo rápido, entonación de creador de contenido.
- SFX discretos en cada aparición (clicks, whooshes en transiciones, "pop" en sellos), música baja.

## Lo que haría mejor
- Subir loudness a −14 LUFS (está en −16).
- El tercio inferior queda vacío en muchas escenas: se puede usar para decoración no textual (luz, partículas) sin invadir la UI.
- Termina con ~1 s en negro: cerrar sobre el CTA en su lugar.

## Implementación
- Motor recomendado: HyperFrames (GSAP: blur/whip transitions, escritura de código, conectores SVG; bloques
  `caption-pill-karaoke`/`caption-highlight`, `code-typing`, `flowchart-vertical`, `tiktok-follow`, `lt-*`) o Remotion con
  widgets nuevos: progress-steps, code-editor, prompt-window, brand-panel, radial-diagram, terminal, studio-mockup, profile-card.
