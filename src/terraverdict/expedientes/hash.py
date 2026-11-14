from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np


def _canon(o: Any) -> Any:
    if isinstance(o, np.ndarray):
        return [_canon(v) for v in o.tolist()]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, dict):
        return {str(k): _canon(v) for k, v in sorted(o.items(), key=lambda kv: str(kv[0]))}
    if isinstance(o, (list, tuple)):
        return [_canon(v) for v in o]
    return o


def sha256_json(o: Any) -> str:
    """Hash estable: claves ordenadas, sin espacios, floats tal cual."""
    return hashlib.sha256(
        json.dumps(_canon(o), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
