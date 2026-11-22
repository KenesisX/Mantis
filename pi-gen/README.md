# Building a flashable MANTIS `.img`

This folder is a [pi-gen](https://github.com/RPi-Distro/pi-gen) **custom stage**
that bakes MANTIS into a standard Raspberry Pi OS image, so you get a single
`.img` you flash and boot — no post-install steps.

> Most people don't need to build this themselves. Either flash plain Raspberry
> Pi OS and run the one-line installer (see [`../INSTALL-PI.md`](../INSTALL-PI.md)),
> or grab a pre-built image from the repo's **Releases** (produced by the
> `Build Pi image` GitHub Action).

## What the stage does
`stage-mantis/` installs, inside the image:
- the MANTIS wheel into a venv at `/opt/mantis/venv` (with system Pillow/numpy/lgpio),
- the Waveshare e-Paper driver (for the e-ink build),
- `dtparam=spi=on` + `dtparam=i2c_arm=on` in the boot config,
- a `mantis.service` that **boots MANTIS on start** (e-ink by default; `web` or
  `color` selectable),
- passwordless poweroff for the e-ink hold-combo.

## Build in CI (recommended)
The included workflow [`.github/workflows/build-image.yml`](../.github/workflows/build-image.yml)
builds the image on GitHub's runners:
1. **Actions → Build Pi image → Run workflow**, choose the display (`eink` / `web`
   / `color`).
2. Download the `mantis-pi-image` artifact (a `.img.xz`).
3. Flash it with Raspberry Pi Imager ("Use custom") and boot.

Pushing a version tag (`vX.Y.Z`) also builds the image and attaches it to the
GitHub Release automatically.

## Build locally
On a Linux box with Docker:
```bash
git clone --depth 1 https://github.com/RPi-Distro/pi-gen
cd pi-gen
# build the MANTIS wheel and stage it
( cd /path/to/Mantis && pip install build && python -m build --wheel --outdir dist )
cp /path/to/Mantis/dist/mantis-*.whl /path/to/Mantis/pi-gen/stage-mantis/00-mantis/files/
# point pi-gen at the custom stage
cat > config <<'EOF'
IMG_NAME=mantis
RELEASE=bookworm
TARGET_HOSTNAME=mantis
FIRST_USER_NAME=mantis
FIRST_USER_PASS=mantis
ENABLE_SSH=1
STAGE_LIST="stage0 stage1 stage2 /path/to/Mantis/pi-gen/stage-mantis"
EOF
sudo MANTIS_DISPLAY=eink ./build-docker.sh
# the image lands in deploy/*.img
```

Flash the resulting image, boot, and MANTIS is alive on first power-up.
