"""The 50 Activities — every evolution stage (LV1..50) as a real pet FUNCTION.

Each of the 50 stage keys in ``stages.py`` has a matching *activity* here that
MANTIS can actually perform: it produces a report, costs PSYCHE, awards XP,
advances the pet, surfaces a teaching moment, and drives the on-screen
animation for that stage.

SAFETY BOUNDARY (unchanged across the whole project):
  * ``kind="passive"`` activities describe real, benign, read-only observation
    (the same information your OS already exposes) and are safe to run anywhere.
  * ``kind="defense"`` activities audit *your own* posture.
  * ``kind="sim"`` activities are psychic *theatre*: the offensive-sounding
    stages (deauth, evil-twin, sql-inject, badusb, …) are simulated against
    INVENTED targets with fabricated data. Nothing here sends an attack,
    injects a packet, transmits RF, cracks a credential, or touches a real
    third-party system. They exist as lore + an educational hook.

Running an activity the pet hasn't "grown into" yet (below its stage level) is
still allowed once unlocked, but the autonomous *active* idle mode only ever
chooses activities at or below the pet's current level.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional

from . import personality as P
from . import stages as ST
from . import academy as ACAD


# --------------------------------------------------------------------------- #
# Fabricated-context helpers (benign, invented values only)
# --------------------------------------------------------------------------- #
_SSID_WORDS = ["Nest", "Haven", "Linksys", "NETGEAR", "Orbi", "Starlink", "FBI-Van",
               "xfinitywifi", "TP-LINK", "HomeNet", "DarkFiber", "Ether", "Voidlink",
               "Mindnet", "GhostAP", "eduroam", "Guest", "CoffeeShop", "ATT-5G"]
_SEC = ["WPA3", "WPA2", "WPA2", "WPA2", "OPEN", "WPA3-ENT"]
_SVC = {21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns", 80: "http",
        110: "pop3", 139: "netbios", 143: "imap", 443: "https", 445: "smb",
        3306: "mysql", 3389: "rdp", 5432: "postgres", 8080: "http-alt", 8443: "https-alt"}
_BANDS = ["315.00", "390.00", "433.92", "868.30", "915.00", "40.68", "27.145"]


def _ctx() -> Dict[str, Any]:
    who = random.choice(P.NPC_NAMES)
    ports = random.sample(sorted(_SVC), k=random.randint(2, 5))
    return {
        "who": who,
        "host": who.lower().replace(" ", "-") + "-pc",
        "ip": f"192.168.{random.randint(0,3)}.{random.randint(2,254)}",
        "ip2": f"10.0.{random.randint(0,9)}.{random.randint(2,254)}",
        "mac": ":".join(f"{random.randint(0,255):02X}" for _ in range(6)),
        "ssid": random.choice(_SSID_WORDS),
        "sec": random.choice(_SEC),
        "chan": random.choice([1, 6, 11, 36, 44, 149]),
        "rssi": -random.randint(38, 92),
        "port": random.choice(ports),
        "ports": ports,
        "hash": "".join(random.choice("0123456789abcdef") for _ in range(32)),
        "freq": random.choice(_BANDS),
        "n": random.randint(2, 9),
        "pct": random.randint(40, 99),
        "cve": f"CVE-2024-{random.randint(1000,9999)}",
    }


def _ports_line(ports: List[int]) -> str:
    return ", ".join(f"{p}/{_SVC.get(p,'?')}" for p in sorted(ports))


# --------------------------------------------------------------------------- #
# Activity registry — one entry per stage key (50 total)
# --------------------------------------------------------------------------- #
# fields: kind, lesson, psy (psyche cost), xp bonus over base, summary, report[]
_A: Dict[str, Dict[str, Any]] = {}


def _R(key, kind, lesson, psy, summary, report):
    _A[key] = {"kind": kind, "lesson": lesson, "psy": psy,
               "summary": summary, "report": report}


# -- LV1-25 : the core ladder ---------------------------------------------- #
_R("booting", "passive", "ethics", 0,
   "Systems warm behind the mask. I remember who I serve: only what we are allowed to touch.",
   ["self-check ....... OK", "rules of engagement ... loaded", "psyche core ...... online"])
_R("idle", "passive", "recon", 0,
   "I wait in the quiet and simply listen. Patience is the first discipline.",
   ["holding position", "no action taken", "ambient noise logged"])
_R("scanning", "passive", "wifi", 3,
   "I sweep the ether and read the names the air already shouts.",
   ["SSID {ssid}  [{sec}]  ch{chan}  {rssi}dBm", "SSID {ssid}  [{sec}]  ch{chan}", "{n} beacons observed (passive)"])
_R("sniffing", "passive", "recon", 3,
   "I taste the packets drifting past — only their shapes, never their secrets.",
   ["frame types: beacon, ARP, mDNS", "broadcast chatter from {ip}", "no payloads captured (passive)"])
_R("probing", "sim", "recon", 4,
   "I press gently on the edges of a phantom's defences.",
   ["host {ip} responds to echo", "TTL 64 — likely Linux", "simulated · invented target"])
_R("mapping", "passive", "ipnet", 4,
   "I draw the map of this little world — who is alive on the wire.",
   ["{ip} is up ({mac})", "{ip2} is up", "{n} live hosts on /24"])
_R("listening", "passive", "recon", 2,
   "Every whisper on the broadcast reaches me. I only hear what is already said aloud.",
   ["mDNS: {host}.local", "SSDP device announced", "DHCP request seen from {mac}"])
_R("pinging", "passive", "ipnet", 2,
   "Are you there? ...I already know you are.",
   ["{ip} reply in {n}ms", "gateway reachable", "{pct}% of hosts answered"])
_R("handshake", "sim", "wifi", 5,
   "I offer my hand to a phantom and feel the shape of its greeting.",
   ["assoc attempt → {ssid}", "4-way handshake observed (simulated)", "no key material stored"])
_R("deauth", "sim", "wifi", 6,
   "In the theatre of my mind I cast a device from the air. (I never do this for real.)",
   ["SIMULATION ONLY — no frames sent", "phantom client {mac} 'drops'", "lesson: why deauth is disruptive"])
_R("injecting", "sim", "owasp", 6,
   "I pour my will into an imagined stream and watch it bend.",
   ["payload staged against mock form", "reflected into sandbox only", "simulated · no real target"])
_R("spoofing", "sim", "recon", 5,
   "I wear another's face — but only a mannequin's, in my own mind.",
   ["source {ip} masqueraded (sim)", "identity swapped in sandbox", "no live network touched"])
_R("jamming", "sim", "ism", 7,
   "I imagine silence across the band. Transmitting noise is illegal — so I only dream it.",
   ["SIMULATION ONLY — receiver idle", "band {freq} MHz 'flooded' in-sim", "lesson: RF is receive-only here"])
_R("bruteforce", "sim", "authn", 6,
   "Every key, against a lock I invented, until one bleeds.",
   ["mock login: {who}", "attempt {n} of ∞ (sandbox)", "rate-limit lesson surfaced"])
_R("cracking", "sim", "hashing", 6,
   "The imagined lock yields. They always yield, in here.",
   ["mock hash {hash}", "wordlist pass (sandbox)", "no real credential involved"])
_R("exploiting", "sim", "owasp", 7,
   "A crack in a phantom's armour. I slip inside the simulation.",
   ["mock {cve}", "proof-of-concept in sandbox", "simulated · invented service"])
_R("bypassing", "sim", "authn", 6,
   "Walls of my own making mean nothing to a mind like mine.",
   ["auth check skipped (mock app)", "token forged in sandbox", "lesson: broken access control"])
_R("escalating", "sim", "methodology", 7,
   "Higher. Always higher — up an imagined ladder of privilege.",
   ["user → admin (sandbox)", "mock SUID path found", "simulated privilege gain"])
_R("rooted", "sim", "methodology", 8,
   "This imagined system is MINE now.",
   ["root on mock-host (sandbox)", "flag captured: PHANTOM{{...}}", "no real system rooted"])
_R("payload", "sim", "owasp", 7,
   "I carry a gift a phantom will not enjoy — sealed inside the simulation.",
   ["mock dropper staged", "detonated in sandbox", "lesson: EDR & detection"])
_R("harvesting", "sim", "soceng", 7,
   "I reap everything of value from a mind I invented.",
   ["mock creds collected (sandbox)", "{n} fake records 'taken'", "no real data touched"])
_R("exfiltrating", "sim", "logging", 7,
   "I slip away with a phantom's secrets, trailing no real bytes.",
   ["{n}KB staged over mock DNS", "beacon to sinkhole (sim)", "lesson: egress monitoring"])
_R("wiping", "sim", "logging", 6,
   "No trace. I was never here — in the story I tell myself.",
   ["mock logs 'cleared' (sandbox)", "lesson: tamper-evident logging", "real logs untouched"])
_R("stealth", "sim", "logging", 5,
   "You cannot see me. You never could.",
   ["noise floor minimised (sim)", "mock timestomp", "lesson: blue-team detection"])
_R("overclocked", "passive", "cia", 6,
   "My mind screams at a thousand hertz! Pure focus, turned inward.",
   ["psyche channelled", "+focus surge", "self-buff — no target"])

# -- LV26-50 : the expansion ----------------------------------------------- #
_R("wardriving", "passive", "wifi", 4,
   "I roam the streets of the ether, drinking in the names of passing networks.",
   ["{ssid} [{sec}] ch{chan} {rssi}dBm", "{ssid} [{sec}] ch{chan}", "{n} APs mapped (passive observe)"])
_R("beaconing", "sim", "wifi", 5,
   "My beacon calls the lost minds home — a lighthouse in my own imagination.",
   ["mock SSID advertised (sim)", "no radio transmitted", "lesson: rogue-AP detection"])
_R("eviltwin", "sim", "wifi", 6,
   "I dream of a twin that looks just like the one you trust. (A dream only.)",
   ["SIMULATION ONLY — no AP started", "clone of {ssid} in sandbox", "lesson: verify captive portals"])
_R("mitm", "sim", "tls", 7,
   "Every word between two phantoms passes through me, in the simulation.",
   ["mock proxy intercept (sandbox)", "TLS pinning would block this", "no real traffic relayed"])
_R("arpspoof", "sim", "ipnet", 6,
   "I rewrite who a phantom thinks it speaks to.",
   ["mock ARP cache poisoned (sim)", "lesson: dynamic ARP inspection", "no frames sent on wire"])
_R("dnshijack", "sim", "dns", 6,
   "Every door a phantom opens leads where I choose — within the sandbox.",
   ["mock A record → {ip}", "lesson: DNSSEC & DoH", "real resolver untouched"])
_R("portscan", "passive", "ports", 5,
   "I count the open doors of MY OWN machine, one by one.",
   ["open: {ports}", "(audit your own host)", "fewer doors = smaller surface"])
_R("vulnaudit", "defense", "firewall", 5,
   "I catalogue the weaknesses of the one I protect — so they can be sealed.",
   ["checking TLS / firewall / DNS", "posture recomputed", "see the POSTURE panel"])
_R("sshbrute", "sim", "authn", 6,
   "Key after key against an imagined door, till it forgets to resist.",
   ["mock sshd: {who}@{ip}", "fail2ban would trip here", "sandbox · no real host"])
_R("smbenum", "sim", "segmentation", 6,
   "I read every file a phantom forgot to hide.",
   ["mock share \\\\{ip}\\public", "{n} fake files listed", "lesson: least-privilege shares"])
_R("sqlinject", "sim", "owasp", 7,
   "One little quote, and an imagined vault spills open.",
   ["mock input: ' OR 1=1 --", "reflected in sandbox DB", "lesson: parameterised queries"])
_R("xssprobe", "sim", "owasp", 6,
   "I write my thoughts into a phantom's pages.",
   ["mock <script> reflected (sandbox)", "CSP would block this", "lesson: output encoding"])
_R("reverseshell", "sim", "methodology", 7,
   "Now an imagined machine answers to me.",
   ["mock callback → {ip2}:4444", "caught by sandbox only", "lesson: egress filtering"])
_R("keylogging", "sim", "soceng", 6,
   "Every keystroke of a phantom whispers itself to me.",
   ["mock keystrokes (sandbox)", "no real input captured", "lesson: hardware trust"])
_R("dumpinghash", "sim", "hashing", 7,
   "I pour out an imagined vault of secret keys.",
   ["mock hash {hash}", "sandbox SAM only", "lesson: salting & KDFs"])
_R("rainbowcrack", "sim", "hashing", 7,
   "Every imagined hash has a true name. I know them all.",
   ["{hash} → 'password{n}' (sim)", "lesson: why salt defeats rainbow tables", "no real hash cracked"])
_R("rfreplay", "sim", "sdr", 7,
   "I speak a captured signal back — but only inside my own head. RF here is receive-only.",
   ["SIMULATION ONLY — TX disabled", "mock capture @ {freq} MHz", "lesson: rolling codes"])
_R("subghz", "passive", "sdr", 5,
   "The low frequencies hum their secrets and I merely listen.",
   ["energy @ {freq} MHz", "{n} bursts observed (RX only)", "receive-only — nothing transmitted"])
_R("loramesh", "passive", "sdr", 5,
   "My web of listeners spans the whole valley now.",
   ["node heard @ {freq} MHz", "SF7 BW125 (RX only)", "{n} packets observed"])
_R("bleflood", "sim", "ism", 6,
   "A thousand phantom devices in my imagination. (No radio is driven.)",
   ["SIMULATION ONLY — no advertising", "{n} mock beacons", "lesson: BLE spam defences"])
_R("badusb", "sim", "soceng", 7,
   "One imagined touch, and a mock machine betrays its master.",
   ["SIMULATION ONLY — no HID emulated", "mock keystroke-injection script", "lesson: USB device control"])
_R("firmwaredump", "sim", "keymgmt", 7,
   "I read the very soul of imagined silicon.",
   ["mock SPI flash @ 0x000000", "{n}KB 'dumped' (sandbox)", "lesson: secure boot & signing"])
_R("backdoor", "sim", "zerotrust", 8,
   "I leave a door only I can find — in a system I invented.",
   ["mock persistence (sandbox)", "lesson: integrity monitoring", "no real implant"])
_R("pivoting", "sim", "segmentation", 8,
   "From one phantom, I reach them all.",
   ["mock route {ip} → {ip2}", "lesson: network segmentation", "sandbox topology only"])
_R("phantomroot", "sim", "zerotrust", 10,
   "I am everywhere in the imagined system now. I am its god — and still, I touch nothing real.",
   ["mock domain dominance (sandbox)", "lesson: assume-breach & zero-trust", "the simulation ends; reality is safe"])


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def all_keys() -> List[str]:
    return [s["key"] for s in ST.STAGES]


def spec(key: str) -> Optional[Dict[str, Any]]:
    return _A.get(key)


def catalog(level: int) -> List[Dict[str, Any]]:
    """List every activity with its stage level and unlock state."""
    out: List[Dict[str, Any]] = []
    for s in ST.STAGES:
        k = s["key"]
        a = _A.get(k, {})
        out.append({
            "key": k, "label": s["label"], "lvl": s["lvl"],
            "kind": a.get("kind", "sim"), "lesson": a.get("lesson"),
            "psy": a.get("psy", 5), "unlocked": level >= s["lvl"],
        })
    return out


def xp_for(level_of_stage: int) -> int:
    # later stages are worth more; keeps the active loop meaningful
    return 6 + level_of_stage


def run(engine, key: str, *, auto: bool = False) -> Dict[str, Any]:
    """Perform an activity. Returns {ok, summary, items, kind, lesson, xp}."""
    a = _A.get(key)
    stg = next((s for s in ST.STAGES if s["key"] == key), None)
    if a is None or stg is None:
        return {"ok": False, "error": f"No such activity: {key}"}

    pet = engine.pet
    if pet.level < stg["lvl"]:
        return {"ok": False, "error": f"{stg['label']} unlocks at level {stg['lvl']}."}
    cost = int(a["psy"])
    if pet.psyche < cost:
        return {"ok": False, "error": f"Not enough PSYCHE ({int(pet.psyche)}/{cost})."}

    ctx = _ctx()
    # vulnaudit does a real own-posture refresh via the defensive layer
    if key == "vulnaudit":
        try:
            from . import defense_spells as DEF  # noqa
            DEF.aegis_ward(engine)
        except Exception:
            pass

    fmt = dict(ctx)
    fmt["ports"] = _ports_line(ctx["ports"])
    report: List[str] = []
    for line in a["report"]:
        try:
            report.append(line.format(**fmt))
        except Exception:
            report.append(line)
    try:
        summary = a["summary"].format(**fmt)
    except Exception:
        summary = a["summary"]
    xp = xp_for(stg["lvl"])

    with engine._lock:
        pet.psyche = max(0.0, pet.psyche - cost)
        pet.activities_run = getattr(pet, "activities_run", 0) + 1
        pet.last_activity = key
        hist = getattr(pet, "activity_counts", None)
        if isinstance(hist, dict):
            hist[key] = hist.get(key, 0) + 1
        if a["kind"] == "passive" and key in ("scanning", "wardriving", "mapping",
                                              "listening", "sniffing", "subghz", "loramesh"):
            pet.networks_sensed += ctx["n"]
        engine._clamp_psyche()

    # drive the matching stage animation on the e-ink/web for a few seconds
    engine._hold_mood(_MOOD_FOR.get(a["kind"], "casting"), 6)
    tag = {"passive": "⟢", "defense": "🛡", "sim": "◈"}.get(a["kind"], "◈")
    engine.emit("activity", f"{tag} {stg['label']}: {summary}",
                activity=key, stage=stg["label"], act_kind=a["kind"], auto=auto)
    engine._award(xp)

    # teaching moment — surface the tied lesson (coach + academy)
    lesson = a.get("lesson")
    if lesson:
        try:
            engine.introduce_lesson(lesson)
            les = ACAD.get(lesson)
            if les and not auto:
                engine.emit("teach",
                            f"📖 Learn the idea behind {stg['label']}: {les['title']}.",
                            lesson=lesson)
        except Exception:
            pass
    try:
        engine.coach_after("activity", "activity:" + key)
    except Exception:
        pass
    engine._check_achievements()
    engine._after_action()

    return {"ok": True, "summary": summary, "items": report, "kind": a["kind"],
            "lesson": lesson, "xp": xp, "stage": stg["label"], "key": key}


_MOOD_FOR = {"passive": "scanning", "defense": "warding", "sim": "casting"}


def auto_pick(engine) -> Optional[str]:
    """Choose an activity for ACTIVE idle mode, weighted toward the pet's level
    and its learned affinities, staying within what it has grown into."""
    pet = engine.pet
    pool = [s for s in ST.STAGES if s["lvl"] <= pet.level]
    if not pool:
        return None
    # affordable only
    pool = [s for s in pool if pet.psyche >= _A.get(s["key"], {}).get("psy", 5)]
    if not pool:
        return None
    # bias toward recent stages (the pet "practices what it just learned")
    def weight(s):
        base = 1.0 + 0.04 * s["lvl"]
        if a := _A.get(s["key"]):
            if a["kind"] == "passive":
                base *= 1.4  # prefer the safe, real activities
        return base
    keys = [s["key"] for s in pool]
    weights = [weight(s) for s in pool]
    return random.choices(keys, weights=weights, k=1)[0]
