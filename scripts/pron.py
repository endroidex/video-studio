"""Pronunciación: cómo se le ESCRIBE una palabra al motor de voz para que la diga bien.
En pantalla y en subtítulos siempre se usa la escritura original. Diccionario: pronunciations.json"""
import json, re
from pathlib import Path
_F = Path(__file__).resolve().parent.parent / "pronunciations.json"


def say(text):
    d = json.loads(_F.read_text()) if _F.exists() else {}
    for k in sorted(d, key=len, reverse=True):
        text = re.sub(rf"(?<![\\wáéíóúñ]){re.escape(k)}(?![\\wáéíóúñ])", d[k], text)
    return text
