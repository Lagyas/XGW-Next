"""Classic multi-window workspace preferences for XGworks-style editors."""

WINDOW_KINDS = ("Piano Roll", "List Editor", "Drum Editor", "Staff",
                "Controller Editor", "Master Track", "MIDI Mixer",
                "XG Part Editor", "Lyrics")


def valid_geometry(value):
    """Accept Tk geometry strings only within practical screen dimensions."""
    import re
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r"(\d{2,4})x(\d{2,4})([+-]\d{1,5})([+-]\d{1,5})", value)
    if not match:
        return False
    width, height = int(match[1]), int(match[2])
    return 250 <= width <= 6000 and 180 <= height <= 4000


class Workspace:
    def __init__(self, app, saved=None):
        self.app = app
        self.windows = {}
        self.geometry = dict(saved or {})

    def open(self, kind, factory):
        existing = self.windows.get(kind)
        if existing is not None and existing.winfo_exists():
            existing.deiconify()
            existing.lift()
            existing.focus_set()
            return existing
        window = factory()
        self.windows[kind] = window
        previous = self.geometry.get(kind)
        if valid_geometry(previous):
            window.geometry(previous)
        window.protocol("WM_DELETE_WINDOW", lambda: self.close(kind))
        return window

    def close(self, kind):
        window = self.windows.pop(kind, None)
        if window is not None and window.winfo_exists():
            self.geometry[kind] = window.geometry()
            window.destroy()

    def close_all(self):
        for kind in tuple(self.windows):
            self.close(kind)
