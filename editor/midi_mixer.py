"""XGworks-inspired MIDI channel mixer."""
import tkinter as tk
from tkinter import ttk, messagebox
from midi import MidiError
from mixer_ops import MIXER_CONTROLLERS, channel_values, set_channel_values

class MidiMixer(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("MIDI Mixer — 16 channels")
        self.geometry("1160x480")
        self.controls = {}
        self.track = tk.IntVar(value=1)
        self.tick = tk.IntVar(value=0)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=8)
        ttk.Label(toolbar, text="Write CC to track").pack(side="left")
        ttk.Spinbox(toolbar, from_=1, to=max(1, len(app.song.tracks)),
                    textvariable=self.track, width=5).pack(side="left", padx=6)
        ttk.Label(toolbar, text="at tick").pack(side="left")
        ttk.Spinbox(toolbar, from_=0, to=268435455, textvariable=self.tick,
                    width=10).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Reload from MIDI", command=self.reload).pack(side="left", padx=12)
        ttk.Button(toolbar, text="Apply all 16 channels", command=self.apply).pack(side="left")
        ttk.Label(toolbar, text="Values are MIDI CC events, not audio gain.").pack(side="right")
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=8, pady=8)
        for channel in range(1, 17):
            frame = ttk.LabelFrame(body, text=f"CH {channel:02d}")
            frame.grid(row=0, column=channel - 1, padx=2, sticky="ns")
            variables = {}
            for name in MIXER_CONTROLLERS:
                ttk.Label(frame, text=name, font=("Arial", 8)).pack()
                variable = tk.IntVar()
                ttk.Scale(frame, from_=127, to=0, orient="vertical",
                          variable=variable, length=42).pack()
                ttk.Label(frame, textvariable=variable, width=4,
                          anchor="center").pack()
                variables[name] = variable
            self.controls[channel] = variables
        self.reload()

    def reload(self):
        if self.app.song is None:
            return
        try:
            tick = self.tick.get()
            for channel, variables in self.controls.items():
                for name, value in channel_values(self.app.song, channel, tick).items():
                    variables[name].set(value)
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
            updates = {channel: {name: max(0, min(127, round(var.get())))
                                 for name, var in variables.items()}
                       for channel, variables in self.controls.items()}
            self.app.snapshot()
            try:
                for channel, values in updates.items():
                    set_channel_values(self.app.song, track_index, channel, values, tick)
            except Exception:
                self.app.song = self.app.history.pop()
                raise
            self.app.show_events()
            self.app.status.set("MIDI Mixer: controller settings written — Save As to save.")
        except (MidiError, tk.TclError) as exc:
            messagebox.showerror("MIDI Mixer", str(exc), parent=self)
