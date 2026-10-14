"""First XGworks-style notation view: read-only treble/bass staves."""
import tkinter as tk
from tkinter import ttk
from staff_ops import staff_notes, staff_position, note_value, staff_rest_spans

LEFT, BEAT_W, STAFF_GAP = 92, 92, 10

class StaffEditor(tk.Toplevel):
    def __init__(self, app, track_index):
        super().__init__(app.root)
        self.app, self.track_index = app, track_index
        self.title(f"Staff — Track {track_index + 1} (preview)")
        self.geometry("1000x520")
        self.clef = tk.StringVar(value="treble")
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=5)
        ttk.Label(top, text="Clef:").pack(side="left")
        ttk.Combobox(top, textvariable=self.clef, values=("treble", "bass"),
                     state="readonly", width=10).pack(side="left", padx=5)
        ttk.Button(top, text="Refresh", command=self.render).pack(side="left")
        ttk.Label(top, text="Notation preview — editing remains in Piano Roll / List Editor").pack(side="left", padx=12)
        area = ttk.Frame(self)
        area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(area, background="white", highlightthickness=0)
        scroll_x = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        scroll_y = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scroll_x.grid(row=1, column=0, sticky="ew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self.clef.trace_add("write", lambda *_: self.render())
        self.render()
        self.after(100, self.poll_playhead)

    def render(self):
        c = self.canvas
        c.delete("all")
        song = self.app.song
        if song is None or not 0 <= self.track_index < len(song.tracks):
            return
        division = song.division
        if not division or division & 0x8000:
            c.create_text(30, 30, anchor="w", text="Notation requires PPQN timing")
            return
        notes = staff_notes(song.tracks[self.track_index])
        max_tick = max((n[1] for n in notes), default=division * 16)
        width = max(1000, LEFT + max_tick / division * BEAT_W + 300)
        c.configure(scrollregion=(0, 0, width, 450))
        bottom_y = 230
        for line in range(5):
            y = bottom_y - line * 2 * STAFF_GAP
            c.create_line(LEFT, y, width, y, fill="#64748b")
        c.create_text(35, 191, text="𝄞" if self.clef.get() == "treble" else "𝄢",
                      font=("Segoe UI Symbol", 42))
        for beat in range(int((width - LEFT) / BEAT_W) + 1):
            x = LEFT + beat * BEAT_W
            c.create_line(x, 160, x, 245, fill="#cbd5e1" if beat % 4 else "#64748b")
            if beat % 4 == 0:
                c.create_text(x + 4, 151, text=str(beat // 4 + 1), anchor="w")
        # Draw rests only in genuinely silent spans (never across held chords).
        for rest_start, rest_end in staff_rest_spans(notes, division):
            x = LEFT + rest_start / division * BEAT_W
            length = rest_end - rest_start
            denom, dotted = note_value(length, division)
            label = {1: "𝄻", 2: "𝄼", 4: "𝄽", 8: "𝄾", 16: "𝄿",
                     32: "𝅀", 64: "𝅁"}[denom]
            c.create_text(x + 10, bottom_y - 4 * STAFF_GAP, text=label,
                          fill="#475569", font=("Segoe UI Symbol", 20),
                          tags="rest")
            if dotted:
                c.create_text(x + 25, bottom_y - 4 * STAFF_GAP, text="·",
                              fill="#475569", font=("Segoe UI", 14), tags="rest")
        for start, end, pitch, velocity, ch in notes:
            denominator, dotted = note_value(max(1, end - start), division)
            step, sharp = staff_position(pitch, self.clef.get())
            x = LEFT + start / division * BEAT_W
            y = bottom_y - step * STAFF_GAP
            # Ledger lines above and below the staff.
            if step < 0:
                for n in range(-2, step - 1, -2):
                    c.create_line(x - 13, bottom_y - n * STAFF_GAP,
                                  x + 13, bottom_y - n * STAFF_GAP, fill="#334155")
            elif step > 8:
                for n in range(10, step + 1, 2):
                    c.create_line(x - 13, bottom_y - n * STAFF_GAP,
                                  x + 13, bottom_y - n * STAFF_GAP, fill="#334155")
            if sharp:
                c.create_text(x - 17, y, text="♯", font=("Segoe UI Symbol", 13))
            c.create_oval(x - 8, y - 5, x + 8, y + 5,
                          fill="white" if denominator in (1, 2) else "#1d4ed8",
                          outline="#1e3a8a", width=2)
            if denominator != 1:
                stem_up = step < 4
                stem_x = x + 8 if stem_up else x - 8
                stem_end = y - 31 if stem_up else y + 31
                c.create_line(stem_x, y, stem_x, stem_end, fill="#1e3a8a", width=2)
                if denominator >= 8:
                    for flag in range({8: 1, 16: 2, 32: 3, 64: 4}[denominator]):
                        offset = flag * (7 if stem_up else -7)
                        c.create_line(stem_x, stem_end + offset,
                                      stem_x + (11 if stem_up else -11),
                                      stem_end + offset + (13 if stem_up else -13),
                                      fill="#1e3a8a", width=2, smooth=True)
            if dotted:
                c.create_oval(x + 14, y - 2, x + 18, y + 2,
                              fill="#1e3a8a", outline="")
        self.update_playhead()

    def update_playhead(self):
        c = self.canvas
        c.delete("playhead")
        song = self.app.song
        if song is None or not song.division or song.division & 0x8000:
            return
        x = LEFT + self.app.playhead_tick / song.division * BEAT_W
        c.create_line(x, 110, x, 300, fill="#dc2626", width=2, tags="playhead")
        if self.app.player.playing:
            left, right = c.canvasx(0), c.canvasx(c.winfo_width())
            if x > right - 60 or x < left + LEFT:
                bounds = c.cget("scrollregion").split()
                if len(bounds) == 4 and float(bounds[2]) > c.winfo_width():
                    fraction = max(0, min(1, (x - c.winfo_width() * 0.4) /
                                           (float(bounds[2]) - c.winfo_width())))
                    c.xview_moveto(fraction)

    def poll_playhead(self):
        if self.winfo_exists():
            self.update_playhead()
            self.after(100, self.poll_playhead)
