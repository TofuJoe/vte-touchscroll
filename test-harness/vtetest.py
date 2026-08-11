#!/usr/bin/env python3
"""Does a touch drag scroll a GTK4 VteTerminal? Logs touch events + scroll position."""
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Vte", "3.91")
from gi.repository import Gtk, Vte, GLib, Gdk, Gio

MODE = sys.argv[1] if len(sys.argv) > 1 else "scrolledwindow"

app = Gtk.Application(application_id="test.VteTouch", flags=Gio.ApplicationFlags.NON_UNIQUE)


def on_activate(a):
    win = Gtk.ApplicationWindow(application=a, default_width=1200, default_height=800)
    win.set_title("vte touch test")
    term = Vte.Terminal()
    term.set_scrollback_lines(10000)
    if MODE == "ptyxis-like":
        # same VTE properties Ptyxis sets on its PtyxisTerminal
        term.set_enable_fallback_scrolling(False)
        term.set_scroll_unit_is_pixels(True)

    if MODE in ("scrolledwindow", "ptyxis-like"):
        sw = Gtk.ScrolledWindow()
        sw.set_child(term)
        win.set_child(sw)
        print(f"[setup] kinetic_scrolling={sw.get_kinetic_scrolling()}")
    else:
        win.set_child(term)
    print(f"[setup] mode={MODE}")

    blob = "".join(f"line {i:04d} " + "." * 60 + "\r\n" for i in range(1, 401))
    term.feed(list(blob.encode()))

    adj = term.get_vadjustment()

    def report(*_):
        print(f"[scroll] value={adj.get_value():.2f} upper={adj.get_upper():.0f} page={adj.get_page_size():.0f}")

    adj.connect("value-changed", report)

    legacy = Gtk.EventControllerLegacy()

    def on_event(_ctrl, _ev):
        ev = _ctrl.get_current_event()
        if ev is None:
            return False
        t = ev.get_event_type()
        names = {
            Gdk.EventType.TOUCH_BEGIN: "TOUCH_BEGIN",
            Gdk.EventType.TOUCH_UPDATE: "TOUCH_UPDATE",
            Gdk.EventType.TOUCH_END: "TOUCH_END",
            Gdk.EventType.TOUCH_CANCEL: "TOUCH_CANCEL",
            Gdk.EventType.BUTTON_PRESS: "BUTTON_PRESS",
            Gdk.EventType.BUTTON_RELEASE: "BUTTON_RELEASE",
            Gdk.EventType.SCROLL: "SCROLL",
        }
        if t in names:
            ok, x, y = ev.get_position()
            picked = win.pick(x, y, Gtk.PickFlags.DEFAULT) if ok else None
            pname = type(picked).__name__ if picked else "?"
            print(f"[event] {names[t]} at ({x:.0f},{y:.0f}) over={pname}")
        return False

    legacy.connect("event", on_event)
    legacy.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    win.add_controller(legacy)

    term_legacy = Gtk.EventControllerLegacy()

    def on_term_event(c, _e):
        ev = c.get_current_event()
        if ev is not None and ev.get_event_type().value_nick.startswith("touch"):
            print(f"[term-event] {ev.get_event_type().value_nick}")
        return False

    term_legacy.connect("event", on_term_event)
    term.add_controller(term_legacy)

    if len(sys.argv) > 2 and sys.argv[2] == 'fs':
        win.fullscreen()
    win.present()
    def ready():
        k = sw.get_kinetic_scrolling() if MODE != "bare" else None
        print(f"[ready] kinetic_scrolling_now={k}")
        sys.stdout.flush()
        return False

    GLib.timeout_add(1000, ready)
    GLib.timeout_add(45000, lambda: (report(), a.quit(), False)[-1])


app.connect("activate", on_activate)
app.run([])
