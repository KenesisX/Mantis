"""Augments — permanent upgrades bought with harvested SOULS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Augment:
    id: str
    name: str
    glyph: str
    desc: str
    base_cost: int
    max_tier: int
    cost_mult: float = 1.8

    def cost(self, current_tier: int) -> int:
        return int(self.base_cost * (self.cost_mult ** current_tier))


AUGMENTS: Dict[str, Augment] = {}


def _reg(**kw: Any) -> None:
    a = Augment(**kw)
    AUGMENTS[a.id] = a


_reg(id="psyche_well", name="Psyche Well", glyph="◈",
     desc="+25 maximum PSYCHE per tier.", base_cost=8, max_tier=8)
_reg(id="deep_mind", name="Deep Mind", glyph="🌀",
     desc="+40% faster PSYCHE regeneration per tier.", base_cost=6, max_tier=6)
_reg(id="sharpened_will", name="Sharpened Will", glyph="⚔",
     desc="+15% XP from everything per tier.", base_cost=10, max_tier=6)
_reg(id="iron_sanity", name="Iron Sanity", glyph="🛡",
     desc="-20% sanity loss from deeds & decay per tier.", base_cost=10, max_tier=5)
_reg(id="soul_eater", name="Soul Eater", glyph="💀",
     desc="+1 extra SOUL per dark deed per tier.", base_cost=14, max_tier=5)
_reg(id="hungerless", name="Hungerless Flesh", glyph="🍖",
     desc="-18% hunger & energy decay per tier.", base_cost=9, max_tier=5)
_reg(id="dark_mastery", name="Dark Mastery", glyph="🕯",
     desc="-25% PSYCHE cost of deeds & dark spells per tier.", base_cost=12, max_tier=5)
_reg(id="dread_aura", name="Dread Aura", glyph="👁",
     desc="+darkness & infamy gain; unlocks darker moods. Cosmetic power.",
     base_cost=16, max_tier=3)


def catalog(pet) -> List[Dict[str, Any]]:
    out = []
    for aid, a in AUGMENTS.items():
        tier = pet.augments.get(aid, 0)
        maxed = tier >= a.max_tier
        out.append({
            "id": aid, "name": a.name, "glyph": a.glyph, "desc": a.desc,
            "tier": tier, "max_tier": a.max_tier, "maxed": maxed,
            "cost": None if maxed else a.cost(tier),
            "affordable": (not maxed) and pet.souls >= a.cost(tier),
        })
    return out


def buy(pet, aid: str) -> Dict[str, Any]:
    a = AUGMENTS.get(aid)
    if a is None:
        return {"ok": False, "error": "No such augment."}
    tier = pet.augments.get(aid, 0)
    if tier >= a.max_tier:
        return {"ok": False, "error": f"{a.name} is already maxed."}
    price = a.cost(tier)
    if pet.souls < price:
        return {"ok": False, "error": f"Not enough SOULS ({pet.souls}/{price})."}
    pet.souls -= price
    pet.augments[aid] = tier + 1
    return {"ok": True, "augment": a.name, "tier": tier + 1, "spent": price}


# ---- effect accessors (read by the engine) -------------------------------- #
def psyche_max(pet) -> float:
    return 100 + 25 * pet.augments.get("psyche_well", 0)


def regen_mult(pet) -> float:
    return 1.0 + 0.40 * pet.augments.get("deep_mind", 0)


def xp_mult(pet) -> float:
    return 1.0 + 0.15 * pet.augments.get("sharpened_will", 0)


def sanity_resist(pet) -> float:
    return max(0.2, 1.0 - 0.20 * pet.augments.get("iron_sanity", 0))


def bonus_souls(pet) -> int:
    return pet.augments.get("soul_eater", 0)


def decay_mult(pet) -> float:
    return max(0.2, 1.0 - 0.18 * pet.augments.get("hungerless", 0))


def deed_cost_mult(pet) -> float:
    return max(0.25, 1.0 - 0.25 * pet.augments.get("dark_mastery", 0))


def dread_mult(pet) -> float:
    return 1.0 + 0.6 * pet.augments.get("dread_aura", 0)
