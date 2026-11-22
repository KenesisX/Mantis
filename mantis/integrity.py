"""Tamper-evidence for the save file — keep duels honest.

Every MANTIS starts at **level 0** and earns everything in play. To stop someone
hand-editing ``soul.json`` (via FileZilla, a text editor, whatever) to inflate
their level/kills/souls before a duel, the engine signs the save with an HMAC
keyed by a per-device secret. On load we re-check the signature:

* signature matches   -> ``verified = True``   (an honest, earned state)
* missing / mismatched -> ``verified = False``  (edited outside the game)

A duel shows the other unit's **VERIFIED** / **⚠ UNVERIFIED** badge, so a tampered
pet is visible to everyone it faces. This is a deterrent, not DRM: someone who
also forges the signature with the secret file is "using something crazy" — but
casual save-editing is caught, and unverified units are flagged in the arena.

The secret lives in ``<home>/.secret`` (0600), created once per install.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any, Dict, Tuple

SECRET_FILE = ".secret"
SIG_SUFFIX = ".sig"
# A build-wide pepper mixed into every device secret. Not a real secret (it ships
# in the source), but it means a bare `.secret` file alone isn't the whole key.
_PEPPER = b"mantis-firefox-psychic-unit/v1"


def _secret(home: str) -> bytes:
    p = os.path.join(home, SECRET_FILE)
    try:
        if os.path.exists(p):
            with open(p, "rb") as fh:
                raw = fh.read().strip()
            if raw:
                return raw
        raw = os.urandom(32).hex().encode()
        with open(p, "wb") as fh:
            fh.write(raw)
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass
        return raw
    except Exception:
        # last resort: a deterministic-but-weak key so signing never crashes
        return hashlib.sha256(home.encode()).hexdigest().encode()


def _key(home: str) -> bytes:
    return hmac.new(_PEPPER, _secret(home), hashlib.sha256).digest()


def sign_bytes(home: str, data: bytes) -> str:
    return hmac.new(_key(home), data, hashlib.sha256).hexdigest()


def canonical(obj: Dict[str, Any]) -> bytes:
    """Stable serialization so the signature is order-independent."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_state(home: str, state: Dict[str, Any]) -> str:
    return sign_bytes(home, canonical(state))


def verify_state(home: str, state: Dict[str, Any], sig: str) -> bool:
    if not sig:
        return False
    try:
        return hmac.compare_digest(sign_state(home, state), str(sig))
    except Exception:
        return False


def sig_path(save_path: str) -> str:
    return save_path + SIG_SUFFIX


def write_sig(home: str, save_path: str, state: Dict[str, Any]) -> None:
    try:
        with open(sig_path(save_path), "w", encoding="utf-8") as fh:
            fh.write(sign_state(home, state))
    except Exception:
        pass


def read_sig(save_path: str) -> str:
    try:
        with open(sig_path(save_path), "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except Exception:
        return ""
