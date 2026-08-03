# Touchscreen scrolling for VTE (Ptyxis) — Fedora 44, GNOME Wayland

VTE is LGPL-3.0-or-later (`gitlab.gnome.org/GNOME/vte`), Ptyxis is GPL-3.0. This tree is
upstream tag **0.84.0**, matching Fedora's `vte291-gtk4-0.84.0-1.fc44`, plus one patch.

## The bug

`VteTerminal`'s click gesture (`src/widget.cc`, `Widget::gesture_click_pressed`) is created
with "any button" + exclusive and is *not* touch-only, so it handles touch sequences too.
It never does anything useful with them — a finger tap sends nothing to the child even with
mouse reporting (`\e[?1000;1002;1006h`) enabled, and a finger drag selects nothing — but the
sequence is consumed, which starves the pan gesture of the containing `GtkScrolledWindow`.
Result: touch drags do nothing at all in the terminal.

Ptyxis's tab UI is `GtkScrolledWindow id=scrolled_window` > `PtyxisTerminal`, and
`kinetic-scrolling` is left at its default `TRUE`, so the kinetic pan is right there,
just never reached.

## The patch — `touch-scroll.patch`

Deny touch sequences in the click gesture (`GTK_EVENT_SEQUENCE_DENIED`) so they propagate to
`GtkScrolledWindow`, which then pans with GTK's own kinetic scrolling. ~30 lines, GTK4 path
only; the GTK3 build is untouched.

The long-press gesture is separate and unaffected, so the touch context menu still works.
Mouse handling is bit-identical: `sequence_is_touch()` is false for pointer events.

## Build

```
meson setup _build -Dgtk3=false -Dgtk4=true -Dvapi=false -Ddocs=false -Dgir=false -Dapp=false
ninja -C _build
./run-ptyxis-patched.sh          # LD_LIBRARY_PATH only — nothing installed
```

`_build-dbg` is the same patch with `-Ddbg=true` (enables `VTE_DEBUG=adj,events`);
`_build-stock` is unpatched-with-debug, kept as the A/B control. Both are only for testing
and can be deleted.

## Verification (synthetic touchscreen via /dev/uinput, single finger, downward drag)

Adjustment changes counted from `VTE_DEBUG=adj`, stock vs patched, three separate harnesses:

| harness | stock 0.84.0 | patched |
|---|---|---|
| real Ptyxis (`ptyxis -s`) | 0 | 297 |
| GTK4 app: `VteTerminal` in a `GtkScrolledWindow` (C and PyGObject twins) | 0 | 145–178 |
| upstream's own `vte-2.91-gtk4 --scrolled-window --scroll-unit-is-pixels` | 0 | 178 |

Regressions checked against the patched library: mouse drag still selects (5680 chars via
`vte_terminal_get_text_selected`), touch long press still fires (`Long Press gesture pressed`).

**Testing pitfall:** every window under test must be fullscreen. GNOME places new windows
unpredictably, and a swipe that misses the window — or clips the scrolled window's *scrollbar*,
which handles touch drags itself — produces both false negatives and false positives. Several
intermittent "stock scrolls too" readings turned out to be exactly that. The reference-app runs
used a local `VTEAPP_FULLSCREEN` hack in `app_action_new_cb` (not kept in the tree; the built
binaries in `_build-dbg` / `_build-stock2` still have it).

## Upstream context

- [#183 Kinetic scrolling](https://gitlab.gnome.org/GNOME/vte/-/issues/183) — about kinetic
  scrolling for *scroll events* (touchpad/wheel). The last comment (andersk, 2021) reports it
  working with `--scroll-unit-is-pixels --scrolled-window`, referencing the commits that made VTE
  behave inside a `GtkScrolledWindow`. That groundwork is why this patch only needs ~30 lines —
  but it does not cover touchscreen drags, which is measured above.
- [#283 Touch drag scroll fix](https://gitlab.gnome.org/GNOME/vte/-/issues/283) (closed, 2020) —
  from the GTK3 era, when touch drag scrolling *did* work through `GtkScrolledWindow`; the fix
  was about the 1:1 speed ratio (rows vs pixels as the adjustment unit).
- [#338](https://gitlab.gnome.org/GNOME/vte/-/issues/338) (open) — touch drag on the alternate
  screen, where there is no scrolled window to help; proposes a touch-only `GtkGestureDrag`.
- [#2329](https://gitlab.gnome.org/GNOME/vte/-/issues/2329) (open, 2016) — "touch scrolling is too
  sensitive", again implying it worked back then.

So the GTK4 port looks like it regressed touchscreen scrolling: the click gesture in the
`VTE_GTK == 4` block claims touch sequences that GTK3 never intercepted. `master` (as of
2026-08-02) has no touch-related commits since 0.84.0 and its gesture setup is byte-identical,
so this patch applies there unchanged — worth filing upstream.

## Installed (2026-08-02)

```
/usr/local/lib64/vte-touchscroll/libvte-2.91-gtk4.so.0     # root:root 755, SELinux lib_t
~/.local/share/dbus-1/services/org.gnome.Ptyxis.service    # D-Bus activation override
~/.local/share/applications/org.gnome.Ptyxis.desktop       # launcher override (all 4 Exec lines)
```

Both overrides prepend `env LD_LIBRARY_PATH=/usr/local/lib64/vte-touchscroll`. Packaged files are
untouched, and `/usr/local/lib64` is not on the default `ld.so` path, so only Ptyxis is affected —
GNOME Console, Builder, etc. keep using the stock library. Ptyxis is `DBusActivatable=true`, so the
`.service` file is the one that actually matters; the `.desktop` is kept in sync for direct launches.

Verified: a Ptyxis started with that env has `/usr/local/lib64/vte-touchscroll/libvte-2.91-gtk4.so.0`
in `/proc/PID/maps`, no SELinux denials, and the installed file is byte-identical (sha256) to the
`_build` library that was A/B tested.

To uninstall:

```
rm ~/.local/share/dbus-1/services/org.gnome.Ptyxis.service
rm ~/.local/share/applications/org.gnome.Ptyxis.desktop
sudo rm -r /usr/local/lib64/vte-touchscroll
```

## Known limitations

- `GtkScrolledWindow` pans by **pixels**. Ptyxis sets `scroll-unit-is-pixels=true`, so the
  scroll tracks the finger 1:1. A GTK4 VTE app that leaves that property off has a
  line-based adjustment and scrolls ~one row-height too fast per pixel.
- A drag that *starts* on the scrollbar is denied by GTK itself (`scrolled_window_drag_begin_cb`),
  so grabbing the scrollbar with a finger still does nothing.
- A finger tap still sends nothing to the child process — unchanged from stock, but it means
  touch cannot click in mouse-reporting TUIs.
- Rebuild needed whenever Fedora ships a new `vte291`.
