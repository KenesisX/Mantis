#!/usr/bin/env bash
# =============================================================================
#  MANTIS — headless first-boot auto-installer.
#
#  Copy this file onto the BOOT partition of a freshly-flashed Raspberry Pi OS
#  card (it shows up as a small FAT drive on your computer right after flashing)
#  and append this to the END of the boot "firstrun.sh" the Raspberry Pi Imager
#  creates — OR enable it as a one-shot systemd service as described in
#  INSTALL-PI.md. On first boot MANTIS installs itself and starts, with no SSH.
#
#  It writes progress to /boot/mantis-install.log so you can check it from your
#  computer if anything goes wrong.
# =============================================================================
set -uo pipefail
LOG=/boot/firmware/mantis-install.log
[ -d /boot/firmware ] || LOG=/boot/mantis-install.log
exec >>"$LOG" 2>&1
echo "=== MANTIS firstrun $(date) ==="

# wait for the network (needed to fetch dependencies)
for i in $(seq 1 30); do
  if ping -c1 -W2 github.com >/dev/null 2>&1; then break; fi
  echo "waiting for network ($i)..."; sleep 5
done

# pick the first normal login user (the one created by Raspberry Pi Imager)
TARGET_USER="$(getent passwd 1000 | cut -d: -f1)"
[ -n "$TARGET_USER" ] || TARGET_USER=pi

REPO="${MANTIS_REPO:-https://github.com/KenesisX/Mantis}"
BRANCH="${MANTIS_BRANCH:-main}"
DISPLAY_MODE="${MANTIS_DISPLAY:-eink}"
DEST="/home/$TARGET_USER/mantis"

apt-get update -y
apt-get install -y git

if [ ! -d "$DEST/.git" ]; then
  git clone --depth 1 --branch "$BRANCH" "$REPO" "$DEST"
  chown -R "$TARGET_USER":"$TARGET_USER" "$DEST"
fi

bash "$DEST/deploy/install_pi.sh" --display "$DISPLAY_MODE"
echo "=== MANTIS firstrun complete $(date) ==="
