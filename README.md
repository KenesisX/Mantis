# 🧠 MANTIS

> *"I can read your mind..."*

A **Tamagotchi-style psychic companion** — a moody, autonomous virtual pet in the
lineage of the handheld recon-pets (pwnagotchi's expressive face & autonomous
life, Bjorn's tool/task list, and the old-school terminal-pet aesthetic), all
re-skinned as **Mantis of FIREFOX**.

He lives on his own, senses the ether around him, gains **XP** across **100
psychic levels** (capped by the title **MANTIS**), cycles through **70
moods**, unlocks a **spellbook** of tools, commits fictional villain **deeds**
(possessions, kidnappings, severings) for **souls**, spends souls on permanent
**augments**, grows a **darkness** meter, and reacts to you with a full-body
floating figure, emotions, mannerisms and phrases in his voice.

Runs **anywhere Python 3.8+ runs**, with **zero dependencies** (standard library
only). Two front-ends: a slick **web dashboard** (gas-mask face, CRT scanlines,
psychic effects) and a live **terminal UI**.

---

## ⚡ Quick start

```bash
cd mantis
python3 -m mantis          # web dashboard → http://127.0.0.1:8777
```

or the launcher:

```bash
./run.sh            # web (default)
./run.sh tui        # terminal pet
```

Open the printed URL in any browser. The default page is the **Command Deck** —
a real-time operator console (hero portrait, live PSYCHE ring, the live activity
stream, a 50-function activity deck, the evolution ladder, security posture, the
Inner Mind coach, Academy, and fleet) that goes well beyond a pwnagotchi/Bjorn
dashboard. The original panel view is still at **`/classic`**.

---

## 🎮 What you can do

| Care action | Effect |
|-------------|--------|
| 🧠 **Feed** | restores psychic *hunger* |
| 🌙 **Rest** | restores *energy* |
| 🧘 **Meditate** | restores *focus* + *sanity* and charges **PSYCHE** |
| 🤍 **Pet** | restores *sanity* (he's fragile) |
| 💬 **Speak** | pull a fresh line from his mind |

He also **acts on his own** (pwnagotchi-style): while running he periodically
*senses the ether* and gains XP without you.

### Needs & mood
Four needs decay over real time — **hunger, energy, focus, sanity** — plus a
**PSYCHE** power meter you spend on spells. His **mood** (watching, smug, hungry,
sleeping, distracted, broken, overcharged, casting…) changes his **face** and the
**phrases** he speaks.

### 🧬 50 evolution stages (cyber-activity cards)
Every level 1→50 is a named **evolution stage** — a full-body pose plus a themed
1-bit scene drawn on the e-ink, exactly like a card: `BOOTING · IDLE · SCANNING ·
SNIFFING · PROBING · MAPPING · LISTENING · PINGING · HANDSHAKE · DEAUTH ·
INJECTING · SPOOFING · JAMMING · BRUTEFORCE · CRACKING · EXPLOITING · BYPASSING ·
ESCALATING · ROOTED · PAYLOAD · HARVESTING · EXFILTRATING · WIPING · STEALTH ·
OVERCLOCKED · WARDRIVING · BEACONING · EVIL TWIN · MITM · ARP SPOOF · DNS HIJACK ·
PORT SCAN · VULN AUDIT · SSH BRUTE · SMB ENUM · SQL INJECT · XSS PROBE ·
REVERSE SHELL · KEYLOGGING · DUMPING HASH · RAINBOW CRACK · RF REPLAY ·
SUB-GHZ SCAN · LORA MESH · BLE FLOOD · BADUSB · FIRMWARE DUMP · BACKDOOR ·
PIVOTING · PHANTOM ROOT`. On every level-up the panel shows the new stage card
as an **evolution reveal** (press any button to dismiss). The current stage also
shows under the pet's name on the status screen and as a browsable gallery in the
web dashboard.

```bash
python3 -m mantis stages     # list all 50 with the current marked
python3 -m mantis gallery    # bake all 50 cards + a contact-sheet gallery
```

### ⚙️ 50 activities — every stage is a real function
Each of the 50 stages is also a **runnable activity** the pet performs — it
produces a report, costs PSYCHE, awards XP, advances the pet, and surfaces a
matching **teaching moment** from the Academy:

```bash
python3 -m mantis activities        # the 50-function deck, locked/unlocked + kind
python3 -m mantis do scanning       # perform one (once you've grown into it)
python3 -m mantis do vulnaudit      # audits YOUR OWN posture (defensive)
```

Activities come in three kinds, colour-coded everywhere:

* **⟢ passive** — real, benign, read-only observation (listing Wi-Fi the air
  already broadcasts, mapping *your own* subnet, auditing *your own* ports,
  receive-only RF). Safe to run anywhere.
* **🛡 defense** — audits *your own* security posture.
* **◈ sim** — the offensive-sounding stages (deauth, evil-twin, sql-inject,
  badusb, …) are **psychic theatre**: simulated against *invented* targets with
  fabricated data. Nothing sends an attack, injects, transmits RF, cracks a
  credential, or touches a real third-party system — each is lore **plus** a
  real lesson on how to defend against it.

### 🌗 Passive / Active idle modes
MANTIS has two idle modes, like a real recon-pet:

```bash
python3 -m mantis mode             # show current mode
python3 -m mantis mode active      # autonomous — hunts the ether on its own
python3 -m mantis mode passive     # quiet watch — only senses passively, acts on command
```

In **active** mode the pet autonomously performs activities it has grown into
(you watch it work in the live stream). In **passive** mode it stays quiet and
only acts when you ask. Toggle it from the web **mode switch**, the CLI, or the
e-ink **meditate+pet** button combo.

> The stage names are **cosmetic evolution art and lore**, and the activities
> are **passive / defensive / simulated** — no stage performs any real attack.

### 🧠 The Inner Mind — adaptive coaching AI
A self-contained (offline) learning engine watches how you play, infers your
**style** (Operator, Defender, Learner, Listener, Shadow, Caretaker, Explorer),
and after **every action suggests your next move** — weighted toward your
interests and your knowledge gaps, and away from advice you keep ignoring. Most
suggestions **teach** (they tie an action to the concept behind it). It needs no
external AI service — it runs privately on-device.

```bash
mantis coach      # your style + the next 3 adaptive suggestions (with commands)
```

In the web dashboard it's the **INNER MIND** panel: clickable suggestion cards
that run the move and immediately surface the next ones — a live learning loop.
It adapts: cast lots of recon and he leans "Operator"; do lessons and he becomes
a "Learner" and pushes study; ignore a suggestion repeatedly and he stops nagging.

### 🎓 Academy — learn real cybersecurity as you play
MANTIS teaches you the **actual concept behind each themed spell** and walks you
up a cert-aligned ladder from **Script Kiddie → Security+ / CySA+ / PenTest+ /
CISSP tracks → Principal Security Expert**. 28 lessons across ethics, networking,
crypto/PKI, web, blue-team, red-team and RF — each with a plain-language
explanation, a practical tip, and a **quiz** that grants *knowledge* and advances
your rank. Casting a spell surfaces a **teachable moment** explaining what the
technique really is.

```bash
python3 -m mantis learn        # next lesson + quiz (interactive)
python3 -m mantis learn tls    # a specific lesson
python3 -m mantis academy      # your rank, progress and the full curriculum
```

It's also a full panel in the **web dashboard** (lesson card + clickable quiz,
live rank bar) and your Academy rank shows on the e-ink **About** screen. Ethics
first: the very first lesson is *authorization and legality* — this is white-hat
education throughout.

### 70 moods
His **mood** is chosen contextually from 70 states across clusters — idle,
content, smug, hunger, low-energy, low-focus, low-sanity, broken, overcharged,
dark, and event moods (casting, possessing, hunting, severing, kidnapping,
harvesting, enraged, grieving, ascending). Each drives a distinct **full-body
pose, eyes, aura and floating effect** on the e-ink, plus its own phrase bank.
High **darkness** pushes him toward sinister, cruel and wrathful moods.

### 100 levels & ranks
Every action, spell and deed grants XP across **100 levels**. Ranks climb from
`Dormant Psyche → Telepath → Mind Render → Nightmare Weaver → Puppeteer →
Soul Harvester → Void Seer → Mind Tyrant → Most Powerful Psychic →` and finally
**`MANTIS`** at level 100 (with ✦ prestige stars beyond).

### 🖤 Dark deeds, souls & darkness  *(pure fiction)*
At higher levels he can perform villain **deeds** on *invented* NPC minds —
**Haunt, Possess, Kidnap, Sever** — plus **Harvest** captured minds into
**◇ souls**. Deeds raise his **darkness** and **infamy**, add **kills /
kidnappings / possessions** counters, and feed his legend.

> These deeds are **theatrical fiction** acting on randomly-named fictional
> characters. They are completely separate from the real recon tools and touch
> no real person, network or device.

### 🕯 Augments (the shop)
Spend souls on **8 permanent upgrades** (each multi-tier): Psyche Well (+max
PSYCHE), Deep Mind (regen), Sharpened Will (+XP), Iron Sanity, Soul Eater
(+souls/deed), Hungerless Flesh, Dark Mastery (cheaper deeds), Dread Aura.

---

## 📖 The Spellbook (tools)

Each spell is a **real but deliberately safe/benign** operation:

| Spell | Lv | What it really does |
|-------|----|---------------------|
| 👁 **Mind Reading** | 1 | Lists nearby **Wi-Fi networks** — passive read-only, the same list your phone shows |
| 🔮 **Clairvoyance** | 2 | Maps **your own** local subnet (host discovery / "who's on my Wi-Fi") |
| 🛡 **The Veil** | 3 | Audits **your own machine's** open ports and flags risky ones (defensive) |
| 📡 **Telepathy** | 4 | Pings devices you already know to see which are "present" |
| 🌌 **Astral Projection** | 5 | `traceroute` to a host — maps the path your packets take |
| 💠 **Hydro-Quartz Gaze** | 6 | DNS resolution of a name |
| ✨ **Psychokinesis** | 7 | Cosmetic "move the controller" theatre (no network action) |
| 🔥 **Soul Scream** | 10 | Ultimate — dramatic psychic cry, huge XP (purely theatrical) |

> **Safety by design.** MANTIS contains **no** deauthentication, packet
> injection, monitor-mode capture, handshake harvesting, password-cracking,
> exploitation, spoofing, jamming, evil-twin or BadUSB code. Those offensive
> "Bjorn/Kali" capabilities are intentionally left out. Everything here is
> **passive or receive-only**: listing visible networks, scanning *your own*
> machine/LAN, listening to public RF broadcasts, reading local logs, and
> ordinary diagnostics any user may run. Missing tools fall back to simulation.

---

## 🖤 Raspberry Pi e-ink (2.13") — the real handheld

MANTIS renders a **pure 1-bit black/white**, full-body **floating
Mantis figure** — gas-masked head, leather coat with tattered tails,
arms posed by mood, bare dangling feet, and a psychic aura — sized exactly for
the **250×122 2.13" e-paper** panels (Waveshare e-Paper HAT or Pimoroni Inky
pHAT), just like a pwnagotchi. Across the **70 moods** his pose, eyes, aura and
floating effects all change: arms raised + lightning when overcharged, a curled
fetal ball when grieving, chains when kidnapping, a skull when cruel, a crown
when a tyrant, Zzz asleep, cracked lenses when broken, psi-waves + a tarot card
when casting. The panel also shows PSYCHE / XP / **DARKNESS** bars, souls,
infamy, and kill / kidnap / possession counts.

