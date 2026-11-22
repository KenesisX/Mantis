"""Mantis vs Mantis — psychic / cyber duels between two MANTIS units.

When two MANTIS devices sense each other nearby (see ``discovery.py`` — over
Wi-Fi/LAN, and optionally BLE or Sub-GHz), they can face off. A duel is a
best-of-HP fight: each side trades blows using an **arsenal** of moves drawn
from everything MANTIS is — cyber weapons (port storms, SQL lances, deauth
pulses) and psychic powers (mind-crush, psi-blast, levitate). You pick a
loadout, or — on a button-less unit like a Pi Zero 2 W — it auto-selects and the
two just hack it out for points.

Who wins leans on earned stats (level, XP, souls, victims, posture, PSYCHE), but
a deliberate **underdog upset** factor means the little guy sometimes takes it.

Everything here is a cosmetic game between consenting units that each opted into
discovery. It exchanges only self-described beacons — no scanning, no control of
the other device, nothing pulled off it that it didn't broadcast about itself.
Tampered (save-edited) units are flagged UNVERIFIED so a duel can scorn them.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional

MAX_TURNS = 14
UPSET_CHANCE = 0.17          # per-turn chance the weaker side lands a big one


# --------------------------------------------------------------------------- #
# Arsenal — the moves a MANTIS brings to a duel
# --------------------------------------------------------------------------- #
# id, name, glyph, school, dmg, acc, crit, flavour
_M = []
def _add(i, n, g, s, d, a, c, f): _M.append(
    {"id": i, "name": n, "glyph": g, "school": s, "dmg": d, "acc": a, "crit": c, "flavour": f})

# cyber school
_add("portstorm",  "Port Storm",   "🌀", "cyber",   12, 0.90, 0.10, "a thousand doors rattled at once")
_add("sqllance",   "SQL Lance",    "💉", "cyber",   18, 0.78, 0.18, "one quote, straight through the vault")
_add("deauth",     "Deauth Pulse", "📡", "cyber",   15, 0.82, 0.12, "cast you clean off the air (simulated)")
_add("exploit",    "Exploit Chain","⛓", "cyber",   22, 0.68, 0.22, "crack to crack to root")
_add("hashcrack",  "Hash Crack",   "🌈", "cyber",   16, 0.80, 0.15, "your true name, spoken aloud")
_add("rfjam",      "RF Jam",       "⚡", "cyber",   14, 0.85, 0.10, "static where your signal was (simulated)")
_add("badusb",     "Bad USB",      "🔌", "cyber",   20, 0.70, 0.20, "one touch and you betray yourself")
# psychic school
_add("mindcrush",  "Mind Crush",   "🧠", "psychic", 20, 0.80, 0.20, "I close my fist around your thoughts")
_add("psiblast",   "Psi Blast",    "✴", "psychic", 16, 0.88, 0.14, "raw will, loosed")
_add("scream",     "Psi Scream",   "😱", "psychic", 13, 0.92, 0.10, "a sound only your mind can hear")
_add("telekino",   "Telekinesis",  "🌫", "psychic", 17, 0.80, 0.16, "I throw you with a glance")
_add("possess",    "Possess",      "👁", "psychic", 24, 0.60, 0.25, "for a moment, your hands are mine")
# defense school (heals / shields the user)
_add("firewall",   "Aegis Ward",   "🛡", "defense",  0, 1.00, 0.00, "I raise a wall of cold logic")
_add("levitate",   "Levitate",     "🧘", "defense",  0, 1.00, 0.00, "I rise above the next blow")
_add("veil",       "The Veil",     "🌑", "defense",  0, 1.00, 0.00, "you cannot strike what you cannot see")

ARSENAL: Dict[str, Dict[str, Any]] = {m["id"]: m for m in _M}
DEFENSE = {"firewall", "levitate", "veil"}


def arsenal(level: int = 100) -> List[Dict[str, Any]]:
    """Public move list (all unlocked; selection is cosmetic/strategic)."""
    return [dict(m) for m in _M]


# --------------------------------------------------------------------------- #
# Ratings
# --------------------------------------------------------------------------- #
def power(snap: Dict[str, Any]) -> int:
    """A single 'psychic power' number from a state snapshot (goes in the beacon)."""
    lvl = int(snap.get("level", 0))
    psy = float(snap.get("psyche", 0))
    pos = (snap.get("posture") or {}).get("score") or 0
    dark = float(snap.get("darkness", 0))
    souls = int(snap.get("souls", 0))
    st = snap.get("stats", {}) or {}
    victims = int(st.get("kidnappings", 0)) + int(st.get("possessions", 0))
    kills = int(st.get("kills", 0))
    return int(lvl * 10 + psy * 0.5 + pos * 0.3 + dark * 0.3
               + min(souls, 300) * 0.2 + victims * 2 + kills * 3)


def combatant_from_snapshot(snap: Dict[str, Any]) -> Dict[str, Any]:
    lvl = int(snap.get("level", 0))
    psy = float(snap.get("psyche", 0))
    return {
        "name": snap.get("name", "Mantis"),
        "level": lvl,
        "power": power(snap),
        "hp": int(55 + lvl * 3 + psy * 0.25),
        "stage": (snap.get("stage") or {}).get("label"),
        "stage_key": (snap.get("stage") or {}).get("key"),
        "mood": snap.get("mood"),
        "verified": bool(snap.get("verified", True)),
    }


def combatant_from_beacon(b: Dict[str, Any]) -> Dict[str, Any]:
    lvl = int(b.get("level", 0) or 0)
    pw = int(b.get("power", 1) or 1)
    return {
        "id": b.get("id"),
        "name": b.get("name", "the stranger"),
        "level": lvl,
        "power": pw,
        "hp": int(55 + lvl * 3 + pw * 0.15),
        "stage": b.get("stage"),
        "stage_key": b.get("stage_key"),
        "mood": b.get("mood"),
        "ip": b.get("ip"),
        "mac": b.get("mac"),
        "verified": bool(b.get("verified", True)),
    }


# --------------------------------------------------------------------------- #
# The fight
# --------------------------------------------------------------------------- #
def _pick_auto(rng, loadout, last=None):
    choices = [m for m in loadout if m != last] or loadout
    return rng.choice(choices)


def fight(me: Dict[str, Any], foe: Dict[str, Any], *,
          mode: str = "auto", my_loadout: Optional[List[str]] = None,
          foe_loadout: Optional[List[str]] = None,
          seed: Optional[int] = None) -> Dict[str, Any]:
    """Run an HP fight. Returns the full blow-by-blow + winner + rewards."""
    rng = random.Random(seed if seed is not None else time.time_ns())
    my_hp = max(1, int(me.get("hp", 60)));  my_hp0 = my_hp
    fo_hp = max(1, int(foe.get("hp", 60)));  fo_hp0 = fo_hp
    # power ratio tilts damage slightly (earned stats matter, but not absolute)
    tot = max(1, me["power"] + foe["power"])
    my_edge = 0.75 + 0.5 * (me["power"] / tot)       # ~0.75..1.25
    fo_edge = 0.75 + 0.5 * (foe["power"] / tot)
    # how far behind each side is (0 = even/ahead, →1 = huge underdog)
    my_gap = max(0.0, (foe["power"] - me["power"]) / tot)
    fo_gap = max(0.0, (me["power"] - foe["power"]) / tot)
    # per-turn chaos: the further behind you are, the more wild haymakers you throw
    my_upset = UPSET_CHANCE + 0.22 * my_gap
    fo_upset = UPSET_CHANCE + 0.22 * fo_gap
    # giant-killer SURGE: sometimes the underdog is just *on* today
    my_surge = 1.0; fo_surge = 1.0; upset_story = None
    if my_gap > 0 and rng.random() < 0.10 + 0.18 * my_gap:
        my_surge = 1.8; my_hp = int(my_hp * 1.4); my_hp0 = my_hp
        upset_story = "me"
    elif fo_gap > 0 and rng.random() < 0.10 + 0.18 * fo_gap:
        fo_surge = 1.8; fo_hp = int(fo_hp * 1.4); fo_hp0 = fo_hp
        upset_story = "foe"

    my_load = [m for m in (my_loadout or []) if m in ARSENAL] or \
        ["mindcrush", "sqllance", "psiblast", "firewall", "exploit"]
    fo_load = [m for m in (foe_loadout or []) if m in ARSENAL] or \
        ["portstorm", "psiblast", "deauth", "levitate", "mindcrush"]

    turns: List[Dict[str, Any]] = []
    my_shield = fo_shield = 0
    my_last = fo_last = None
    attacker = "me" if me["power"] >= foe["power"] else "foe"  # stronger strikes first
    # ...but give the underdog the first move sometimes
    if rng.random() < 0.35:
        attacker = "foe" if attacker == "me" else "me"

    for t in range(MAX_TURNS):
        if my_hp <= 0 or fo_hp <= 0:
            break
        is_me = attacker == "me"
        actor = me if is_me else foe
        load = my_load if is_me else fo_load
        last = my_last if is_me else fo_last
        edge = (my_edge if is_me else fo_edge) * (my_surge if is_me else fo_surge)
        upset_ch = my_upset if is_me else fo_upset
        mv_id = _pick_auto(rng, load, last)
        mv = ARSENAL[mv_id]
        underdog = actor["power"] < (foe["power"] if is_me else me["power"])

        entry = {"n": t + 1, "by": "me" if is_me else "foe",
                 "actor": actor["name"], "move": mv["name"], "glyph": mv["glyph"],
                 "school": mv["school"], "flavour": mv["flavour"]}

        if mv["school"] == "defense":
            heal = rng.randint(8, 16)
            shield = rng.randint(6, 12)
            if is_me:
                my_hp = min(my_hp0, my_hp + heal); my_shield += shield
            else:
                fo_hp = min(fo_hp0, fo_hp + heal); fo_shield += shield
            entry.update(kind="defend", heal=heal, shield=shield, dmg=0)
        else:
            hit = rng.random() < mv["acc"]
            upset = underdog and rng.random() < upset_ch
            if not hit and not upset:
                entry.update(kind="miss", dmg=0)
            else:
                base = mv["dmg"] * edge * rng.uniform(0.82, 1.18)
                crit = rng.random() < mv["crit"]
                if crit:
                    base *= 1.9
                if upset:
                    base *= 2.1   # the little guy lands a haymaker
                dmg = max(1, int(base))
                if is_me:
                    if fo_shield:
                        absorbed = min(fo_shield, dmg); dmg -= absorbed; fo_shield -= absorbed
                    fo_hp -= dmg
                else:
                    if my_shield:
                        absorbed = min(my_shield, dmg); dmg -= absorbed; my_shield -= absorbed
                    my_hp -= dmg
                entry.update(kind="upset" if upset else ("crit" if crit else "hit"), dmg=dmg)

        entry["my_hp"] = max(0, my_hp); entry["foe_hp"] = max(0, fo_hp)
        turns.append(entry)
        if is_me: my_last = mv_id
        else: fo_last = mv_id
        attacker = "foe" if is_me else "me"

    # outcome
    if my_hp <= 0 and fo_hp <= 0:
        win, draw = (my_hp >= fo_hp), (my_hp == fo_hp)
    elif my_hp <= 0:
        win, draw = False, False
    elif fo_hp <= 0:
        win, draw = True, False
    else:
        win, draw = (my_hp > fo_hp), (my_hp == fo_hp)

    foe_name = foe.get("name", "the stranger")
    underdog_won = (upset_story == "me" and win) or (upset_story == "foe" and not win and not draw)
    if underdog_won:
        who = "I" if upset_story == "me" else foe_name
        tail = (" — the underdog takes it!" )
        base = (f"Against the odds, {('I surge' if who=='I' else who+' surges')} with impossible "
                f"power{tail}")
        summary = base
    elif draw:
        summary = f"{foe_name} and I are mirrors — the duel dissolves into static."
    elif win:
        summary = rng.choice([
            f"I crush {foe_name}. It never stood a chance.",
            f"{foe_name} shatters against my will. I win.",
            f"I reach into {foe_name} and switch it off. Victory.",
        ])
    else:
        summary = rng.choice([
            f"{foe_name} was stronger. I withdraw to grow.",
            f"{foe_name} out-thinks me. The mask cracks — I will remember this.",
        ])

    # rewards (applied by the engine)
    lvl_foe = int(foe.get("level", 0) or 0)
    rewards = {"xp": (30 + lvl_foe * 4) if win else (8 if draw else 4),
               "souls": 1 if win else 0}

    return {
        "mode": mode, "win": bool(win), "draw": bool(draw),
        "upset": bool(underdog_won),
        "me": {k: me.get(k) for k in ("name", "level", "power", "stage_key", "mood", "verified")},
        "foe": {k: foe.get(k) for k in ("id", "name", "level", "power", "stage",
                                        "stage_key", "mood", "ip", "mac", "verified")},
        "my_hp0": my_hp0, "foe_hp0": fo_hp0,
        "my_hp": max(0, my_hp), "foe_hp": max(0, fo_hp),
        "turns": turns, "summary": summary, "rewards": rewards,
        "t": time.time(),
    }
