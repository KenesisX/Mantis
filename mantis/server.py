"""Stdlib HTTP server: JSON API + the web dashboard. No dependencies."""

from __future__ import annotations

import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from .engine import Engine
from .spells import SPELLS, cast, spell_catalog, autonomous_sense, SpellError
from . import upgrades as U

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


class _Handler(BaseHTTPRequestHandler):
    engine: Engine = None  # type: ignore[assignment]

    def log_message(self, *a: Any) -> None:  # silence
        pass

    # -- helpers ---------------------------------------------------- #
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _json(self, obj: Dict[str, Any], code: int = 200) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def _file(self, name: str, ctype: str) -> None:
        path = os.path.join(WEB_DIR, name)
        try:
            with open(path, "rb") as fh:
                self._send(200, fh.read(), ctype)
        except FileNotFoundError:
            self._send(404, b"not found", "text/plain")

    def _art(self, name: str) -> None:
        """Serve the bundled hero/portrait artwork (assets/art/)."""
        safe = os.path.basename(name)
        art_dir = os.path.join(os.path.dirname(WEB_DIR), "assets", "art")
        ctype = ("image/webp" if safe.endswith(".webp")
                 else "image/png" if safe.endswith(".png") else "application/octet-stream")
        try:
            with open(os.path.join(art_dir, safe), "rb") as fh:
                self._send(200, fh.read(), ctype)
        except FileNotFoundError:
            self._send(404, b"not found", "text/plain")

    def _epaper(self, eng) -> None:
        """Serve a live PNG mirror of the e-ink status screen."""
        try:
            import io
            from . import eink
            eng.tick()
            img = eink.render_screen(eng.snapshot()).convert("L").resize(
                (eink.WIDTH * 2, eink.HEIGHT * 2))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self._send(200, buf.getvalue(), "image/png")
        except Exception:
            self._send(503, b"no frame (Pillow required)", "text/plain")

    def _colorframe(self, eng) -> None:
        """Serve a live color (HyperPixel) frame."""
        try:
            import io
            from . import color
            eng.tick()
            buf = io.BytesIO()
            color.render(eng.snapshot()).save(buf, format="PNG")
            self._send(200, buf.getvalue(), "image/png")
        except Exception:
            self._send(503, b"no color frame (Pillow/numpy required)", "text/plain")

    def _read_body(self) -> Dict[str, Any]:
        try:
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n) if n else b"{}"
            return json.loads(raw or b"{}")
        except Exception:
            return {}

    # -- routes ----------------------------------------------------- #
    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        eng = self.engine
        if path in ("/", "/index.html", "/console"):
            self._file("console.html", "text/html; charset=utf-8")
        elif path in ("/classic", "/classic.html"):
            self._file("index.html", "text/html; charset=utf-8")
        elif path.startswith("/art/"):
            self._art(path.rsplit("/", 1)[-1])
        elif path == "/console.js":
            self._file("console.js", "application/javascript")
        elif path == "/console.css":
            self._file("console.css", "text/css")
        elif path == "/manifest.webmanifest":
            self._file("manifest.webmanifest", "application/manifest+json")
        elif path == "/sw.js":
            self._file("sw.js", "application/javascript")
        elif path.startswith("/icons/"):
            name = os.path.basename(path)
            self._file(os.path.join("icons", name), "image/png")
        elif path == "/watch":
            self._file("watch.html", "text/html; charset=utf-8")
        elif path == "/remote":
            self._file("remote.html", "text/html; charset=utf-8")
        elif path == "/color":
            self._file("color.html", "text/html; charset=utf-8")
        elif path == "/epaper.png":
            self._epaper(eng)
        elif path == "/color.png":
            self._colorframe(eng)
        elif path == "/app.js":
            self._file("app.js", "application/javascript")
        elif path == "/style.css":
            self._file("style.css", "text/css")
        elif path == "/api/state":
            eng.tick()
            snap = eng.snapshot()
            try:
                from .power import read_battery
                b = read_battery(eng.home)
                if b is not None:
                    snap["battery"] = b
            except Exception:
                pass
            self._json(snap)
        elif path == "/api/spells":
            self._json({"spells": spell_catalog(eng.pet.unlocked_spells, eng.pet.level)})
        elif path == "/api/augments":
            self._json({"augments": U.catalog(eng.pet), "souls": eng.pet.souls})
        elif path == "/api/fleet":
            from . import fleet
            self._json({"fleet": fleet.roster(eng.home),
                        "self": fleet.gather_self(eng)})
        elif path == "/api/stages":
            from . import stages as ST
            self._json({"stages": [{"lvl": s["lvl"], "label": s["label"],
                                    "key": s["key"]} for s in ST.STAGES],
                        "level": eng.pet.level})
        elif path == "/api/activities":
            from . import activities as ACT
            self._json({"activities": ACT.catalog(eng.pet.level),
                        "level": eng.pet.level,
                        "mode": eng.pet.idle_mode,
                        "run": getattr(eng.pet, "activities_run", 0)})
        elif path == "/api/peers":
            self._json({"peers": eng.peers(),
                        "duels": {"won": eng.pet.duels_won, "lost": eng.pet.duels_lost,
                                  "draw": eng.pet.duels_draw},
                        "log": eng.pet.duel_log[-20:]})
        elif path == "/api/arsenal":
            from . import duel as DUEL
            self._json({"arsenal": DUEL.arsenal(eng.pet.level)})
        elif path == "/api/persona":
            from . import persona as PERSONA, config as CFG
            self._json({
                "profile": eng.profile,
                "interests": {k: v["label"] for k, v in PERSONA.INTERESTS.items()},
                "traits": PERSONA.TRAITS,
                "presets": PERSONA.TRAIT_PRESETS,
                "reading": eng.read_keeper(),
                "theme": (CFG.load(eng.home).get("web", {}) or {}).get("theme", "red"),
            })
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
        eng = self.engine
        body = self._read_body()
        try:
            if path == "/api/action":
                act = body.get("action")
                fn = {"feed": eng.feed, "rest": eng.rest, "meditate": eng.meditate,
                      "pet": eng.pet_it, "speak": eng.speak}.get(act)
                if not fn:
                    return self._json({"error": "unknown action"}, 400)
                msg = fn()
                return self._json({"ok": True, "message": msg, "state": eng.snapshot()})
            elif path == "/api/cast":
                res = cast(eng, body.get("spell", ""))
                return self._json({"ok": True, "result": res, "state": eng.snapshot()})
            elif path == "/api/activity":
                res = eng.run_activity(str(body.get("activity", "")))
                return self._json({**res, "state": eng.snapshot()},
                                  200 if res.get("ok") else 400)
            elif path == "/api/mode":
                mode = eng.set_mode(str(body.get("mode", "active")))
                return self._json({"ok": True, "mode": mode, "state": eng.snapshot()})
            elif path == "/api/duel":
                res = eng.duel_peer(str(body.get("peer", "")),
                                    mode=str(body.get("mode", "auto")),
                                    my_loadout=body.get("loadout") or None)
                return self._json({**res, "state": eng.snapshot()},
                                  200 if res.get("ok") else 400)
            elif path == "/api/deed":
                res = eng.deed(body.get("deed", ""))
                return self._json({**res, "state": eng.snapshot()},
                                  200 if res.get("ok") else 400)
            elif path == "/api/harvest":
                res = eng.harvest()
                return self._json({**res, "state": eng.snapshot()},
                                  200 if res.get("ok") else 400)
            elif path == "/api/push_xp":
                # external gadgets (watch, SDR, mesh) feed XP into MANTIS
                rf = int(body.get("rf_captures", 0) or 0)
                ble = int(body.get("ble_beacons", 0) or 0)
                wpa = int(body.get("wpa_handshakes", 0) or 0)
                extra = int(body.get("xp", 0) or 0)
                gained = rf * 40 + ble * 15 + wpa * 120 + extra
                if rf or ble or wpa:
                    with eng._lock:
                        eng.pet.networks_sensed += rf + ble + wpa
                if gained:
                    eng.award_xp(gained, reason="external telemetry")
                    eng.emit("push", f"Distant minds feed me (+{gained} XP).")
                    eng.save()
                return self._json({"ok": True, "gained": gained,
                                   "level": eng.pet.level, "state": eng.snapshot()})
            elif path == "/api/learn":
                res = eng.answer_lesson(body.get("lesson", ""), int(body.get("answer", -1)))
                return self._json({**res, "state": eng.snapshot()},
                                  200 if res.get("ok") else 400)
            elif path == "/api/buy":
                res = eng.buy_augment(body.get("augment", ""))
                return self._json({**res, "augments": U.catalog(eng.pet),
                                   "state": eng.snapshot()},
                                  200 if res.get("ok") else 400)
            elif path == "/api/rename":
                eng.rename(body.get("name", ""))
                return self._json({"ok": True, "state": eng.snapshot()})
            elif path == "/api/persona":
                eng.set_profile(body or {})
                return self._json({"ok": True, "profile": eng.profile,
                                   "reading": eng.read_keeper(),
                                   "state": eng.snapshot()})
            elif path == "/api/theme":
                from . import config as CFG
                theme = str(body.get("theme", "red"))
                if theme in ("red", "mono", "green", "amber"):
                    CFG.update(eng.home, web={"theme": theme})
                return self._json({"ok": True, "theme": theme})
            elif path == "/api/fleet/report":
                from . import config as CFG, fleet
                key = (CFG.load(eng.home).get("fleet", {}) or {}).get("key", "")
                if not key:
                    return self._json({"ok": False, "error": "fleet disabled (no key set)"}, 403)
                if str(body.get("key", "")) != str(key):
                    return self._json({"ok": False, "error": "bad fleet key"}, 403)
                dev = body.get("device") or {}
                if dev:
                    fleet.record(eng.home, dev)
                return self._json({"ok": True})
            elif path == "/api/fleet/forget":
                from . import fleet
                return self._json({"ok": fleet.forget(eng.home, body.get("id", ""))})
            else:
                return self._json({"error": "not found"}, 404)
        except SpellError as e:
            return self._json({"ok": False, "error": str(e), "state": eng.snapshot()}, 400)
        except Exception as e:  # pragma: no cover
            return self._json({"ok": False, "error": str(e)}, 500)


