from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class LlmConfig:
    enabled: bool
    endpoint: str
    model: str
    api_key: str
    timeout_seconds: float = 1.5


class LlmClient:
    def __init__(self, config: LlmConfig) -> None:
        self.config = config

    def complete(self, system: str, user: str) -> str | None:
        if not self.config.enabled:
            return None

        endpoint = self.config.endpoint.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
            return None

        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None
        return str(content).strip() or None
