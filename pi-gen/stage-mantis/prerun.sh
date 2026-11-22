#!/bin/bash -e
# pi-gen stage bootstrap: copy the previous stage's rootfs forward.
if [ ! -d "${ROOTFS_DIR}" ]; then
	copy_previous
fi
