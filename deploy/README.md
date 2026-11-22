# MANTIS — install kit

Everything you need to get MANTIS running on a Raspberry Pi (or any Linux box),
from a one-liner to a fully-baked flashable image. For the full walkthrough see
[`../INSTALL-PI.md`](../INSTALL-PI.md).

## Pick your path

| You want… | Do this |
|---|---|
| **Flash & go** (zero steps after boot) | Grab the `.img.xz` from **Releases**, flash with Raspberry Pi Imager. Built by [`pi-gen/`](../pi-gen/README.md). |
| **Hands-free on plain Raspberry Pi OS** (no SSH) | Copy [`firstrun-mantis.sh`](firstrun-mantis.sh) onto the boot partition; it installs on first boot. |
| **One line over SSH** | `curl -sSL https://raw.githubusercontent.com/KenesisX/Mantis/main/deploy/bootstrap.sh \| bash` |
| **From a clone** | `sudo bash deploy/install_pi.sh` |
| **Desktop / dev machine** | `pip install ".[eink]"` then `python -m mantis web` |

## Files here

| File | What it is |
|---|---|
| `install_pi.sh` | The installer. Detects your user, enables SPI/I²C, builds a venv, installs the panel driver, and generates a **boot-on-start** `mantis.service`. Options: `--display eink\|web\|color`, `--driver auto\|waveshare\|inky`, `--rotate`, `--port`, `--no-buttons`, `--pins`. Safe to re-run. |
| `bootstrap.sh` | `curl \| bash` one-liner: clones the repo to `~/mantis` and runs the installer. Pass installer options after `-s --`. |
| `firstrun-mantis.sh` | Headless first-boot auto-installer for the SD card's boot partition — no SSH needed. Logs to `mantis-install.log` on the boot drive. |
| `mantis-eink.service` | Reference systemd unit — e-ink 2.13" handheld. |
| `mantis-web.service` | Reference systemd unit — web Command Deck on `:8777`. |
| `mantis-color.service` | Reference systemd unit — HyperPixel colour (framebuffer daemon). |
| `mantis-agent.service` | Reference systemd unit — fleet self-telemetry to a hub you own. |

## After install

```bash
systemctl status mantis       # running?
journalctl -u mantis -f       # live logs
/opt/mantis/venv/bin/mantis status
```

- **e-ink:** the pet is on the panel; buttons work out of the box.
- **web:** open `http://mantis.local:8777/` → the Command Deck (installable as an
  app). The touch **Remote** is at `/remote`.
- **colour:** MANTIS is drawn to `/dev/fb0`.

Everyone starts at **level 0** and earns everything in play — saves are
tamper-evident, so edited (cheated) units are flagged when they duel.
