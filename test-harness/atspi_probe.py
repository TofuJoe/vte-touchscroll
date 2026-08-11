#!/usr/bin/env python3
"""Report scrollbar / scrollable state of running Ptyxis windows via AT-SPI."""
import sys
import pyatspi


def walk(node, depth=0, out=None):
    if out is None:
        out = []
    try:
        role = node.getRoleName()
        name = node.name or ""
    except Exception:
        return out
    entry = f"{'  ' * depth}{role} '{name[:40]}'"
    try:
        val = node.queryValue()
        entry += f"  VALUE={val.currentValue:.2f} min={val.minimumValue:.2f} max={val.maximumValue:.2f}"
    except NotImplementedError:
        pass
    except Exception:
        pass
    out.append(entry)
    if depth < 12:
        for i in range(node.childCount):
            try:
                walk(node.getChildAtIndex(i), depth + 1, out)
            except Exception:
                pass
    return out


desktop = pyatspi.Registry.getDesktop(0)
found = False
for app in desktop:
    try:
        n = app.name or ""
    except Exception:
        continue
    if "ptyxis" in n.lower():
        found = True
        print(f"=== app: {n} ===")
        for line in walk(app):
            print(line)
if not found:
    print("no ptyxis app on the a11y bus", file=sys.stderr)
    sys.exit(1)