def _background(engine: Engine, stop: threading.Event) -> None:
    last_sense = 0.0
    last_act = 0.0
    while not stop.is_set():
        engine.tick()
        now = time.time()
        if now - last_sense > 40:
            autonomous_sense(engine)          # passive sensing — runs in both modes
            last_sense = now
        # ACTIVE idle mode: MANTIS autonomously performs an activity now and then
        if now - last_act > 25 + random.random() * 20:
            engine.auto_activity()
            last_act = now
        engine.save()
        stop.wait(5)


def serve(engine: Engine, host: str = "127.0.0.1", port: int = 8777) -> None:
    _Handler.engine = engine
    engine._web_port = port
    # sense nearby MANTIS units (LAN + optional BLE/Sub-GHz); opt-out via config
    try:
        from . import config as CFG
        disc = (CFG.load(engine.home).get("discovery", {}) or {})
        if disc.get("enabled", True):
            engine.start_discovery(enabled=True,
                                   extra_radios=disc.get("radios", True))
    except Exception:
        pass
    stop = threading.Event()
    bg = threading.Thread(target=_background, args=(engine, stop), daemon=True)
    bg.start()
    httpd = ThreadingHTTPServer((host, port), _Handler)
    url = f"http://{host}:{port}"
    print("\n  \033[38;5;201m╔════════════════════════════════════════════╗")
    print("  ║   MANTIS is awake and listening...   ║")
    print("  ╚════════════════════════════════════════════╝\033[0m")
    print(f"\n  Open your mind (and browser) at:  \033[38;5;51m{url}\033[0m")
    print("  Press Ctrl+C to let him sleep.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        engine.save()
        httpd.server_close()
        print("\n  The mask goes dark. I am always listening...\n")
