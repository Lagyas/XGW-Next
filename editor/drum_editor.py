"""Drum grid for channel 10, with XG/GM percussion labels.

Reuses tested note operations; no destructive change occurs without a
snapshot in the application's undo history.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from midi import MidiError
from piano_roll import extract_notes
from note_ops import insert_note, delete_note, move_note
from xg_drums import GM_DRUM_NOTES

ROW_H = 23
BEAT_W = 80
LEFT = 190
TOP = 30

class DrumEditor(tk.Toplevel):
    def __init__(self, app, track_index):
        super().__init__(app.root)
        self.app = app
        self.track_index = track_index
        self.title(f"Drum Editor — Track {track_index + 1}")
        self.geometry("1100x650")
        self.channel = tk.IntVar(value=10)
        self.selected = None
        self.notes = []
        self.pitches = sorted(GM_DRUM_NOTES, reverse=True)
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(bar, text="MIDI channel:").pack(side="left")
        ttk.Spinbox(bar, from_=1, to=16, textvariable=self.channel, width=5,
                    command=self.render).pack(side="left", padx=5)
        ttk.Button(bar, text="Insert hit...", command=self.insert_hit).pack(side="left", padx=5)
        ttk.Button(bar, text="Delete selected", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(bar, text="Move selected...", command=self.move_selected).pack(side="left", padx=5)
        self.info = tk.StringVar(value="Click a drum hit to select; double-click empty grid to insert.")
        ttk.Label(self, textvariable=self.info).pack(fill="x", padx=8)
        area = ttk.Frame(self)
        area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(area, background="#ffffff", highlightthickness=0)
        xscroll = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        yscroll = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        xscroll.grid(row=1, column=0, sticky="ew")
        yscroll.grid(row=0, column=1, sticky="ns")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self.canvas.bind("<Button-1>", self.select)
        self.canvas.bind("<Double-Button-1>", self.double_click)
        self.render()

    def channel_value(self):
        try:
            value = self.channel.get()
            return value if 1 <= value <= 16 else None
        except tk.TclError:
            return None

    def render(self):
        canvas = self.canvas
        canvas.delete("all")
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
                               fill="#ea580c" if idx == self.selected else "#2563eb",
                               outline="#1e40af", tags=(f"hit_{idx}", "hit"))

    def hit_at(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for item in reversed(self.canvas.find_overlapping(x, y, x, y)):
            for tag in self.canvas.gettags(item):
                if tag.startswith("hit_"):
                    return int(tag[4:])
        return None

    def select(self, event):
        self.selected = self.hit_at(event)
        if self.selected is not None:
            start, end, pitch, channel, velocity, _, _ = self.notes[self.selected]
            self.info.set(f"{GM_DRUM_NOTES[pitch]} | tick {start} | velocity {velocity} | channel {channel}")
        self.render()

    def double_click(self, event):
        if self.hit_at(event) is not None:
            return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        row = int((y - TOP) // ROW_H)
        if row < 0 or row >= len(self.pitches) or x < LEFT:
            return
        pitch = self.pitches[row]
        division = self.app.song.division
        # Quantize the insertion point to a 1/16 note.
        step = max(1, division // 4)
        tick = max(0, round(((x - LEFT) / BEAT_W * division) / step) * step)
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
            self._insert(tick, pitch)

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
        if self.selected is None or self.selected >= len(self.notes):
            return
        _, _, _, _, _, on_idx, off_idx = self.notes[self.selected]
        try:
            self.app.snapshot()
            delete_note(self.app.song, self.track_index, on_idx, off_idx)
            self.selected = None
            self.render()
            self.app.show_events()
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            self.app.refresh()
            messagebox.showerror("Delete hit", str(exc), parent=self)

    def move_selected(self):
        if self.selected is None or self.selected >= len(self.notes):
            return
        start, _, pitch, _, _, on_idx, off_idx = self.notes[self.selected]
        tick = simpledialog.askinteger("Move hit", "New start tick:",
                                       initialvalue=start, minvalue=0, parent=self)
        if tick is None:
            return
        new_pitch = simpledialog.askinteger("Move hit", "New drum note (35–81):",
                                            initialvalue=pitch, minvalue=35, maxvalue=81, parent=self)
        if new_pitch is None:
            return
        if new_pitch not in GM_DRUM_NOTES:
            messagebox.showerror("Move hit", "Note not in GM map.", parent=self)
            return
        try:
            self.app.snapshot()
            move_note(self.app.song, self.track_index, on_idx, off_idx, tick, new_pitch)
            self.selected = None
            self.render()
            self.app.show_events()
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            self.app.refresh()
            messagebox.showerror("Move hit", str(exc), parent=self)