Preview every face without hardware:

```bash
python3 -m mantis faces        # writes PNGs + a contact sheet
```

Run it on the panel (auto-detects Waveshare, then Inky, else writes previews):

```bash
python3 -m mantis eink --interval 30 --rotate 0
```

One-command Pi install (deps, SPI, driver, auto-start service):

```bash
cd mantis && ./deploy/install_pi.sh
```

That installs a **systemd service** (`deploy/mantis-eink.service`) so the
Mantis boots with the Pi and keeps living on the screen. Hardware extras are in
`requirements-eink.txt` (only needed for the physical panel — the web/terminal
pet need nothing). The renderer refreshes **only when his face/phrase/level
changes**, to spare the e-ink from ghosting and wear.

Panel wiring: seat the 2.13" HAT on the 40-pin header, `sudo raspi-config` →
Interface → **SPI on**, reboot. Waveshare V2/V3/V4 and Inky pHAT are
auto-detected; force one with `--driver waveshare` or `--driver inky`.

### 🎛️ Physical buttons + idle animation

Five GPIO buttons map to actions (auto no-op if no GPIO):

| Button | Action | Default pin (BCM) |
|--------|--------|-------------------|
| 1 | 🧠 Feed | GPIO 5 |
| 2 | 🧘 Meditate | GPIO 6 |
| 3 | 🤍 Pet | GPIO 16 |
| 4 | ✦ Cast best spell | GPIO 24 |
| 5 | ☠ Commit a dark deed | GPIO 26 |

