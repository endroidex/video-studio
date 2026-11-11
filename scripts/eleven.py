#!/usr/bin/env python3
"""Cliente mínimo de ElevenLabs. La clave la inyecta el proxy del entorno (cabecera xi-api-key);
fuera de este entorno se toma de la variable ELEVENLABS_API_KEY."""
import json, os, urllib.request, urllib.error
BASE = "https://api.elevenlabs.io"


PAID = ("/v1/text-to-speech", "/v1/sound-generation", "/v1/music", "/v1/speech-to-speech", "/v1/text-to-dialogue", "/v1/voices/add")


def call(path, body=None, method=None, raw=False, timeout=180):
    # REGLA DEL USUARIO: ElevenLabs solo se usa cuando pide explícitamente un video con ElevenLabs.
    # Nada de pruebas ni demos. Las llamadas que gastan créditos exigen ELEVEN_APPROVED=1 en ese comando.
    if path.startswith(PAID) and os.environ.get("ELEVEN_APPROVED") != "1":
        raise RuntimeError("ElevenLabs bloqueado: esta llamada gasta créditos. Solo se permite cuando el usuario pide "
                           "explícitamente un video con ElevenLabs; en ese caso ejecuta el comando con ELEVEN_APPROVED=1.")
    if path.startswith("/v1/music"):
        raise RuntimeError("La música nunca se genera con ElevenLabs (instrucción del usuario).")
    headers = {"Content-Type": "application/json"}
    if os.environ.get("ELEVENLABS_API_KEY"):
        headers["xi-api-key"] = os.environ["ELEVENLABS_API_KEY"]
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method or ("POST" if body is not None else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            return data if raw else json.loads(data)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ElevenLabs {e.code} en {path}: {e.read().decode(errors='replace')[:500]}") from None


if __name__ == "__main__":
    s = call("/v1/user/subscription")
    print({k: s.get(k) for k in ["tier", "status", "character_count", "character_limit", "voice_limit", "can_use_instant_voice_cloning"]})
