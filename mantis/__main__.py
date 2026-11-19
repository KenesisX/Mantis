"""Command-line entry point.

Usage:
    python -m mantis            # launch web dashboard (default)
    python -m mantis web        # web dashboard
    python -m mantis tui        # live terminal pet
    python -m mantis status     # one-shot status print
    python -m mantis cast <id>  # cast a spell once from the shell
    python -m mantis feed|rest|meditate|pet
    python -m mantis spells      # list the spellbook
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from . import __version__
from .engine import Engine
from .spells import SPELLS, cast, spell_catalog, SpellError


def _mod_ver(mod: str) -> str:
    try:
        m = __import__(mod)
        return getattr(m, "__version__", "ok")
    except Exception:
        return "missing"


def _detect_driver() -> str:
    for mod in ("waveshare_epd.epd2in13_V4", "waveshare_epd.epd2in13_V3",
                "waveshare_epd.epd2in13_V2", "waveshare_epd.epd2in13"):
        try:
            __import__(mod)
            return "waveshare (" + mod.split(".")[-1] + ")"
        except Exception:
            continue
    try:
        __import__("inky")
        return "inky"
    except Exception:
        return "none (preview/PNG fallback)"


def _selfcheck(engine) -> int:
    from . import personality as P, stages as ST, spells, upgrades, config as CFG
    checks = []

    def ok(name, cond, detail=""):
        checks.append((name, bool(cond), detail))

    # modules
    mods_ok = True
    for m in ("engine", "personality", "stages", "activities", "spells", "rf_spells",
              "defense_spells", "posture", "academy", "persona", "color", "fleet", "coach", "upgrades", "buttons", "power", "config", "menu",
              "server", "eink", "tui"):
        try:
            __import__(f"mantis.{m}")
        except Exception as exc:
            mods_ok = False
            ok(f"import {m}", False, str(exc))
    ok("all modules import", mods_ok)

    # data integrity
    ok("70 moods", len(P.MOODS) == 70, f"{len(P.MOODS)}")
    ok("50 stages", len(ST.STAGES) == 50, f"{len(ST.STAGES)}")
    from . import activities as ACT
    ok("50 activities", len(ACT.catalog(100)) == 50
       and all(ACT.spec(k) for k in ACT.all_keys()), f"{len(ACT._A)} wired")
    ok("spellbook", len(spells.SPELLS) >= 8, f"{len(spells.SPELLS)}")
    ok("augments", len(upgrades.AUGMENTS) >= 8, f"{len(upgrades.AUGMENTS)}")
    ok("cap = MANTIS", P.rank_for(100) == "MANTIS")

    # config + state
    ok("config loads", isinstance(CFG.load(engine.home), dict))
    try:
        engine.save()
        snap = engine.snapshot()
        ok("state save/snapshot", "stage" in snap and "level" in snap)
    except Exception as exc:
        ok("state save/snapshot", False, str(exc))

    # rendering (needs Pillow)
    pil = _mod_ver("PIL")
    if pil != "missing":
        try:
            from . import eink
            snap = engine.snapshot()
            eink.render_splash()
            eink.render_screen(snap)
            eink.render_stage_card(ST.stage_for(1), 1)
            eink.render_message("TEST")
            for s in ST.STAGES[:3]:
                eink.render_stage_card(s, s["lvl"])
            ok("e-ink rendering (Pillow)", True, f"Pillow {pil}")
        except Exception as exc:
            ok("e-ink rendering (Pillow)", False, str(exc))
    else:
        checks.append(("e-ink rendering", None, "Pillow not installed (web/tui still work)"))

    print(f"MANTIS {__version__} — selfcheck\n")
    failed = 0
    for name, passed, detail in checks:
        if passed is None:
            mark = "WARN"
        elif passed:
            mark = "PASS"
        else:
            mark = "FAIL"; failed += 1
        line = f"  [{mark}] {name}"
        if detail:
            line += f"  — {detail}"
        print(line)
    print(f"\ndriver: {_detect_driver()}")
    try:
        from .power import read_battery
        b = read_battery(engine.home)
        print(f"battery source: {b['source'] + ' ' + str(int(b['percent'])) + '%' if b else 'none'}")
    except Exception:
        pass
    print(f"\n{'ALL CRITICAL CHECKS PASSED' if failed == 0 else str(failed) + ' CHECK(S) FAILED'}")
    return 0 if failed == 0 else 1


def _ask(prompt, default, choices=None, cast=str):
    hint = f" [{'/'.join(str(c) for c in choices)}]" if choices else ""
    while True:
        try:
            raw = input(f"  {prompt}{hint} ({default}): ").strip()
        except EOFError:
            return default          # no input stream -> default
        if raw == "":
            return default
        if choices and raw.lower() not in [str(c).lower() for c in choices]:
            print("    choose one of:", ", ".join(str(c) for c in choices)); continue
        try:
            return cast(raw)
        except Exception:
            print("    invalid value"); continue


def _yesno(prompt, default):
    try:
        raw = input(f"  {prompt}? [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    except EOFError:
        return default
    return default if raw == "" else raw.startswith("y")


def _ask_multi(prompt, options, default_keys):
    keys = list(options.keys())
    print(f"  {prompt}")
    for i, k in enumerate(keys):
        mark = "x" if k in (default_keys or []) else " "
        print(f"    [{mark}] {i+1}. {options[k]['label']}")
    try:
        raw = input("  pick numbers (comma-separated), Enter to keep: ").strip()
    except EOFError:
        return list(default_keys or [])
    if not raw:
        return list(default_keys or [])
    out = []
    for tok in raw.replace(" ", "").split(","):
        if tok.isdigit() and 1 <= int(tok) <= len(keys):
            out.append(keys[int(tok) - 1])
    return out


MANTIS_BANNER = r"""
   __  __   _   _  _  _____ ___ ___
  |  \/  | /_\ | \| ||_   _|_ _/ __|
  | |\/| |/ _ \| .` |  | |  | |\__ \
  |_|  |_/_/ \_\_|\_|  |_| |___|___/   behind the mask, a mind awakens
"""


def _install_wizard(engine) -> int:
    from . import persona as PERSONA
    prof = dict(engine.profile)
    print(MANTIS_BANNER)
    print("  A new mind stirs behind the mask. Let it learn you...\n")

    keeper = _ask("your name or handle", prof.get("keeper", "keeper"))
    pron = _ask("your pronouns (optional)", prof.get("pronouns", "they"))
    exp = _ask("your experience level", prof.get("experience", "beginner"),
               choices=["beginner", "intermediate", "pro"])
    interests = _ask_multi("what draws you? (MANTIS will attune to these)",
                           PERSONA.INTERESTS, prof.get("interests", []))
    mname = _ask("what shall you call MANTIS", prof.get("mantis_name", "Mantis"))

    print("\n  Now shape his mind:")
    preset = _ask("  temperament preset", "balanced",
                  choices=list(PERSONA.TRAIT_PRESETS.keys()) + ["custom"])
    if preset == "custom":
        traits = {}
        for t in PERSONA.TRAITS:
            traits[t] = _ask(f"    {t} (0-100)",
                             PERSONA.TRAIT_PRESETS["balanced"][t], cast=int)
    else:
        traits = dict(PERSONA.TRAIT_PRESETS[preset])
    style = _ask("  speaking style", prof.get("style", "poetic"),
                 choices=["poetic", "plain", "clinical"])

    prof.update({"keeper": keeper, "pronouns": pron, "experience": exp,
                 "interests": interests, "mantis_name": mname, "traits": traits,
                 "style": style, "configured": True})
    engine.set_profile(prof)

    print("\n  ...the gas-mask lenses flicker to life.\n")
    print("  \"" + PERSONA.greeting(engine.profile) + "\"")
    print("  \"" + engine.read_keeper() + "\"\n")

    if _yesno("set up the e-ink handheld hardware now too", False):
        _setup_wizard(engine)

    print("\n  MANTIS is bound to you. Wake him:")
    print("    python3 -m mantis web      (browser)")
    print("    python3 -m mantis eink     (handheld)")
    print("    python3 -m mantis read     (let him read you anytime)\n")
    return 0


def _setup_wizard(engine) -> int:
    from . import config as CFG
    tty = sys.stdin.isatty()
    print("\n=== MANTIS setup ===")
    print("Press Enter to accept each default.\n" if tty
          else "(non-interactive input — writing sensible defaults)\n")

    driver = _ask("e-ink panel driver", "auto", choices=["auto", "waveshare", "inky"])
    rotate = _ask("screen rotation", 0, choices=[0, 90, 180, 270], cast=int)
    interval = _ask("status refresh seconds", 30, cast=int)
    splash = _yesno("show the boot splash", True)
    animate = _yesno("idle float animation", True)
    slideshow = _yesno("idle stage slideshow", True)
    poweroff = _yesno("enable the hold cast+pet power-off combo", True)

    buttons_on = _yesno("enable GPIO buttons", True)
    pins = {}
    defaults = {"feed": 5, "meditate": 6, "pet": 16, "cast": 24, "deed": 26}
    if buttons_on and tty and _yesno("customise button pins", False):
        for b, dft in defaults.items():
            pins[b] = _ask(f"GPIO pin for {b}", dft, cast=int)
    else:
        pins = dict(defaults)

    batt = _ask("battery source", "auto",
                choices=["auto", "none", "pisugar", "file", "command"])
    batt_cmd = _ask("battery command", "") if batt == "command" else ""

    host = _ask("web host", "127.0.0.1")
    port = _ask("web port", 8777, cast=int)

    eink = dict(interval=interval, rotate=rotate, driver=driver, buttons=buttons_on,
                animate=animate, splash=splash, slideshow=slideshow,
                slideshow_interval=25, low_battery=20, sleep_below=6,
                poweroff_combo=poweroff, poweroff_hold=3)
    text = CFG.build_toml(eink, pins, {"host": host, "port": port},
                          {"source": batt, "command": batt_cmd})
    path = CFG.write(engine.home, text)
    print(f"\nWrote config -> {path}")
    print("Start it with:  python3 -m mantis eink      (handheld)")
    print("            or: python3 -m mantis web       (browser)")
    return 0


def _apply_config_defaults(ap, cfg) -> None:
    """Map config.toml values onto the argparse defaults."""
    e = cfg.get("eink", {}) if cfg else {}
    w = cfg.get("web", {}) if cfg else {}
    d = {}
    for k in ("interval", "rotate", "driver", "slideshow_interval",
              "low_battery", "sleep_below", "poweroff_hold"):
        if k in e:
            d[k] = e[k]
    for flag, key in (("no_buttons", "buttons"), ("no_animate", "animate"),
                      ("no_splash", "splash"), ("no_slideshow", "slideshow"),
                      ("no_poweroff", "poweroff_combo")):
        if key in e:
            d[flag] = not bool(e[key])
    if "host" in w:
        d["host"] = w["host"]
    if "port" in w:
        d["port"] = w["port"]
    if d:
        ap.set_defaults(**d)


def main(argv=None) -> int:
    # make piping into head/less clean (ignore SIGPIPE where supported)
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (ImportError, AttributeError, ValueError):
        pass
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="mantis",
                                 description="MANTIS — a psychic Tamagotchi (Mantis).")
    ap.add_argument("command", nargs="?", default="web",
                    help="web | eink | color | theme | slice | sprites | install | "
                         "read | coach | persona | fleet | agent | setup | faces | gallery | stages | config | "
                         "version | selfcheck | posture | learn | academy | tui | "
                         "status | spells | activities | do | mode | cast | feed | rest | meditate | pet | "
                         "possess | kidnap | sever | haunt | harvest | shop | buy")
    ap.add_argument("arg", nargs="?", default=None, help="id for 'cast' / 'buy'")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8777)
    ap.add_argument("--home", default=None, help="state directory")
    ap.add_argument("--interval", type=int, default=30, help="eink refresh seconds")
    ap.add_argument("--rotate", type=int, default=0, help="eink rotation (0/90/180/270)")
    ap.add_argument("--driver", default="auto", help="eink driver: auto|waveshare|inky")
    ap.add_argument("--out", default=None, help="output dir for 'faces'")
    ap.add_argument("--rows", type=int, default=5, help="slice: grid rows")
    ap.add_argument("--cols", type=int, default=5, help="slice: grid cols")
    ap.add_argument("--start", type=int, default=1, help="slice: first level/index")
    ap.add_argument("--label-pct", type=float, default=0.16,
                    help="slice: fraction of each cell bottom to trim (baked-in label)")
    ap.add_argument("--trim-pct", type=float, default=0.03,
                    help="slice: fraction of each cell border to trim")
    ap.add_argument("--kind", default="stage", help="slice target: stage | mood")
    ap.add_argument("--threshold", type=int, default=128, help="slice: b/w threshold")
    ap.add_argument("--blank-badge", dest="blank_badge", action="store_true", default=True,
                    help="slice: white-out a baked-in LV badge (top-left)")
    ap.add_argument("--keep-badge", dest="blank_badge", action="store_false",
                    help="slice: keep the baked-in top-left badge")
    ap.add_argument("--no-buttons", action="store_true", help="disable GPIO buttons")
    ap.add_argument("--no-animate", action="store_true", help="disable idle bob")
    ap.add_argument("--pins", default=None,
                    help="button pins, e.g. feed=5,meditate=6,pet=16,cast=24,deed=26")
    ap.add_argument("--low-battery", type=int, default=20,
                    help="percent below which to enter low-power mode")
    ap.add_argument("--sleep-below", type=int, default=6,
                    help="percent below which to deep-sleep (hibernate)")
    ap.add_argument("--no-splash", action="store_true", help="skip the boot splash")
    ap.add_argument("--no-slideshow", action="store_true",
                    help="disable the idle stage slideshow")
    ap.add_argument("--slideshow-interval", type=int, default=25,
                    help="seconds between idle stage cards")
    ap.add_argument("--no-poweroff", action="store_true",
                    help="disable the hold cast+pet power-off combo")
    ap.add_argument("--poweroff-hold", type=float, default=3.0,
                    help="seconds to hold the power-off combo")
    ap.add_argument("--force", action="store_true", help="for 'config init': overwrite")
    ap.add_argument("--version", action="version", version=f"MANTIS {__version__}")

    # ---- apply ~/.mantis/config.toml as defaults (CLI flags still override) --- #
    from . import config as CFG
    from .engine import default_home
    pre, _ = ap.parse_known_args(argv)
    home = pre.home or default_home()
    cfg = CFG.load(home)
    _apply_config_defaults(ap, cfg)
    ns = ap.parse_args(argv)

    engine = Engine(home=ns.home)
    cmd = ns.command.lower()

    if cmd == "install":
        return _install_wizard(engine)

    if cmd == "setup":
        return _setup_wizard(engine)

    if cmd == "read":
        print(engine.read_keeper())
        return 0

    if cmd in ("coach", "suggest"):
        from . import coach as CO
        engine.tick()
        c = engine.snapshot()["coach"]
        print(f"Your style: {c['style']} — {CO.STYLES.get(c['style'], '')}")
        print(f"({c['actions_seen']} actions observed)\n")
        sugs = CO.suggest(engine)
        if not sugs:
            print("Act, and I will show you your next step.")
            return 0
        print("The inner mind suggests:")
        for s in sugs:
            t, i = s["cmd"]["type"], s["cmd"].get("id", "")
            line = {"cast": f"mantis cast {i}", "action": f"mantis {i}",
                    "deed": f"mantis {i}", "buy": f"mantis buy {i}",
                    "learn": f"mantis learn {i}", "harvest": "mantis harvest"}.get(t, "")
            tag = " 📖" if s.get("teach") else ""
            print(f"  → {s['text']}{tag}")
            if line:
                print(f"      $ {line}")
        return 0

    if cmd == "fleet":
        from . import fleet, config as CFG
        if ns.arg == "key":            # mantis fleet key <value>  (set shared secret)
            if ns.out:
                CFG.update(engine.home, fleet={"key": ns.out})
                print("Fleet key set. Devices using this key may report to this hub.")
            else:
                k = (CFG.load(engine.home).get("fleet", {}) or {}).get("key", "")
                print(f"Fleet key: {'(set)' if k else '(none — set with: mantis fleet key --out <secret>)'}")
            return 0
        rows = fleet.roster(engine.home)
        if not rows:
            print("No devices in the fleet yet.")
            print("On each device you own, run:  mantis agent --hub http://<hub-ip>:8777 --pins ''")
            print("(set a shared key first:  mantis fleet key --out <secret>)")
            return 0
        print(f"{'DEVICE':<20} {'PLAT':<16} {'LV':>3} {'POS':>3} {'BATT':>5} {'UP':>6}  STATUS")
        for d in rows:
            dot = "● online" if d["online"] else f"○ {fleet.fmt_uptime(d['ago'])} ago"
            batt = f"{d['battery']}%" if d.get("battery") is not None else "—"
            print(f"{(d.get('name') or '?')[:20]:<20} {(d.get('platform') or '?')[:16]:<16} "
                  f"{str(d.get('level') or '?'):>3} {str(d.get('posture_grade') or '?'):>3} "
                  f"{batt:>5} {fleet.fmt_uptime(d.get('uptime_s')):>6}  {dot}")
        return 0

    if cmd == "agent":
        import json as _json
        import urllib.request
        from . import fleet, config as CFG
        hub = ns.hub or (CFG.load(engine.home).get("fleet", {}) or {}).get("hub")
        if not hub:
            print("usage: mantis agent --hub http://<hub-ip>:8777 [--interval 60]")
            return 2
        key = ns.key or (CFG.load(engine.home).get("fleet", {}) or {}).get("key", "")
        url = hub.rstrip("/") + "/api/fleet/report"
        print(f"[agent] reporting this device to {hub} every {ns.interval}s. Ctrl+C to stop.")
        try:
            while True:
                engine.tick()
                payload = _json.dumps({"key": key, "device": fleet.gather_self(engine)}).encode()
                try:
                    req = urllib.request.Request(url, data=payload,
                                                 headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=8) as r:
                        ok = _json.load(r).get("ok")
                    print(f"[agent] reported ({'ok' if ok else 'rejected'})")
                except Exception as e:
                    print(f"[agent] report failed: {e}")
                engine.save()
                time.sleep(max(15, ns.interval))
        except KeyboardInterrupt:
            print("\n[agent] stopped.")
        return 0

    if cmd == "theme":
        from . import config as CFG
        valid = ("red", "mono", "green", "amber")
        cur = (CFG.load(engine.home).get("web", {}) or {}).get("theme", "red")
        if ns.arg:
            if ns.arg not in valid:
                print(f"Unknown theme '{ns.arg}'. Choose: {', '.join(valid)}")
                return 2
            CFG.update(engine.home, web={"theme": ns.arg})
            print(f"Theme set to '{ns.arg}'. (web + color display)")
        else:
            print(f"Current theme: {cur}")
            print(f"Available: {', '.join(valid)}   —  set with: mantis theme <name>")
        return 0

    if cmd == "slice":
        if not ns.arg:
            print("usage: mantis slice <sheet.png> [--rows 5 --cols 5 --start 1 "
                  "--kind stage|mood --label-pct 0.16]")
            return 2
        try:
            from PIL import Image
            from . import eink, stages as ST, personality as P
        except Exception as e:
            print(f"Slicing needs Pillow: {e}")
            return 1
        if not os.path.exists(ns.arg):
            print(f"No such sheet: {ns.arg}")
            return 1
        outdir = ns.out or eink.sprite_dir()
        os.makedirs(outdir, exist_ok=True)
        img = Image.open(ns.arg).convert("L")
        cw, ch = img.width / ns.cols, img.height / ns.rows
        # key list for naming
        if ns.kind == "stage":
            keys = [s["key"] for s in ST.STAGES]
            prefix = "stage_"
        else:
            keys = list(P.MOODS.keys())
            prefix = "mood_"
        idx = ns.start - 1
        n = 0
        for r in range(ns.rows):
            for c in range(ns.cols):
                if idx >= len(keys):
                    break
                tx, ty = cw * ns.trim_pct, ch * ns.trim_pct
                box = (int(c * cw + tx), int(r * ch + ty),
                       int((c + 1) * cw - tx),
                       int((r + 1) * ch - ty - ch * ns.label_pct))  # drop label bar
                cell = img.crop(box)
                if ns.blank_badge:   # white-out the baked-in "LV n" badge (top-left)
                    from PIL import ImageDraw
                    dd = ImageDraw.Draw(cell)
                    dd.rectangle([0, 0, int(cell.width * 0.32), int(cell.height * 0.15)],
                                 fill=255)
                bw = cell.point(lambda v: 0 if v < ns.threshold else 255, "1")
                name = f"{prefix}{keys[idx]}.png"
                bw.save(os.path.join(outdir, name))
                n += 1
                idx += 1
        # bust the cache so a running loop picks them up
        eink._SPRITE_CACHE.clear()
        print(f"Sliced {n} sprites -> {outdir}")
        print("MANTIS will now use your art on the e-ink, color and web displays.")
        return 0

    if cmd == "sprites":
        from . import eink, stages as ST
        d = eink.sprite_dir()
        print(f"Sprite folder: {d}")
        if not os.path.isdir(d):
            print("(empty — add PNG/BMP files named stage_<key>.png or mood_<name>.png,")
            print(" or run:  mantis slice yoursheet.png)")
            return 0
        files = sorted(f for f in os.listdir(d) if f.lower().endswith((".png", ".bmp", ".gif")))
        print(f"{len(files)} sprite(s) installed:")
        for f in files:
            print("   " + f)
        return 0

    if cmd == "color":
        try:
            from . import color
        except Exception as e:
            print(f"Color renderer needs Pillow (+numpy recommended): {e}")
            return 1
        engine.tick()
        if ns.arg in ("fb", "loop", "fbloop"):
            if ns.arg in ("loop", "fbloop"):
                # continuous HyperPixel daemon: tick, (auto-)act, blit to the framebuffer
                import time as _t
                from .spells import autonomous_sense
                period = max(2, int(ns.interval))
                last_auto = 0.0
                print(f"MANTIS color daemon → /dev/fb0  (every {period}s, Ctrl+C to stop)")
                try:
                    while True:
                        engine.tick()
                        now = _t.time()
                        if now - last_auto > max(period, 40):
                            try:
                                autonomous_sense(engine); engine.auto_activity()
                            except Exception:
                                pass
                            last_auto = now
                        color.blit_framebuffer(color.render(engine.snapshot()))
                        engine.save()
                        _t.sleep(period)
                except KeyboardInterrupt:
                    print("\ncolor daemon stopped.")
                    return 0
            ok = color.blit_framebuffer(color.render(engine.snapshot()))
            print("blitted to /dev/fb0" if ok else "framebuffer blit failed (no /dev/fb0?)")
            return 0 if ok else 1
        outdir = ns.out or os.path.join(engine.home, "color")
        p = color.bake_preview(outdir, engine.snapshot())
        print(f"Wrote color preview -> {p}")
        print("On a HyperPixel, run the web UI full-screen at  http://<ip>:PORT/color")
        print("  e.g.  chromium-browser --kiosk http://localhost:8777/color")
        return 0

    if cmd == "persona":
        from . import persona as PERSONA
        p = engine.profile
        print(f"Keeper: {p.get('keeper')}  ({p.get('pronouns','they')})   "
              f"experience: {p.get('experience')}   style: {p.get('style')}")
        ints = p.get("interests", [])
        print("Interests: " + (", ".join(PERSONA.INTERESTS.get(i, {}).get('label', i)
                                         for i in ints) if ints else "(none yet)"))
        print(f"MANTIS name: {p.get('mantis_name')}")
        print("Traits: " + "  ".join(f"{t}={p.get('traits',{}).get(t,50)}"
                                     for t in PERSONA.TRAITS))
        aff = engine.pet.affinities
        if aff:
            top = PERSONA.top_affinity(aff)
            print(f"Sensed affinity: {PERSONA.INTERESTS.get(top,{}).get('label',top)} "
                  f"(from your casting)")
        if not p.get("configured"):
            print("\nNot personalized yet — run:  python3 -m mantis install")
        return 0

    if cmd == "academy":
        from . import academy as ACAD
        a = ACAD.summary(engine.pet.academy)
        print(f"ACADEMY RANK:  {a['tier']}   (tier {a['tier_idx']+1}/{a['tier_max']})")
        print(f"Lessons: {a['completed']}/{a['total']} ({a['pct']}%)   "
              f"Knowledge XP: {a['knowledge_xp']}   Quiz accuracy: {a['quiz_accuracy']}%\n")
        done = set(a["done_ids"])
        cur_tier = None
        for les in ACAD.LESSONS:
            if les["tier"] != cur_tier:
                cur_tier = les["tier"]
                print(f"  -- Tier {cur_tier} --")
            mark = "✓" if les["id"] in done else " "
            print(f"   [{mark}] {les['id']:<14} {les['title']}")
        if a["next"]:
            print(f"\nNext up:  mantis learn {a['next']['id']}   ({a['next']['title']})")
        else:
            print("\nAll lessons complete — you've mastered the Academy!")
        return 0

    if cmd == "learn":
        from . import academy as ACAD
        les = ACAD.get(ns.arg) if ns.arg else None
        if les is None:
            nxt = ACAD.next_lesson(engine._acad()["completed"])
            if nxt is None:
                print("You've completed every lesson. Mastery achieved.")
                return 0
            les = nxt
        q = les["quiz"]
        print(f"\n╔══ {les['topic'].upper()} · Tier {les['tier']} ══╗")
        print(f"  {les['title']}\n")
        print("  " + les["body"].replace(". ", ".\n  "))
        print(f"\n  💡 TIP: {les['tip']}\n")
        print(f"  QUIZ: {q['q']}")
        for i, ch in enumerate(q["choices"]):
            print(f"    {i+1}. {ch}")
        try:
            raw = input("\n  Your answer (number): ").strip()
            choice = int(raw) - 1
        except (EOFError, ValueError, KeyboardInterrupt):
            print("  (skipped — run again to answer)")
            return 0
        res = engine.answer_lesson(les["id"], choice)
        engine.save()
        if res.get("correct"):
            print(f"\n  ✅ Correct! {res['explain']}")
            if not res.get("already"):
                print(f"  +{les['xp']} knowledge. Rank: "
                      f"{ACAD.summary(engine.pet.academy)['tier']}")
        else:
            ans = q["choices"][res["answer"]]
            print(f"\n  ❌ Not quite. The answer is: {ans}\n     {res['explain']}")
            print("  Try again anytime: mantis learn " + les["id"])
        return 0

    if cmd == "posture":
        engine.tick()
        p = engine.snapshot()["posture"]
        score = "—" if p["score"] is None else str(p["score"])
        print(f"SECURITY POSTURE:  {p['grade']}   ({score}/100, {p['known']}/{p['total']} wards cast)\n")
        for c in p["components"]:
            sc = "—" if c["score"] is None else f"{c['score']:>3}"
            print(f"  [{c['grade']}] {c['label']:<14} {sc}   {c['note']}")
        if p["known"] < p["total"]:
            print("\nCast the remaining ward spells for a full grade:")
            for c in p["components"]:
                if c["score"] is None:
                    print(f"    python3 -m mantis cast {c['spell']}")
        return 0

    if cmd == "version":
        import platform
        print(f"MANTIS {__version__}")
        print(f"python {platform.python_version()} on {platform.system()} {platform.machine()}")
        print(f"Pillow: {_mod_ver('PIL')}   numpy: {_mod_ver('numpy')}   "
              f"RPi.GPIO: {_mod_ver('RPi.GPIO')}")
        print(f"e-ink driver: {_detect_driver()}")
        try:
            from .rf_spells import detect_sdrs
            sdrs = detect_sdrs()
            print("SDR devices: " + (", ".join(s["device"] for s in sdrs) if sdrs else "none (simulation)"))
        except Exception:
            pass
        try:
            from .power import read_battery
            b = read_battery(engine.home)
            print(f"battery source: {b['source'] if b else 'none'}")
        except Exception:
            pass
        print(f"state: {engine.home}")
        return 0

    if cmd == "selfcheck":
        return _selfcheck(engine)

    if cmd == "config":
        path = CFG.config_path(engine.home)
        if (ns.arg or "").lower() == "init":
            existed = os.path.exists(path)
            if existed and not ns.force:
                print(f"Config already exists: {path}")
                print("Edit it, or re-run with --force to reset to defaults.")
            else:
                CFG.write_default(engine.home, force=True)
                print(f"Wrote default config to {path}")
            return 0
        print(f"Config file: {path}"
              f"  ({'loaded' if os.path.exists(path) else 'not created — run: mantis config init'})")
        for sec, vals in (cfg or {}).items():
            print(f"[{sec}]")
            for k, v in vals.items():
                print(f"  {k} = {v!r}")
        print("\nEffective eink settings:")
        print(f"  interval={ns.interval}  rotate={ns.rotate}  driver={ns.driver}")
        print(f"  buttons={not ns.no_buttons}  animate={not ns.no_animate}  "
              f"splash={not ns.no_splash}  slideshow={not ns.no_slideshow}")
        print(f"  slideshow_interval={ns.slideshow_interval}  "
              f"low_battery={ns.low_battery}  sleep_below={ns.sleep_below}")
        return 0

    if cmd == "web":
        from .server import serve
        serve(engine, host=ns.host, port=ns.port)
        return 0

    if cmd == "tui":
        from .tui import run
        run(engine)
        return 0

    if cmd == "eink":
        try:
            from .eink import run_eink
        except ImportError:
            print("The e-ink display needs Pillow:  pip install pillow")
            print("On a Raspberry Pi panel also:     pip install waveshare-epd  (or inky)")
            return 1
        from .buttons import DEFAULT_PINS
        # pins precedence: defaults < config [buttons] < env < --pins
        pins = dict(DEFAULT_PINS)
        pins.update(CFG.pins_from_config(cfg))
        for spec in (os.environ.get("MANTIS_PINS") or os.environ.get("PSYCHOMANTIS_PINS"),
                     ns.pins):
            if spec:
                for part in spec.split(","):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        try:
                            pins[k.strip()] = int(v)
                        except ValueError:
                            pass
        run_eink(engine, interval=ns.interval, rotate=ns.rotate, driver=ns.driver,
                 use_buttons=not ns.no_buttons, animate=not ns.no_animate,
                 pins=pins,
                 low_battery=ns.low_battery, sleep_below=ns.sleep_below,
                 splash=not ns.no_splash, slideshow=not ns.no_slideshow,
                 slideshow_interval=ns.slideshow_interval,
                 poweroff_combo=not ns.no_poweroff, poweroff_hold=ns.poweroff_hold)
        return 0

    if cmd == "faces":
        try:
            from .eink import bake_faces
        except ImportError:
            print("Baking faces needs Pillow:  pip install pillow")
            return 1
        outdir = ns.out or os.path.join(engine.home, "faces")
        paths = bake_faces(outdir)
        print(f"Wrote {len(paths)} previews to {outdir}")
        for p in paths:
            print("  " + p)
        return 0

    if cmd == "gallery":
        try:
            from .eink import bake_stages
        except ImportError:
            print("Baking the gallery needs Pillow:  pip install pillow")
            return 1
        outdir = ns.out or os.path.join(engine.home, "stages")
        paths = bake_stages(outdir)
        print(f"Wrote {len(paths)} stage cards to {outdir} (gallery = {paths[-1]})")
        return 0

    if cmd == "stages":
        from . import stages as ST
        cur = engine.pet.level
        for s in ST.STAGES:
            mark = ">" if s["lvl"] == min(cur, ST.MAX_STAGE) else \
                   ("+" if s["lvl"] <= cur else " ")
            print(f" {mark} LV{s['lvl']:<2} {s['label']:<14} {s['phrase']}")
        return 0

    if cmd == "status":
        engine.tick()
        snap = engine.snapshot()
        print(f"{snap['name']}  lv{snap['level']}/{snap['level_cap']} ({snap['rank']})")
        print(f"mood: {snap['mood']}  psyche: {int(snap['psyche'])}/{int(snap['psyche_max'])}"
              f"  age: {snap['age']}")
        print(f"xp: {snap['xp']}/{snap['xp_to_next']}   "
              f"◇{snap['souls']} souls   darkness {snap['darkness']}   infamy {snap['infamy']}")
        n = snap["needs"]
        print(f"hunger {n['hunger']}  energy {n['energy']}  "
              f"focus {n['focus']}  sanity {n['sanity']}")
        st = snap["stats"]
        print(f"kills {st['kills']}  kidnaps {st['kidnappings']}  "
              f"possess {st['possessions']}  harvested {st['souls_harvested']}")
        print(f'"{snap["phrase"]}"')
        return 0

    if cmd == "spells":
        for sp in spell_catalog(engine.pet.unlocked_spells, engine.pet.level):
            lock = "" if sp["unlocked"] else f"  [LOCKED lv{sp['min_level']}]"
            print(f"{sp['glyph']}  {sp['id']:<16} {sp['name']:<20} "
                  f"cost {sp['psyche_cost']:>2}  +{sp['xp']}xp{lock}")
        return 0

    if cmd == "cast":
        if not ns.arg:
            print("usage: python -m mantis cast <spell_id>")
            print("try:   python -m mantis spells")
            return 2
        try:
            res = cast(engine, ns.arg)
        except SpellError as e:
            print(f"✖ {e}")
            return 1
        print(res.get("summary"))
        for item in res.get("items", [])[:20]:
            print("   ", json.dumps(item))
        engine.save()
        return 0

    if cmd == "activities":
        from . import activities as ACT
        lvl = engine.pet.level
        print(f"MANTIS activities — LV{lvl}  (mode: {engine.pet.idle_mode})\n")
        tagmap = {"passive": "⟢ passive", "defense": "🛡 defense", "sim": "◈ sim"}
        for a in ACT.catalog(lvl):
            lock = "  " if a["unlocked"] else "🔒"
            print(f"{lock} LV{a['lvl']:<2} {a['key']:<14} {tagmap.get(a['kind'],a['kind']):<11}"
                  f" ◈{a['psy']:<2}  {a['label']}")
        print("\nrun one:  python -m mantis do <key>     toggle autonomy:  python -m mantis mode passive|active")
        return 0

    if cmd == "do":
        if not ns.arg:
            print("usage: python -m mantis do <activity_key>   (see 'activities')")
            return 2
        res = engine.run_activity(ns.arg)
        if not res.get("ok"):
            print(f"✖ {res.get('error')}")
            return 1
        print(f"◈ {res['stage']}: {res['summary']}")
        for it in res.get("items", []):
            print("    -", it)
        if res.get("lesson"):
            from . import academy as ACAD
            les = ACAD.get(res["lesson"])
            if les:
                print(f"  📖 teaches: {les['title']}  (python -m mantis academy)")
        engine.save()
        return 0

    if cmd == "mode":
        if ns.arg in ("passive", "active"):
            m = engine.set_mode(ns.arg)
            print(f"Idle mode → {m}.")
        elif ns.arg in (None, "", "toggle"):
            m = engine.toggle_mode() if ns.arg == "toggle" else engine.pet.idle_mode
            print(f"Idle mode: {m}   (passive = quiet watch · active = autonomous hunting)")
            print("set with:  python -m mantis mode passive   |   python -m mantis mode active")
        else:
            print("usage: python -m mantis mode [passive|active|toggle]")
            return 2
        engine.save()
        return 0

    if cmd in ("feed", "rest", "meditate", "pet"):
        fn = {"feed": engine.feed, "rest": engine.rest,
              "meditate": engine.meditate, "pet": engine.pet_it}[cmd]
        print(fn())
        engine.save()
        return 0

    if cmd in ("possess", "kidnap", "sever", "haunt"):
        res = engine.deed(cmd)
        print(res.get("summary") if res.get("ok") else f"✖ {res.get('error')}")
        engine.save()
        return 0 if res.get("ok") else 1

    if cmd == "harvest":
        res = engine.harvest()
        print(res.get("summary") if res.get("ok") else f"✖ {res.get('error')}")
        engine.save()
        return 0 if res.get("ok") else 1

    if cmd == "shop":
        from . import upgrades as U
        print(f"SOULS: ◇{engine.pet.souls}\n")
        for a in U.catalog(engine.pet):
            price = "MAX" if a["maxed"] else f"◇{a['cost']}"
            print(f"{a['glyph']}  {a['id']:<14} T{a['tier']}/{a['max_tier']}  "
                  f"{price:<6} {a['name']} — {a['desc']}")
        print("\nbuy with:  python -m mantis buy <id>")
        return 0

    if cmd == "buy":
        if not ns.arg:
            print("usage: python -m mantis buy <augment_id>  (see 'shop')")
            return 2
        res = engine.buy_augment(ns.arg)
        print(f"Bought {res['augment']} tier {res['tier']} (−◇{res['spent']})"
              if res.get("ok") else f"✖ {res.get('error')}")
        engine.save()
        return 0 if res.get("ok") else 1

    print(f"Unknown command: {cmd}")
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
