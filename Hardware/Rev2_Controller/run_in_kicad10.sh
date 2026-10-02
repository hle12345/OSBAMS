#!/bin/bash
# Run a command inside the KiCad 10.0.6 container rootfs (see Hardware/Rev2_Controller/BUILD_ENVIRONMENT.md); repo is mounted at /work.
exec /usr/local/bin/kc10 "$@"
