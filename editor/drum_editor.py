"""Drum grid for channel 10, with XG/GM percussion labels.

Reuses tested note operations; no destructive change occurs without a
snapshot in the application's undo history.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from midi import MidiError
from piano_roll import extract_notes
from note_ops import insert_note, delete_note, move_note, transform_notes
from xg_drums import GM_DRUM_NOTES
from note_ops import paired_notes, delete_notes
from velocity_ops import set_note_velocities, scale_note_velocities
from snap_grid import SNAP_OPTIONS, snapped_tick, snap_ticks
from editor_cursor import ruler_tick, seek_editor

ROW_H = 23
BEAT_W = 80
LEFT = 190
TOP = 30
VELOCITY_H = 115


def drum_insert_tick(tick, division, snap="1/16"):
    """Quantize a drum insertion position with the shared Piano Roll grid."""
    if isinstance(tick, bool) or not isinstance(tick, (int, float)):
        raise MidiError("Invalid drum tick")
    if tick < 0 or tick > 0x0fffffff:
        raise MidiError("Invalid drum tick")
    return snapped_tick(int(tick + 0.5), division, snap)

def velocity_from_y(y, height=VELOCITY_H):
    """Convert a velocity lane y coordinate into a valid MIDI note velocity."""
    if height <= 32:
        raise ValueError("Velocity lane is too short")
    return max(1, min(127, round((height - 12 - y) * 127 / (height - 32))))

class DrumEditor(tk.Toplevel):
    def __init__(self, app, track_index):
        super().__init__(app.root)
        self.app = app
        self.track_index = track_index
        self.title(f"Drum Editor — Track {track_index + 1}")
        self.geometry("1100x650")
        self.channel = tk.IntVar(value=10)
        self.snap_option = tk.StringVar(value="1/16")
        self.selected = None
        self.selected_hits = set()
        self.notes = []
        self._velocity_drag = None
        self.pitches = sorted(GM_DRUM_NOTES, reverse=True)
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(bar, text="MIDI channel:").pack(side="left")
        ttk.Spinbox(bar, from_=1, to=16, textvariable=self.channel, width=5,
                    command=self.render).pack(side="left", padx=5)
        ttk.Label(bar, text="Snap:").pack(side="left", padx=(8, 2))
        ttk.Combobox(bar, textvariable=self.snap_option, values=SNAP_OPTIONS,
                     state="readonly", width=7).pack(side="left", padx=3)
        ttk.Button(bar, text="Insert hit...", command=self.insert_hit).pack(side="left", padx=5)
        ttk.Button(bar, text="Delete selected", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(bar, text="Move selected...", command=self.move_selected).pack(side="left", padx=5)
        ttk.Button(bar, text="Copy selected...", command=self.copy_selected).pack(side="left", padx=5)
        ttk.Button(bar, text="Velocity...", command=self.edit_velocity).pack(side="left", padx=5)
        ttk.Button(bar, text="Scale velocity...", command=self.scale_velocity).pack(side="left", padx=5)
        ttk.Button(bar, text="Select all hits", command=self.select_all_hits).pack(side="left", padx=5)
        ttk.Button(bar, text="Clear selection", command=self.clear_selection).pack(side="left", padx=5)
        self.info = tk.StringVar(value="Click to select; Ctrl+click to add/remove hits; double-click empty grid to insert.")
        ttk.Label(self, textvariable=self.info).pack(fill="x", padx=8)
        area = ttk.Frame(self)
        area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(area, background="#ffffff", highlightthickness=0)
        xscroll = ttk.Scrollbar(area, orient="horizontal", command=self.scroll_horizontal)
        yscroll = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        xscroll.grid(row=1, column=0, sticky="ew")
        yscroll.grid(row=0, column=1, sticky="ns")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self.velocity_canvas = tk.Canvas(self, height=VELOCITY_H, background="#f8fafc",
                                         highlightthickness=1, highlightbackground="#cbd5e1")
        self.velocity_canvas.pack(fill="x", padx=8, pady=(2, 8))
        self.velocity_canvas.bind("<Button-1>", self.begin_velocity_drag)
        self.velocity_canvas.bind("<B1-Motion>", self.drag_velocity)
        self.velocity_canvas.bind("<ButtonRelease-1>", self.end_velocity_drag)
        self.canvas.bind("<Button-1>", self.select)
        self.canvas.bind("<Control-Button-1>", self.toggle_selection)
        self.canvas.bind("<Double-Button-1>", self.double_click)
        self.canvas.bind("<Shift-Button-1>", self.seek_ruler)
        self.canvas.bind("<MouseWheel>", lambda _e: self.after_idle(self.refresh_velocity))
        self.canvas.bind("<ButtonRelease-1>", lambda _e: self.after_idle(self.refresh_velocity))
        self.velocity_canvas.bind("<Configure>", lambda _e: self.refresh_velocity())
        self.render()

    def seek_ruler(self, event):
        """Shift-click the drum timeline to move the common song cursor."""
        if self.app.song is None:
            return "break"
        try:
            tick = ruler_tick(self.canvas.canvasx(event.x), LEFT, BEAT_W,
                              self.app.song.division, self.snap_option.get())
            seek_editor(self.app, tick)
        except MidiError as exc:
            self.info.set(str(exc))
        return "break"

    def channel_value(self):
        try:
            value = self.channel.get()
            return value if 1 <= value <= 16 else None
        except tk.TclError:
            return None

    def render(self):
        canvas = self.canvas
        canvas.delete("all")
        self.velocity_canvas.delete("all")
        song = self.app.song
        if song is None or self.track_index >= len(song.tracks):
            return
        division = song.division
        if division <= 0 or division & 0x8000:
            self.info.set("PPQN MIDI timing required.")
            return
        channel = self.channel_value()
        if channel is None:
            self.info.set("Choose a valid MIDI channel (1–16).")
            return
        self.notes = [n for n in extract_notes(song.tracks[self.track_index])
                      if n[3] == channel and n[2] in GM_DRUM_NOTES]
        self.selected_hits.intersection_update(range(len(self.notes)))
        max_tick = max((e.tick for e in song.tracks[self.track_index].events), default=0)
        width = max(1300, LEFT + (max_tick / division) * BEAT_W + 400)
        height = TOP + ROW_H * len(self.pitches)
        canvas.configure(scrollregion=(0, 0, width, height))
        for row, pitch in enumerate(self.pitches):
            y = TOP + row * ROW_H
            canvas.create_rectangle(0, y, width, y + ROW_H,
                                    fill="#f1f5f9" if row % 2 == 0 else "#ffffff",
                                    outline="#dce3eb")
            canvas.create_text(8, y + ROW_H/2, anchor="w",
                               text=f"{pitch:3d}  {GM_DRUM_NOTES[pitch]}")
        beats = int((width - LEFT) // BEAT_W)
        for beat in range(beats + 1):
            x = LEFT + beat * BEAT_W
            canvas.create_line(x, TOP, x, height,
                               fill="#9ca3af" if beat % 4 == 0 else "#e2e8f0")
            if beat % 4 == 0:
                canvas.create_text(x + 4, 14, anchor="w", text=f"Bar {beat//4+1}")
        for idx, (start, end, pitch, _, velocity, _, _) in enumerate(self.notes):
            x = LEFT + start / division * BEAT_W
            y = TOP + self.pitches.index(pitch) * ROW_H + ROW_H/2
            canvas.create_oval(x-6, y-6, x+6, y+6,
                               fill="#ea580c" if idx in self.selected_hits else "#2563eb",
                               outline="#1e40af", tags=(f"hit_{idx}", "hit"))
        self.draw_velocity(division)

    def draw_velocity(self, division):
        """Draw note-on velocities in a fixed-height overview aligned to visible grid."""
        c = self.velocity_canvas
        c.delete("all")
        width = max(c.winfo_width(), 400)
        c.create_text(8, 10, anchor="w", text="Velocity (1–127)", fill="#334155")
        for value in (0, 64, 127):
            y = VELOCITY_H - 12 - value / 127 * (VELOCITY_H - 32)
            c.create_line(42, y, width, y, fill="#e2e8f0")
            c.create_text(4, y, anchor="w", text=str(value), fill="#64748b")
        # Keep the velocity overview in sync with the drum grid's horizontal scroll.
        scroll_left = self.canvas.canvasx(0)
        for idx, (start, _end, _pitch, _channel, velocity, _on, _off) in enumerate(self.notes):
            x = LEFT + start / division * BEAT_W - scroll_left
            if x < 42 or x > width + 8:
                continue
            y = VELOCITY_H - 12 - velocity / 127 * (VELOCITY_H - 32)
            c.create_rectangle(x - 3, y, x + 3, VELOCITY_H - 12,
                               fill="#ea580c" if idx in self.selected_hits else "#6366f1",
                               outline="", tags=(f"velocity_{idx}",))

    def begin_velocity_drag(self, event):
        """Select a velocity bar and start a preview; do not mutate the song yet."""
        self._velocity_drag = None
        for item in reversed(self.velocity_canvas.find_overlapping(event.x, event.y, event.x, event.y)):
            for tag in self.velocity_canvas.gettags(item):
                if tag.startswith("velocity_"):
                    index = int(tag.split("_", 1)[1])
                    if index >= len(self.notes):
                        return
                    self.selected = index
                    self.selected_hits = {index}
                    self._velocity_drag = (index, self.notes[index][4])
                    self.render()
                    self.info.set(f"Velocity {self.notes[index][4]} — drag to adjust")
                    return

    def drag_velocity(self, event):
        """Preview the dragged value without creating undo snapshots on each motion."""
        if self._velocity_drag is None:
            return
        index, original = self._velocity_drag
        if index >= len(self.notes):
            return
        value = velocity_from_y(event.y, self.velocity_canvas.winfo_height())
        self.draw_velocity(self.app.song.division)
        c = self.velocity_canvas
        scroll_left = self.canvas.canvasx(0)
        x = LEFT + self.notes[index][0] / self.app.song.division * BEAT_W - scroll_left
        y = VELOCITY_H - 12 - value / 127 * (VELOCITY_H - 32)
        c.create_rectangle(x - 4, y, x + 4, VELOCITY_H - 12,
                           fill="#ea580c", outline="", tags="drag_preview")
        self.info.set(f"Velocity: {original} → {value} (release to apply)")

    def end_velocity_drag(self, event):
        """Commit one atomic velocity edit on release, preserving undo history."""
        pending = self._velocity_drag
        self._velocity_drag = None
        if pending is None:
            return
        index, original = pending
        if index >= len(self.notes) or self.app.song is None:
            return
        value = velocity_from_y(event.y, self.velocity_canvas.winfo_height())
        if value == original:
            self.render()
            return
        track = self.app.song.tracks[self.track_index]
        on_idx, off_idx = self.notes[index][5:7]
        if (on_idx, off_idx) not in paired_notes(track):
            messagebox.showerror("Velocity", "Selected note pair is no longer valid.", parent=self)
            self.render()
            return
        self.app.snapshot()
        on = track.events[on_idx]
        on.data = bytes((on.data[0], value))
        self.app.song.dirty = True
        self.selected = index
        self.selected_hits = {index}
        self.render()
        self.app.show_events()
        self.info.set(f"Velocity changed: {original} → {value}")

    def scroll_horizontal(self, *args):
        self.canvas.xview(*args)
        self.refresh_velocity()

    def refresh_velocity(self):
        song = self.app.song
        if song is not None and 0 < song.division < 0x8000:
            self.draw_velocity(song.division)

    def hit_at(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for item in reversed(self.canvas.find_overlapping(x, y, x, y)):
            for tag in self.canvas.gettags(item):
                if tag.startswith("hit_"):
                    return int(tag[4:])
        return None

    def _selection_info(self):
        count = len(self.selected_hits)
        if count > 1:
            self.info.set(f"{count} drum hits selected (Ctrl+click to toggle).")
        elif self.selected is not None and self.selected < len(self.notes):
            start, end, pitch, channel, velocity, _, _ = self.notes[self.selected]
            self.info.set(f"{GM_DRUM_NOTES[pitch]} | tick {start} | velocity {velocity} | channel {channel}")
        else:
            self.info.set("No drum hits selected. Ctrl+click to select multiple.")

    def publish_note_selection(self):
        shared = getattr(self.app, "shared_note_selection", None)
        if shared is None:
            return
        shared.set(self.track_index, ((self.notes[i][5], self.notes[i][6])
                                      for i in self.selected_hits if 0 <= i < len(self.notes)),
                   self.app.song.tracks[self.track_index].events)
        other = self.app.workspace.windows.get("Piano Roll")
        if other is not None and other.winfo_exists() and other.track_index == self.track_index:
            other.receive_note_selection()

    def receive_note_selection(self):
        shared = getattr(self.app, "shared_note_selection", None)
        if shared is None:
            return
        pairs = shared.get(self.track_index, self.notes, self.app.song.tracks[self.track_index].events)
        self.selected_hits = {i for i, note in enumerate(self.notes)
                              if (note[5], note[6]) in pairs}
        self.selected = min(self.selected_hits) if self.selected_hits else None
        self.render()

    def select(self, event):
        self.selected = self.hit_at(event)
        self.selected_hits = {self.selected} if self.selected is not None else set()
        self._selection_info()
        self.render()
        getattr(self, "publish_note_selection", lambda: None)()

    def toggle_selection(self, event):
        index = self.hit_at(event)
        if index is not None:
            if index in self.selected_hits:
                self.selected_hits.remove(index)
            else:
                self.selected_hits.add(index)
        self.selected = min(self.selected_hits) if self.selected_hits else None
        self._selection_info()
        self.render()
        getattr(self, "publish_note_selection", lambda: None)()
        return "break"

    def select_all_hits(self):
        self.selected_hits = set(range(len(self.notes)))
        self.selected = 0 if self.notes else None
        self._selection_info()
        self.render()
        getattr(self, "publish_note_selection", lambda: None)()

    def clear_selection(self):
        self.selected_hits.clear()
        self.selected = None
        self._selection_info()
        self.render()
        getattr(self, "publish_note_selection", lambda: None)()

    def double_click(self, event):
        if self.hit_at(event) is not None:
            return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        row = int((y - TOP) // ROW_H)
        if row < 0 or row >= len(self.pitches) or x < LEFT:
            return
        pitch = self.pitches[row]
        division = self.app.song.division
        tick = drum_insert_tick((x - LEFT) / BEAT_W * division, division,
                                self.snap_option.get())
        self._insert(tick, pitch)

    def insert_hit(self):
        pitch = simpledialog.askinteger("Drum hit", "MIDI drum note (35–81):",
                                        initialvalue=36, minvalue=35, maxvalue=81, parent=self)
        if pitch is None:
            return
        if pitch not in GM_DRUM_NOTES:
            messagebox.showerror("Drum hit", "This note is not in the current GM map.", parent=self)
            return
        tick = simpledialog.askinteger("Drum hit", "Start tick:",
                                       initialvalue=0, minvalue=0, parent=self)
        if tick is not None:
            try:
                self._insert(drum_insert_tick(tick, self.app.song.division,
                                              self.snap_option.get()), pitch)
            except MidiError as exc:
                messagebox.showerror("Drum hit", str(exc), parent=self)

    def _insert(self, tick, pitch):
        channel = self.channel_value()
        if channel is None:
            return
        duration = max(1, self.app.song.division // 4)
        try:
            self.app.snapshot()
            insert_note(self.app.song, self.track_index, tick, duration,
                        pitch, channel=channel, velocity=100)
            self.selected = None
            self.render()
            self.app.show_events()
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            self.app.refresh()
            messagebox.showerror("Drum hit", str(exc), parent=self)

    def delete_selected(self):
        indices = sorted(self.selected_hits)
        if not indices:
            return
        pairs = [self.notes[i][5:7] for i in indices if i < len(self.notes)]
        if not pairs:
            return
        try:
            self.app.snapshot()
            delete_notes(self.app.song, self.track_index, pairs)
            self.clear_selection()
            self.app.show_events()
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            self.app.refresh()
            messagebox.showerror("Delete hits", str(exc), parent=self)

    def edit_velocity(self):
        indices = sorted(self.selected_hits)
        if not indices:
            return
        current = self.notes[indices[0]][4]
        value = simpledialog.askinteger("Velocity", f"Velocity for {len(indices)} hit(s) (1–127):",
                                        initialvalue=current, minvalue=1, maxvalue=127, parent=self)
        if value is None:
            return
        changes = {self.notes[i][5]: value for i in indices if i < len(self.notes)
                   and self.notes[i][4] != value}
        if not changes:
            return
        try:
            # Validate every selected note pair before taking an undo snapshot.
            valid = set(paired_notes(self.app.song.tracks[self.track_index]))
            if any(self.notes[i][5:7] not in valid for i in indices):
                raise MidiError("Selected note pair is no longer valid")
            self.app.snapshot()
            set_note_velocities(self.app.song, self.track_index, changes)
            self.render()
            self.app.show_events()
            self.info.set(f"Velocity {value} applied to {len(changes)} hit(s).")
        except MidiError as exc:
            messagebox.showerror("Velocity", str(exc), parent=self)

    def scale_velocity(self):
        """Scale selected drum hits in one undoable operation."""
        indices = sorted(i for i in self.selected_hits if i < len(self.notes))
        if not indices:
            self.info.set("Select drum hits before scaling velocity.")
            return
        percent = simpledialog.askinteger("Scale drum velocity", "Percent (0–400):",
                                          initialvalue=100, minvalue=0, maxvalue=400, parent=self)
        if percent is None:
            return
        try:
            from copy import deepcopy
            on_indices = [self.notes[i][5] for i in indices]
            # Preview validation and detect a no-op before adding an undo entry.
            preview = deepcopy(self.app.song)
            changed = scale_note_velocities(preview, self.track_index, on_indices, percent)
            if not changed:
                return
            self.app.snapshot()
            scale_note_velocities(self.app.song, self.track_index, on_indices, percent)
            self.render()
            self.app.show_events()
            self.info.set(f"Scaled {changed} drum velocities to {percent}%.")
        except MidiError as exc:
            messagebox.showerror("Scale drum velocity", str(exc), parent=self)

    def _transform_selected(self, duplicate=False):
        """Move/copy all selected hits by a relative tick/pitch offset."""
        indices = sorted(i for i in self.selected_hits if 0 <= i < len(self.notes))
        if not indices or self.app.song is None:
            return
        verb = "Copy" if duplicate else "Move"
        delta = simpledialog.askinteger(verb + " hits", "Offset in ticks (negative = earlier):",
                                        initialvalue=0, parent=self)
        if delta is None:
            return
        semitones = simpledialog.askinteger(verb + " hits", "Drum note offset (semitones):",
                                            initialvalue=0, minvalue=-127, maxvalue=127,
                                            parent=self)
        if semitones is None:
            return
        if not duplicate and delta == 0 and semitones == 0:
            return
        # Validate the drum map and note pairs before creating an undo snapshot.
        pairs = [self.notes[i][5:7] for i in indices]
        try:
            if any(self.notes[i][2] + semitones not in GM_DRUM_NOTES for i in indices):
                raise MidiError("Destination note is not in the GM drum map")
            track = self.app.song.tracks[self.track_index]
            if any(pair not in set(paired_notes(track)) for pair in pairs):
                raise MidiError("Selected note pair is no longer valid")
            for i in indices:
                start, end = self.notes[i][:2]
                if not 0 <= start + delta <= end + delta <= 0x0fffffff:
                    raise MidiError("Destination tick is outside the MIDI range")
            self.app.snapshot()
            count = transform_notes(self.app.song, self.track_index, pairs,
                                    delta_ticks=delta, delta_pitch=semitones,
                                    duplicate=duplicate)
            self.selected = None
            self.selected_hits.clear()
            self.render()
            self.app.show_events()
            self.info.set(f"{count} drum hit(s) {'copied' if duplicate else 'moved'}.")
        except MidiError as exc:
            messagebox.showerror(verb + " hits", str(exc), parent=self)

    def move_selected(self):
        self._transform_selected(duplicate=False)

    def copy_selected(self):
        self._transform_selected(duplicate=True)
