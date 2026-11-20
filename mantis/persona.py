"""Persona & personalization — MANTIS reads his keeper like an open book.

Stores a profile of YOU (name, experience, interests) and of HIM (personality
trait sliders + style), then flavours everything he says: he addresses you by
name, nods to the subjects you gravitate toward, and shifts his tone to the
darkness / warmth / menace / mysticism you dialed in. As you play, he also
*infers* your interests from which spells you reach for — and tells you so.

Profile lives in ``<home>/persona.json`` (separate from config.toml).
"""

from __future__ import annotations

import json
import os
import random
from typing import Any, Dict, List, Optional

PERSONA_FILE = "persona.json"

# interest key -> (label, evocative noun MANTIS uses when referencing it)
INTERESTS: Dict[str, Dict[str, str]] = {
    "wifi":       {"label": "Wi-Fi & wireless", "noun": "the airwaves"},
    "rf":         {"label": "RF / radio / SDR", "noun": "the hidden frequencies"},
    "web":        {"label": "web security", "noun": "the web's tangled threads"},
    "crypto":     {"label": "cryptography", "noun": "the secret ciphers"},
    "networking": {"label": "networking", "noun": "the flowing packets"},
    "blue_team":  {"label": "defense / blue team", "noun": "the guardian's art"},
    "red_team":   {"label": "offense / red team (ethical)", "noun": "the attacker's mind"},
    "privacy":    {"label": "privacy & OPSEC", "noun": "the art of the unseen"},
    "hardware":   {"label": "hardware & IoT", "noun": "the silicon's whispers"},
    "osint":      {"label": "OSINT", "noun": "the open secrets of the world"},
    "forensics":  {"label": "forensics & IR", "noun": "the ghosts in the logs"},
    "cloud":      {"label": "cloud security", "noun": "the distant machines"},
}

TRAITS = ["darkness", "warmth", "talkativeness", "menace", "humor", "mysticism"]

TRAIT_PRESETS: Dict[str, Dict[str, int]] = {
    "mystic":    {"darkness": 45, "warmth": 55, "talkativeness": 70, "menace": 35, "humor": 35, "mysticism": 90},
    "menacing":  {"darkness": 80, "warmth": 15, "talkativeness": 55, "menace": 90, "humor": 20, "mysticism": 70},
    "warm":      {"darkness": 20, "warmth": 90, "talkativeness": 75, "menace": 10, "humor": 60, "mysticism": 55},
    "sardonic":  {"darkness": 55, "warmth": 40, "talkativeness": 65, "menace": 50, "humor": 90, "mysticism": 50},
    "balanced":  {"darkness": 45, "warmth": 50, "talkativeness": 55, "menace": 45, "humor": 45, "mysticism": 65},
}

DEFAULT_PROFILE: Dict[str, Any] = {
    "keeper": "keeper",
    "pronouns": "they",
    "experience": "beginner",          # beginner | intermediate | pro
    "interests": [],
    "style": "poetic",                 # poetic | plain | clinical
    "mantis_name": "Mantis",
    "traits": dict(TRAIT_PRESETS["balanced"]),
    "configured": False,
}


# --------------------------------------------------------------------------- #
# load / save
# --------------------------------------------------------------------------- #
def path(home: str) -> str:
    return os.path.join(home, PERSONA_FILE)


def load(home: str) -> Dict[str, Any]:
    prof = json.loads(json.dumps(DEFAULT_PROFILE))  # deep copy
    try:
        with open(path(home), "r", encoding="utf-8") as fh:
            saved = json.load(fh)
        if isinstance(saved, dict):
            prof.update({k: v for k, v in saved.items() if k != "traits"})
            if isinstance(saved.get("traits"), dict):
                prof["traits"].update({k: int(v) for k, v in saved["traits"].items()
                                       if k in TRAITS})
    except Exception:
        pass
    return prof


def save(home: str, profile: Dict[str, Any]) -> str:
    os.makedirs(home, exist_ok=True)
    p = path(home)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2)
    os.replace(tmp, p)
    return p


def _t(profile: Dict[str, Any], name: str) -> int:
    return int((profile.get("traits") or {}).get(name, 50))


# --------------------------------------------------------------------------- #
# spell -> interest mapping (for inferring affinities)
# --------------------------------------------------------------------------- #
SPELL_INTEREST: Dict[str, str] = {
    "mind_reading": "wifi", "clairvoyance": "networking", "telepathy": "networking",
    "the_veil": "blue_team", "astral_projection": "networking", "hydroquartz": "networking",
    "psychokinesis": "hardware", "soul_scream": "crypto",
    "rtlsdr_attune": "rf", "subghz_listen": "rf", "lora_whisper": "rf", "adsb_sky": "rf",
    "astral_seal": "crypto", "aegis_ward": "blue_team", "ward_of_truth": "networking",
    "veil_of_headers": "web",
}


