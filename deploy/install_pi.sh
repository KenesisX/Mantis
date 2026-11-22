#!/usr/bin/env bash
# =============================================================================
#  MANTIS — Raspberry Pi installer
#  Turns a fresh Raspberry Pi OS into a MANTIS handheld that boots straight
#  into the pet. Safe to re-run (idempotent).
#
#  Usage (from the project directory):
#     sudo bash deploy/install_pi.sh                 # e-ink 2.13" (default)
#     sudo bash deploy/install_pi.sh --display web   # web Command Deck on :8777
#     sudo bash deploy/install_pi.sh --display color # HyperPixel (framebuffer)
#
#  Options:
#     --display eink|web|color   what MANTIS drives          (default: eink)
#     --driver  auto|waveshare|inky   e-ink panel driver     (default: auto)
#     --rotate  0|90|180|270     screen rotation             (default: 0)
#     --port    N                web port                    (default: 8777)
#     --no-buttons               disable GPIO buttons (e-ink)
#     --pins "feed=5,..."        custom button pins
#     --no-enable                install but don't start/enable the service
# =============================================================================
set -euo pipefail

DISPLAY_MODE="eink"; DRIVER="auto"; ROTATE="0"; PORT="8777"
BTN_ARGS=""; DO_ENABLE="yes"
while [ $# -gt 0 ]; do
  case "$1" in
    --display) DISPLAY_MODE="$2"; shift 2;;
    --driver)  DRIVER="$2"; shift 2;;
    --rotate)  ROTATE="$2"; shift 2;;
    --port)    PORT="$2"; shift 2;;
    --no-buttons) BTN_ARGS="$BTN_ARGS --no-buttons"; shift;;
    --pins)    BTN_ARGS="$BTN_ARGS --pins $2"; shift 2;;
    --no-enable) DO_ENABLE="no"; shift;;
    *) echo "unknown option: $1"; exit 2;;
  esac
done

# --- who are we installing for? (the user who ran sudo, not root) ----------
TARGET_USER="${SUDO_USER:-${USER:-pi}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
[ -n "$TARGET_HOME" ] || TARGET_HOME="/home/$TARGET_USER"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="/opt/mantis/venv"
MANTIS_HOME="$TARGET_HOME/.mantis"

echo "=============================================="
echo "  MANTIS Pi installer"
echo "  user      : $TARGET_USER"
echo "  project   : $PROJECT_DIR"
echo "  display   : $DISPLAY_MODE   (driver=$DRIVER rotate=$ROTATE)"
echo "  venv      : $VENV"
echo "=============================================="

if [ "$(id -u)" -ne 0 ]; then echo "Please run with sudo."; exit 1; fi

# --- 1. system packages ----------------------------------------------------
echo "[1/6] apt packages..."
apt-get update -y
apt-get install -y --no-install-recommends \
  python3 python3-venv python3-pip python3-dev git \
  python3-pil python3-numpy \
  libopenjp2-7 libjpeg-dev zlib1g-dev fonts-dejavu-core ca-certificates
# GPIO lib: Bookworm ships rpi-lgpio (drop-in for RPi.GPIO); older uses rpi.gpio
apt-get install -y python3-rpi-lgpio 2>/dev/null || apt-get install -y python3-rpi.gpio 2>/dev/null || true

# --- 2. enable the right bus ----------------------------------------------
echo "[2/6] enabling hardware buses..."
if command -v raspi-config >/dev/null 2>&1; then
  if [ "$DISPLAY_MODE" = "eink" ]; then raspi-config nonint do_spi 0 || true; fi
  raspi-config nonint do_i2c 0 || true   # Inky / HyperPixel use I2C
fi

# --- 3. python venv (sees system PIL/numpy/gpio) ---------------------------
echo "[3/6] python environment..."
mkdir -p /opt/mantis
python3 -m venv --system-site-packages "$VENV"
"$VENV/bin/pip" install --upgrade pip >/dev/null
"$VENV/bin/pip" install "$PROJECT_DIR"          # installs the mantis package + data

# --- 4. panel driver -------------------------------------------------------
if [ "$DISPLAY_MODE" = "eink" ]; then
  echo "[4/6] e-ink driver..."
  if ! "$VENV/bin/python" -c "import waveshare_epd" 2>/dev/null \
     && ! "$VENV/bin/python" -c "import inky" 2>/dev/null; then
    if [ "$DRIVER" = "inky" ]; then
      "$VENV/bin/pip" install inky || true
    else
      TMP="$(mktemp -d)"
      git clone --depth 1 https://github.com/waveshareteam/e-Paper "$TMP/e-Paper" || true
      PYDIR="$TMP/e-Paper/RaspberryPi_JetsonNano/python"
      [ -d "$PYDIR" ] && (cd "$PYDIR" && "$VENV/bin/pip" install .) || \
        echo "  (!) Waveshare lib not installed — MANTIS will use the PNG preview fallback."
      rm -rf "$TMP"
    fi
  fi
else
  echo "[4/6] driver step skipped ($DISPLAY_MODE uses the framebuffer/web)."
fi

# --- 5. config + permissions ----------------------------------------------
echo "[5/6] config + permissions..."
sudo -u "$TARGET_USER" env MANTIS_HOME="$MANTIS_HOME" "$VENV/bin/python" -m mantis config init || true
# let the e-ink power-off hold-combo shut down without a password
echo "$TARGET_USER ALL=(root) NOPASSWD: /sbin/poweroff, /usr/sbin/poweroff" \
  > /etc/sudoers.d/mantis-poweroff
chmod 440 /etc/sudoers.d/mantis-poweroff

# --- 6. systemd service (generated for this host) --------------------------
echo "[6/6] systemd service..."
case "$DISPLAY_MODE" in
  eink)  EXEC="$VENV/bin/python -m mantis eink --interval 30 --rotate $ROTATE --driver $DRIVER$BTN_ARGS";;
  web)   EXEC="$VENV/bin/python -m mantis web --host 0.0.0.0 --port $PORT";;
  color) EXEC="$VENV/bin/python -m mantis color loop --interval 3";;
esac
cat > /etc/systemd/system/mantis.service <<EOF
# MANTIS — generated by install_pi.sh ($DISPLAY_MODE)
[Unit]
Description=MANTIS ($DISPLAY_MODE)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$TARGET_USER
WorkingDirectory=$PROJECT_DIR
Environment=MANTIS_HOME=$MANTIS_HOME
ExecStart=$EXEC
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
chown -R "$TARGET_USER":"$TARGET_USER" "$MANTIS_HOME" 2>/dev/null || true
systemctl daemon-reload
if [ "$DO_ENABLE" = "yes" ]; then
  systemctl enable --now mantis.service
fi

echo ""
echo "=============================================="
echo "  Done — MANTIS is installed."
echo "  service : systemctl status mantis"
echo "  logs    : journalctl -u mantis -f"
echo "  status  : $VENV/bin/mantis status"
case "$DISPLAY_MODE" in
  web)   echo "  open    : http://$(hostname -I 2>/dev/null | awk '{print $1}'):$PORT/";;
  color) echo "  screen  : driving /dev/fb0 (HyperPixel)";;
  eink)  echo "  panel   : driving the 2.13\" e-ink HAT";;
esac
[ "$DISPLAY_MODE" = "eink" ] && echo "  NOTE: if SPI was just enabled, reboot once:  sudo reboot"
echo "=============================================="
