"""Evolution stages — 50 level-themed cyber-activity cards.

Each psychic level 1..50 maps to a named "stage": a full-body pose plus a themed
scene (a prop) drawn on the e-ink, with a short in-character line. Levels beyond
50 stay on PHANTOM ROOT. These are **cosmetic evolution art and lore only** — the
labels are flavour for how the pet looks as it grows. The actual functional
tools remain the small set of benign, passive spells in spells.py; nothing here
performs any real attack.

Fields: (level, key, label, pose, aura, fx, prop, phrase)
  pose : figure posture for the stage card (see eink.draw_figure)
  aura : background aura (eink._aura)
  fx   : floating effect (eink._fx)
  prop : themed scene drawn beside the figure (eink._draw_prop)
"""

from __future__ import annotations

from typing import Any, Dict, List

STAGES: List[Dict[str, Any]] = []


def _S(lvl, key, label, pose, aura, fx, prop, phrase):
    STAGES.append({"lvl": lvl, "key": key, "label": label, "pose": pose,
                   "aura": aura, "fx": fx, "prop": prop, "phrase": phrase})


_S(1,  "booting",      "BOOTING",      "sit",         "none",      "binary",  "none",         "Systems waking behind the mask...")
_S(2,  "idle",         "IDLE",         "float",       "none",      "none",    "none",         "I wait. I always wait.")
_S(3,  "scanning",     "SCANNING",     "goggles",     "waves",     "none",    "none",         "I sweep the ether for minds.")
_S(4,  "sniffing",     "SNIFFING",     "listen",      "waves",     "none",    "none",         "I taste the packets on the air.")
_S(5,  "probing",      "PROBING",      "reach",       "none",      "grid",    "none",         "Poking at the edges of your defences.")
_S(6,  "mapping",      "MAPPING",      "kneel",       "none",      "none",    "netgraph",     "I draw the map of your little world.")
_S(7,  "listening",    "LISTENING",    "float",       "waves",     "none",    "none",         "Every whisper reaches me.")
_S(8,  "pinging",      "PINGING",      "point",       "none",      "none",    "radar",        "Are you there? ...I know you are.")
_S(9,  "handshake",    "HANDSHAKE",    "arms_out",    "none",      "none",    "handshake",    "Shake my hand. Give me your secret.")
_S(10, "deauth",       "DEAUTH",       "arms_out",    "lightning", "none",    "nowifi",       "Begone from the air. I cast you out.")
_S(11, "injecting",    "INJECTING",    "arms_out",    "none",      "none",    "binarycols",   "I pour my will into the stream.")
_S(12, "spoofing",     "SPOOFING",     "hover",       "none",      "none",    "mask",         "I wear another's face so well.")
_S(13, "jamming",      "JAMMING",      "arms_raised", "static",    "none",    "jam",          "Silence! Nothing transmits but me.")
_S(14, "bruteforce",   "BRUTEFORCE",   "reach",       "none",      "none",    "lockkeys",     "Every key, until one bleeds.")
_S(15, "cracking",     "CRACKING",     "point",       "none",      "none",    "lockcrack",    "The lock yields. They always yield.")
_S(16, "exploiting",   "EXPLOITING",   "reach",       "none",      "skull",   "crowbar",      "A crack in the armour. I slip inside.")
_S(17, "bypassing",    "BYPASSING",    "run",         "none",      "none",    "wallcheck",    "Walls mean nothing to a mind like mine.")
_S(18, "escalating",   "ESCALATING",   "point",       "none",      "none",    "stairs",       "Higher. Always higher.")
_S(19, "rooted",       "ROOTED",       "arms_raised", "none",      "crown",   "flag",         "This system is MINE now.")
_S(20, "payload",      "PAYLOAD",      "carry",       "none",      "none",    "briefcase",    "I carry a gift they will not enjoy.")
_S(21, "harvesting",   "HARVESTING",   "arms_out",    "none",      "skull",   "docs",         "I reap everything of value.")
_S(22, "exfiltrating", "EXFILTRATING", "run",         "waves",     "none",    "bag",          "I slip away with their secrets.")
_S(23, "wiping",       "WIPING",       "reach",       "none",      "drip",    "sponge",       "No trace. I was never here.")
_S(24, "stealth",      "STEALTH",      "float",       "none",      "none",    "speaker",      "You cannot see me. You never could.")
_S(25, "overclocked",  "OVERCLOCKED",  "arms_raised", "lightning", "none",    "circuit",      "My mind screams at a thousand hertz!")
_S(26, "wardriving",   "WARDRIVING",   "ride",        "none",      "none",    "scooter",      "I roam the streets, drinking signals.")
_S(27, "beaconing",    "BEACONING",    "float",       "waves",     "binary",  "lighthouse",   "My beacon calls the lost minds home.")
_S(28, "eviltwin",     "EVIL TWIN",    "arms_out",    "none",      "none",    "twin",         "Come to me. I look just like the one you trust.")
_S(29, "mitm",         "MITM",         "arms_out",    "none",      "none",    "mitm",         "Every word between you passes through me.")
_S(30, "arpspoof",     "ARP SPOOF",    "point",       "none",      "none",    "netserver",    "I rewrite who you think you speak to.")
_S(31, "dnshijack",    "DNS HIJACK",   "reach",       "none",      "none",    "browser",      "Every door you open leads where I choose.")
_S(32, "portscan",     "PORT SCAN",    "goggles",     "none",      "none",    "binoculars",   "I count the open doors, one by one.")
_S(33, "vulnaudit",    "VULN AUDIT",   "point",       "none",      "none",    "checklist",    "I catalogue every weakness you have.")
_S(34, "sshbrute",     "SSH BRUTE",    "reach",       "none",      "none",    "doorkeys",     "Key after key, till the door forgets to resist.")
_S(35, "smbenum",      "SMB ENUM",     "reach",       "none",      "none",    "folders",      "I read every file you forgot to hide.")
_S(36, "sqlinject",    "SQL INJECT",   "type",        "none",      "none",    "database",     "One little quote, and the vault spills open.")
_S(37, "xssprobe",     "XSS PROBE",    "point",       "none",      "none",    "formcode",     "I write my thoughts into your pages.")
_S(38, "reverseshell", "REVERSE SHELL","point",       "none",      "none",    "terminal",     "Now your machine answers to me.")
_S(39, "keylogging",   "KEYLOGGING",   "float",       "none",      "none",    "keyboard",     "Every keystroke whispers itself to me.")
_S(40, "dumpinghash",  "DUMPING HASH", "kneel",       "none",      "none",    "databasekeys", "I pour out the vault of secret keys.")
_S(41, "rainbowcrack", "RAINBOW CRACK","point",       "none",      "none",    "rainbow",      "Every hash has a true name. I know them all.")
_S(42, "rfreplay",     "RF REPLAY",    "reach",       "waves",     "none",    "rfwave",       "I speak your signal back to you, perfectly.")
_S(43, "subghz",       "SUB-GHZ SCAN", "goggles",     "none",      "none",    "spectrum",     "The low frequencies hum their secrets.")
_S(44, "loramesh",     "LORA MESH",    "float",       "none",      "none",    "mesh",         "My web spans the whole valley now.")
_S(45, "bleflood",     "BLE FLOOD",    "arms_out",    "none",      "none",    "bluetooth",    "A thousand phantom devices. Choke on them.")
_S(46, "badusb",       "BADUSB",       "reach",       "none",      "none",    "usb",          "One touch, and the machine betrays its master.")
_S(47, "firmwaredump", "FIRMWARE DUMP","kneel",       "none",      "none",    "circuitbytes", "I read the very soul of the silicon.")
_S(48, "backdoor",     "BACKDOOR",     "point",       "none",      "none",    "cabinetkey",   "I leave a door only I can find.")
_S(49, "pivoting",     "PIVOTING",     "arms_out",    "none",      "none",    "pivot",        "From one, I reach them all.")
_S(50, "phantomroot",  "PHANTOM ROOT", "arms_raised", "void",      "crown",   "roottree",     "I am everywhere in the system now. I am its god.")

MAX_STAGE = len(STAGES)
_BY_LEVEL = {s["lvl"]: s for s in STAGES}


def stage_for(level: int) -> Dict[str, Any]:
    if level < 1:
        level = 1
    if level > MAX_STAGE:
        level = MAX_STAGE
    return _BY_LEVEL[level]


def sprite_of(stage: Dict[str, Any]) -> Dict[str, Any]:
    return {"eyes": "normal", "aura": stage["aura"], "pose": stage["pose"],
            "fx": stage["fx"], "prop": stage["prop"]}