Buttons and a **2-frame idle float animation** (he gently bobs while calm) are
**on by default** in `eink` mode. Change pins or turn features off:

```bash
python3 -m mantis eink --pins "feed=5,meditate=6,pet=16,cast=24,deed=26"
python3 -m mantis eink --no-buttons --no-animate
```

Wire each button between its GPIO pin and **GND** (internal pull-ups are
enabled). Needs `RPi.GPIO` (installed by `deploy/install_pi.sh`).

**Combo shortcuts** — hold two buttons together:

| Hold | Shortcut |
|------|----------|
| Feed + Pet | 🕊 Soothe (big sanity restore, darkness down) |
| Feed + Meditate | ⚡ Power surge (PSYCHE to max, +focus/energy) |
| Meditate + Deed | 🕯 Quick-buy cheapest affordable augment |
| Cast + Deed | 💀 Harvest captured souls |
| Cast + Meditate | ℹ️ **About screen** — version + identity + lifetime stats on the panel |
| **Hold Pet + Deed (3s)** | ⚙️ **Settings menu** — edit config on-device, no keyboard |
| **Hold Cast + Pet (3s)** | ⏻ **Safe power-off** — saves, shows a shutdown screen, then `poweroff` |

### ⚙️ On-device settings menu
Hold **Pet + Deed** to open a settings menu right on the e-ink — no keyboard:
**Meditate/Cast** move between fields, **Feed/Pet** change the value, **Deed**
saves to `config.toml`. Edit panel driver, rotation, refresh rate, splash,
animation, slideshow, power-off combo, battery thresholds and battery source.
Changes to timing/animation apply live; driver/rotation apply on restart.

