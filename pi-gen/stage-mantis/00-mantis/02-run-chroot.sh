#!/bin/bash -e
# In-chroot: install MANTIS into a venv, enable SPI/I2C, and set it to boot on start.

USER_NAME="$(cat /opt/mantis/.user 2>/dev/null || echo mantis)"
DISPLAY_MODE="$(cat /opt/mantis/.display 2>/dev/null || echo eink)"
HOME_DIR="/home/${USER_NAME}"
VENV="/opt/mantis/venv"

# --- venv (sees the system PIL/numpy/lgpio installed via apt) ---------------
python3 -m venv --system-site-packages "${VENV}"
"${VENV}/bin/pip" install --upgrade pip >/dev/null
if ls /opt/mantis/mantis-*.whl >/dev/null 2>&1; then
	"${VENV}/bin/pip" install /opt/mantis/mantis-*.whl
else
	# fallback: pull from the repo at first opportunity
	echo "WARNING: no bundled wheel; installing from GitHub"
	"${VENV}/bin/pip" install "git+https://github.com/KenesisX/Mantis@main" || true
fi

# --- e-ink panel driver (Waveshare) -----------------------------------------
if [ "${DISPLAY_MODE}" = "eink" ]; then
	git clone --depth 1 https://github.com/waveshareteam/e-Paper /tmp/e-Paper || true
	if [ -d /tmp/e-Paper/RaspberryPi_JetsonNano/python ]; then
		(cd /tmp/e-Paper/RaspberryPi_JetsonNano/python && "${VENV}/bin/pip" install .) || true
	fi
	rm -rf /tmp/e-Paper
fi

# --- enable the hardware buses (persist into the image) ---------------------
BOOTCFG=/boot/firmware/config.txt
[ -f "${BOOTCFG}" ] || BOOTCFG=/boot/config.txt
grep -q "^dtparam=spi=on"     "${BOOTCFG}" || echo "dtparam=spi=on"     >> "${BOOTCFG}"
grep -q "^dtparam=i2c_arm=on" "${BOOTCFG}" || echo "dtparam=i2c_arm=on" >> "${BOOTCFG}"

# --- MANTIS_HOME + default config -------------------------------------------
install -d -o "${USER_NAME}" -g "${USER_NAME}" "${HOME_DIR}/.mantis"
sudo -u "${USER_NAME}" env MANTIS_HOME="${HOME_DIR}/.mantis" "${VENV}/bin/python" -m mantis config init || true

# passwordless poweroff for the e-ink hold-combo
echo "${USER_NAME} ALL=(root) NOPASSWD: /sbin/poweroff, /usr/sbin/poweroff" > /etc/sudoers.d/mantis-poweroff
chmod 440 /etc/sudoers.d/mantis-poweroff

# --- boot-on-start service --------------------------------------------------
case "${DISPLAY_MODE}" in
	web)   EXEC="${VENV}/bin/python -m mantis web --host 0.0.0.0 --port 8777";;
	color) EXEC="${VENV}/bin/python -m mantis color loop --interval 3";;
	*)     EXEC="${VENV}/bin/python -m mantis eink --interval 30 --rotate 0 --driver auto";;
esac
cat > /etc/systemd/system/mantis.service <<EOF
[Unit]
Description=MANTIS (${DISPLAY_MODE})
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=/opt/mantis
Environment=MANTIS_HOME=${HOME_DIR}/.mantis
ExecStart=${EXEC}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl enable mantis.service

chown -R "${USER_NAME}:${USER_NAME}" "${HOME_DIR}/.mantis" || true
rm -f /opt/mantis/.user /opt/mantis/.display
echo "MANTIS baked into the image (${DISPLAY_MODE}) — it starts on first boot."
