"""Optional AI cleanup for chatbox text: spelling and fitting the 144-char limit.

Off by default. Needs your own API key for an OpenAI-compatible chat
completions endpoint (OpenAI itself, or any compatible self-hosted server) -
nothing is bundled or called without one. Processing runs on a background
thread and returns the original text immediately while it works, since an
LLM call can take a second or more and must never stall the chatbox tick.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
TIMEOUT = 15
CACHE_SECONDS = 300

SYSTEM_PROMPT = (
    "Fix spelling and grammar in the given text and shorten it to fit within "
    "{limit} characters if needed. Preserve the original meaning and tone. "
    "Reply with only the corrected text, nothing else - no quotes, no explanation."
)


@dataclass(frozen=True)
class IntelliChatConfig:
    enabled: bool = False
    api_key: str = ""
    api_base: str = DEFAULT_API_BASE
    model: str = DEFAULT_MODEL

    @property
    def configured(self) -> bool:
        return self.enabled and bool(self.api_key)


class IntelliChatService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[str, float]] = {}
        self._pending: set[str] = set()
        self._lock = threading.Lock()

    def process(self, text: str, config: IntelliChatConfig, *, limit: int) -> str:
        """Returns the best text available right now: cached AI output if
        ready, otherwise the original while a background request runs."""
        if not config.configured or not text.strip():
            return text

        with self._lock:
            cached = self._cache.get(text)
            if cached and time.monotonic() - cached[1] < CACHE_SECONDS:
                return cached[0]
            if text in self._pending:
                return text
            self._pending.add(text)

        thread = threading.Thread(target=self._fetch, args=(text, config, limit), daemon=True)
        thread.start()
        return text

    def _fetch(self, text: str, config: IntelliChatConfig, limit: int) -> None:
        result = _call_chat_completions(text, config, limit)
        with self._lock:
            self._pending.discard(text)
            if result:
                self._cache[text] = (result, time.monotonic())


def _call_chat_completions(text: str, config: IntelliChatConfig, limit: int) -> str | None:
    body = json.dumps(
        {
            "model": config.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.format(limit=limit)},
                {"role": "user", "content": text},
            ],
            "temperature": 0.3,
            "max_tokens": 120,
        }
    ).encode()

    request = urllib.request.Request(
        f"{config.api_base.rstrip('/')}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    choices = payload.get("choices") or []
    if not choices:
        return None
    content = (choices[0].get("message") or {}).get("content", "").strip()
    return content or None
