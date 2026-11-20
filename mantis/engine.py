"""Core pet engine: state, needs, XP/levelling, deeds, augments, persistence."""

from __future__ import annotations

import json
import os
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from . import personality as P
from . import upgrades as U
from . import stages as ST
from . import posture as POST
from . import academy as ACAD
from . import persona as PERSONA
from . import coach as COACH
from . import activities as ACT


def default_home() -> str:
    env = os.environ.get("MANTIS_HOME") or os.environ.get("PSYCHOMANTIS_HOME")
    if env:
        return os.path.expanduser(env)
    home = os.path.join(os.path.expanduser("~"), ".mantis")
    # migrate state from the old ~/.psychomantis location if present
    legacy = os.path.join(os.path.expanduser("~"), ".psychomantis")
    if not os.path.exists(home) and os.path.exists(legacy):
        try:
            import shutil
            shutil.copytree(legacy, home)
        except Exception:
            return legacy
    return home


SAVE_NAME = "soul.json"


# --------------------------------------------------------------------------- #
# Levelling
# --------------------------------------------------------------------------- #
def xp_to_next(level: int) -> int:
    return int(60 * (max(1, level) ** 1.45)) + 30


def rank_for(level: int) -> str:
    return P.rank_for(level)


# --------------------------------------------------------------------------- #
# Pet model
# --------------------------------------------------------------------------- #
@dataclass
class Pet:
    name: str = "Mantis"
    born: float = field(default_factory=time.time)
    last_tick: float = field(default_factory=time.time)

    level: int = 1
    xp: int = 0

    hunger: float = 80.0
    energy: float = 80.0
    focus: float = 70.0
    sanity: float = 70.0
    psyche: float = 20.0

    # dark economy
    souls: int = 0
    darkness: float = 0.0        # 0 (restrained) .. 100 (monstrous)
    infamy: int = 0

    # lifetime / recon stats
    networks_sensed: int = 0
    devices_read: int = 0
    spells_cast: int = 0
    sessions: int = 0
    feedings: int = 0
    meditations: int = 0
    pets_received: int = 0
    deaths: int = 0
    best_level: int = 1

    # dark deed counters (fiction)
    kills: int = 0
    kidnappings: int = 0
    possessions: int = 0
    hauntings: int = 0
    souls_harvested: int = 0

    known_networks: List[Dict[str, Any]] = field(default_factory=list)
    known_devices: List[Dict[str, Any]] = field(default_factory=list)
    unlocked_spells: List[str] = field(default_factory=lambda: ["mind_reading"])
    achievements: List[str] = field(default_factory=list)
    augments: Dict[str, int] = field(default_factory=dict)
    pawns: List[Dict[str, Any]] = field(default_factory=list)      # possessed/captive
    inventory: List[Dict[str, Any]] = field(default_factory=list)  # relics/trophies
    posture: Dict[str, Any] = field(default_factory=dict)          # defensive findings
    academy: Dict[str, Any] = field(default_factory=lambda: {
        "completed": [], "introduced": [], "knowledge_xp": 0,
        "quiz_correct": 0, "quiz_total": 0})                       # learning progress
    affinities: Dict[str, int] = field(default_factory=dict)       # inferred interests
    coach: Dict[str, Any] = field(default_factory=dict)            # inner-AI learning state

    # activities + idle behaviour
    idle_mode: str = "active"          # "active" (autonomous) | "passive" (quiet watch)
    activities_run: int = 0
    last_activity: str = ""
    activity_counts: Dict[str, int] = field(default_factory=dict)

    mood: str = "watching"
    last_phrase: str = "..."
    log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Pet":
        pet = cls()
        for k in pet.__dataclass_fields__:
            if k in d:
                setattr(pet, k, d[k])
        return pet


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
class Engine:
    def __init__(self, home: Optional[str] = None):
        self.home = home or default_home()
        os.makedirs(self.home, exist_ok=True)
        self.save_path = os.path.join(self.home, SAVE_NAME)
        self._lock = threading.RLock()
        self._hold_until = 0.0            # keep an event mood on screen briefly
        self.profile = PERSONA.load(self.home)
        self.pet = self.load()
        if self.pet.name == "Mantis" and self.profile.get("mantis_name"):
            self.pet.name = self.profile["mantis_name"]
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

    # -- persistence --------------------------------------------------- #
    def load(self) -> Pet:
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, "r", encoding="utf-8") as fh:
                    pet = Pet.from_dict(json.load(fh))
                pet.sessions += 1
                if pet.name == "Psycho Mantis":      # migrate old saves -> Mantis
                    pet.name = "Mantis"
                return pet
            except Exception:
                pass
        pet = Pet()
        pet.sessions = 1
        pet.log.append(_event("birth", "The Mantis opens its eyes behind the mask."))
        return pet

    def save(self) -> None:
        with self._lock:
            tmp = self.save_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self.pet.to_dict(), fh, indent=2)
            os.replace(tmp, self.save_path)

    # -- events -------------------------------------------------------- #
    def subscribe(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        self._subscribers.append(fn)

    def emit(self, kind: str, text: str, **extra: Any) -> Dict[str, Any]:
        ev = _event(kind, text, **extra)
        with self._lock:
            self.pet.log.append(ev)
            self.pet.log = self.pet.log[-400:]
        for fn in list(self._subscribers):
            try:
                fn(ev)
            except Exception:
                pass
        return ev

    # -- helpers ------------------------------------------------------- #
    def psyche_cap(self) -> float:
        return U.psyche_max(self.pet)

    def _clamp_psyche(self) -> None:
        self.pet.psyche = max(0.0, min(self.psyche_cap(), self.pet.psyche))

    def _hold_mood(self, mood: str, seconds: float = 6.0) -> None:
        self.pet.mood = mood
        self._hold_until = time.time() + seconds

    # -- time / needs -------------------------------------------------- #
    def tick(self, now: Optional[float] = None) -> None:
        with self._lock:
            pet = self.pet
            now = now or time.time()
            dt = max(0.0, now - pet.last_tick)
            pet.last_tick = now
            minutes = dt / 60.0
            dm = U.decay_mult(pet)

            pet.hunger = _clamp(pet.hunger - 0.55 * dm * minutes)
            pet.energy = _clamp(pet.energy - 0.40 * dm * minutes)
            pet.focus = _clamp(pet.focus - 0.50 * minutes)
            strain = sum(0.30 for v in (pet.hunger, pet.energy, pet.focus) if v < 20)
            pet.sanity = _clamp(pet.sanity - (0.18 + strain) * U.sanity_resist(pet) * minutes)
            pet.psyche = pet.psyche + 0.25 * U.regen_mult(pet) * minutes
            # darkness slowly cools toward a floor set by deeds history
            pet.darkness = _clamp(pet.darkness - 0.05 * minutes)
            self._clamp_psyche()
            self._refresh_mood()
            self._maybe_speak()

    # -- care actions -------------------------------------------------- #
    def feed(self) -> str:
        with self._lock:
            self.pet.hunger = _clamp(self.pet.hunger + 28)
            self.pet.sanity = _clamp(self.pet.sanity + 4)
            self.pet.feedings += 1
        self._award(6)
        return self._do("feed", P.pick(P.PHRASES["fed"]))

    def rest(self) -> str:
        with self._lock:
            self.pet.energy = _clamp(self.pet.energy + 34)
            self.pet.focus = _clamp(self.pet.focus + 8)
        self._award(4)
        return self._do("rest", P.pick(P.PHRASES["rested"]))

    def meditate(self) -> str:
        with self._lock:
            self.pet.focus = _clamp(self.pet.focus + 26)
            self.pet.sanity = _clamp(self.pet.sanity + 14)
            self.pet.psyche += 24
            self.pet.energy = _clamp(self.pet.energy - 5)
            self.pet.meditations += 1
            self._clamp_psyche()
        self._award(8)
        return self._do("meditate", P.pick(P.PHRASES["meditate"]), mood="meditative")

    def pet_it(self) -> str:
        with self._lock:
            self.pet.sanity = _clamp(self.pet.sanity + 10)
            self.pet.darkness = _clamp(self.pet.darkness - 2)
            self.pet.pets_received += 1
        self._award(3)
        return self._do("pet", P.pick(P.PHRASES["petted"]), mood="affectionate")

    def rename(self, name: str) -> None:
        name = (name or "").strip()[:32] or "Mantis"
        with self._lock:
            self.pet.name = name
        self.emit("rename", f"I shall answer to '{name}' now.")
        self._after_action()

    def _do(self, kind: str, msg: str, mood: Optional[str] = None) -> str:
        if mood:
            self._hold_mood(mood, 5)
        self.emit(kind, msg)
        if kind in ("feed", "rest", "meditate", "pet"):
            self.coach_after("care", "action:" + kind)
        self._after_action()
        return msg

    # -- dark deeds (FICTION — invented NPCs, not the real recon tools) - #
    DEEDS = {
        "possess": dict(min_level=8, psyche=18, xp=45, dark=5, souls=1,
                        counter="possessions", mood="possessing"),
        "kidnap":  dict(min_level=12, psyche=22, xp=60, dark=7, souls=2,
                        counter="kidnappings", mood="kidnapping"),
        "sever":   dict(min_level=16, psyche=26, xp=80, dark=10, souls=2, sanity=-8,
                        counter="kills", mood="severing"),
        "haunt":   dict(min_level=6, psyche=10, xp=30, dark=3, souls=1,
                        counter="hauntings", mood="hunting"),
    }

    def deed(self, name: str) -> Dict[str, Any]:
        spec = self.DEEDS.get(name)
        if spec is None:
            return {"ok": False, "error": f"No such deed: {name}"}
        pet = self.pet
        if pet.level < spec["min_level"]:
            return {"ok": False, "error": f"Requires level {spec['min_level']}."}
        cost = int(spec["psyche"] * U.deed_cost_mult(pet))
        if pet.psyche < cost:
            return {"ok": False, "error": f"Not enough PSYCHE ({int(pet.psyche)}/{cost})."}
        who = random.choice(P.NPC_NAMES)
        with self._lock:
            pet.psyche -= cost
            setattr(pet, spec["counter"], getattr(pet, spec["counter"]) + 1)
            gained = spec["souls"] + U.bonus_souls(pet)
            pet.souls += gained
            pet.darkness = _clamp(pet.darkness + spec["dark"] * U.dread_mult(pet))
            pet.infamy += int(2 * U.dread_mult(pet))
            if "sanity" in spec:
                pet.sanity = _clamp(pet.sanity + spec["sanity"] * U.sanity_resist(pet))
            if name in ("possess", "kidnap"):
                pet.pawns.append({"who": who, "deed": name, "t": time.time()})
                pet.pawns = pet.pawns[-60:]
            if name == "sever" and pet.pawns:
                pet.pawns.pop(0)
            self._clamp_psyche()
        self._hold_mood(spec["mood"], 6)
        msg = P.pick(P.PHRASES[name]).format(who=who)
        self.emit("deed", msg, deed=name)
        self._award(spec["xp"])
        self.coach_after("deed", "deed:" + name)
        self._check_achievements()
        self._after_action()
        return {"ok": True, "summary": msg, "who": who, "souls": gained,
                "darkness": round(pet.darkness, 1)}

    def harvest(self) -> Dict[str, Any]:
        pet = self.pet
        if pet.level < 10:
            return {"ok": False, "error": "Requires level 10."}
        if not pet.pawns:
            return {"ok": False, "error": "No captured minds to harvest."}
        with self._lock:
            n = len(pet.pawns)
            gained = n * 2 + U.bonus_souls(pet) * n
            pet.souls += gained
            pet.souls_harvested += gained
            pet.pawns.clear()
            pet.darkness = _clamp(pet.darkness + 4)
            pet.psyche += n * 3
            self._clamp_psyche()
        self._hold_mood("harvesting", 6)
        self._award(10 + n * 5)
        self.emit("harvest", f"{P.pick(P.PHRASES['harvest'])} (+{gained} souls)")
        self.coach_after("deed", "deed:harvest")
        self._check_achievements()
        self._after_action()
        return {"ok": True, "summary": f"Harvested {n} minds for {gained} souls.",
                "souls": gained}

    # -- academy / learning -------------------------------------------- #
    def _acad(self) -> Dict[str, Any]:
        a = self.pet.academy
        for k, dv in (("completed", []), ("introduced", []), ("knowledge_xp", 0),
                      ("quiz_correct", 0), ("quiz_total", 0)):
            a.setdefault(k, dv if not isinstance(dv, list) else list(dv))
        return a

    def introduce_lesson(self, lesson_id: str) -> None:
        """Mark a lesson as 'seen' (a teachable moment) without completing it."""
        a = self._acad()
        if lesson_id not in a["introduced"]:
            a["introduced"].append(lesson_id)

    def answer_lesson(self, lesson_id: str, choice: int) -> Dict[str, Any]:
        les = ACAD.get(lesson_id)
        if les is None:
            return {"ok": False, "error": f"No such lesson: {lesson_id}"}
        a = self._acad()
        quiz = les["quiz"]
        correct = int(choice) == quiz["answer"]
        already = lesson_id in a["completed"]
        with self._lock:
            a["quiz_total"] += 1
            if correct:
                a["quiz_correct"] += 1
                if not already:
                    a["completed"].append(lesson_id)
                    a["knowledge_xp"] += les["xp"]
        if correct and not already:
            self._award(les["xp"])
            before = ACAD.tier_for(len(a["completed"]) - 1)[1]
            after = ACAD.tier_for(len(a["completed"]))[1]
            self.emit("learn", f"Lesson passed: {les['title']} (+{les['xp']} knowledge).")
            if after != before:
                self.emit("rank_up", f"ACADEMY RANK UP — you are now a {after}.")
            self.coach_after("lesson", "learn:" + lesson_id)
        self._after_action()
        return {"ok": True, "correct": correct,
                "answer": quiz["answer"], "explain": quiz["explain"],
                "completed": lesson_id in a["completed"],
                "already": already}

    # -- security posture ---------------------------------------------- #
    def record_posture(self, component: str, data: Dict[str, Any]) -> None:
        with self._lock:
            entry = dict(data)
            entry["t"] = time.time()
            self.pet.posture[component] = entry

    # -- augments ------------------------------------------------------ #
    def buy_augment(self, aid: str) -> Dict[str, Any]:
        res = U.buy(self.pet, aid)
        if res.get("ok"):
            self._clamp_psyche()
            self.emit("upgrade", f"{P.pick(P.PHRASES['upgrade'])} "
                                 f"[{res['augment']} T{res['tier']}]")
            self.coach_after("augment", "buy:" + aid)
            self._check_achievements()
            self._after_action()
        return res

    # -- XP / levelling ------------------------------------------------ #
    def award_xp(self, amount: int, reason: str = "") -> List[int]:
        return self._award(amount, reason)

    def _award(self, amount: int, reason: str = "") -> List[int]:
        leveled: List[int] = []
        with self._lock:
            pet = self.pet
            pet.xp += int(amount * U.xp_mult(pet))
            while pet.xp >= xp_to_next(pet.level):
                pet.xp -= xp_to_next(pet.level)
                pet.level += 1
                pet.best_level = max(pet.best_level, pet.level)
                pet.psyche += 20
                pet.sanity = _clamp(pet.sanity + 8)
                self._clamp_psyche()
                leveled.append(pet.level)
        for lvl in leveled:
            self._on_level_up(lvl)
        return leveled

    def _on_level_up(self, level: int) -> None:
        from .spells import SPELLS
        newly = []
        with self._lock:
            for sid, spell in SPELLS.items():
                if spell.min_level <= level and sid not in self.pet.unlocked_spells:
                    self.pet.unlocked_spells.append(sid)
                    newly.append(spell.name)
        rank = rank_for(level)
        if level == P.LEVEL_CAP:
            self._hold_mood("ascending", 8)
            self.emit("ascend", P.pick(P.PHRASES["ascend_cap"]), level=level, rank=rank)
        else:
            self._hold_mood("ascending", 4)
            stg = ST.stage_for(level)
            self.emit("levelup",
                      f"LEVEL {level} — {rank} // evolved into {stg['label']}. "
                      f"{P.pick(P.PHRASES['levelup'])}",
                      level=level, rank=rank, stage=stg["label"])
        for nm in newly:
            self.emit("unlock", f"New spell learned: {nm}.")
        self._check_achievements()

    # -- mood / speech ------------------------------------------------- #
    def _refresh_mood(self) -> None:
        if time.time() < self._hold_until:
            return
        self.pet.mood = self._auto_mood()

    def _auto_mood(self) -> str:
        pet = self.pet
        cap = self.psyche_cap()
        if pet.energy < 10:
            cluster = "energy"
        elif pet.sanity < 15:
            cluster = "broken"
        elif pet.hunger < 16:
            cluster = "hunger"
        elif pet.energy < 24:
            cluster = "energy"
        elif pet.sanity < 32:
            cluster = "sanity"
        elif pet.focus < 22:
            cluster = "focus"
        elif pet.psyche >= 0.9 * cap:
            cluster = "power"
        else:
            traits = self.profile.get("traits", {}) if self.profile else {}
            dark_bias = int(traits.get("darkness", 45))
            warm_bias = int(traits.get("warmth", 50))
            if pet.darkness >= 65:
                pool = ["dark", "dark", "smug"]
            elif pet.darkness >= 35:
                pool = ["idle", "dark", "smug"]
            elif pet.sanity > 70 and pet.hunger > 55 and pet.energy > 55:
                pool = ["content", "idle", "smug"]
            else:
                pool = ["idle", "idle", "content"]
            # personality tilts the pool toward the keeper's chosen temperament
            if dark_bias >= 65:
                pool += ["dark"]
            if warm_bias >= 65:
                pool += ["content"]
            cluster = random.choice(pool)
        names = P.CLUSTERS.get(cluster) or P.CLUSTERS["idle"]
        return random.choice(names)

    def _maybe_speak(self, force: bool = False) -> None:
        if force or (time.time() % 40) < 1.2:
            base = P.mood_phrase(self.pet.mood)
            try:
                self.pet.last_phrase = PERSONA.flavor(
                    base, self.pet.mood, self.profile, self.pet.affinities)
            except Exception:
                self.pet.last_phrase = base

    def speak(self) -> str:
        self._maybe_speak(force=True)
        return self.pet.last_phrase

    # -- persona / personalization ------------------------------------- #
    def reload_profile(self) -> None:
        self.profile = PERSONA.load(self.home)

    def set_profile(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            prof = PERSONA.load(self.home)
            for k, v in (updates or {}).items():
                if k == "traits" and isinstance(v, dict):
                    prof.setdefault("traits", {})
                    for tk, tv in v.items():
                        if tk in PERSONA.TRAITS:
                            try:
                                prof["traits"][tk] = max(0, min(100, int(tv)))
                            except (TypeError, ValueError):
                                pass
                elif k in ("keeper", "pronouns", "experience", "style",
                           "mantis_name", "interests", "configured"):
                    prof[k] = v
            PERSONA.save(self.home, prof)
            self.profile = prof
            if prof.get("mantis_name"):
                self.pet.name = prof["mantis_name"]
        self.emit("persona", "I feel you more clearly now. I adjust.")
        self._after_action()
        return prof

    # -- inner AI / coaching ------------------------------------------- #
    def coach_after(self, cat: str, key: str) -> None:
        """Observe an action and regenerate adaptive suggestions."""
        try:
            COACH.observe(self.pet, cat, key)
            sugs = COACH.suggest(self, cat, key)
            if sugs:
                self.emit("coach", "I sense your next step: " + sugs[0]["text"])
        except Exception:
            pass

    def note_affinity(self, spell_id: str) -> None:
        interest = PERSONA.spell_interest(spell_id)
        if interest:
            with self._lock:
                self.pet.affinities[interest] = self.pet.affinities.get(interest, 0) + 1

    def read_keeper(self) -> str:
        return PERSONA.reading(self.profile, self.pet.affinities,
                               {"spells_cast": self.pet.spells_cast})

    # -- idle modes / activities --------------------------------------- #
    def set_mode(self, mode: str) -> str:
        mode = "passive" if str(mode).lower().startswith("p") else "active"
        with self._lock:
            self.pet.idle_mode = mode
        self.emit("mode",
                  "I withdraw into passive watch — I act only when you ask."
                  if mode == "passive"
                  else "I am active now. I will hunt the ether on my own.",
                  mode=mode)
        self._after_action()
        return mode

    def toggle_mode(self) -> str:
        return self.set_mode("active" if self.pet.idle_mode == "passive" else "passive")

    def run_activity(self, key: str, auto: bool = False) -> Dict[str, Any]:
        """Perform one of the 50 stage activities on demand."""
        return ACT.run(self, key, auto=auto)

    def auto_activity(self) -> None:
        """Background hook. ACTIVE: autonomously perform an activity it has grown
        into. PASSIVE: stay quiet (no actions; gentle psyche recovery via tick)."""
        pet = self.pet
        if pet.idle_mode == "passive":
            return
        if pet.mood == "sleeping" or pet.psyche < 14:
            return
        key = ACT.auto_pick(self)
        if key:
            try:
                ACT.run(self, key, auto=True)
            except Exception:
                pass

    def _after_action(self) -> None:
        self._refresh_mood()
        self._maybe_speak(force=True)
        self.save()

    # -- achievements -------------------------------------------------- #
    def _check_achievements(self) -> None:
        pet = self.pet
        checks = [
            ("first_contact", pet.networks_sensed >= 1, "First Contact — a mind in the ether."),
            ("full_coven", len(pet.unlocked_spells) >= 6, "Full Coven — six spells mastered."),
            ("first_blood", pet.kills >= 1, "First Severing — a mind silenced."),
            ("abductor", pet.kidnappings >= 10, "Abductor — ten minds taken."),
            ("puppeteer", pet.possessions >= 25, "Puppeteer — 25 bodies worn."),
            ("reaper", pet.souls_harvested >= 100, "Reaper — 100 souls harvested."),
            ("dread_lord", pet.darkness >= 80, "Dread Lord — darkness consumes you."),
            ("ascended", pet.level >= 50, "Ascended — halfway to the mask."),
            ("the_mantis", pet.level >= P.LEVEL_CAP, "MANTIS — the most powerful psychic."),
            ("augmented", sum(pet.augments.values()) >= 10, "Augmented — ten upgrades carved."),
        ]
        for key, cond, text in checks:
            if cond and key not in pet.achievements:
                pet.achievements.append(key)
                self.emit("achievement", "★ " + text)

    # -- snapshot ------------------------------------------------------ #
    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            pet = self.pet
            need = xp_to_next(pet.level)
            cap = self.psyche_cap()
            meta = P.MOODS.get(pet.mood, P.MOODS["watching"])
            stg = ST.stage_for(pet.level)
            return {
                "name": pet.name,
                "level": pet.level,
                "level_cap": P.LEVEL_CAP,
                "rank": rank_for(pet.level),
                "stage": {"lvl": stg["lvl"], "key": stg["key"], "label": stg["label"],
                          "phrase": stg["phrase"], "max_stage": ST.MAX_STAGE},
                "idle_mode": pet.idle_mode,
                "activity": {"last": pet.last_activity,
                             "run": getattr(pet, "activities_run", 0),
                             "counts": dict(getattr(pet, "activity_counts", {}))},
                "activities": ACT.catalog(pet.level),
                "xp": pet.xp,
                "xp_to_next": need,
                "xp_pct": round(100 * pet.xp / need, 1) if need else 0,
                "mood": pet.mood,
                "mood_dark": meta["dark"],
                "face": P.face(pet.mood),
                "face_web": meta["web"],
                "sprite": {"eyes": meta["eyes"], "aura": meta["aura"],
                           "pose": meta["pose"], "fx": meta["fx"]},
                "phrase": pet.last_phrase,
                "needs": {"hunger": round(pet.hunger, 1), "energy": round(pet.energy, 1),
                          "focus": round(pet.focus, 1), "sanity": round(pet.sanity, 1)},
                "psyche": round(pet.psyche, 1),
                "psyche_max": round(cap, 1),
                "psyche_pct": round(100 * pet.psyche / cap, 1) if cap else 0,
                "souls": pet.souls,
                "darkness": round(pet.darkness, 1),
                "infamy": pet.infamy,
                "age": _age_str(time.time() - pet.born),
                "age_seconds": int(time.time() - pet.born),
                "stats": {
                    "networks_sensed": pet.networks_sensed, "devices_read": pet.devices_read,
                    "spells_cast": pet.spells_cast, "sessions": pet.sessions,
                    "feedings": pet.feedings, "meditations": pet.meditations,
                    "pets_received": pet.pets_received, "best_level": pet.best_level,
                    "kills": pet.kills, "kidnappings": pet.kidnappings,
                    "possessions": pet.possessions, "hauntings": pet.hauntings,
                    "souls_harvested": pet.souls_harvested,
                },
                "posture": POST.compute(pet.posture),
                "academy": ACAD.summary(pet.academy),
                "keeper": (self.profile.get("keeper") or "keeper"),
                "persona": {
                    "keeper": self.profile.get("keeper", "keeper"),
                    "experience": self.profile.get("experience", "beginner"),
                    "interests": list(self.profile.get("interests", [])),
                    "style": self.profile.get("style", "poetic"),
                    "traits": dict(self.profile.get("traits", {})),
                    "configured": bool(self.profile.get("configured", False)),
                    "affinities": dict(pet.affinities),
                    "top_affinity": PERSONA.top_affinity(pet.affinities),
                },
                "reading": self.read_keeper(),
                "coach": COACH.summary(pet),
                "unlocked_spells": list(pet.unlocked_spells),
                "achievements": list(pet.achievements),
                "augments": pet.augments,
                "pawns": pet.pawns[-30:],
                "inventory": pet.inventory[-30:],
                "known_networks": pet.known_networks[-40:],
                "known_devices": pet.known_devices[-40:],
                "log": pet.log[-80:],
            }


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _event(kind: str, text: str, **extra: Any) -> Dict[str, Any]:
    ev = {"t": time.time(), "ts": time.strftime("%H:%M:%S"), "kind": kind, "text": text}
    ev.update(extra)
    return ev


def _age_str(seconds: float) -> str:
    seconds = int(max(0, seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
