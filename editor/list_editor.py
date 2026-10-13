"""XGworks-style MIDI event list for a selected track."""
import tkinter as tk
from tkinter import ttk, messagebox
from midi import MidiError

class ListEditor(tk.Toplevel):
    def __init__(self, app, track_index):
        super().__init__(app.root)
        self.app = app
        self.track_index = track_index
        self.title(f"List Editor — Track {track_index + 1}")
        self.geometry("950x620")
        self.filter = tk.StringVar(value="All events")
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=8)
        ttk.Label(header, text="Event filter:").pack(side="left")
        filter_box = ttk.Combobox(header, state="readonly", textvariable=self.filter,
                                  values=("All events", "Notes", "Control changes",
                                          "Program changes", "Pitch bend", "Meta", "SysEx"),
                                  width=21)
        filter_box.pack(side="left", padx=8)
        filter_box.bind("<<ComboboxSelected>>", lambda _: self.refresh())
        ttk.Button(header, text="Refresh", command=self.refresh).pack(side="left")
        columns = ("tick", "channel", "type", "data")
        self.events = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        for col, width in (("tick", 110), ("channel", 80), ("type", 160), ("data", 530)):
            self.events.heading(col, text=col.title())
            self.events.column(col, width=width, stretch=col == "data")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.events.yview)
        self.events.configure(yscrollcommand=scroll.set)
        self.events.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        scroll.pack(side="left", fill="y", pady=(0, 10))
        buttons = ttk.Frame(self)
        buttons.pack(side="bottom", fill="x", padx=10, pady=8)
        ttk.Button(buttons, text="Edit selected", command=self.edit_selected).pack(side="left", padx=4)
        ttk.Button(buttons, text="Delete selected", command=self.delete_selected).pack(side="left", padx=4)
        ttk.Button(buttons, text="Undo", command=self.undo).pack(side="left", padx=4)
        self.events.bind("<Double-1>", lambda _: self.edit_selected())
        self.events.bind("<Delete>", lambda _: self.delete_selected())
        self.refresh()

    def matches(self, event):
        kind = self.filter.get()
        if kind == "All events":
            return True
        if kind == "Notes":
            return event.status & 0xf0 in (0x80, 0x90) and event.status < 0xf0
        if kind == "Control changes":
            return event.status & 0xf0 == 0xb0 and event.status < 0xf0
        if kind == "Program changes":
            return event.status & 0xf0 == 0xc0 and event.status < 0xf0
        if kind == "Pitch bend":
            return event.status & 0xf0 == 0xe0 and event.status < 0xf0
        if kind == "Meta":
            return event.status == 0xff
        return event.status in (0xf0, 0xf7)

    def refresh(self):
        self.events.delete(*self.events.get_children())
        if self.app.song is None or self.track_index >= len(self.app.song.tracks):
            return
        track = self.app.song.tracks[self.track_index]
        for index, event in sorted(enumerate(track.events), key=lambda item: (item[1].tick, item[1].order)):
            if self.matches(event):
                self.events.insert("", "end", iid=str(index), values=(
                    event.tick, event.channel() or "-", event.label(), event.description()))

    def selected_index(self):
        selection = self.events.selection()
        return int(selection[0]) if selection else None

    def edit_selected(self):
        index = self.selected_index()
        if index is None:
            return
        event = self.app.song.tracks[self.track_index].events[index]
        if event.status >= 0xf0:
            messagebox.showinfo("List Editor", "Editing raw SysEx and meta events is not supported yet.", parent=self)
            return
        dialog = tk.Toplevel(self)
        dialog.title("Edit MIDI event")
        dialog.transient(self)
        dialog.grab_set()
        tick = tk.StringVar(value=str(event.tick))
        data = tk.StringVar(value=event.data.hex(" "))
        for label, var in (("Absolute tick", tick), ("MIDI data bytes (hex)", data)):
            row = ttk.Frame(dialog)
            row.pack(fill="x", padx=14, pady=7)
            ttk.Label(row, text=label, width=23).pack(side="left")
            ttk.Entry(row, textvariable=var, width=30).pack(side="left")
        def save():
            try:
                target_tick = int(tick.get())
                raw = bytes.fromhex(data.get())
                if not 0 <= target_tick <= 0x0fffffff:
                    raise MidiError("Tick must be within MIDI limits")
                expected = 1 if event.status & 0xf0 in (0xc0, 0xd0) else 2
                if len(raw) != expected or any(byte > 127 for byte in raw):
                    raise MidiError("Invalid MIDI data bytes")
                self.app.snapshot()
                self.app.song.set_event(self.track_index, index, tick=target_tick, data=raw)
                self.refresh()
                self.app.show_events()
                dialog.destroy()
            except (ValueError, MidiError) as exc:
                messagebox.showerror("Edit event", str(exc), parent=dialog)
        ttk.Button(dialog, text="Apply", command=save).pack(pady=10)

    def delete_selected(self):
        index = self.selected_index()
        if index is None:
            return
        track = self.app.song.tracks[self.track_index]
        event = track.events[index]
        if event.status == 0xff and event.meta_type == 0x2f:
            messagebox.showwarning("List Editor", "End-of-track event cannot be deleted.", parent=self)
            return
        if event.status & 0xf0 in (0x80, 0x90) and event.status < 0xf0:
            messagebox.showwarning("List Editor",
                "Delete complete notes in Piano Roll to preserve note-on/note-off pairing.", parent=self)
            return
        self.app.snapshot()
        del track.events[index]
        self.app.song.dirty = True
        self.refresh()
        self.app.show_events()

    def undo(self):
        if not self.app.history:
            return
        self.app.undo()
        self.refresh()
