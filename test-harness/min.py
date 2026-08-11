#!/usr/bin/env python3
"""Minimal VTE-in-ScrolledWindow, no extra event controllers. Logs adjustment changes.
usage: min.py [fs] [px] [pty]"""
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Vte", "3.91")
from gi.repository import Gtk, GLib, Gio, Vte

A = sys.argv[1:]
app = Gtk.Application(application_id="test.Min", flags=Gio.ApplicationFlags.NON_UNIQUE)


def on_activate(a):
    win = Gtk.ApplicationWindow(application=a, default_width=1000, default_height=800)
    term = Vte.Terminal()
    term.set_scrollback_lines(10000)
    if "px" in A:
        term.set_scroll_unit_is_pixels(True)
        term.set_enable_fallback_scrolling(False)
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.NEVER,
                  Gtk.PolicyType.AUTOMATIC if "auto" in A else Gtk.PolicyType.ALWAYS)
    if "nooverlay" in A:
        sw.set_overlay_scrolling(False)
    sw.set_kinetic_scrolling(True)
    sw.set_child(term)
    win.set_child(sw)

    if "pty" in A:
        term.spawn_async(
            Vte.PtyFlags.DEFAULT, None,
            ["/bin/bash", "-c", "seq 1 500; sleep 40"], None,
            GLib.SpawnFlags.DEFAULT, None, None, -1, None, None, None,
        )
    else:
        blob = "".join(f"line {i:04d} " + "." * 60 + "\r\n" for i in range(1, 401))
        term.feed(list(blob.encode()))

    term.get_vadjustment().connect(
        "value-changed", lambda adj: print(f"[scroll] {adj.get_value():.1f}", flush=True))

    if "fs" in A:
        win.fullscreen()
    win.present()
    if "focus" in A:
        term.grab_focus()
    print(f"[ready] {A}", flush=True)
    GLib.timeout_add(40000, lambda: (a.quit(), False)[-1])


app.connect("activate", on_activate)
app.run([])
