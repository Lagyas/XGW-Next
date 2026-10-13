"""XGworks-inspired 16-channel MIDI mixer.

Only edited parameters are written; opening the mixer never adds events.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from midi import MidiError
from mixer_ops import MIXER_CONTROLLERS, channel_values, set_channel_values

class MidiMixer(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("MIDI Mixer — 16 channels")
        self.geometry("910x690")
        self.minsize(760, 480)
        self.controls = {}
        self.baseline = {}
        selected = app.selected_track()
        self.track = tk.IntVar(value=(selected + 1) if selected is not None else 1)
        self.tick = tk.IntVar(value=0)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=10)
        ttk.Label(toolbar, text="Destination track:").pack(side="left")
        ttk.Spinbox(toolbar, from_=1, to=max(1, len(app.song.tracks)),
                    textvariable=self.track, width=5).pack(side="left", padx=6)
        ttk.Label(toolbar, text="Tick:").pack(side="left")
        ttk.Spinbox(toolbar, from_=0, to=268435455, textvariable=self.tick,
                    width=10).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Reload", command=self.reload).pack(side="left", padx=8)
        ttk.Button(toolbar, text="Apply changed values", command=self.apply).pack(side="left", padx=8)

        table = ttk.Frame(self)
        table.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        ttk.Label(table, text="MIDI channel").grid(row=0, column=0, padx=8, pady=5)
        for column, name in enumerate(MIXER_CONTROLLERS, start=1):
            ttk.Label(table, text=name).grid(row=0, column=column, padx=8, pady=5)
            table.columnconfigure(column, weight=1)
        for channel in range(1, 17):
            ttk.Label(table, text=f"CH {channel:02d}").grid(
                row=channel, column=0, sticky="w", padx=8, pady=3)
            variables = {}
            for column, name in enumerate(MIXER_CONTROLLERS, start=1):
                value = tk.IntVar()
                spin = ttk.Spinbox(table, from_=0, to=127, increment=1,
                                   textvariable=value, width=9)
                spin.grid(row=channel, column=column, sticky="ew", padx=7, pady=3)
                variables[name] = value
            self.controls[channel] = variables

        self.info = tk.StringVar(value="Edit a value, then Apply. Unchanged channels are not written.")
        ttk.Label(self, textvariable=self.info, wraplength=850).pack(
            fill="x", padx=12, pady=(0, 12))
        self.reload()

    def reload(self):
        if self.app.song is None:
            return
        try:
            tick = self.tick.get()
            values = {channel: channel_values(self.app.song, channel, tick)
                      for channel in self.controls}
            for channel, parameters in values.items():
                for name, value in parameters.items():
                    self.controls[channel][name].set(value)
            self.baseline = values
            self.info.set("Loaded MIDI values at selected tick. Edit only what you want to change.")
        except (MidiError, tk.TclError) as exc:
            messagebox.showerror("MIDI Mixer", str(exc), parent=self)

    def apply(self):
        if self.app.song is None:
            return
        if self.app.player.playing:
            messagebox.showwarning("MIDI Mixer", "Stop playback before editing.", parent=self)
            return
        try:
            track_index = self.track.get() - 1
            tick = self.tick.get()
            if not 0 <= track_index < len(self.app.song.tracks):
                raise MidiError("Invalid destination track")
            if not 0 <= tick <= 0x0fffffff:
                raise MidiError("Invalid MIDI tick")
            updates = {}
            for channel, variables in self.controls.items():
                changes = {}
                for name, variable in variables.items():
                    value = variable.get()
                    if not 0 <= value <= 127:
                        raise MidiError(f"CH {channel} {name}: value must be 0–127")
                    if value != self.baseline.get(channel, {}).get(name):
                        changes[name] = value
                if changes:
                    updates[channel] = changes
            if not updates:
                self.info.set("No changes — MIDI file left untouched.")
                return
            self.app.snapshot()
            try:
                for channel, changes in updates.items():
                    set_channel_values(self.app.song, track_index, channel, changes, tick)
            except Exception:
                self.app.song = self.app.history.pop()
                raise
            count = sum(len(changes) for changes in updates.values())
            self.app.show_events()
            self.reload()
            self.info.set(f"Saved {count} controller value(s) across {len(updates)} MIDI channel(s).")
            self.app.status.set("MIDI Mixer modified — Save As to save.")
        except (MidiError, tk.TclError) as exc:
            messagebox.showerror("MIDI Mixer", str(exc), parent=self)
