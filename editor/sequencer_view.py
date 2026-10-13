"""Arrangement overview for a MIDI song, grouped by track and time."""
import tkinter as tk
from track_voice import used_channels, channel_voice_at
from xg_voices import voice_label
from tkinter import ttk
from arrangement import track_clips

ROW_HEIGHT = 42
LEFT_WIDTH = 230
BEAT_WIDTH = 28
HEADER_HEIGHT = 38

def track_spans(song):
    """Return one note span per track, preserving empty tracks."""
    result = []
    for track in song.tracks:
        note_ticks = [e.tick for e in track.events
                      if 0x80 <= e.status <= 0x9f and len(e.data) == 2]
        result.append((min(note_ticks), max(note_ticks)) if note_ticks else None)
    return result

class SequencerView(ttk.Frame):
    def __init__(self, parent, on_track=None, on_open=None, on_toggle=None, on_instrument=None, on_clip=None):
        super().__init__(parent)
        self.song = None
        self.on_track = on_track
        self.on_open = on_open
        self.on_toggle = on_toggle
        self.on_instrument = on_instrument
        self.on_clip = on_clip
        self.muted = set()
        self.solo = set()
        self.selected_track = 0
        self.canvas = tk.Canvas(self, background="#f9fafb", highlightthickness=0)
        xs = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        ys = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        xs.grid(row=1, column=0, sticky="ew")
        ys.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Double-Button-1>", self.double_click)
        self.draw()

    def set_mix(self, muted, solo):
        self.muted = set(muted)
        self.solo = set(solo)
        self.draw()

    def set_song(self, song):
        self.song = song
        self.selected_track = 0
        self.draw()

    def select_track(self, index):
        self.selected_track = index
        self.draw()

    def _row_at(self, event):
        y = self.canvas.canvasy(event.y)
        row = int((y - HEADER_HEIGHT) // ROW_HEIGHT)
        if self.song is None or not 0 <= row < len(self.song.tracks):
            return None
        return row

    def click(self, event):
        row = self._row_at(event)
        if row is not None:
            x = self.canvas.canvasx(event.x)
            if 0 <= x < 150 and self.on_instrument and event.y > 0:
                self.selected_track = row
                if self.on_track:
                    self.on_track(row)
                self.on_instrument(row)
                return
            if 155 <= x < 185 and self.on_toggle:
                self.on_toggle(row, "mute")
                return
            if 185 <= x < 215 and self.on_toggle:
                self.on_toggle(row, "solo")
                return
            if x >= LEFT_WIDTH and self.on_clip and self.song is not None:
                tick = int((x - LEFT_WIDTH) / BEAT_WIDTH * self.song.division)
                for clip_index, (start, end) in enumerate(track_clips(self.song.tracks[row], self.song.division)):
                    if start <= tick <= end:
                        self.selected_track = row
                        self.on_clip(row, clip_index)
                        return
            self.selected_track = row
            self.draw()
            if self.on_track:
                self.on_track(row)

    def double_click(self, event):
        row = self._row_at(event)
        if row is not None and self.on_open:
            self.on_open(row)

    def draw(self):
        c = self.canvas
        c.delete("all")
        if self.song is None:
            c.create_text(28, 32, anchor="w", text="Open a MIDI file to view the sequencer.")
            return
        division = self.song.division
        if division <= 0 or division & 0x8000:
            c.create_text(28, 32, anchor="w", text="SMPTE timeline is not yet supported.")
            return
        spans = [track_clips(track, division) for track in self.song.tracks]
        max_tick = max((e.tick for t in self.song.tracks for e in t.events), default=division * 16)
        beats = max(32, int(max_tick / division) + 8)
        width = LEFT_WIDTH + beats * BEAT_WIDTH
        height = HEADER_HEIGHT + max(10, len(self.song.tracks)) * ROW_HEIGHT
        c.configure(scrollregion=(0, 0, width, height))
        c.create_rectangle(0, 0, LEFT_WIDTH, HEADER_HEIGHT, fill="#e2e8f0", outline="#cbd5e1")
        c.create_text(12, 18, text="TRACK / MIDI PARTS", anchor="w", font=("Arial", 10, "bold"))
        for beat in range(beats + 1):
            x = LEFT_WIDTH + beat * BEAT_WIDTH
            c.create_line(x, HEADER_HEIGHT, x, height,
                          fill="#94a3b8" if beat % 4 == 0 else "#e2e8f0")
            if beat % 4 == 0:
                c.create_text(x + 3, 18, anchor="w", text=str(beat // 4 + 1))
        for index, track in enumerate(self.song.tracks):
            y = HEADER_HEIGHT + index * ROW_HEIGHT
            active = index == self.selected_track
            c.create_rectangle(0, y, width, y + ROW_HEIGHT,
                               fill="#dbeafe" if active else ("#f8fafc" if index % 2 == 0 else "#ffffff"),
                               outline="#cbd5e1")
            c.create_text(10, y + 15, anchor="w", text=f"{index+1:02d}  {track.name()[:26]}")
            channels = sorted({(e.status & 15) + 1 for e in track.events if 0x80 <= e.status <= 0xef})
            if channels:
                channel = channels[0]
                voice = channel_voice_at(self.song, index, channel)
                subtitle = f"CH {channel} · {voice_label(voice.msb, voice.lsb, voice.program)}"
            else:
                subtitle = "CH — · no instrument"
            c.create_text(10, y + 31, anchor="w", text=subtitle[:23],
                          fill="#475569", font=("Arial", 9))
            for x, name, active in ((155, "M", index in self.muted),
                                    (185, "S", index in self.solo)):
                c.create_rectangle(x, y + 9, x + 26, y + 32,
                                   fill=("#f59e0b" if name == "M" else "#22c55e") if active else "#e2e8f0",
                                   outline="#94a3b8")
                c.create_text(x + 13, y + 20, text=name, font=("Arial", 10, "bold"))
            for start, end in spans[index]:
                x1 = LEFT_WIDTH + start / division * BEAT_WIDTH
                x2 = LEFT_WIDTH + max(end, start + division // 4) / division * BEAT_WIDTH
                c.create_rectangle(x1, y + 8, max(x1 + 8, x2), y + ROW_HEIGHT - 8,
                                   fill="#3b82f6", outline="#1d4ed8")
                c.create_text(x1 + 5, y + ROW_HEIGHT / 2, anchor="w",
                              text=f"{max(1, (end-start)//division)} beats",
                              fill="white", font=("Arial", 9))
        c.create_line(LEFT_WIDTH, 0, LEFT_WIDTH, height, fill="#64748b", width=2)