### 📻 Receive-only RF spells (RTL-SDR / Xenu flavour)
With an RTL-SDR dongle you get four **listen-only** spells in the spellbook —
**Ether Attunement** (probe the SDR + noise floor), **Sub-GHz Whisper**
(`rtl_433` ISM reception: weather/sensor/TPMS telemetry on 315/433/915 MHz),
**LoRa Mesh Whisper** (reads local Meshtastic logs), and **Sky-Mind 1090**
(ADS-B aircraft from a local `dump1090` feed). They **only receive / read** —
no transmit, replay, jamming or injection — and simulate when no SDR is present.

### 🛡 Defensive spells (blue-team, read-only)
Protective "ward" spells that check security posture without touching anything:
- **Astral Seal** — reads a site's TLS certificate and warns how many days until it expires.
- **Aegis Ward** — audits *your own* firewall status and listening ports, and flags risky ones.
- **Ward of Truth** — checks whether a domain is protected by **DNSSEC**.
- **Veil of Headers** — reads a site's HTTP security headers (HSTS, CSP, X-Frame-Options…) and names what's missing.

All are passive inspections (or an ordinary GET), with simulation fallback offline.

**Posture score** — the four ward results roll up into one **A–F security grade**
(0–100). See it with `python3 -m mantis posture` (lists which wards still need
casting), on the e-ink via the **Feed + Cast** combo, and in the web dashboard's
stats panel + the **POSTURE** tab. Un-cast wards are "unknown" and don't count
against the grade until you check them.

### 🖼️ Use your OWN sprite art (drop-in, or slice a sheet)
MANTIS draws a procedural gas-mask figure by default, but you can replace it with
**your own graphics** — they're used everywhere (e-ink status, stage cards, the
color HyperPixel display, and the web mirror).

Two ways:

1. **Drop in files** — put 1-bit-friendly PNG/BMP images in `~/.mantis/sprites/`
   named by what they replace:
   - `stage_<key>.png` for an evolution stage (keys: run `mantis stages`, e.g. `stage_wardriving.png`)
   - `mood_<name>.png` for a mood (names: e.g. `mood_watching.png`, `mood_overcharged.png`)

2. **Slice a grid sheet** — have a 5×5 sheet like the LV1–50 cards? Export a clean
   PNG (no watermark) and let MANTIS cut it into the right sprites:
   ```bash
   mantis slice lv1-25.png   --rows 5 --cols 5 --start 1     # LV1–25
   mantis slice lv26-50.png  --rows 5 --cols 5 --start 26    # LV26–50
   mantis sprites            # list what's installed
   ```
   `--label-pct` trims a baked-in label bar at each cell's bottom (default 0.16),
   `--trim-pct` trims cell borders, `--kind mood` targets moods instead of stages.

