# 🔥 Burn MANTIS to a Raspberry Pi

MANTIS runs on a Raspberry Pi and boots straight into the pet — on a **2.13"
e-ink HAT**, a **Pimoroni HyperPixel** colour screen, or as a **web Command
Deck** you open from your phone. This guide takes you from a blank microSD card
to a living MANTIS.

> There is no custom `.img` to download — you flash **standard Raspberry Pi OS**
> (which you trust and can update) and MANTIS installs itself on top. This is the
> same, safe approach Bjorn uses, and it works on **Pi Zero 2 W, Pi 3, 4, and
> 5**. (A Pi Zero 2 W + a Waveshare 2.13" HAT is the classic handheld build.)

---

## What you need
- A Raspberry Pi (Zero 2 W / 3 / 4 / 5) + microSD card (8 GB+).
- One display:
  - **Waveshare 2.13" e-Paper HAT** (the handheld look), **or**
  - **Pimoroni Inky** 2.13", **or**
  - **Pimoroni HyperPixel 4.0** (800×480 colour), **or**
  - **nothing** — just use the web Command Deck.
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on your computer.

---

## Step 1 — Flash Raspberry Pi OS
1. Open **Raspberry Pi Imager**.
2. **Choose OS →** *Raspberry Pi OS (other)* → **Raspberry Pi OS Lite (64-bit)**
   (no desktop needed; Lite is lighter and boots faster). For a HyperPixel you
   may prefer the full desktop version.
3. **Choose Storage →** your microSD card.
4. Click the **⚙ gear / "Edit Settings"** (advanced options) and set:
   - **Hostname:** `mantis`
   - **Enable SSH** → *Use password authentication*
   - **Username & password** (remember these — e.g. user `pi`)
   - **Wi-Fi SSID + password** (and your country)
   - **Locale / timezone**
5. **Save → Write.** When it finishes, keep the card in your computer for Step 2
   if you want the hands-free install; otherwise skip to Step 3.

---

## Step 2 — (Optional) Hands-free, no-SSH install
Make MANTIS install itself on first boot, with nothing to type:

1. After flashing, the card re-mounts as a small **`bootfs`** drive. Open it.
2. Copy **`deploy/firstrun-mantis.sh`** from this repo onto that drive.
3. Open the file **`firstrun.sh`** that Imager created on the same drive and add
   this as the **last line before `exit 0`**:
   ```bash
   bash /boot/firmware/firstrun-mantis.sh || bash /boot/firmware/../firstrun-mantis.sh &
   ```
   (On older OS versions the boot drive is `/boot` instead of `/boot/firmware`.)
4. Eject the card, put it in the Pi, power on. First boot installs MANTIS and
   starts it automatically. Progress is logged to **`mantis-install.log`** on the
   boot drive. Give it 5–10 minutes on the first boot.
   *Default display is e-ink; for web/colour set `MANTIS_DISPLAY=web` (or
   `color`) at the top of `firstrun-mantis.sh`.*

> Prefer the simple route? Skip Step 2 and use Step 3.

---

## Step 3 — One-line install over SSH
Put the card in the Pi, power on, wait a minute, then from your computer:

```bash
ssh pi@mantis.local         # or ssh pi@<pi-ip-address>
```

Then run **one** of these:

```bash
# e-ink 2.13" handheld (default)
curl -sSL https://raw.githubusercontent.com/KenesisX/Mantis/main/deploy/bootstrap.sh | bash

# web Command Deck (open http://mantis.local:8777 from any device)
curl -sSL https://raw.githubusercontent.com/KenesisX/Mantis/main/deploy/bootstrap.sh | bash -s -- --display web

# HyperPixel colour screen (drives the framebuffer directly)
curl -sSL https://raw.githubusercontent.com/KenesisX/Mantis/main/deploy/bootstrap.sh | bash -s -- --display color
```

That clones the repo to `~/mantis` and runs the installer. If SPI was just
enabled for an e-ink HAT, reboot once: `sudo reboot`.

### Already cloned the repo?
```bash
cd ~/mantis
sudo bash deploy/install_pi.sh                 # e-ink (default)
sudo bash deploy/install_pi.sh --display web   # or web / color
```

Installer options: `--display eink|web|color`, `--driver auto|waveshare|inky`,
`--rotate 0|90|180|270`, `--port 8777`, `--no-buttons`, `--pins "feed=5,…"`.

---

## Step 4 — It's alive
MANTIS now runs as a service and starts on every boot.

```bash
systemctl status mantis          # is it running?
journalctl -u mantis -f          # live logs
/opt/mantis/venv/bin/mantis status
```

- **e-ink:** the pet is on the panel. Buttons (feed / meditate / pet / cast /
  deed) work out of the box; hold **pet+deed** for the on-device settings menu,
  **cast+pet** to power off, **meditate+pet** to toggle passive/active mode.
- **web:** open `http://mantis.local:8777/` → the Command Deck.
- **HyperPixel:** the pet is drawn to the screen; attach a keyboard or use the
  web deck for controls.

---

## Wiring notes
- **Waveshare 2.13" HAT:** seats on the 40-pin header; uses **SPI** (enabled by
  the installer). If the panel stays blank, `sudo raspi-config` → Interface →
  SPI → enable, then reboot. Set `--driver waveshare`.
- **Pimoroni Inky:** uses **I²C + SPI**; install with `--driver inky`.
- **HyperPixel 4.0:** uses the full GPIO header (no other HAT at the same time);
  the colour service writes to `/dev/fb0`.
- **Buttons (optional, e-ink):** wire momentary buttons from a GPIO pin to GND.
  Defaults: `feed=5, meditate=6, pet=16, cast=24, deed=26` (BCM). Change with
  `--pins`.
- **Battery (optional):** a PiSugar or similar is auto-detected; see the main
  README's battery section.

---

## Updating
```bash
cd ~/mantis && git pull
sudo bash deploy/install_pi.sh --display <your-mode>   # re-runs safely
sudo systemctl restart mantis
```

## Uninstall
```bash
sudo systemctl disable --now mantis
sudo rm /etc/systemd/system/mantis.service /etc/sudoers.d/mantis-poweroff
sudo rm -rf /opt/mantis ~/mantis ~/.mantis
```

---

## Troubleshooting
| Symptom | Fix |
|---|---|
| e-ink stays blank | enable SPI (`sudo raspi-config`), reboot; check the HAT is fully seated; try `--driver waveshare` |
| `No module named waveshare_epd` | re-run the installer; it falls back to a PNG preview in `~/.mantis/` meanwhile |
| buttons do nothing | check BCM pin numbers and that each button goes to **GND**; pass `--pins` |
| service won't start | `journalctl -u mantis -e` — usually a wrong display mode or a missing driver |
| HyperPixel black | confirm `/dev/fb0` exists (`ls /dev/fb*`); HyperPixel overlay must be installed per Pimoroni's docs |
| want it on a different screen | re-run `sudo bash deploy/install_pi.sh --display web` (or `color`/`eink`) |

Passive &amp; defensive only — MANTIS performs no attacks, injection, or cracking.
