#!/bin/bash -e
# Host-side: stage the MANTIS wheel (and chosen display mode) into the image rootfs.
# The CI workflow drops the built wheel into this step's files/ directory first.

install -d "${ROOTFS_DIR}/opt/mantis"

# the wheel built by CI (mantis-*.whl)
if ls files/mantis-*.whl >/dev/null 2>&1; then
	cp files/mantis-*.whl "${ROOTFS_DIR}/opt/mantis/"
fi

# remember which login user and display mode to configure in the chroot
echo "${FIRST_USER_NAME:-mantis}" > "${ROOTFS_DIR}/opt/mantis/.user"
echo "${MANTIS_DISPLAY:-eink}"    > "${ROOTFS_DIR}/opt/mantis/.display"
