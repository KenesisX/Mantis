#!/usr/bin/env bash
# One-shot installer for MANTIS on a Raspberry Pi with a 2.13" e-ink HAT.
set -e
echo "== MANTIS Pi installer =="

# 1. system deps
sudo apt-get update
sudo apt-get install -y python3-pip python3-pil python3-numpy python3-rpi.gpio git

# 2. enable SPI (needed by the e-ink HAT)
if ! lsmod | grep -q spi_bcm2835; then
  echo "Enabling SPI..."
  sudo raspi-config nonint do_spi 0 || true
fi

# 3. panel driver — Waveshare e-Paper (most common). Skip if you use Inky.
if ! python3 -c "import waveshare_epd" 2>/dev/null; then
  echo "Installing Waveshare e-Paper library..."
  TMP=$(mktemp -d)
  git clone --depth 1 https://github.com/waveshareteam/e-Paper "$TMP/e-Paper" || true
  if [ -d "$TMP/e-Paper/RaspberryPi_JetsonNano/python" ]; then
    (cd "$TMP/e-Paper/RaspberryPi_JetsonNano/python" && sudo python3 setup.py install)
  fi
fi
# Pimoroni Inky users instead:  pip3 install inky

# 4. install the pet + service
DEST=/home/pi/mantis
echo "Copying project to $DEST"
mkdir -p "$DEST"; cp -r ./* "$DEST"/
sudo cp deploy/mantis-eink.service /etc/systemd/system/
sudo systemctl daemon-reload
# allow the power-off hold-combo to shut down without a password
echo 'pi ALL=(root) NOPASSWD: /sbin/poweroff, /usr/sbin/poweroff' | sudo tee /etc/sudoers.d/mantis-poweroff >/dev/null
sudo chmod 440 /etc/sudoers.d/mantis-poweroff

# write a default config the user can edit
sudo -u pi MANTIS_HOME=/home/pi/.mantis python3 -m mantis config init || true

sudo systemctl enable --now mantis-eink

echo ""
echo "Done. MANTIS is now living on your e-ink panel."
echo "  logs:    journalctl -u mantis-eink -f"
echo "  status:  python3 -m mantis status"
echo "Reboot if SPI was just enabled:  sudo reboot"
