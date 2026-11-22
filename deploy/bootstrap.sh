#!/usr/bin/env bash
# =============================================================================
#  MANTIS — one-line bootstrap for a freshly-flashed Raspberry Pi.
#
#  After flashing Raspberry Pi OS and logging in over SSH, run:
#
#     curl -sSL https://raw.githubusercontent.com/KenesisX/Mantis/main/deploy/bootstrap.sh | bash
#
#  or with options (passed straight to install_pi.sh):
#
#     curl -sSL .../deploy/bootstrap.sh | bash -s -- --display web
#
#  It clones the repo to ~/mantis and runs the installer.
# =============================================================================
set -euo pipefail

REPO="${MANTIS_REPO:-https://github.com/KenesisX/Mantis}"
BRANCH="${MANTIS_BRANCH:-main}"
DEST="$HOME/mantis"

echo "== MANTIS bootstrap =="
command -v git >/dev/null 2>&1 || sudo apt-get update -y && sudo apt-get install -y git

if [ -d "$DEST/.git" ]; then
  echo "Updating existing checkout in $DEST"
  git -C "$DEST" pull --ff-only || true
else
  echo "Cloning $REPO ($BRANCH) -> $DEST"
  git clone --depth 1 --branch "$BRANCH" "$REPO" "$DEST"
fi

cd "$DEST"
echo "Running installer (sudo)..."
sudo bash deploy/install_pi.sh "$@"
