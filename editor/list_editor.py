"""XGworks-style MIDI event list for a selected track."""
import tkinter as tk
from tkinter import ttk, messagebox
from midi import MidiError
from note_ops import edit_note_event, delete_note_event
from event_fields import event_fields, encode_fields

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
                                          "Program changes", "Pitch bend", "Aftertouch", "Meta", "SysEx"),
                                  width=21)
        filter_box.pack(side="left", padx=8)
        filter_box.bind("<<ComboboxSelected>>", lambda _: self.refresh())
        ttk.Button(header, text="Refresh", command=self.refresh).pack(side="left")
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        columns = ("tick", "channel", "type", "data")
        self.events = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        for col, width in (("tick", 110), ("channel", 80), ("type", 160), ("data", 530)):
            self.events.heading(col, text=col.title())
            self.events.column(col, width=width, stretch=col == "data")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.events.yview)
        self.events.configure(yscrollcommand=scroll.set)
        self.events.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=10, pady=8)
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
        if kind == "Aftertouch":
            return event.status < 0xf0 and event.status & 0xf0 in (0xa0, 0xd0)
        if kind == "Meta":
            return event.status == 0xff
        return event.status in (0xf0, 0xf7)

    def refresh(self):
        previous = self.selected_index()
        self.events.delete(*self.events.get_children())
        if self.app.song is None or self.track_index >= len(self.app.song.tracks):
            return
        track = self.app.song.tracks[self.track_index]
        for index, event in sorted(enumerate(track.events), key=lambda item: (item[1].tick, item[1].order)):
            if self.matches(event):
                self.events.insert("", "end", iid=str(index), values=(
                    event.tick, event.channel() or "-", event.label(), event.description()))
        if previous is not None and self.events.exists(str(previous)):
            self.events.selection_set(str(previous))
            self.events.see(str(previous))

    def selected_index(self):
        selection = self.events.selection()
        return int(selection[0]) if selection else None

    def edit_selected(self):
        index = self.selected_index()
        if index is None:
            return
        if self.app.player.playing:
            messagebox.showwarning("List Editor", "Stop playback before editing.", parent=self)
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
        fields = event_fields(event)
        variables = [tk.StringVar(value=str(value)) for _, value, _, _ in fields]
        rows = [("Absolute tick", tick)] + [
            (f"{name} [{low}–{high}]", var)
            for (name, _, low, high), var in zip(fields, variables)]
        for label, var in rows:
            row = ttk.Frame(dialog)
            row.pack(fill="x", padx=14, pady=7)
            ttk.Label(row, text=label, width=36).pack(side="left")
            ttk.Entry(row, textvariable=var, width=20).pack(side="left")
        def save():
            try:
                target_tick = int(tick.get())
                raw = encode_fields(event, [int(var.get()) for var in variables])
                if not 0 <= target_tick <= 0x0fffffff:
                    raise MidiError("Tick must be within MIDI limits")
                expected = 1 if event.status & 0xf0 in (0xc0, 0xd0) else 2
                if len(raw) != expected or any(byte > 127 for byte in raw):
                    raise MidiError("Invalid MIDI data bytes")
                is_note = 0x80 <= event.status <= 0x9f
                if is_note:
                    # Validate against a snapshot-free copy before recording undo.
                    from copy import deepcopy
                    probe = deepcopy(self.app.song)
                    changed = edit_note_event(probe, self.track_index, index, target_tick, raw)
                else:
                    changed = target_tick != event.tick or raw != event.data
                if changed:
                    self.app.snapshot()
                    if is_note:
                        edit_note_event(self.app.song, self.track_index, index, target_tick, raw)
                    else:
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
        if self.app.player.playing:
            messagebox.showwarning("List Editor", "Stop playback before editing.", parent=self)
            return
        track = self.app.song.tracks[self.track_index]
        event = track.events[index]
        is_note = 0x80 <= event.status <= 0x9f
        if is_note and not messagebox.askyesno(
                "Delete note", "Delete the complete note (Note On and Note Off)?",
                parent=self):
            return
        try:
            # Check validity before adding an undo snapshot.
            from copy import deepcopy
            probe = deepcopy(self.app.song)
            delete_note_event(probe, self.track_index, index)
            self.app.snapshot()
            delete_note_event(self.app.song, self.track_index, index)
            self.refresh()
            self.app.show_events()
        except MidiError as exc:
            messagebox.showerror("List Editor", str(exc), parent=self)

    def undo(self):
        if not self.app.history:
            return
        self.app.undo()
        self.refresh()
