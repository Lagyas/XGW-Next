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
        self.geometry("860x650")
        self.channel = tk.IntVar(value=1)
        self.controller = tk.IntVar(value=7)
        self.tick = tk.IntVar(value=0)
        self.value = tk.IntVar(value=100)
        self.event_index = None
        self.graph_drag = None
        self.graph_channel = tk.IntVar(value=1)
        self.graph_cc = tk.IntVar(value=7)
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
        graph_header = ttk.Frame(self)
        graph_header.pack(fill="x", padx=10)
        ttk.Label(graph_header, text="Controller graph:").pack(side="left")
        ttk.Label(graph_header, text="Channel").pack(side="left", padx=(12, 2))
        ttk.Spinbox(graph_header, from_=1, to=16, width=4,
                    textvariable=self.graph_channel, command=self.draw_graph).pack(side="left")
        ttk.Label(graph_header, text="CC").pack(side="left", padx=(12, 2))
        ttk.Spinbox(graph_header, from_=0, to=127, width=4,
                    textvariable=self.graph_cc, command=self.draw_graph).pack(side="left")
        ttk.Button(graph_header, text="Refresh graph", command=self.draw_graph).pack(side="left", padx=8)
        ttk.Label(graph_header, text="Click: add point  |  Drag: move point").pack(side="right")
        self.graph = tk.Canvas(self, height=175, background="#f8fafc", highlightthickness=1,
                               highlightbackground="#cbd5e1")
        self.graph.pack(fill="x", padx=10, pady=6)
        self.graph.bind("<ButtonPress-1>", self.graph_press)
        self.graph.bind("<B1-Motion>", self.graph_motion)
        self.graph.bind("<ButtonRelease-1>", self.graph_release)
        self.graph_channel.trace_add("write", lambda *_: self.draw_graph())
        self.graph_cc.trace_add("write", lambda *_: self.draw_graph())
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
        self.draw_graph()

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
        self.draw_graph()

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

    def graph_filter(self):
        try:
            channel, cc = self.graph_channel.get(), self.graph_cc.get()
            if not 1 <= channel <= 16 or not 0 <= cc <= 127:
                return None
            return channel, cc
        except (ValueError, tk.TclError):
            return None

    def graph_scale(self):
        width = max(400, self.graph.winfo_width())
        height = max(100, self.graph.winfo_height())
        events = self.app.song.tracks[self.track_index].events
        last_tick = max((event.tick for event in events), default=0)
        # Keep a minimum four-bar timeline, and allow editing past last event.
        max_tick = max(self.app.song.division * 16, last_tick + self.app.song.division * 4, 1)
        return width, height, max_tick

    def graph_to_values(self, x, y):
        width, height, max_tick = self.graph_scale()
        tick = round(max(0, min(1, (x - 28) / max(1, width - 42))) * max_tick)
        value = round(max(0, min(1, (height - 18 - y) / max(1, height - 34))) * 127)
        return tick, value

    def graph_from_values(self, tick, value):
        width, height, max_tick = self.graph_scale()
        x = 28 + tick / max_tick * (width - 42)
        y = height - 18 - value / 127 * (height - 34)
        return x, y

    def draw_graph(self):
        if not hasattr(self, "graph"):
            return
        graph = self.graph
        graph.delete("all")
        selected = self.graph_filter()
        if selected is None or self.app.song is None:
            return
        channel, cc = selected
        width, height, _ = self.graph_scale()
        for value in (0, 32, 64, 96, 127):
            y = self.graph_from_values(0, value)[1]
            graph.create_line(28, y, width - 12, y, fill="#e2e8f0")
            graph.create_text(24, y, text=str(value), anchor="e", fill="#64748b")
        events = controller_events(self.app.song, self.track_index, channel, cc)
        points = [(idx, *self.graph_from_values(e.tick, e.data[1])) for idx, e in events]
        for (idx1, x1, y1), (_, x2, y2) in zip(points, points[1:]):
            graph.create_line(x1, y1, x2, y2, fill="#2563eb", width=2)
        for idx, x, y in points:
            graph.create_oval(x - 5, y - 5, x + 5, y + 5,
                              fill="#ea580c" if idx == self.event_index else "#2563eb",
                              outline="#ffffff", tags=(f"cc_{idx}", "point"))
        graph.create_text(width - 12, height - 3, text=f"CC {cc} / Ch {channel}",
                          anchor="se", fill="#475569")

    def graph_press(self, event):
        if self.graph_filter() is None:
            return
        hits = self.graph.find_overlapping(event.x - 7, event.y - 7,
                                           event.x + 7, event.y + 7)
        selected_index = None
        for item in reversed(hits):
            for tag in self.graph.gettags(item):
                if tag.startswith("cc_"):
                    selected_index = int(tag[3:])
                    break
            if selected_index is not None:
                break
        self.graph_drag = (selected_index, event.x, event.y)
        if selected_index is not None:
            self.event_index = selected_index
            if self.list.exists(str(selected_index)):
                self.list.selection_set(str(selected_index))
                self.list.see(str(selected_index))
            self.draw_graph()

    def graph_motion(self, event):
        if self.graph_drag is None:
            return
        index, x, y = self.graph_drag
        self.draw_graph()
        tick, value = self.graph_to_values(event.x, event.y)
        px, py = self.graph_from_values(tick, value)
        self.graph.create_oval(px - 6, py - 6, px + 6, py + 6,
                               outline="#16a34a", width=2, tags="preview")

    def graph_release(self, event):
        if self.graph_drag is None:
            return
        index, x, y = self.graph_drag
        self.graph_drag = None
        if index is not None and abs(event.x - x) + abs(event.y - y) < 4:
            self.draw_graph()
            return
        selected = self.graph_filter()
        if selected is None:
            return
        channel, cc = selected
        tick, value = self.graph_to_values(event.x, event.y)
        try:
            self.app.snapshot()
            try:
                set_controller(self.app.song, self.track_index, channel, cc, tick,
                               value, event_index=index)
            except Exception:
                self.app.history.pop()
                raise
            self.refresh()
            self.app.show_events()
            self.app.status.set(f"CC {cc} on channel {channel} edited — Save As to save.")
        except MidiError as exc:
            messagebox.showerror("Controller graph", str(exc), parent=self)
            self.draw_graph()