Sprites are picked up live (a running `eink` loop reloads changed files). Remove
a file to fall back to the procedural figure.

### 🎨 Themes (incl. black & white)
Switch the whole look from the dashboard's header dropdown, the `mantis theme`
command, or `[web] theme` in the config. Four themes, applied to the web UI **and**
the color HyperPixel display:
- **`red`** — red/black FIREFOX (default)
- **`mono`** — stark **black & white**, high-contrast
- **`green`** — the original green/magenta terminal
- **`amber`** — amber/orange CRT

```bash
mantis theme mono      # set it; persists in config
mantis theme           # show current + options
```
The e-ink panel is physically 1-bit, so it's always black & white (your sprite
art shows the same regardless of theme).

### 🎨 Color display (Pimoroni HyperPixel) + remote console
MANTIS isn't only e-ink. A **full-color renderer** (`mantis/color.py`, default
800×480, HyperPixel-ready) draws the figure as a green-CRT ghost with colored
bars, posture grade, academy rank and your personalized phrase.

- **`/color`** — a full-screen page for a **HyperPixel** (run a kiosk browser at it).
- **`/color.png`** — live color frame. **`/epaper.png`** — live e-ink frame.
- **`/remote`** — a **VNC-style remote console** for *your own device*: it live-mirrors
  both screens and gives you working controls (feed, meditate, cast, harvest, posture).
- `python3 -m mantis color` bakes a preview; `mantis color fb` best-effort blits to `/dev/fb0`.

Runs on RPi Zero 2W / 2 / 3 / 4 / 5, Jetson, uConsole, desktop Linux/Windows, and
Android (Termux) — it's pure Python.

### 📡 More SDR receivers (receive-only)
`Ether Attunement` now detects **RTL-SDR (incl. Blog V4 R828D), HackRF One,
USRP/Ettus, Airspy, and any SoapySDR device** (LimeSDR, PlutoSDR, SDRplay…).
MANTIS only ever **listens** — it never drives transmit/replay/jamming. `mantis
version` lists detected SDRs.

### 🕸 Your own fleet (consensual telemetry — not a botnet)
Other devices **you own** can run MANTIS and feed XP/telemetry to one another via
`POST /api/push_xp`. This is opt-in monitoring of gear you control — MANTIS does
**not** reach into, control, or pull files from devices that aren't yours, and
contains no offensive / "black-hat" capability. That line is deliberate.

### 🛰 Fleet — monitor your own devices
Run MANTIS on every device you own (Pi, Jetson, laptop…) and have them report
their *own* telemetry to one hub, shown as a live roster on the dashboard and
`mantis fleet`.

```bash
# on the HUB (the MANTIS you watch):
mantis fleet key --out <shared-secret>     # enable the fleet with a shared key
mantis web                                  # roster appears in the FLEET panel

# on each OTHER device you own:
mantis agent --hub http://<hub-ip>:8777 --key <shared-secret> --interval 60
```

Each agent reports only about **itself** — hostname, platform, level, posture
grade, battery, uptime, version. There is **no remote control, no file access,
and no scanning of anyone else's devices**; a device can't even report without
your shared key. It's consensual monitoring of gear you own, nothing more.
A ready `deploy/mantis-agent.service` auto-starts the agent on boot.

### ⌚ Companion views
- **`/watch`** — a circular high-contrast page for a Galaxy Watch / small screen.
- **`/epaper.png`** — a live PNG mirror of the e-ink screen (for VNC / remote view).
- **`POST /api/push_xp`** — let other gadgets feed XP in: `{"rf_captures":1,"ble_beacons":5,"wpa_handshakes":1}`.

The power-off combo must be *held* (default 3s); releasing early cancels it. Tune
with `[eink] poweroff_combo` / `poweroff_hold` in the config, or `--no-poweroff`.
The Pi installer grants passwordless `poweroff` so it works from the handheld.

### 🔋 Battery indicator + deep-sleep

If the handheld has a battery gauge, a **battery icon** shows on the e-ink (and
a chip in the web header). Sources are auto-detected in order: `MANTIS_BATTERY`
env, a `MANTIS_BATTERY_CMD` command, a `~/.mantis/battery` file, or a
**PiSugar 2/3** (socket `127.0.0.1:8423`). No gauge → the indicator is simply hidden.

