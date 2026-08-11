# Synthetic touchscreen harness

Throwaway tools used to measure the VTE touch-scroll patch. Kept because re-verifying after a
`vte291` update takes about a minute with them.

| file | what it does |
| --- | --- |
| `vtouch.c` | creates a virtual MT protocol-B touchscreen on `/dev/uinput` and swipes it. `gcc -O2 -o vtouch vtouch.c`, then `./vtouch x1 y1 x2 y2 [steps] [step_ms] [hold_ms] [repeats]`. Coordinates are screen pixels, hardcoded to 1920x1200 — edit `W`/`H` for another panel. |
| `min.c` / `min.py` | smallest possible reproducer: `VteTerminal` in a `GtkScrolledWindow`, prints every adjustment change. `min.py` takes `fs`, `px`, `pty`, `focus`, `auto`, `nooverlay`. |
| `touchprobe.py` | same, plus event logging — `--vte`, `--text` (GtkTextView control), `--px`, `--fs`. The capture-phase gesture is what proves touch reaches the window even when the widget eats it. |
| `ptytest.py` | terminal with a real PTY and mouse reporting on; logs what touch sends to the child (nothing, patched or not). |
| `windows.py` | AT-SPI window list. Sizes are usable, **positions are not** — GTK4 reports 0,0. |
| `vtetest.py` | earlier variant of `touchprobe.py`, kept for its bare-vs-scrolledwindow mode. |

`/dev/uinput` needs to be writable by your user — it already is here via the uaccess ACL.

## The one rule

**Fullscreen the window under test.** GNOME places windows where it likes, so a swipe can miss
entirely (false negative), and a swipe that clips the scrolled window's scrollbar makes *stock* VTE
look like it scrolls, because the scrollbar handles touch drags itself (false positive). Both
happened repeatedly before this rule.

## Typical run

```sh
gcc -O2 -o vtouch vtouch.c
VTE_DEBUG=adj LD_LIBRARY_PATH=../_build-dbg/src ptyxis -s -x "bash -c 'seq 1 500; sleep 40'" > run.log 2>&1 &
sleep 8
./vtouch 960 500 960 850 20 16          # downward drag == scroll up into the scrollback
grep -c 'Scrolling by' run.log          # 0 stock, a few hundred patched
```

Swipe *downward* from a terminal sitting at the bottom of its scrollback. Upward has nowhere to go
and reads as a failure.
