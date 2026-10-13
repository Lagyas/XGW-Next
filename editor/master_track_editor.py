"""XGworks-inspired Master Track window for tempo and meter changes."""
import tkinter as tk
from tkinter import ttk, messagebox
from midi import MidiError
from master_ops import (master_events, tempo_payload, time_signature_payload,
                        put_master_event, delete_master_event)

class MasterTrackEditor(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("Master Track — Tempo / Time Signature")
        self.geometry("760x490")
        self.tick = tk.StringVar(value="0")
        self.bpm = tk.StringVar(value="120")
        self.numerator = tk.StringVar(value="4")
        self.denominator = tk.StringVar(value="4")
        self.selected = None
        form = ttk.Frame(self)
        form.pack(fill="x", padx=10, pady=10)
        for column, (label, variable) in enumerate((
            ("Tick", self.tick), ("Tempo BPM", self.bpm),
            ("Numerator", self.numerator), ("Denominator", self.denominator)
        )):
            ttk.Label(form, text=label).grid(row=0, column=column, padx=8)
            ttk.Entry(form, textvariable=variable, width=13).grid(row=1, column=column, padx=8)
        columns = ("track", "tick", "kind", "value")
        self.list = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        for col, width in (("track", 90), ("tick", 120), ("kind", 160), ("value", 180)):
            self.list.heading(col, text=col.title())
            self.list.column(col, width=width)
        self.list.pack(fill="both", expand=True, padx=10, pady=6)
        self.list.bind("<<TreeviewSelect>>", self.on_select)
        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=10, pady=10)
        for label, callback in (
            ("Add tempo", self.add_tempo), ("Add time signature", self.add_signature),
            ("Update selected", self.update_selected), ("Delete selected", self.delete_selected),
            ("Refresh", self.refresh), ("Undo", self.undo)
        ):
            ttk.Button(actions, text=label, command=callback).pack(side="left", padx=3)
        self.refresh()

    def refresh(self):
        self.list.delete(*self.list.get_children())
        self.selected = None
        if self.app.song is None:
            return
        for track_index, event_index, event in master_events(self.app.song):
            if event.meta_type == 0x51 and len(event.data) == 3:
                microseconds = int.from_bytes(event.data, "big")
                value = f"{60000000 / microseconds:.2f} BPM" if microseconds else "Invalid tempo"
                kind = "Tempo"
            elif event.meta_type == 0x58 and len(event.data) >= 2:
                value = f"{event.data[0]}/{2 ** event.data[1]}"
                kind = "Time signature"
            else:
                value, kind = "Invalid data", "Master"
            self.list.insert("", "end", iid=f"{track_index}:{event_index}",
                             values=(track_index + 1, event.tick, kind, value))

    def on_select(self, _event=None):
        selection = self.list.selection()
        if not selection:
            return
        track_index, event_index = map(int, selection[0].split(":"))
        self.selected = (track_index, event_index)
        event = self.app.song.tracks[track_index].events[event_index]
        self.tick.set(str(event.tick))
        if event.meta_type == 0x51 and len(event.data) == 3:
            microseconds = int.from_bytes(event.data, "big")
            if microseconds:
                self.bpm.set(str(round(60000000 / microseconds, 2)))
        elif event.meta_type == 0x58 and len(event.data) >= 2:
            self.numerator.set(str(event.data[0]))
            self.denominator.set(str(2 ** event.data[1]))

    def apply(self, meta_type, updating=False):
        if self.app.song is None:
            return
        if updating and self.selected is None:
            messagebox.showinfo("Master Track", "Select an event to update.", parent=self)
            return
        try:
            tick = int(self.tick.get())
            if meta_type == 0x51:
                payload = tempo_payload(float(self.bpm.get()))
            else:
                payload = time_signature_payload(int(self.numerator.get()),
                                                 int(self.denominator.get()))
            track_index, event_index = self.selected if updating else (0, None)
            self.app.snapshot()
            try:
                put_master_event(self.app.song, tick, meta_type, payload, track_index, event_index)
            except Exception:
                self.app.history.pop()
                raise
            self.refresh()
            self.app.show_events()
            self.app.status.set("Master Track modified — Save As to save.")
        except (ValueError, MidiError) as exc:
            messagebox.showerror("Master Track", str(exc), parent=self)

    def add_tempo(self):
        self.apply(0x51)

    def add_signature(self):
        self.apply(0x58)

    def update_selected(self):
        if self.selected is None:
            return
        track_index, event_index = self.selected
        event = self.app.song.tracks[track_index].events[event_index]
        self.apply(event.meta_type, updating=True)

    def delete_selected(self):
        if self.selected is None:
            return
        track_index, event_index = self.selected
        try:
            self.app.snapshot()
            delete_master_event(self.app.song, track_index, event_index)
            self.refresh()
            self.app.show_events()
        except MidiError as exc:
            self.app.history.pop()
            messagebox.showerror("Master Track", str(exc), parent=self)

    def undo(self):
        if self.app.history:
            self.app.undo()
            self.refresh()
