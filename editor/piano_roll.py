"""Piano Roll view for the XGW Next Tkinter prototype.

Pairs note-on/off events per MIDI channel and pitch. Editing uses the
existing Song.set_event() method and the application's undo snapshots.
"""
from collections import defaultdict, deque
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from midi import MidiError
from note_ops import insert_note, delete_note, move_note, quantize_notes

NOTE_HEIGHT = 12
PIXELS_PER_BEAT = 64
KEYBOARD_WIDTH = 68
TOP_MARGIN = 24

def extract_notes(track):
    """Return (start_tick, end_tick, pitch, channel, velocity, on_index, off_index).

    FIFO pairing makes overlapping same-pitch notes deterministic. Orphaned
    note-on events are excluded until an explicit note-off exists.
    """
    pending = defaultdict(deque)
    notes = []
    indexed = sorted(enumerate(track.events), key=lambda item: (item[1].tick, item[1].order))
    for idx, event in indexed:
        if not 0x80 <= event.status <= 0x9F or len(event.data) != 2:
            continue
        key = (event.status & 0x0F, event.data[0])
        on = event.status & 0xF0 == 0x90 and event.data[1] > 0
        if on:
            pending[key].append((idx, event))
        elif pending[key]:
            on_idx, start = pending[key].popleft()
            notes.append((start.tick, event.tick, key[1], key[0] + 1,
                          start.data[1], on_idx, idx))
    return sorted(notes, key=lambda n: (n[0], n[2], n[3]))

