#!/usr/bin/env python3
"""VTE with a real PTY + SGR mouse reporting on; logs what touch sends to the child."""
import os
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Vte", "3.91")
from gi.repository import Gtk, GLib, Gio, Vte

LOG = "/tmp/claude-1000/-home-dhon-ai/d7f0ca97-e166-494d-acb2-0c804fba3e4d/scratchpad/mouse-in.log"

app = Gtk.Application(application_id="test.PtyTouch", flags=Gio.ApplicationFlags.NON_UNIQUE)


def on_activate(a):
    win = Gtk.ApplicationWindow(application=a, default_width=1400, default_height=900)
    term = Vte.Terminal()
    term.set_scrollback_lines(10000)
    sw = Gtk.ScrolledWindow()
    sw.set_child(term)
    win.set_child(sw)
    adj = term.get_vadjustment()
    adj.connect("value-changed", lambda x: print(f"[scroll] {x.get_value():.1f}", flush=True))

    script = (
        "printf 'seed\\n'; for i in $(seq 1 400); do echo \"line $i ....................\"; done; "
        f"printf '\\033[?1000;1002;1006h'; cat -v > {LOG}"
    )
    term.spawn_async(
        Vte.PtyFlags.DEFAULT, None, ["/bin/bash", "-c", script], None,
        GLib.SpawnFlags.DEFAULT, None, None, -1, None,
        lambda t, pid, err, data: print(f"[spawn] pid={pid} err={err}", flush=True), None,
    )

    if "--fs" in sys.argv:
        win.fullscreen()
    win.present()
    print("[ready]", flush=True)
    GLib.timeout_add(45000, lambda: (a.quit(), False)[-1])


app.connect("activate", on_activate)
app.run([])
