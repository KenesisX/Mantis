"""The Inner Mind — MANTIS's adaptive coaching intelligence.

A self-contained (offline) learning engine. As you use the program it watches
what you do, infers your *style*, and after every action suggests next moves that
teach you something — weighted toward your interests and the gaps in your
knowledge, and away from advice you keep ignoring. No external AI service; it
runs anywhere, privately.

State lives in ``pet.coach``:
    usage : {key: {n, t, cat}}      what you do, how often, how recently
    sug   : {key: {shown, done}}    which suggestions landed vs were ignored
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

# which category each spell belongs to (for style inference + suggestions)
SPELL_CAT = {
    "mind_reading": "recon", "clairvoyance": "recon", "telepathy": "recon",
    "astral_projection": "recon", "hydroquartz": "recon", "psychokinesis": "recon",
    "soul_scream": "recon",
    "the_veil": "defense", "astral_seal": "defense", "aegis_ward": "defense",
    "ward_of_truth": "defense", "veil_of_headers": "defense",
    "rtlsdr_attune": "rf", "subghz_listen": "rf", "lora_whisper": "rf", "adsb_sky": "rf",
}

# ward spell per posture component (to coach toward a full grade)
POSTURE_SPELL = {"tls": "astral_seal", "firewall": "aegis_ward",
                 "dnssec": "ward_of_truth", "headers": "veil_of_headers"}

STYLES = {
    "Learner":   "You chase understanding — I will teach as we go.",
    "Defender":  "You harden and protect — a true blue-team mind.",
    "Operator":  "You reach into the ether — recon is your instinct.",
    "Listener":  "You favour the airwaves — the radio speaks to you.",
    "Shadow":    "You walk the dark path — power calls to you.",
    "Caretaker": "You tend to me well — balance in all things.",
    "Explorer":  "You wander widely — curious about everything.",
}


def _c(pet) -> Dict[str, Any]:
    c = pet.coach
    c.setdefault("usage", {})
    c.setdefault("sug", {})
    c.setdefault("current", [])
    c.setdefault("style", "Explorer")
    return c


def observe(pet, cat: str, key: str) -> None:
    c = _c(pet)
    u = c["usage"].setdefault(key, {"n": 0, "t": 0.0, "cat": cat})
    u["n"] += 1
    u["t"] = time.time()
    u["cat"] = cat
    # if this action was recently suggested, count it as accepted
    s = c["sug"].get(key)
    if s is not None:
        s["done"] = s.get("done", 0) + 1
    c["style"] = infer_style(pet)


def infer_style(pet) -> str:
    c = _c(pet)
    tally: Dict[str, int] = {}
    for u in c["usage"].values():
        tally[u["cat"]] = tally.get(u["cat"], 0) + u["n"]
    care = tally.get("care", 0)
    total = sum(tally.values()) or 1
    if total < 4:
        return "Explorer"
    top = max(tally, key=tally.get)
    mapping = {"lesson": "Learner", "defense": "Defender", "recon": "Operator",
               "rf": "Listener", "deed": "Shadow", "augment": "Shadow",
               "care": "Caretaker"}
    # distinct categories used -> explorer
    if len([k for k, v in tally.items() if v]) >= 5 and tally[top] < total * 0.4:
        return "Explorer"
    return mapping.get(top, "Explorer")


def _penalty(pet, key: str) -> float:
    s = _c(pet)["sug"].get(key)
    if not s:
        return 0.0
    shown, done = s.get("shown", 0), s.get("done", 0)
    if done:
        return 0.0
    return min(3.0, 0.8 * shown)      # keep showing it less if you ignore it


def _recently(pet, key: str, within=25) -> bool:
    u = _c(pet)["usage"].get(key)
    return bool(u and time.time() - u["t"] < within)


def suggest(engine, last_cat: str = None, last_key: str = None) -> List[Dict[str, Any]]:
    """Produce up to 3 teaching suggestions, adapted to the keeper."""
    from . import academy as ACAD, spells, upgrades as U, persona as PERSONA
    pet = engine.pet
    c = _c(pet)
    style = c["style"]
    affinity = PERSONA.top_affinity(getattr(pet, "affinities", {}) or {})
    snap_posture = None
    try:
        from . import posture as POST
        snap_posture = POST.compute(pet.posture)
    except Exception:
        pass

    cands: List[Dict[str, Any]] = []

    def add(key, text, cmd, why, cat, base, teach=True):
        if _recently(pet, key):
            return
        score = base + 2.0 - _penalty(pet, key)
        if affinity and affinity in key:
            score += 1.2
        # style boosts
        if style == "Learner" and cmd["type"] == "learn":
            score += 1.5
        if style == "Defender" and ("ward" in key or cmd.get("id") in POSTURE_SPELL.values()):
            score += 1.3
        if style == "Operator" and cat == "recon":
            score += 1.0
        if style == "Listener" and cat == "rf":
            score += 1.3
        cands.append({"key": key, "text": text, "cmd": cmd, "why": why,
                      "cat": cat, "teach": teach, "score": score})

    # 1) teach the concept behind what you just did
    if last_key and last_key.startswith("cast:"):
        sid = last_key.split(":", 1)[1]
        les = ACAD.spell_lesson(sid)
        if les and les["id"] not in pet.academy.get("completed", []):
            add("learn:" + les["id"], f"Learn the idea behind that: {les['title']}",
                {"type": "learn", "id": les["id"]},
                "understand what you just cast", "lesson", 3.5)

    # 2) next Academy lesson (always a teaching option)
    nxt = ACAD.next_lesson(pet.academy.get("completed", []))
    if nxt:
        add("learn:" + nxt["id"], f"Study: {nxt['title']} ({nxt['topic']})",
            {"type": "learn", "id": nxt["id"]}, "advance your rank", "lesson", 2.2)

    # 3) harden posture — cast a ward you haven't run
    if snap_posture:
        for comp in snap_posture.get("components", []):
            if comp.get("score") is None:
                sid = POSTURE_SPELL.get(comp["key"])
                if sid:
                    add("cast:" + sid, f"Check your {comp['label']} — cast {spells.SPELLS[sid].name}",
                        {"type": "cast", "id": sid}, "raise your security grade", "defense", 2.6)
                break

    # 4) explore an unlocked spell you've never cast
    for sid in pet.unlocked_spells:
        if "cast:" + sid not in c["usage"] and sid in spells.SPELLS:
            sp = spells.SPELLS[sid]
            add("cast:" + sid, f"Try a new spell: {sp.glyph} {sp.name}",
                {"type": "cast", "id": sid}, "you've unlocked but never used it",
                SPELL_CAT.get(sid, "recon"), 2.1)
            break

    # 5) spend souls on the cheapest useful augment
    aff = [a for a in U.catalog(pet) if not a["maxed"] and a["affordable"]]
    if aff:
        a = min(aff, key=lambda x: x["cost"])
        add("buy:" + a["id"], f"Augment yourself: {a['name']} (◇{a['cost']})",
            {"type": "buy", "id": a["id"]}, "permanent upgrade", "augment", 1.6, teach=False)

    # 6) care, if a need is low
    n = {"hunger": pet.hunger, "energy": pet.energy, "focus": pet.focus, "sanity": pet.sanity}
    low = min(n, key=n.get)
    if n[low] < 35:
        act = {"hunger": "feed", "energy": "rest", "focus": "meditate", "sanity": "pet"}[low]
        add("action:" + act, f"I grow weak ({low}) — {act} me",
            {"type": "action", "id": act}, "keep me healthy", "care", 2.8, teach=False)

    cands.sort(key=lambda x: x["score"], reverse=True)
    # keep top 3, distinct categories
    picked: List[Dict[str, Any]] = []
    seen_cat = set()
    for cd in cands:
        if cd["cat"] in seen_cat and len(picked) >= 2:
            continue
        picked.append(cd)
        seen_cat.add(cd["cat"])
        if len(picked) == 3:
            break

    for cd in picked:
        s = c["sug"].setdefault(cd["key"], {"shown": 0, "done": 0})
        s["shown"] = s.get("shown", 0) + 1
    c["current"] = [{"text": cd["text"], "cmd": cd["cmd"], "why": cd["why"],
                     "teach": cd["teach"], "key": cd["key"]} for cd in picked]
    return c["current"]


def summary(pet) -> Dict[str, Any]:
    c = _c(pet)
    return {
        "style": c.get("style", "Explorer"),
        "style_desc": STYLES.get(c.get("style", "Explorer"), ""),
        "suggestions": c.get("current", []),
        "actions_seen": sum(u["n"] for u in c.get("usage", {}).values()),
    }