def pitch_label(pitch):
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[pitch % 12]}{pitch // 12 - 1}"

class PianoRoll(tk.Toplevel):
    def __init__(self, app, track_index):
        super().__init__(app.root)
        self.app = app
        self.track_index = track_index
        self.title(f"Piano Roll — Track {track_index + 1}")
        self.geometry("1100x650")
        self.notes = []
        self.selected = None
        self.info = tk.StringVar(value="Click a note to select; double-click to edit pitch, start and duration.")
        ttk.Label(self, textvariable=self.info).pack(fill="x", padx=8, pady=5)
        area = ttk.Frame(self)
        area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(area, background="#f8fafc", highlightthickness=0)
        yscroll = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        xscroll = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self.canvas.bind("<Button-1>", self.select_note)
        self.canvas.bind("<Double-Button-1>", self.edit_note)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=4)
        ttk.Button(toolbar, text="Insert note", command=self.insert_note).pack(side="left")
        ttk.Button(toolbar, text="Delete selected", command=self.delete_selected).pack(side="left")
        ttk.Button(toolbar, text="Quantize 1/16", command=self.quantize).pack(side="left")
        self.canvas.bind("<ButtonPress-3>", self.begin_drag)
        self.canvas.bind("<ButtonRelease-3>", self.end_drag)
        self.drag_origin = None
        self.render()
        self.canvas.yview_moveto(0.32)

    def render(self):
        canvas = self.canvas
        canvas.delete("all")
        song = self.app.song
        track = song.tracks[self.track_index]
        self.notes = extract_notes(track)
        division = song.division
        if division & 0x8000:
            self.info.set("SMPTE time division: Piano Roll beat grid not yet supported.")
            return
        if division <= 0:
            self.info.set("Invalid MIDI division.")
            return
        max_tick = max((e.tick for e in track.events), default=0)
        width = max(1200, KEYBOARD_WIDTH + int(max_tick / division * PIXELS_PER_BEAT) + 300)
        height = TOP_MARGIN + 128 * NOTE_HEIGHT
        canvas.configure(scrollregion=(0, 0, width, height))
        for pitch in range(128):
            y = TOP_MARGIN + (127 - pitch) * NOTE_HEIGHT
            white = pitch % 12 not in (1, 3, 6, 8, 10)
            canvas.create_rectangle(0, y, width, y + NOTE_HEIGHT,
                                    fill="#ffffff" if white else "#e8edf4",
                                    outline="#d7dde6", width=0.5)
            if pitch % 12 == 0:
                canvas.create_text(6, y + NOTE_HEIGHT / 2, text=pitch_label(pitch),
                                   anchor="w", font=("Arial", 9))
                canvas.create_line(0, y + NOTE_HEIGHT, width, y + NOTE_HEIGHT,
                                   fill="#b6c0d0")
        beats = max(1, (width - KEYBOARD_WIDTH) // PIXELS_PER_BEAT)
        for beat in range(beats + 1):
            x = KEYBOARD_WIDTH + beat * PIXELS_PER_BEAT
            is_bar = beat % 4 == 0
            canvas.create_line(x, TOP_MARGIN, x, height,
                               fill="#a4adbb" if is_bar else "#d9dee8",
                               width=1 if is_bar else 0.5)
            if is_bar:
                canvas.create_text(x + 3, 12, text=str(beat // 4 + 1),
                                   anchor="w", fill="#334155")
        for index, (start, end, pitch, channel, velocity, _, _) in enumerate(self.notes):
            x1 = KEYBOARD_WIDTH + start / division * PIXELS_PER_BEAT
            x2 = KEYBOARD_WIDTH + max(end, start + 1) / division * PIXELS_PER_BEAT
            y = TOP_MARGIN + (127 - pitch) * NOTE_HEIGHT
            color = "#ea580c" if index == self.selected else "#2563eb"
            canvas.create_rectangle(x1, y + 1, max(x1 + 3, x2), y + NOTE_HEIGHT - 1,
                                    fill=color, outline="#1e40af",
                                    tags=(f"note_{index}", "note"))
        self.canvas.tag_raise("note")

    def hit_note(self):
        x = self.canvas.canvasx(self.winfo_pointerx() - self.canvas.winfo_rootx())
        y = self.canvas.canvasy(self.winfo_pointery() - self.canvas.winfo_rooty())
        found = self.canvas.find_overlapping(x, y, x, y)
        for item in reversed(found):
            for tag in self.canvas.gettags(item):
                if tag.startswith("note_"):
                    return int(tag[5:])
        return None

    def select_note(self, _event=None):
        self.selected = self.hit_note()
        if self.selected is not None:
            start, end, pitch, channel, velocity, _, _ = self.notes[self.selected]
            self.info.set(f"{pitch_label(pitch)} | channel {channel} | start {start} | "
                          f"duration {end-start} ticks | velocity {velocity}")
        self.render()

    def insert_note(self):
        if self.app.song.division & 0x8000:
            messagebox.showerror("Insert note", "SMPTE division is not supported.", parent=self)
            return
        tick = simpledialog.askinteger("Insert note", "Start tick:", initialvalue=0, minvalue=0, parent=self)
        if tick is None:
            return
        duration = simpledialog.askinteger("Insert note", "Duration (ticks):",
                                           initialvalue=self.app.song.division, minvalue=1, parent=self)
        if duration is None:
            return
        pitch = simpledialog.askinteger("Insert note", "MIDI pitch (0–127):",
                                        initialvalue=60, minvalue=0, maxvalue=127, parent=self)
        if pitch is None:
            return
        channel = simpledialog.askinteger("Insert note", "Channel (1–16):",
                                          initialvalue=1, minvalue=1, maxvalue=16, parent=self)
        if channel is None:
            return
        try:
            self.app.snapshot()
            insert_note(self.app.song, self.track_index, tick, duration, pitch, channel=channel)
            self.selected = None
            self.render()
            self.app.show_events()
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            messagebox.showerror("Insert note", str(exc), parent=self)

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
            messagebox.showerror("Delete note", str(exc), parent=self)

    def quantize(self):
        try:
            self.app.snapshot()
            count = quantize_notes(self.app.song, self.track_index, 16)
            if count == 0:
                self.app.history.pop()
            self.selected = None
            self.render()
            self.app.show_events()
            self.info.set(f"Quantized {count} notes to 1/16.")
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            messagebox.showerror("Quantize", str(exc), parent=self)

    def begin_drag(self, event):
        index = self.hit_note()
        if index is None:
            self.drag_origin = None
            return
        self.selected = index
        self.drag_origin = (index, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

    def end_drag(self, event):
        if self.drag_origin is None:
            return
        index, old_x, old_y = self.drag_origin
        self.drag_origin = None
        if index >= len(self.notes) or self.app.song.division & 0x8000:
            return
        start, end, pitch, _, _, on_idx, off_idx = self.notes[index]
        dx = self.canvas.canvasx(event.x) - old_x
        dy = self.canvas.canvasy(event.y) - old_y
        tick = max(0, round(start + dx * self.app.song.division / PIXELS_PER_BEAT))
        target_pitch = max(0, min(127, pitch - round(dy / NOTE_HEIGHT)))
        try:
            self.app.snapshot()
            move_note(self.app.song, self.track_index, on_idx, off_idx, tick, target_pitch)
            self.selected = None
            self.render()
            self.app.show_events()
            self.info.set(f"Moved note to {pitch_label(target_pitch)}, tick {tick}.")
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            messagebox.showerror("Move note", str(exc), parent=self)

    def edit_note(self, _event=None):
        self.selected = self.hit_note()
        if self.selected is None:
            return
        start, end, pitch, channel, velocity, on_idx, off_idx = self.notes[self.selected]
        new_pitch = simpledialog.askinteger("Pitch", "MIDI note (0–127):",
                                            initialvalue=pitch, minvalue=0, maxvalue=127, parent=self)
        if new_pitch is None:
            return
        new_start = simpledialog.askinteger("Start", "Start tick:",
                                            initialvalue=start, minvalue=0, parent=self)
        if new_start is None:
            return
        duration = simpledialog.askinteger("Duration", "Duration in ticks:",
                                           initialvalue=max(1, end-start), minvalue=1, parent=self)
        if duration is None:
            return
        track = self.app.song.tracks[self.track_index]
        on = track.events[on_idx]
        off = track.events[off_idx]
        try:
            # Validate both changes before changing the song.
            if new_start + duration > 0x7fffffff:
                raise MidiError("Note end tick is too large")
            self.app.snapshot()
            self.app.song.set_event(self.track_index, on_idx,
                                    tick=new_start, data=bytes((new_pitch, on.data[1])))
            self.app.song.set_event(self.track_index, off_idx,
                                    tick=new_start+duration, data=bytes((new_pitch, off.data[1])))
            self.app.show_events()
            self.app.status.set("Piano Roll modified — Save As to write a MIDI file.")
            self.selected = None
            self.render()
        except MidiError as exc:
            if self.app.history:
                self.app.song = self.app.history.pop()
                self.app.refresh()
            messagebox.showerror("Cannot edit note", str(exc), parent=self)
