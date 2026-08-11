#!/usr/bin/env python3
"""Minimal GTK4 window that logs every input event it receives."""
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Vte", "3.91")
from gi.repository import Gtk, Gdk, GLib, Gio, Vte

app = Gtk.Application(application_id="test.TouchProbe", flags=Gio.ApplicationFlags.NON_UNIQUE)


def on_activate(a):
    win = Gtk.ApplicationWindow(application=a, default_width=1400, default_height=900)
    if "--vte" in sys.argv:
        term = Vte.Terminal()
        term.set_scrollback_lines(10000)
        if "--px" in sys.argv:  # what Ptyxis sets
            term.set_scroll_unit_is_pixels(True)
            term.set_enable_fallback_scrolling(False)
        blob = "".join(f"line {i:04d} " + "." * 60 + "\r\n" for i in range(1, 401))
        term.feed(list(blob.encode()))
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        sw.set_child(term)
        win.set_child(sw)
        adj = term.get_vadjustment()
        adj.connect("value-changed", lambda a: print(f"[scroll] {a.get_value():.1f}", flush=True))
        GLib.timeout_add(2000, lambda: (print(f"[kinetic] {sw.get_kinetic_scrolling()}", flush=True), True)[-1])

        def report_selection():
            if term.get_has_selection():
                txt = term.get_text_selected(Vte.Format.TEXT) or ""
                print(f"[selection] {len(txt)} chars: {txt[:60]!r}", flush=True)
            return True

        GLib.timeout_add(500, report_selection)
    elif "--text" in sys.argv:
        # control: an ordinary scrollable GTK4 widget, same ScrolledWindow setup
        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.get_buffer().set_text("\n".join(f"line {i:04d} " + "." * 60 for i in range(1, 401)))
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        sw.set_child(tv)
        win.set_child(sw)
        adj = sw.get_vadjustment()
        adj.connect("value-changed", lambda a: print(f"[scroll] {a.get_value():.1f}", flush=True))
    else:
        win.set_child(Gtk.Label(label="touch probe"))

    ctrl = Gtk.EventControllerLegacy()

    def on_event(c, _e):
        ev = c.get_current_event()
        if ev is None:
            return False
        t = ev.get_event_type().value_nick
        dev = ev.get_device()
        src = dev.get_source().value_nick if dev else "?"
        if t not in ("motion-notify",):
            ok, x, y = ev.get_position()
            print(f"[ev] {t} src={src} at ({x:.0f},{y:.0f})", flush=True)
        return False

    ctrl.connect("event", on_event)
    win.add_controller(ctrl)

    # capture-phase gesture on the window: sees touch before any child can claim it
    cap = Gtk.GestureClick()
    cap.set_touch_only(True)
    cap.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    cap.connect("pressed", lambda g, n, x, y: print(f"[capture] pressed at ({x:.0f},{y:.0f})", flush=True))
    win.add_controller(cap)
    if '--fs' in sys.argv:
        win.fullscreen()
    win.present()
    print("[ready]", flush=True)
    GLib.timeout_add(45000, lambda: (a.quit(), False)[-1])


app.connect("activate", on_activate)
app.run([])