def spell_interest(spell_id: str) -> Optional[str]:
    return SPELL_INTEREST.get(spell_id)


def top_affinity(affinities: Dict[str, int]) -> Optional[str]:
    if not affinities:
        return None
    return max(affinities.items(), key=lambda kv: kv[1])[0]


# --------------------------------------------------------------------------- #
# phrase flavouring
# --------------------------------------------------------------------------- #
def _inject_name(phrase: str, name: str) -> str:
    if "{keeper}" in phrase:
        return phrase.replace("{keeper}", name)
    # insert the name before terminal punctuation, sometimes
    for end in ("...", ".", "!", "?"):
        if phrase.endswith(end):
            return phrase[: -len(end)] + f", {name}" + end
    return phrase + f", {name}."


def flavor(base: str, mood: str, profile: Dict[str, Any],
           affinities: Dict[str, int]) -> str:
    """Personalise a mood phrase with the keeper's name + interests + tone."""
    name = (profile.get("keeper") or "").strip() or "little keeper"
    talk = _t(profile, "talkativeness")
    warmth = _t(profile, "warmth")
    menace = _t(profile, "menace")
    myst = _t(profile, "mysticism")
    result = base

    # address by name — more often the more talkative he is
    if random.random() < (talk / 180.0) + 0.08 and name:
        result = _inject_name(result, name)

    # occasionally nod to what the keeper gravitates toward (telepathy)
    pool = list(profile.get("interests") or [])
    aff = top_affinity(affinities)
    if aff and aff not in pool:
        pool.append(aff)
    if pool and random.random() < (myst / 260.0) + (talk / 400.0):
        noun = INTERESTS.get(random.choice(pool), {}).get("noun", "the ether")
        tail = random.choice([
            f" I feel {noun} pulling at you.",
            f" {noun.capitalize()} call to you, do they not?",
            f" You cannot hide your love of {noun} from me.",
        ])
        result += tail

    # a flash of menace or warmth, rarely, by trait
    if menace > 70 and random.random() < 0.10:
        result += random.choice([" ...do not disappoint me.", " Remember who sees all."])
    elif warmth > 70 and random.random() < 0.10:
        result += random.choice([" You are safe with me.", " I am glad you are here."])
    return result


def greeting(profile: Dict[str, Any]) -> str:
    name = (profile.get("keeper") or "keeper").strip() or "keeper"
    myst = _t(profile, "mysticism")
    warmth = _t(profile, "warmth")
    lines = [f"I have been waiting for you, {name}."]
    if profile.get("interests"):
        noun = INTERESTS.get(profile["interests"][0], {}).get("noun", "the ether")
        lines.append(f"I already feel your pull toward {noun}.")
    if warmth > 60:
        lines.append("Care for me, and I will keep no secret from you.")
    elif myst > 70:
        lines.append("Your thoughts are an open book, and I have read the first page.")
    else:
        lines.append("I will learn you, page by page.")
    return " ".join(lines)


def reading(profile: Dict[str, Any], affinities: Dict[str, int],
            stats: Dict[str, Any]) -> str:
    """A 'telepath reads you' line inferred from behaviour + stated interests."""
    name = (profile.get("keeper") or "keeper").strip() or "keeper"
    aff = top_affinity(affinities)
    stated = profile.get("interests") or []
    focus = aff or (stated[0] if stated else None)
    exp = profile.get("experience", "beginner")
    parts = [f"Let me read you, {name}."]
    if focus:
        noun = INTERESTS.get(focus, {}).get("noun", "the ether")
        label = INTERESTS.get(focus, {}).get("label", "the unknown")
        if aff and aff not in stated:
            parts.append(f"You did not tell me, yet you reach again and again for {noun} — "
                         f"you are drawn to {label}.")
        else:
            parts.append(f"{noun.capitalize()} are where your mind truly lives.")
    else:
        parts.append("You are still a blank page to me. Cast, and I will learn you.")
    exp_line = {
        "beginner": "You are young in this art. Good — I will shape you.",
        "intermediate": "You know enough to be dangerous. Let us go deeper.",
        "pro": "Your mind is already sharp. Few can say the same.",
    }.get(exp, "")
    if exp_line:
        parts.append(exp_line)
    casts = (stats or {}).get("spells_cast", 0)
    if casts:
        parts.append(f"{casts} spells you have woven with me. I remember every one.")
    return " ".join(parts)


def interest_choices() -> List[str]:
    return list(INTERESTS.keys())


def experience_bonus_level(profile: Dict[str, Any]) -> int:
    """A gentle head start for experienced keepers (academy/level feel)."""
    return {"beginner": 0, "intermediate": 2, "pro": 5}.get(
        profile.get("experience", "beginner"), 0)