Power management kicks in automatically:
- **≤ 20 %** → low-power mode: refreshes slow 4×, idle animation off, autonomous sensing paused.
- **≤ 6 %** (and not charging) → **hibernate**: draws a sleeping screen, puts the
  e-ink panel into deep sleep, and only wakes on a button press or when power returns.

Tune with `--low-battery 20 --sleep-below 6`. Test the states on a laptop with
`MANTIS_BATTERY=4 python3 -m mantis eink`.

## ⚙️ Config file (`~/.mantis/config.toml`)

Easiest: run the **setup wizard** once — it asks for panel type, rotation, pins,
battery source, web host/port and the feature toggles, then writes the config:

```bash
python3 -m mantis setup           # interactive first-run wizard
```

Or manage the file directly:

```bash
python3 -m mantis config init     # write a commented default config
python3 -m mantis config          # show the config path + effective settings
```

A `[battery]` section lets you pin the source (`auto`, `none`, `pisugar`,
`file`, or a `command`). Everything is set once and reused on every run.

```toml
[eink]
interval = 30            # seconds between full status refreshes
driver = "auto"          # auto | waveshare | inky
buttons = true
animate = true           # idle float bob
splash = true            # boot splash
slideshow = true         # calm pet flips through unlocked stage cards
slideshow_interval = 25
low_battery = 20         # <= % -> low-power mode
sleep_below = 6          # <= % -> hibernate

[buttons]                # GPIO pins (BCM)
feed = 5
meditate = 6
pet = 16
cast = 24
deed = 26

[web]
host = "127.0.0.1"
port = 8777
```

Precedence (low → high): **built-in defaults → config.toml → env vars → CLI flags**,
so a flag like `--interval 10` always wins over the file. The Pi installer writes
this file for you. State lives beside it in `~/.mantis/` (override with `MANTIS_HOME`).

## 🖥️ CLI reference

```bash
python -m mantis            # web dashboard (default)
python -m mantis web --port 9000 --host 0.0.0.0
python -m mantis eink        # drive the Pi 2.13" e-ink panel
python -m mantis faces       # bake the 1-bit mood faces to PNG
python -m mantis tui        # live terminal pet
python -m mantis status     # one-shot status
python -m mantis spells      # list the spellbook
python -m mantis cast mind_reading
python -m mantis activities  # the 50-function activity deck (locked/unlocked)
python -m mantis do scanning # perform one of the 50 stage activities
python -m mantis mode active|passive   # autonomous hunting vs. quiet watch
python -m mantis feed|rest|meditate|pet
python -m mantis install           # friendly first-run wizard (profiles you + MANTIS)
python -m mantis read              # MANTIS reads you (interests/experience)
python -m mantis persona           # show your keeper profile + his traits
python -m mantis color             # render a color (HyperPixel) preview
python -m mantis setup             # hardware config wizard
python -m mantis config init       # write ~/.mantis/config.toml
python -m mantis config            # show effective settings
python -m mantis version           # version + Python/deps/driver/battery
python -m mantis selfcheck         # verify every module imports & renders (Pi health check)
python -m mantis posture           # security posture grade (A-F) from the ward spells
python -m mantis learn             # interactive lesson + quiz (the Academy)
python -m mantis academy           # learning rank, progress and curriculum
python -m mantis possess|kidnap|sever|haunt   # dark deeds (fiction)
python -m mantis harvest                       # convert captives → souls
python -m mantis shop                          # list augments
python -m mantis buy psyche_well               # purchase an augment
```

State is saved to `~/.mantis/soul.json` (override with `--home` or the
`MANTIS_HOME` env var). He remembers everything between sessions — his
level, his relics, the minds he's heard.

---

## 🧩 Architecture

```
mantis/
├── __main__.py      CLI dispatch
├── engine.py        pet state, needs decay, XP/levels, persistence, event log
├── personality.py   faces, moods, ranks, the Mantis voice
├── spells.py        the spellbook — safe passive tools + fallbacks
├── tui.py           live terminal interface (ANSI)
├── server.py        stdlib HTTP server: JSON API + autonomous ticker
└── web/             index.html · style.css · app.js  (the dashboard)
```

No pip install required. No internet required. Pure Python + one HTML page.

An original, non-commercial creation. MANTIS, its artwork, lore, and characters
are invented for this project; any resemblance to other works is coincidental.
