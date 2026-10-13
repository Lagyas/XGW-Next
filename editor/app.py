"""XGW Next prototype: track/event inspector and basic MIDI editor."""
import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from midi import Song, MidiError
from piano_roll import PianoRoll

THEMES = {
    "Classic": ("#ece9d8", "#000000", "#ffffff"),
    "Modern Light": ("#f4f6fa", "#20242c", "#ffffff"),
    "Modern Dark": ("#252830", "#f3f4f7", "#353943"),
}

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("XGW Next 0.2 — MIDI Editor")
        self.root.geometry("1050x650")
        self.song = None
        self.path = None
        self.history = []
        self.theme = tk.StringVar(value="Classic")
        self.make_ui()
        self.apply_theme()

    def make_ui(self):
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Open MIDI...", command=self.open_file)
        file_menu.add_command(label="Save As...", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menu.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(menu, tearoff=0)
        edit_menu.add_command(label="Edit selected event...", command=self.edit_event)
        edit_menu.add_command(label="Transpose selected track...", command=self.transpose)
        edit_menu.add_command(label="Undo", command=self.undo)
        view_menu = tk.Menu(menu, tearoff=0)
        view_menu.add_command(label="Piano Roll (selected track)...", command=self.open_piano_roll)
        menu.add_cascade(label="View", menu=view_menu)
        menu.add_cascade(label="Edit", menu=edit_menu)
        theme_menu = tk.Menu(menu, tearoff=0)
        for name in THEMES:
            theme_menu.add_radiobutton(label=name, variable=self.theme, value=name, command=self.apply_theme)
        menu.add_cascade(label="Appearance", menu=theme_menu)
        self.root.config(menu=menu)

        outer = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        left = ttk.Frame(outer)
        right = ttk.Frame(outer)
        outer.add(left, weight=1)
        outer.add(right, weight=4)
        ttk.Label(left, text="Tracks").pack(anchor="w")
        self.tracks = ttk.Treeview(left, columns=("events",), show="tree headings", selectmode="browse")
        self.tracks.heading("#0", text="Track")
        self.tracks.heading("events", text="Events")
        self.tracks.column("#0", width=170)
        self.tracks.column("events", width=65, anchor="e")
        self.tracks.pack(fill=tk.BOTH, expand=True)
        self.tracks.bind("<<TreeviewSelect>>", lambda _: self.show_events())
        ttk.Label(right, text="MIDI Events").pack(anchor="w")
        cols = ("tick", "channel", "type", "data")
        self.events = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        for col, width in (("tick", 95), ("channel", 75), ("type", 155), ("data", 420)):
            self.events.heading(col, text=col.title())
            self.events.column(col, width=width)
        self.events.pack(fill=tk.BOTH, expand=True)
        self.events.bind("<Double-1>", lambda _: self.edit_event())
        self.status = tk.StringVar(value="Open a MIDI file to begin.")
        ttk.Label(self.root, textvariable=self.status).pack(fill=tk.X, padx=8, pady=(0, 6))

    def apply_theme(self):
        bg, fg, field = THEMES[self.theme.get()]
        self.root.configure(bg=bg)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=bg, foreground=fg)
        style.configure("Treeview", background=field, fieldbackground=field,
                        foreground="#151515" if self.theme.get() != "Modern Dark" else "#f0f0f0")
        style.configure("Treeview.Heading", background=bg, foreground=fg)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")])
        if not path:
            return
        try:
            song = Song.read(path)
        except (OSError, MidiError) as exc:
            messagebox.showerror("Cannot open MIDI", str(exc))
            return
        self.song, self.path, self.history = song, Path(path), []
        self.refresh()
        self.status.set(f"{self.path.name} | Format {song.fmt} | {len(song.tracks)} tracks | division {song.division}")

    def refresh(self):
        self.tracks.delete(*self.tracks.get_children())
        self.events.delete(*self.events.get_children())
        if self.song:
            for i, track in enumerate(self.song.tracks):
                self.tracks.insert("", "end", iid=str(i), text=f"{i+1}: {track.name()}", values=(len(track.events),))
            if self.song.tracks:
                self.tracks.selection_set("0")
                self.show_events()

    def selected_track(self):
        selected = self.tracks.selection()
        return int(selected[0]) if selected else None

    def show_events(self):
        self.events.delete(*self.events.get_children())
        idx = self.selected_track()
        if idx is None or not self.song:
            return
        for i, event in enumerate(self.song.tracks[idx].events):
            self.events.insert("", "end", iid=str(i), values=(
                event.tick, event.channel() or "-", event.label(), event.description()))

    def snapshot(self):
        self.history.append(copy.deepcopy(self.song))
        if len(self.history) > 15:
            self.history.pop(0)

    def edit_event(self):
        track = self.selected_track()
        selected = self.events.selection()
        if self.song is None or track is None or not selected:
            return
        idx = int(selected[0])
        event = self.song.tracks[track].events[idx]
        tick = simpledialog.askinteger("Event time", "Absolute tick:", initialvalue=event.tick, minvalue=0)
        if tick is None:
            return
        data = None
        if event.status < 0xf0:
            raw = simpledialog.askstring("MIDI data", "Hex data bytes:", initialvalue=event.data.hex(" "))
            if raw is None:
                return
            try:
                data = bytes.fromhex(raw)
            except ValueError:
                messagebox.showerror("Invalid data", "Enter valid hexadecimal bytes.")
                return
        try:
            self.snapshot()
            self.song.set_event(track, idx, tick=tick, data=data)
            self.show_events()
            self.status.set("Modified — use Save As to save a copy.")
        except MidiError as exc:
            self.history.pop()
            messagebox.showerror("Invalid event", str(exc))

    def transpose(self):
        track = self.selected_track()
        if self.song is None or track is None:
            return
        steps = simpledialog.askinteger("Transpose", "Semitones (-127 to 127):", minvalue=-127, maxvalue=127)
        if steps is None:
            return
        try:
            self.snapshot()
            changed = self.song.transpose(track, steps)
            self.show_events()
            self.status.set(f"Transposed {changed} note events.")
        except MidiError as exc:
            self.history.pop()
            messagebox.showerror("Transpose failed", str(exc))

    def undo(self):
        if self.history:
            self.song = self.history.pop()
            self.refresh()
            self.status.set("Undo completed.")

    def open_piano_roll(self):
        track = self.selected_track()
        if self.song is None or track is None:
            messagebox.showinfo('Piano Roll', 'Open a MIDI file and select a track first.')
            return
        PianoRoll(self, track)

    def save_as(self):
        if not self.song:
            return
        target = filedialog.asksaveasfilename(defaultextension=".mid",
                    initialfile=(self.path.stem + "_edited.mid") if self.path else "edited.mid",
                    filetypes=[("MIDI files", "*.mid")])
        if not target:
            return
        try:
            self.song.save(target)
            self.status.set(f"Saved: {target}")
        except (OSError, MidiError) as exc:
            messagebox.showerror("Save failed", str(exc))

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
