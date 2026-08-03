#!/bin/bash
# Run Ptyxis against the locally built, touch-scroll-patched libvte.
# Nothing is installed system-wide; this only affects the instance launched here.
#
#   ./run-ptyxis-patched.sh              # normal separate-instance Ptyxis
#   VTE_DEBUG=adj ./run-ptyxis-patched.sh   # needs the _build-dbg library instead
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
lib="$here/_build/src"
[ -n "${VTE_DEBUG:-}" ] && lib="$here/_build-dbg/src"

if [ ! -e "$lib/libvte-2.91-gtk4.so.0" ]; then
    echo "no library in $lib — build it first:" >&2
    echo "  meson setup _build -Dgtk3=false -Dgtk4=true -Dvapi=false -Ddocs=false -Dgir=false -Dapp=false" >&2
    echo "  ninja -C _build" >&2
    exit 1
fi

# -s keeps this out of the already-running system Ptyxis instance, which would
# otherwise just open a tab there using the stock library.
exec env LD_LIBRARY_PATH="$lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ptyxis -s "$@"
