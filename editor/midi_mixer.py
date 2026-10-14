"""XGworks-inspired 16-channel MIDI mixer.

Only edited parameters are written; opening the mixer never adds events.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from midi import MidiError
from mixer_ops import MIXER_CONTROLLERS, channel_values, set_mixer_batch
from meter_activity import update_activity_meters
from mixer_follow import follow_automation
from mixer_track_sync import destination_for_selection
from xg_mixer_bridge import mixer_channel_snapshot, default_part_assignments, normalize_part_assignments

class MidiMixer(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("MIDI Mixer — 16 channels")
        self.geometry("910x690")
        self.minsize(760, 480)
        self.controls = {}
        self.baseline = {}
        self.mute_vars = {}
        self.solo_vars = {}
        self.meter_widgets = {}
        self._last_activity = None
        self._meter_hold = [0] * 16
        self._reloading = False
        self._last_follow_tick = None
        self._follow_track_selection = tk.BooleanVar(value=True)
        selected = app.selected_track()
        self.track = tk.IntVar(value=(selected + 1) if selected is not None else 1)
        self.tick = tk.IntVar(value=0)
        self.output_port = tk.StringVar(value=app.output_name.get())
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=10)
        ttk.Label(toolbar, text="Destination track:").pack(side="left")
        ttk.Spinbox(toolbar, from_=1, to=max(1, len(app.song.tracks)),
                    textvariable=self.track, width=5).pack(side="left", padx=6)
        ttk.Checkbutton(toolbar, text="Follow Track View", variable=self._follow_track_selection,
                        command=self.sync_selected_track).pack(side="left", padx=5)
        ttk.Label(toolbar, text="Output:").pack(side="left")
        self.port_choice = ttk.Combobox(toolbar, textvariable=self.output_port,
                                         values=sorted({app.output_name.get()} | {p for p, _ in app.track_routes.values()}),
                                         state="readonly", width=18)
        self.port_choice.pack(side="left", padx=4)
        self.port_choice.bind('<<ComboboxSelected>>', lambda _event: (self.refresh_meters_once(), self.sync_monitor_mix()))
        ttk.Label(toolbar, text="Tick:").pack(side="left")
        ttk.Spinbox(toolbar, from_=0, to=268435455, textvariable=self.tick,
                    width=10).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Reload", command=self.reload).pack(side="left", padx=8)
        if not hasattr(app, "xg_part_assignments"):
            app.xg_part_assignments = default_part_assignments()
        self.xg_mode = tk.BooleanVar(value=False)
        self.xg_device = tk.IntVar(value=0)
        ttk.Checkbutton(toolbar, text="Read XG Part SysEx (Part = CH)",
                        variable=self.xg_mode, command=self.reload).pack(side="left", padx=4)
        ttk.Label(toolbar, text="XG device:").pack(side="left")
        ttk.Spinbox(toolbar, from_=0, to=15, textvariable=self.xg_device, width=3).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Map Parts...", command=self.configure_part_mapping).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Apply changed values", command=self.apply).pack(side="left", padx=8)

        # A horizontally scrollable bank of sixteen classic channel strips.
        bank = ttk.Frame(self)
        bank.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        canvas = tk.Canvas(bank, highlightthickness=0, height=490)
        scrollbar = ttk.Scrollbar(bank, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=scrollbar.set)
        canvas.pack(fill="both", expand=True)
        scrollbar.pack(fill="x")
        strips = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=strips, anchor="nw")
        strips.bind("<Configure>", lambda _event: canvas.configure(
            scrollregion=canvas.bbox("all")))
        for channel in range(1, 17):
            strip = ttk.LabelFrame(strips, text=f"CH {channel:02d}")
            strip.grid(row=0, column=channel - 1, sticky="ns", padx=3, pady=5)
            mute = tk.BooleanVar(value=(channel - 1) in app.muted_channels)
            solo = tk.BooleanVar(value=(channel - 1) in app.solo_channels)
            self.mute_vars[channel] = mute
            self.solo_vars[channel] = solo
            ttk.Checkbutton(strip, text="Mute", variable=mute, command=self.update_monitor_mix).pack()
            ttk.Checkbutton(strip, text="Solo", variable=solo, command=self.update_monitor_mix).pack()
            meter = tk.Canvas(strip, width=14, height=55, bg="#202020", highlightthickness=1, highlightbackground="#555555")
            meter.pack(pady=(5, 2))
            meter.create_rectangle(2, 2, 12, 53, fill="#333333", outline="", tags="bar")
            self.meter_widgets[channel] = meter
            variables = {}
            for name in MIXER_CONTROLLERS:
                variables[name] = tk.IntVar()
            self.controls[channel] = variables
            ttk.Label(strip, text="Volume").pack(pady=(8, 0))
            ttk.Scale(strip, from_=127, to=0, orient="vertical", length=180,
                      variable=variables["Volume"],
                      command=lambda value, ch=channel: self.slider_changed(ch, "Volume", value)).pack(padx=8)
            ttk.Label(strip, textvariable=variables["Volume"]).pack()
            ttk.Label(strip, text="Pan").pack(pady=(8, 0))
            ttk.Scale(strip, from_=0, to=127, orient="horizontal", length=92,
                      variable=variables["Pan"],
                      command=lambda value, ch=channel: self.slider_changed(ch, "Pan", value)).pack(padx=5)
            ttk.Label(strip, textvariable=variables["Pan"]).pack()
            for name in ("Expression", "Reverb", "Chorus", "Variation"):
                ttk.Label(strip, text=name).pack(pady=(5, 0))
                ttk.Spinbox(strip, from_=0, to=127, width=5,
                            textvariable=variables[name]).pack(pady=(0, 3))

        self.info = tk.StringVar(value="Edit a value, then Apply. Unchanged channels are not written.")
        ttk.Label(self, textvariable=self.info, wraplength=850).pack(
            fill="x", padx=12, pady=(0, 12))
        self.reload()
        self.bind("<FocusIn>", lambda _event: self.sync_monitor_mix())
        self.after(70, self.refresh_meters)

    def part_assignment(self, channel):
        """Return the explicit Part/device assignment for a mixer channel."""
        return self.app.xg_part_assignments.get(channel, (channel, self.xg_device.get()))

    def configure_part_mapping(self):
        """Edit all channel-to-Part/device assignments without changing the MIDI file."""
        window = tk.Toplevel(self)
        window.title("XG channel → Part / device mapping")
        window.transient(self)
        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="MIDI CH").grid(row=0, column=0)
        ttk.Label(frame, text="XG Part").grid(row=0, column=1)
        ttk.Label(frame, text="Device").grid(row=0, column=2)
        values = {}
        for channel in range(1, 17):
            part, device = self.part_assignment(channel)
            part_var, device_var = tk.IntVar(value=part), tk.IntVar(value=device)
            values[channel] = (part_var, device_var)
            ttk.Label(frame, text=f"{channel:02d}").grid(row=channel, column=0, padx=8)
            ttk.Spinbox(frame, from_=1, to=16, width=6, textvariable=part_var).grid(row=channel, column=1, padx=8)
            ttk.Spinbox(frame, from_=0, to=15, width=6, textvariable=device_var).grid(row=channel, column=2, padx=8)
        def save():
            try:
                mapping = normalize_part_assignments({ch: (a.get(), b.get())
                                                      for ch, (a, b) in values.items()})
            except (MidiError, tk.TclError) as exc:
                messagebox.showerror("XG mapping", str(exc), parent=window)
                return
            self.app.xg_part_assignments = mapping
            window.destroy()
            self.reload()
            self.app.notify_midi_editors(origin=self)
            self.app.save_preferences()
            self.info.set("XG Part mapping saved to preferences; MIDI song unchanged.")
        ttk.Button(frame, text="Apply mapping", command=save).grid(row=17, column=0, columnspan=3, pady=10)

    def slider_changed(self, channel, name, value):
        """Snap ttk.Scale's fractional positions to integer MIDI CC values."""
        integer = max(0, min(127, round(float(value))))
        variable = self.controls[channel][name]
        variable.set(integer)
        self.live_controller(channel, name, integer)

    def live_controller(self, channel, name, value):
        """Audition slider changes immediately; Apply still persists them to SMF."""
        if self._reloading or not self.app.player.playing:
            return
        cc = MIXER_CONTROLLERS[name]
        try:
            if self.app.track_routes:
                self.app.player.send_routed_cc(self.output_port.get(), channel - 1, cc,
                                               max(0, min(127, round(float(value)))))
            else:
                self.app.player.send_live_cc(channel - 1, cc, max(0, min(127, round(float(value)))))
        except (MidiError, ValueError) as exc:
            self.info.set(str(exc))

    def refresh_meters_once(self):
        self._last_activity = None
        self._meter_hold = [0] * 16

    def refresh_meters(self):
        """Show recent MIDI traffic, not an audio amplitude measurement."""
        if not self.winfo_exists():
            return
        if self.app.track_routes:
            routed = self.app.player.routed_activity_snapshot()
            current = tuple(routed.get((self.output_port.get(), ch), 0) for ch in range(16))
        else:
            current = self.app.player.activity_snapshot()
        previous = self._last_activity
        self._last_activity = current
        self._meter_hold, active_channels = update_activity_meters(previous, current, self._meter_hold)
        for channel, widget in self.meter_widgets.items():
            active = active_channels[channel - 1]
            widget.itemconfigure("bar", fill="#35e06b" if active else "#333333")
        self.sync_selected_track()
        self.follow_playback_controllers()
        self.after(70, self.refresh_meters)

    def follow_playback_controllers(self):
        """Follow song CC automation without clobbering unsaved fader edits."""
        if not self.app.player.playing or self.app.song is None or self._reloading:
            self._last_follow_tick = None
            return
        tick = self.app.playhead_tick
        if tick == self._last_follow_tick:
            return
        self._last_follow_tick = tick
        self._reloading = True
        try:
            for channel, variables in self.controls.items():
                displayed = {name: var.get() for name, var in variables.items()}
                incoming = (mixer_channel_snapshot(self.app.song, channel, self.part_assignment(channel), tick)[0] if self.xg_mode.get()
                            else channel_values(self.app.song, channel, tick))
                visible, baseline = follow_automation(
                    displayed, self.baseline[channel], incoming)
                for name, value in visible.items():
                    if displayed[name] != value:
                        variables[name].set(value)
                self.baseline[channel] = baseline
        finally:
            self._reloading = False

    def sync_selected_track(self):
        """Keep Apply destination aligned with Track View unless opted out."""
        if not self._follow_track_selection.get() or self.app.song is None:
            return
        destination = destination_for_selection(
            self.app.song, self.app.selected_track(), self.track.get())
        if destination != self.track.get():
            self.track.set(destination)

    def update_monitor_mix(self):
        """Playback-only channel filter; does not modify the MIDI song."""
        if self.app.track_routes:
            from multiport_state import effective_port_channels
            port = self.output_port.get()
            muted = {ch - 1 for ch, var in self.mute_vars.items() if var.get()}
            solo = {ch - 1 for ch, var in self.solo_vars.items() if var.get()}
            try:
                state = dict(self.app.routed_monitor)
                state[port] = (muted, solo)
                enabled = set()
                for name in self.app.player._routed_ports:
                    m, so = state.get(name, (set(), set()))
                    enabled.update(effective_port_channels(name, m, so))
                if self.app.player.playing:
                    self.app.player.set_routed_enabled(enabled)
                self.app.routed_monitor = state
                self.info.set('Port-specific Mute/Solo applied; MIDI song unchanged.')
            except (MidiError, ValueError) as exc:
                self.sync_monitor_mix()
                self.info.set(str(exc))
            return
        try:
            self.app.set_channel_monitor_mix(
                {ch - 1 for ch, var in self.mute_vars.items() if var.get()},
                {ch - 1 for ch, var in self.solo_vars.items() if var.get()})
        except (ValueError, RuntimeError) as exc:
            self.sync_monitor_mix()
            self.info.set(f"Monitor mix unchanged: {exc}")
            return
        if self.app.player.playing:
            self.info.set("Mute/Solo applied during playback; MIDI song unchanged.")
        else:
            self.info.set("Mute/Solo ready for playback; no MIDI events were changed.")

    def sync_monitor_mix(self):
        """Refresh toggles when another mixer window changed channel monitoring."""
        if self.app.track_routes:
            muted, solo = self.app.routed_monitor.get(self.output_port.get(), (set(), set()))
        else:
            muted, solo = self.app.muted_channels, self.app.solo_channels
        for channel in range(1, 17):
            self.mute_vars[channel].set(channel - 1 in muted)
            self.solo_vars[channel].set(channel - 1 in solo)

    def reload(self):
        if self.app.song is None:
            return
        try:
            tick = self.tick.get()
            values = {channel: (mixer_channel_snapshot(self.app.song, channel, self.part_assignment(channel), tick)[0]
                                if self.xg_mode.get() else channel_values(self.app.song, channel, tick))
                      for channel in self.controls}
            self._reloading = True
            for channel, parameters in values.items():
                for name, value in parameters.items():
                    self.controls[channel][name].set(value)
            self._reloading = False
            self.baseline = {channel: dict(params) for channel, params in values.items()}
            self._last_follow_tick = None
            self.info.set("Loaded values at selected tick (XG + CC). Apply writes MIDI CC only."
                          if self.xg_mode.get() else
                          "Loaded MIDI CC values at selected tick. Apply writes MIDI CC only.")
        except (MidiError, tk.TclError) as exc:
            self._reloading = False
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
                set_mixer_batch(self.app.song, track_index, updates, tick)
            except Exception:
                self.app.song = self.app.history.pop()
                raise
            count = sum(len(changes) for changes in updates.values())
            self.app.show_events()
            self.reload()
            self.app.notify_midi_editors(origin=self)
            self.info.set(f"Saved {count} controller value(s) across {len(updates)} MIDI channel(s).")
            self.app.status.set("MIDI Mixer modified — Save As to save.")
        except (MidiError, tk.TclError) as exc:
            messagebox.showerror("MIDI Mixer", str(exc), parent=self)
