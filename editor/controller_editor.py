"""MIDI controller event editor for the selected sequencer track."""
import tkinter as tk
from tkinter import ttk, messagebox
from midi import MidiError
from controller_ops import CONTROLLERS, controller_events, set_controller, delete_controller

class ControllerEditor(tk.Toplevel):
    def __init__(self, app, track_index):
        super().__init__(app.root)
        self.app, self.track_index = app, track_index
        self.title(f"MIDI Controller Editor — Track {track_index + 1}")
        self.geometry("760x490")
        self.channel = tk.IntVar(value=1)
        self.controller = tk.IntVar(value=7)
        self.tick = tk.IntVar(value=0)
        self.value = tk.IntVar(value=100)
        self.event_index = None
        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=10, pady=10)
        for col, (label, var, low, high) in enumerate((
            ("Channel", self.channel, 1, 16), ("CC number", self.controller, 0, 127),
            ("Tick", self.tick, 0, 268435455), ("Value", self.value, 0, 127)
        )):
            ttk.Label(controls, text=label).grid(row=0, column=col, padx=8)
            ttk.Spinbox(controls, from_=low, to=high, textvariable=var,
                        width=12).grid(row=1, column=col, padx=8)
        self.description = tk.StringVar()
        ttk.Label(self, textvariable=self.description).pack(anchor="w", padx=15)
        self.controller.trace_add("write", lambda *_: self.update_description())
        self.update_description()
        columns = ("tick", "channel", "cc", "name", "value")
        self.list = ttk.Treeview(self, columns=columns, show="headings")
        for col, width in zip(columns, (95, 75, 75, 210, 80)):
            self.list.heading(col, text=col.title())
            self.list.column(col, width=width)
        self.list.pack(fill="both", expand=True, padx=10, pady=8)
        self.list.bind("<<TreeviewSelect>>", self.on_select)
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=10, pady=10)
        ttk.Button(buttons, text="Insert new CC", command=self.insert).pack(side="left", padx=4)
        ttk.Button(buttons, text="Update selected", command=self.update).pack(side="left", padx=4)
        ttk.Button(buttons, text="Delete selected", command=self.delete).pack(side="left", padx=4)
        ttk.Button(buttons, text="Refresh", command=self.refresh).pack(side="left", padx=4)
        self.refresh()

    def update_description(self):
        try:
            number = self.controller.get()
            self.description.set(f"CC {number}: {CONTROLLERS.get(number, 'General MIDI controller')}")
        except tk.TclError:
            self.description.set("Enter a controller number 0–127")

    def refresh(self):
        self.list.delete(*self.list.get_children())
        for index, event in controller_events(self.app.song, self.track_index):
            cc, value = event.data
            self.list.insert("", "end", iid=str(index),
                             values=(event.tick, (event.status & 15) + 1,
                                     cc, CONTROLLERS.get(cc, ""), value))
        self.event_index = None

    def on_select(self, _event=None):
        selection = self.list.selection()
        if not selection:
            return
        self.event_index = int(selection[0])
        event = self.app.song.tracks[self.track_index].events[self.event_index]
        self.tick.set(event.tick)
        self.channel.set((event.status & 15) + 1)
        self.controller.set(event.data[0])
        self.value.set(event.data[1])

    def apply(self, updating=False):
        if updating and self.event_index is None:
            messagebox.showinfo("Controller", "Select a CC event first.", parent=self)
            return
        try:
            args = (self.channel.get(), self.controller.get(),
                    self.tick.get(), self.value.get())
            self.app.snapshot()
            try:
                set_controller(self.app.song, self.track_index, *args,
                               event_index=self.event_index if updating else None)
            except Exception:
                self.app.history.pop()
                raise
            self.refresh()
            self.app.show_events()
            self.app.status.set("MIDI controller changed — Save As to save.")
        except (MidiError, ValueError, tk.TclError) as exc:
            messagebox.showerror("Controller", str(exc), parent=self)

    def insert(self):
        self.apply(False)

    def update(self):
        self.apply(True)

    def delete(self):
        if self.event_index is None:
            return
        try:
            self.app.snapshot()
            delete_controller(self.app.song, self.track_index, self.event_index)
            self.refresh()
            self.app.show_events()
        except MidiError as exc:
            self.app.history.pop()
            messagebox.showerror("Controller", str(exc), parent=self)
