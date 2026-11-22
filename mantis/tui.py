"""Terminal UI — a live, interactive Mantis console (stdlib only)."""

from __future__ import annotations

import os
import sys
import time
from typing import Dict

from . import personality as P
from .engine import Engine
from .spells import SPELLS, cast, autonomous_sense, SpellError

# ANSI
R = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
GREEN = "\033[38;5;46m"; CYAN = "\033[38;5;51m"; MAG = "\033[38;5;201m"
RED = "\033[38;5;196m"; YEL = "\033[38;5;226m"; PUR = "\033[38;5;135m"
GREY = "\033[38;5;245m"; BG = "\033[48;5;234m"


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _bar(val: float, width: int = 20, color: str = GREEN) -> str:
    filled = int(round(width * val / 100))
    return f"{color}{'█' * filled}{DIM}{'░' * (width - filled)}{R}"


def _menu() -> str:
    return (f"{GREY}[f]{R}eed  {GREY}[r]{R}est  {GREY}[m]{R}editate  "
            f"{GREY}[p]{R}et  {GREY}[c]{R}ast  {GREY}[s]{R}peak  "
            f"{GREY}[n]{R}ame  {GREY}[q]{R}uit")


def render(engine: Engine) -> None:
    engine.tick()
    snap = engine.snapshot()
    _clear()
    face = P.face(snap["mood"])
    print(f"{MAG}{BOLD}")
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║            P S Y C H O   M A N T I S                  ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print(R)
    # face + core stats side by side
    face_lines = face.splitlines()
    info = [
        f"{BOLD}{snap['name']}{R}  {DIM}lv{R} {YEL}{snap['level']}{R}  {PUR}{snap['rank']}{R}",
        f"{DIM}age{R} {snap['age']}   {DIM}mood{R} {CYAN}{snap['mood']}{R}",
        f"{DIM}XP {R}{_bar(snap['xp_pct'], 18, YEL)} {snap['xp']}/{snap['xp_to_next']}",
        f"{DIM}PSY{R}{_bar(snap['psyche'], 18, MAG)} {int(snap['psyche'])}",
        "",
        f"{DIM}hunger{R} {_bar(snap['needs']['hunger'], 14, GREEN)}",
        f"{DIM}energy{R} {_bar(snap['needs']['energy'], 14, CYAN)}",
        f"{DIM}focus {R} {_bar(snap['needs']['focus'], 14, YEL)}",
        f"{DIM}sanity{R} {_bar(snap['needs']['sanity'], 14, RED)}",
    ]
    rows = max(len(face_lines), len(info))
    for i in range(rows):
        left = face_lines[i] if i < len(face_lines) else ""
        right = info[i] if i < len(info) else ""
        print(f"{PUR}{left:<28}{R}{right}")
    print()
    print(f'  {CYAN}"{snap["phrase"]}"{R}')
    print()
    # recent log
    print(f"  {DIM}── ether log ──{R}")
    for ev in snap["log"][-6:]:
        print(f"  {DIM}{ev['ts']}{R} {ev['text'][:60]}")
    print()
    print("  " + _menu())


def _prompt(engine: Engine, text: str) -> str:
    try:
        return input(text)
    except (EOFError, KeyboardInterrupt):
        return "q"


def _cast_menu(engine: Engine) -> None:
    snap = engine.snapshot()
    _clear()
    print(f"{MAG}{BOLD}  SPELLBOOK{R}   PSYCHE: {MAG}{int(snap['psyche'])}{R}\n")
    ids = []
    for i, (sid, sp) in enumerate(sorted(SPELLS.items(),
                                         key=lambda kv: kv[1].min_level), 1):
        unlocked = sid in snap["unlocked_spells"] or sp.min_level <= snap["level"]
        lock = "" if unlocked else f"{RED}🔒lv{sp.min_level}{R}"
        color = "" if unlocked else DIM
        print(f"  {color}{i}. {sp.glyph} {sp.name:<20}{R} "
              f"{DIM}cost {sp.psyche_cost}  +{sp.xp}xp{R} {lock}")
        print(f"     {DIM}{sp.desc[:66]}{R}")
        ids.append(sid)
    print(f"\n  {GREY}pick a number, or [b]ack{R}")
    choice = _prompt(engine, "  > ").strip().lower()
    if choice in ("b", "q", ""):
        return
    try:
        sid = ids[int(choice) - 1]
    except Exception:
        return
    try:
        res = cast(engine, sid)
        _clear()
        print(f"\n  {MAG}{res.get('spell')}{R}\n")
        print(f'  {CYAN}{res.get("summary")}{R}\n')
        for item in res.get("items", [])[:15]:
            print(f"    {GREY}{item}{R}")
        input(f"\n  {DIM}(enter to return){R}")
    except SpellError as e:
        input(f"\n  {RED}{e}{R}  {DIM}(enter){R}")


def run(engine: Engine) -> None:
    print(f"{MAG}{BOLD}")
    for line in P.INTRO_LINES:
        print("  " + line)
        time.sleep(0.05)
    print(R)
    time.sleep(0.3)
    last_auto = 0.0
    while True:
        render(engine)
        # autonomous sensing in the background of the loop
        if time.time() - last_auto > 30:
            autonomous_sense(engine)
            last_auto = time.time()
        engine.save()
        choice = _prompt(engine, "\n  > ").strip().lower()
        if choice in ("q", "quit", "exit"):
            engine.save()
            print(f"\n  {MAG}The mask goes dark. I am always listening...{R}\n")
            return
        elif choice == "f":
            engine.feed()
        elif choice == "r":
            engine.rest()
        elif choice == "m":
            engine.meditate()
        elif choice == "p":
            engine.pet_it()
        elif choice == "s":
            engine.speak()
        elif choice == "c":
            _cast_menu(engine)
        elif choice == "n":
            name = _prompt(engine, "  new name > ").strip()
            if name:
                engine.rename(name)
