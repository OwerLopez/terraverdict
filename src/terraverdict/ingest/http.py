"""Sesión HTTP con reintentos. 'ok' SOLO si 2xx/3xx (corrige el hallazgo 9)."""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def sesion(reintentos: int = 4) -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "terraverdict/0.1"
    r = Retry(total=reintentos, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504),
              allowed_methods=("GET", "POST"), respect_retry_after_header=True)
    s.mount("https://", HTTPAdapter(max_retries=r))
    return s


def estado_ok(s: requests.Session, url: str, timeout: int = 60) -> dict:
    try:
        c = s.get(url, timeout=timeout, allow_redirects=True).status_code
        return {"ok": 200 <= c < 400, "http": c}
    except requests.RequestException as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
