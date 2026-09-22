"""Speaks chatbox text out loud, via whichever local TTS engine is present.

Tries piper (better quality, needs a downloaded voice model) then falls back
to espeak-ng (worse quality, present on most distros already). Pure speech
synthesis of text you already wrote - no generation, nothing sent anywhere.
"""

from __future__ import annotations

import shutil
import subprocess

ENGINES = ("piper", "espeak-ng", "espeak")


def available_engine() -> str | None:
    for engine in ENGINES:
        if shutil.which(engine):
            return engine
    return None


def speak(text: str, *, engine: str | None = None, voice: str | None = None) -> bool:
    """Fire-and-forget speech. Returns whether an engine was launched."""
    if not text.strip():
        return False

    engine = engine or available_engine()
    if engine is None:
        return False

    try:
        if engine == "piper" and voice and shutil.which("aplay"):
            piper = subprocess.Popen(
                ["piper", "--model", voice, "--output-raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            subprocess.Popen(
                ["aplay", "-q", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                stdin=piper.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if piper.stdin:
                piper.stdin.write(text.encode("utf-8"))
                piper.stdin.close()
        else:
            subprocess.Popen([engine, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False

    return True
