"""Security posture score — rolls the defensive spell findings into one grade.

Each defensive ward spell records its latest finding into ``pet.posture``; this
module turns those findings into per-component scores (0-100), an overall score,
and a letter grade. Components never cast yet are "unknown" and don't count
against the grade.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _tls_score(d: Dict[str, Any]) -> Optional[int]:
    days = d.get("days_left")
    if days is None:
        return None
    if days < 0:
        return 0
    if days < 14:
        return 40
    if days < 30:
        return 70
    return 100


def _firewall_score(d: Dict[str, Any]) -> Optional[int]:
    active = d.get("active")
    exposed = int(d.get("exposed", 0) or 0)
    if active is None and "exposed" not in d:
        return None
    base = 100 if active else (50 if active is False else 80)
    return max(0, base - 15 * exposed)


def _dnssec_score(d: Dict[str, Any]) -> Optional[int]:
    signed = d.get("signed")
    if signed is None:
        return None
    return 100 if signed else 40


def _headers_score(d: Dict[str, Any]) -> Optional[int]:
    total = int(d.get("total", 0) or 0)
    if not total:
        return None
    return int(round(100 * int(d.get("present", 0)) / total))


_COMPONENTS = [
    ("tls", "TLS cert", _tls_score, "astral_seal"),
    ("firewall", "Firewall", _firewall_score, "aegis_ward"),
    ("dnssec", "DNSSEC", _dnssec_score, "ward_of_truth"),
    ("headers", "HTTP headers", _headers_score, "veil_of_headers"),
]


def grade_for(score: Optional[float]) -> str:
    if score is None:
        return "?"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def compute(posture: Dict[str, Any]) -> Dict[str, Any]:
    posture = posture or {}
    components: List[Dict[str, Any]] = []
    known: List[int] = []
    for key, label, fn, spell in _COMPONENTS:
        data = posture.get(key) or {}
        score = fn(data) if data else None
        if score is not None:
            known.append(score)
        components.append({
            "key": key, "label": label, "spell": spell,
            "score": score, "grade": grade_for(score),
            "note": _note(key, data) if data else "not cast",
        })
    overall = round(sum(known) / len(known)) if known else None
    return {
        "score": overall,
        "grade": grade_for(overall),
        "known": len(known),
        "total": len(_COMPONENTS),
        "components": components,
    }


def _note(key: str, d: Dict[str, Any]) -> str:
    if key == "tls":
        return f"{d.get('host','?')}: {d.get('days_left','?')}d left"
    if key == "firewall":
        fw = "on" if d.get("active") else ("off" if d.get("active") is False else "?")
        return f"fw {fw}, {int(d.get('exposed',0))} exposed"
    if key == "dnssec":
        return f"{d.get('domain','?')}: {'signed' if d.get('signed') else 'unsigned'}"
    if key == "headers":
        return f"{d.get('present',0)}/{d.get('total',0)} headers"
    return ""
