#!/usr/bin/env python3
"""List AT-SPI frames with screen extents and state, so we can aim touch events."""
import pyatspi

desktop = pyatspi.Registry.getDesktop(0)
for app in desktop:
    try:
        appname = app.name
    except Exception:
        continue
    for i in range(app.childCount):
        try:
            frame = app.getChildAtIndex(i)
            if frame is None:
                continue
            ext = frame.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
            states = frame.getState().getStates()
            snames = {pyatspi.stateToString(s) for s in states}
            flags = ",".join(sorted(snames & {"active", "showing", "visible", "iconified"}))
            print(f"{appname!r:24} frame={frame.name[:38]!r:42} x={ext.x} y={ext.y} w={ext.width} h={ext.height} [{flags}]")
        except Exception as e:
            print(f"{appname!r}: error {e}")
