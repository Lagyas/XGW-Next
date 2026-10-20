"""Lyrics / Karaoke editor window: list and edit lyric events, type the song
text and spread its syllables over the notes of a melody track, and follow
the song in a karaoke view (XF / .kar line and page markers)."""
import tkinter as tk
from copy import deepcopy
from tkinter import messagebox, simpledialog, ttk

from lyrics_ops import (assign_syllables, delete_lyrics, edit_lyric, insert_lyric, karaoke_pages,
                        lyric_events, note_starts, page_index_at, parse_lyrics_text)
from midi import MidiError, get_text_encoding, TEXT_ENCODINGS
from song_position import format_bbt, parse_bbt

HELP = ('Type the song text below: words separated by spaces, syllables by "-" '
        '(Ka-ra-o-ke). A new line becomes "/", an empty line a new page "<".')


class LyricsEditor(tk.Toplevel):
    def __init__(self, app, track_index):
        super().__init__(app.root)
        self.app = app
        self.track_index = track_index
        self.geometry("980x640")
        self._page_cache = None
        self._timer = None
        self.info = tk.StringVar()

        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=(6, 2))
        ttk.Label(top, text="Lyrics track:").pack(side="left")
        self.track_choice = tk.StringVar()
        self.track_box = ttk.Combobox(top, textvariable=self.track_choice, state="readonly", width=28)
        self.track_box.pack(side="left", padx=(4, 12))
        self.track_box.bind("<<ComboboxSelected>>", self._choose_track)
        for text, command in (("Insert at song position…", self.insert_at_position),
                              ("Edit…", self.edit_selected),
                              ("Move to song position", self.move_to_position),
                              ("Delete", self.delete_selected)):
            ttk.Button(top, text=text, command=command).pack(side="left", padx=2)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=4)
        left = ttk.Frame(body)
        self.tree = ttk.Treeview(left, columns=("pos", "tick", "text"), show="headings", selectmode="extended")
        for col, title, width in (("pos", "Position", 110), ("tick", "Tick", 70), ("text", "Lyric", 200)):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, stretch=col == "text")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())
        self.tree.bind("<Delete>", lambda _e: self.delete_selected())
        self.tree.bind("<BackSpace>", lambda _e: self.delete_selected())
        body.add(left, weight=1)

        right = ttk.Frame(body)
        ttk.Label(right, text=HELP, wraplength=420, justify="left").pack(anchor="w")
        self.text = tk.Text(right, height=10, wrap="word", undo=True)
        self.text.pack(fill="both", expand=True, pady=4)
        row = ttk.Frame(right)
        row.pack(fill="x")
        ttk.Label(row, text="Melody notes from:").pack(side="left")
        self.note_track_choice = tk.StringVar()
        self.note_track_box = ttk.Combobox(row, textvariable=self.note_track_choice, state="readonly", width=22)
        self.note_track_box.pack(side="left", padx=4)
        ttk.Label(row, text="from").pack(side="left")
        self.from_position = tk.StringVar(value="0001:01:000")
        ttk.Entry(row, textvariable=self.from_position, width=12).pack(side="left", padx=4)
        row2 = ttk.Frame(right)
        row2.pack(fill="x", pady=4)
        self.replace_existing = tk.BooleanVar(value=True)
        ttk.Checkbutton(row2, text="Replace lyrics in that range", variable=self.replace_existing).pack(side="left")
        ttk.Button(row2, text="Assign syllables to notes", command=self.assign).pack(side="left", padx=8)
        ttk.Button(row2, text="Load current lyrics", command=self.load_text_from_lyrics).pack(side="left")
        body.add(right, weight=1)

        self.karaoke = tk.Canvas(self, height=150, background="#101418", highlightthickness=0)
        self.karaoke.pack(fill="x", padx=8, pady=(2, 4))
        ttk.Label(self, textvariable=self.info).pack(fill="x", padx=8, pady=(0, 6))
        self.reload()
        self._poll()

    # ------------------------------------------------------------------
    def _track_labels(self):
        return [f"{i + 1}: {t.name()}" for i, t in enumerate(self.app.song.tracks)]

    def _choose_track(self, _event=None):
        self.track_index = self.track_box.current()
        self.reload()

    def reload(self):
        """Re-read the song (after edits, undo or a new file)."""
        song = self.app.song
        if song is None or not song.tracks:
            self.destroy()
            return
        self.track_index = max(0, min(self.track_index, len(song.tracks) - 1))
        labels = self._track_labels()
        self.track_box.configure(values=labels)
        self.track_box.current(self.track_index)
        self.note_track_box.configure(values=labels)
        if self.note_track_box.current() < 0 or self.note_track_box.current() >= len(labels):
            self.note_track_box.current(self.track_index)
        self.title(f"Lyrics / Karaoke — Track {self.track_index + 1}")
        selected = set(self.tree.selection())
        self.tree.delete(*self.tree.get_children())
        self.rows = lyric_events(song.tracks[self.track_index])
        for index, tick, text in self.rows:
            iid = str(index)
            self.tree.insert("", "end", iid=iid, values=(self._pos(tick), tick, text))
            if iid in selected:
                self.tree.selection_add(iid)
        self._page_cache = karaoke_pages([(tick, text) for _, tick, text in self.rows])
        self.info.set(f"{len(self.rows)} lyric events · text encoding {TEXT_ENCODINGS[get_text_encoding()]}")
        self.draw_karaoke(force=True)

    def _pos(self, tick):
        try:
            return format_bbt(self.app.song, tick)
        except MidiError:
            return str(tick)

    def _selected_indices(self):
        return [int(i) for i in self.tree.selection()]

    def _commit(self, title, change):
        """Run `change(song)` on a trial copy, then for real with an undo snapshot."""
        try:
            change(deepcopy(self.app.song))
        except MidiError as exc:
            messagebox.showerror(title, str(exc), parent=self)
            return False
        self.app.snapshot()
        try:
            change(self.app.song)
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            messagebox.showerror(title, str(exc), parent=self)
            return False
        self.app.refresh()
        self.reload()
        return True

    # ------------------------------------------------------------------
    def insert_at_position(self):
        tick = int(getattr(self.app, "playhead_tick", 0))
        text = simpledialog.askstring("Insert lyric", f"Lyric at {self._pos(tick)}:", parent=self)
        if text:
            self._commit("Insert lyric", lambda s: insert_lyric(s, self.track_index, tick, text))

    def edit_selected(self):
        indices = self._selected_indices()
        if not indices:
            return
        index = indices[0]
        row = next((r for r in self.rows if r[0] == index), None)
        if row is None:
            return
        text = simpledialog.askstring("Edit lyric", "Lyric:", initialvalue=row[2], parent=self)
        if text is None:
            return
        pos = simpledialog.askstring("Edit lyric", "Position (bar:beat:tick):", initialvalue=self._pos(row[1]), parent=self)
        if pos is None:
            return
        try:
            tick = parse_bbt(self.app.song, pos)
        except MidiError as exc:
            messagebox.showerror("Edit lyric", str(exc), parent=self)
            return
        self._commit("Edit lyric", lambda s: edit_lyric(s, self.track_index, index, tick=tick, text=text))

    def move_to_position(self):
        indices = self._selected_indices()
        if not indices:
            return
        tick = int(getattr(self.app, "playhead_tick", 0))
        first = min(r[1] for r in self.rows if r[0] in indices)

        def change(song):
            for i in indices:
                old = song.tracks[self.track_index].events[i].tick
                edit_lyric(song, self.track_index, i, tick=old - first + tick)
        self._commit("Move lyrics", change)

    def delete_selected(self):
        indices = self._selected_indices()
        if indices:
            self._commit("Delete lyrics", lambda s: delete_lyrics(s, self.track_index, indices))
        return "break"

    def load_text_from_lyrics(self):
        """Put the existing lyrics into the text box (markers shown as line breaks)."""
        out = []
        for _, _, text in self.rows:
            if text.startswith(("<", "\\")):
                out.append("\n\n" + text[1:])
            elif text.startswith("/"):
                out.append("\n" + text[1:])
            elif out and not out[-1].endswith((" ", "\n")):
                out.append("-" + text)
            else:
                out.append(text)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "".join(out).strip())

    def assign(self):
        syllables = parse_lyrics_text(self.text.get("1.0", "end"))
        if not syllables:
            messagebox.showinfo("Assign lyrics", "Type the song text first.", parent=self)
            return
        note_track = self.note_track_box.current()
        try:
            start = parse_bbt(self.app.song, self.from_position.get())
        except MidiError as exc:
            messagebox.showerror("Assign lyrics", str(exc), parent=self)
            return
        starts = note_starts(self.app.song.tracks[note_track], start)
        if not starts:
            messagebox.showinfo("Assign lyrics", "No notes on that track after the position.", parent=self)
            return
        placed = {}

        def change(song):
            placed["n"] = assign_syllables(song, self.track_index, syllables, starts, replace=self.replace_existing.get())
        if self._commit("Assign lyrics", change):
            n = placed.get("n", 0)
            rest = len(syllables) - n
            self.info.set(f"Placed {n} syllables on notes of track {note_track + 1}"
                          + (f"; {rest} syllables left over (not enough notes)." if rest > 0 else "."))

    # ------------------------------------------------------------------
    def _poll(self):
        self._timer = None
        try:
            if self.winfo_exists():
                self.draw_karaoke()
                self._timer = self.after(80, self._poll)
        except tk.TclError:
            return

    def draw_karaoke(self, force=False):
        pages = self._page_cache or []
        c = self.karaoke
        tick = int(getattr(self.app, "playhead_tick", 0))
        state = (page_index_at(pages, tick) if pages else -1, tick)
        if not force and getattr(self, "_last_state", None) == state:
            return
        self._last_state = state
        c.delete("all")
        if not pages:
            c.create_text(12, 20, anchor="w", text="No lyrics on this track.", fill="#8a94a6", font=("Arial", 14))
            return
        page = pages[state[0]]
        y = 26
        for line in page[:4]:
            x = 16
            for s_tick, text in line:
                color = "#ff9c1a" if s_tick <= tick else "#f2f5f8"
                item = c.create_text(x, y, anchor="w", text=text, fill=color, font=("Arial", 20, "bold"))
                x = c.bbox(item)[2] + (0 if not text.endswith(" ") else 2)
            y += 34

    def destroy(self):
        if self._timer is not None:
            try:
                self.after_cancel(self._timer)
            except tk.TclError:
                pass
            self._timer = None
        super().destroy()
