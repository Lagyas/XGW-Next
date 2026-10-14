"""Piano Roll view for the XGW Next Tkinter prototype.

Pairs note-on/off events per MIDI channel and pitch. Editing uses the
existing Song.set_event() method and the application's undo snapshots.
"""
from collections import defaultdict, deque
from copy import deepcopy
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from midi import MidiError
from expressive_quantize import transform as expressive_transform
from note_ops import insert_note, delete_note, move_note, quantize_notes, quantize_selected_notes, resize_note, transform_notes, delete_notes
from velocity_ops import set_note_velocities, scale_note_velocities
from cc_names import cc_label
from piano_cc_ops import insert_cc
from piano_pitch_ops import insert_pitch_bend
from controller_ramp import ramp_points, apply_ramp
from controller_delete import delete_controller
from controller_bulk import bulk_controller_edit
from controller_region import controller_indices_in_range
from controller_move import move_controller_events
from controller_transform import transform_controllers
from meter_grid import grid_lines
from snap_grid import SNAP_OPTIONS, snapped_tick, snap_ticks
from editor_cursor import ruler_tick, seek_editor

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

def grid_note_position(x, y, division, snap_option):
    """Convert scrolled canvas coordinates to a snapped note start and pitch."""
    if division <= 0 or division & 0x8000:
        raise MidiError("Beat-grid note drawing requires PPQN time division")
    if x < KEYBOARD_WIDTH or y < TOP_MARGIN:
        return None
    pitch = 127 - int((y - TOP_MARGIN) // NOTE_HEIGHT)
    if not 0 <= pitch <= 127:
        return None
    raw_tick = max(0, round((x - KEYBOARD_WIDTH) * division / PIXELS_PER_BEAT))
    return snapped_tick(raw_tick, division, snap_option), pitch

def controller_channel(track, notes, selection="Auto"):
    """Resolve controller drawing channel; Auto uses first paired note or channel 1."""
    if selection != "Auto":
        try:
            channel = int(selection)
        except (ValueError, TypeError) as exc:
            raise MidiError("MIDI channel must be 1–16") from exc
        if not 1 <= channel <= 16:
            raise MidiError("MIDI channel must be 1–16")
        return channel
    return notes[0][3] if notes else 1

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
        self.selected_pairs = set()
        self.info = tk.StringVar(value="Drag notes to move; Ctrl+left-drag to copy; drag right edge to resize.")
        ttk.Label(self, textvariable=self.info).pack(fill="x", padx=8, pady=5)
        area = ttk.Frame(self)
        area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(area, background="#f8fafc", highlightthickness=0)
        yscroll = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        xscroll = ttk.Scrollbar(area, orient="horizontal", command=self.horizontal_scroll)
        self.canvas.configure(yscrollcommand=yscroll.set, xscrollcommand=self.sync_velocity_scroll)
        self.velocity_canvas = tk.Canvas(area, background="#f0f3f8", height=115, highlightthickness=0)
        self.velocity_canvas.bind("<ButtonPress-1>", self.velocity_press)
        self.velocity_canvas.bind("<B1-Motion>", self.velocity_motion)
        self.velocity_canvas.bind("<ButtonRelease-1>", self.velocity_release)
        self.velocity_drag = None
        self.lane_cc = None
        self.controller_channel_choice = tk.StringVar(value="Auto")
        self.selected_controllers = set()
        self.controller_region_preview = None
        self.controller_transform_preview = None
        self.velocity_canvas.bind("<Button-3>", self.controller_context_menu)
        self.xscroll = xscroll
        self.canvas.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        self.velocity_canvas.grid(row=1, column=0, sticky="ew")
        xscroll.grid(row=2, column=0, sticky="ew")
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self._last_transport_tick = None
        self._playhead_timer = self.after(80, self._poll_playhead)
        self.canvas.bind("<ButtonPress-1>", self.begin_drag)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
        self.canvas.bind("<Double-Button-1>", self.edit_note)
        self.canvas.bind("<Shift-Button-1>", self.seek_ruler)
        self.canvas.bind("<ButtonPress-3>", self.begin_selection_box)
        self.canvas.bind("<B3-Motion>", self.move_selection_box)
        self.canvas.bind("<ButtonRelease-3>", self.finish_selection_box)
        self.bind("<Delete>", lambda event: self.delete_selected())
        self.bind("<Control-z>", self.undo_note_edit)
        self.bind("<Control-y>", self.redo_note_edit)
        self.bind("<Control-Shift-Z>", self.redo_note_edit)
        self.bind("<Control-a>", self.select_all_notes)
        self.bind("<Control-d>", self.duplicate_selected)
        self.bind("<Alt-Up>", lambda event: self.nudge_selected_notes(pitch=1))
        self.bind("<Alt-Down>", lambda event: self.nudge_selected_notes(pitch=-1))
        self.bind("<Alt-Left>", lambda event: self.nudge_selected_notes(steps=-1))
        self.bind("<Alt-Right>", lambda event: self.nudge_selected_notes(steps=1))
        self.bind("<Control-Shift-z>", self.redo_note_edit)
        self.protocol("WM_DELETE_WINDOW", self.close_editor)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=4)
        self.snap_option = tk.StringVar(value="1/16")
        ttk.Label(toolbar, text="Snap:").pack(side="left", padx=(0, 4))
        self.snap_box = ttk.Combobox(toolbar, textvariable=self.snap_option, values=SNAP_OPTIONS,
                                      state="readonly", width=7)
        self.snap_box.pack(side="left", padx=(0, 12))
        self.snap_box.bind("<<ComboboxSelected>>", self.change_snap)
        ttk.Label(toolbar, text="CC channel:").pack(side="left", padx=(0, 3))
        self.controller_channel_box = ttk.Combobox(
            toolbar, textvariable=self.controller_channel_choice,
            values=("Auto",) + tuple(str(i) for i in range(1, 17)),
            state="readonly", width=5)
        self.controller_channel_box.pack(side="left", padx=(0, 8))
        self.controller_channel_box.bind("<<ComboboxSelected>>", self.change_controller_channel)
        ttk.Button(toolbar, text="CC −10", command=lambda: self.bulk_controller_change(-10)).pack(side="left")
        ttk.Button(toolbar, text="CC +10", command=lambda: self.bulk_controller_change(10)).pack(side="left")
        ttk.Button(toolbar, text="Delete CC", command=lambda: self.bulk_controller_change(delete=True)).pack(side="left")
        ttk.Button(toolbar, text="CC value −1", command=lambda: self.nudge_controller_value(-1)).pack(side="left")
        ttk.Button(toolbar, text="CC value +1", command=lambda: self.nudge_controller_value(1)).pack(side="left")
        ttk.Button(toolbar, text="CC ←", command=lambda: self.shift_selected_controllers(-1)).pack(side="left")
        ttk.Button(toolbar, text="CC →", command=lambda: self.shift_selected_controllers(1)).pack(side="left")
        ttk.Button(toolbar, text="Insert note", command=self.insert_note).pack(side="left")
        ttk.Button(toolbar, text="Delete selected", command=self.delete_selected).pack(side="left")
        ttk.Button(toolbar, text="Select all", command=self.select_all_notes).pack(side="left")
        ttk.Button(toolbar, text="Scale velocity...", command=self.scale_selected_velocity).pack(side="left")
        ttk.Button(toolbar, text="Duplicate +1 beat", command=self.duplicate_selected).pack(side="left")
        self.quantize_strength = tk.StringVar(value="100")
        ttk.Label(toolbar, text="Quantize strength %:").pack(side="left", padx=(10, 3))
        ttk.Combobox(toolbar, textvariable=self.quantize_strength,
                     values=("25", "50", "75", "100"), width=5).pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="Quantize to snap", command=self.quantize).pack(side="left")
        ttk.Button(toolbar, text="Quantize length", command=lambda: self.expressive_quantize(length=True)).pack(side="left")
        self.swing_amount = tk.StringVar(value="50")
        self.human_timing = tk.StringVar(value="8")
        self.human_velocity = tk.StringVar(value="8")
        ttk.Label(toolbar, text="Swing %:").pack(side="left")
        ttk.Combobox(toolbar, textvariable=self.swing_amount,
                     values=("0", "25", "50", "67", "75", "100"), width=4).pack(side="left")
        ttk.Button(toolbar, text="Swing", command=self.apply_swing).pack(side="left")
        ttk.Label(toolbar, text="Human ticks:").pack(side="left")
        ttk.Entry(toolbar, textvariable=self.human_timing, width=4).pack(side="left")
        ttk.Label(toolbar, text="Vel:").pack(side="left")
        ttk.Entry(toolbar, textvariable=self.human_velocity, width=4).pack(side="left")
        ttk.Button(toolbar, text="Humanize", command=self.apply_humanize).pack(side="left")
        self.draw_tool = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="Pencil (click empty grid)", variable=self.draw_tool).pack(side="left", padx=(10, 0))
        self.drag_origin = None
        self.selection_origin = None
        self.right_origin = None
        self.context_menu = tk.Menu(self, tearoff=0)
        self.render()
        self.canvas.yview_moveto(0.32)

    def seek_ruler(self, event):
        """Shift-click the timeline to reposition the shared transport cursor."""
        if self.app.song is None:
            return "break"
        try:
            tick = ruler_tick(self.canvas.canvasx(event.x), KEYBOARD_WIDTH,
                              PIXELS_PER_BEAT, self.app.song.division,
                              self.snap_option.get())
            seek_editor(self.app, tick)
        except MidiError as exc:
            self.info.set(str(exc))
        return "break"

    def change_snap(self, _event=None):
        try:
            snap_ticks(self.app.song.division, self.snap_option.get())
        except MidiError as exc:
            self.snap_option.set("Off")
            self.info.set(f"Snap disabled: {exc}")
        self.render()

    def horizontal_scroll(self, *args):
        self.canvas.xview(*args)
        self.velocity_canvas.xview(*args)

    def sync_velocity_scroll(self, first, last):
        self.xscroll.set(first, last)
        if hasattr(self, "velocity_canvas"):
            self.velocity_canvas.xview_moveto(float(first))

    def render_velocity(self, width):
        lane = self.velocity_canvas
        lane.delete("all")
        lane.configure(scrollregion=(0, 0, width, 115))
        lane.create_text(6, 10, anchor="w", text=("Velocity" if self.lane_cc is None else ("Pitch Bend" if self.lane_cc == "pitch" else cc_label(self.lane_cc))) + " ▼", fill="#334155")
        lane.create_line(KEYBOARD_WIDTH, 14, width, 14, fill="#94a3b8")
        lane.create_line(KEYBOARD_WIDTH, 109, width, 109, fill="#94a3b8")
        if self.controller_transform_preview is not None:
            lane.create_text(KEYBOARD_WIDTH + 10, 28, anchor="w", text=self.controller_transform_preview, fill="#b45309")
        if self.controller_region_preview is not None:
            a, b = self.controller_region_preview
            lane.create_rectangle(min(a, b), 16, max(a, b), 113, fill="#bfdbfe", stipple="gray50", outline="#2563eb", tags=("controller_region",))
        division = self.app.song.division
        if division <= 0 or division & 0x8000:
            return
        channel = controller_channel(self.app.song.tracks[self.track_index], self.notes,
                                     self.controller_channel_choice.get())
        if self.lane_cc == "pitch":
            lane.create_line(KEYBOARD_WIDTH, 64, width, 64, fill="#94a3b8", dash=(3, 3))
            for index, event in enumerate(self.app.song.tracks[self.track_index].events):
                if event.status != 0xe0 | (channel - 1) or len(event.data) != 2:
                    continue
                x = KEYBOARD_WIDTH + event.tick / division * PIXELS_PER_BEAT
                value = event.data[0] | (event.data[1] << 7)
                y = 109 - value * 90 / 16383
                lane.create_line(x, 64, x, y, width=3, fill="#ea580c" if index in self.selected_controllers else "#7c3aed", tags=(f"cc_{index}",))
                lane.create_oval(x-4, y-4, x+4, y+4, fill="#7c3aed", outline="", tags=(f"cc_{index}",))
            return
        if self.lane_cc is not None:
            for index, event in enumerate(self.app.song.tracks[self.track_index].events):
                if event.status != 0xb0 | (channel - 1) or len(event.data) != 2 or event.data[0] != self.lane_cc:
                    continue
                x = KEYBOARD_WIDTH + event.tick / division * PIXELS_PER_BEAT
                y = 109 - event.data[1] * 90 / 127
                lane.create_line(x, 109, x, y, width=4, fill="#ea580c" if index in self.selected_controllers else "#0d9488", tags=(f"cc_{index}",))
                lane.create_oval(x-4, y-4, x+4, y+4, fill="#0d9488", outline="", tags=(f"cc_{index}",))
            return
        for start, _, _, _, velocity, on_idx, off_idx in self.notes:
            x = KEYBOARD_WIDTH + start / division * PIXELS_PER_BEAT
            y = 109 - velocity * 90 / 127
            selected = (on_idx, off_idx) in self.selected_pairs
            lane.create_line(x, 109, x, y, width=4,
                             fill="#ea580c" if selected else "#2563eb",
                             tags=(f"velocity_{on_idx}", "velocity"))
            lane.create_oval(x - 4, y - 4, x + 4, y + 4,
                             fill="#ea580c" if selected else "#2563eb",
                             outline="", tags=(f"velocity_{on_idx}", "velocity"))

    def controller_context_menu(self, event):
        """Right-click a CC/Pitch point to remove it, or choose a lane."""
        index = self.cc_target(event) if self.lane_cc is not None else None
        if index is None:
            self.choose_lane(event)
            return
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Delete controller event", command=lambda i=index: self.delete_controller_point(i))
        menu.add_separator()
        menu.add_command(label="Change controller lane...", command=lambda: self.choose_lane(event))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def delete_controller_point(self, index):
        if self.app.player.playing:
            messagebox.showwarning("Controller", "Stop playback before editing.", parent=self)
            return
        try:
            # Validate before snapshot so an invalid target cannot pollute Undo.
            events = self.app.song.tracks[self.track_index].events
            point = events[index]
            lane = self.lane_cc
            valid = ((lane == "pitch" and point.status & 0xf0 == 0xe0) or
                     (type(lane) is int and point.status & 0xf0 == 0xb0 and
                      len(point.data) == 2 and point.data[0] == lane))
            if not valid:
                raise MidiError("Selected event is not in the active controller lane")
            self.app.snapshot()
            delete_controller(self.app.song, self.track_index, index, lane)
            self.selected_controllers.clear()
            self.render()
            self.app.show_events()
            self.info.set("Controller event deleted (Undo: Ctrl+Z)")
        except (MidiError, IndexError) as exc:
            messagebox.showerror("Controller", str(exc), parent=self)

    def choose_lane(self, event=None):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Velocity", command=lambda: self.set_lane(None))
        menu.add_command(label="Pitch Bend (14-bit)", command=lambda: self.set_lane("pitch"))
        menu.add_separator()
        for start in range(0, 128, 16):
            sub = tk.Menu(menu, tearoff=0)
            for cc in range(start, start + 16):
                sub.add_command(label=cc_label(cc), command=lambda n=cc: self.set_lane(n))
            menu.add_cascade(label=f"CC {start}–{start+15}", menu=sub)
        x = event.x_root if event else self.velocity_canvas.winfo_rootx()
        y = event.y_root if event else self.velocity_canvas.winfo_rooty()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def change_controller_channel(self, _event=None):
        self.selected_controllers.clear()
        self.render()

    def bulk_controller_change(self, delta=0, delete=False):
        if self.lane_cc is None or not self.selected_controllers:
            self.info.set("Ctrl+click controller points to select them first")
            return
        if self.app.player.playing:
            messagebox.showwarning("Controller", "Stop playback before editing.", parent=self)
            return
        try:
            channel = controller_channel(self.app.song.tracks[self.track_index], self.notes, self.controller_channel_choice.get())
            preview = deepcopy(self.app.song)
            count = bulk_controller_edit(preview, self.track_index, self.selected_controllers, self.lane_cc, channel, delta, delete)
            if not count:
                return
            self.app.snapshot()
            self.app.song = preview
            if delete:
                self.selected_controllers.clear()
            self.render()
            self.app.show_events()
            self.info.set(f"Edited {count} controller events (Undo: Ctrl+Z)")
        except MidiError as exc:
            messagebox.showerror("Controller", str(exc), parent=self)

    def shift_selected_controllers(self, direction):
        """Move selected controller events one Snap step left/right as one Undo."""
        if self.lane_cc is None or not self.selected_controllers:
            self.info.set("Select controller points first (Ctrl+click or Alt+drag)")
            return
        if self.app.player.playing:
            messagebox.showwarning("Controller", "Stop playback before editing.", parent=self)
            return
        try:
            division = self.app.song.division
            if division <= 0 or division & 0x8000:
                raise MidiError("Controller move requires PPQN time division")
            step = snap_ticks(division, self.snap_option.get()) or 1
            channel = controller_channel(self.app.song.tracks[self.track_index], self.notes, self.controller_channel_choice.get())
            preview = deepcopy(self.app.song)
            count = move_controller_events(preview, self.track_index, self.selected_controllers,
                                           self.lane_cc, channel, direction * step)
            if not count:
                return
            self.app.snapshot()
            self.app.song = preview
            self.render()
            self.app.show_events()
            self.info.set(f"Moved {count} controller events by {direction * step} ticks (Undo: Ctrl+Z)")
        except MidiError as exc:
            messagebox.showerror("Controller move", str(exc), parent=self)

    def apply_controller_transform(self, tick_delta=0, value_delta=0, copy=False):
        """Preview before snapshot, preserve selected event indices after edit."""
        if self.lane_cc is None or not self.selected_controllers:
            return 0
        if self.app.player.playing:
            messagebox.showwarning("Controller", "Stop playback before editing.", parent=self)
            return 0
        try:
            channel = controller_channel(self.app.song.tracks[self.track_index], self.notes,
                                         self.controller_channel_choice.get())
            preview = deepcopy(self.app.song)
            count, new_indices = transform_controllers(preview, self.track_index,
                self.selected_controllers, self.lane_cc, channel, tick_delta, value_delta, copy)
            if count:
                self.app.snapshot()
                self.app.song = preview
                self.selected_controllers = new_indices
                self.render()
                self.app.show_events()
                self.info.set(f"Edited {count} controller events (Undo: Ctrl+Z)")
            return count
        except MidiError as exc:
            messagebox.showerror("Controller transform", str(exc), parent=self)
            return 0

    def nudge_controller_value(self, delta):
        self.apply_controller_transform(value_delta=delta)

    def set_lane(self, cc):
        if cc is not None and cc != "pitch" and (type(cc) is not int or not 0 <= cc <= 127):
            raise MidiError("CC number must be 0–127")
        self.lane_cc = cc
        self.selected_controllers.clear()
        self.velocity_drag = None
        self.render()

    def cc_target(self, event):
        x, y = self.velocity_canvas.canvasx(event.x), self.velocity_canvas.canvasy(event.y)
        for item in reversed(self.velocity_canvas.find_overlapping(x-5, y-5, x+5, y+5)):
            for tag in self.velocity_canvas.gettags(item):
                if tag.startswith("cc_"):
                    return int(tag[3:])
        return None

    def velocity_target(self, event):
        x = self.velocity_canvas.canvasx(event.x)
        y = self.velocity_canvas.canvasy(event.y)
        items = self.velocity_canvas.find_overlapping(x - 5, 14, x + 5, 112)
        indices = []
        for item in reversed(items):
            for tag in self.velocity_canvas.gettags(item):
                if tag.startswith("velocity_"):
                    indices.append(int(tag[9:]))
        if not indices:
            return None
        if len(indices) == 1:
            return indices[0]
        # Overlapping notes: prefer a selected velocity bar.
        selected = {pair[0] for pair in self.selected_pairs}
        return next((index for index in indices if index in selected), indices[0])

    def velocity_value(self, event):
        y = self.velocity_canvas.canvasy(event.y)
        return max(1, min(127, round((109 - y) * 127 / 90)))

    def velocity_press(self, event):
        if event.y <= 16 and event.x <= 110:
            self.choose_lane(event)
            return
        if self.app.player.playing:
            messagebox.showwarning("Velocity", "Stop playback before editing.", parent=self)
            return
        if self.lane_cc is not None:
            if event.state & 0x0008:  # Alt+drag selects a time range of controllers
                self.velocity_drag = ("region", self.velocity_canvas.canvasx(event.x), bool(event.state & 0x0004))
                self.controller_region_preview = (self.velocity_drag[1], self.velocity_drag[1])
                self.render()
                return
            index = self.cc_target(event)
            if index is not None and index in self.selected_controllers and not (event.state & 0x0008):
                self.velocity_drag = ("transform", self.velocity_canvas.canvasx(event.x),
                                      self.velocity_canvas.canvasy(event.y), bool(event.state & 0x0004))
                return
            if event.state & 0x0004:  # Ctrl+click toggles point selection
                if index is not None:
                    if index in self.selected_controllers:
                        self.selected_controllers.remove(index)
                    else:
                        self.selected_controllers.add(index)
                    self.render()
                return
            if event.state & 0x0001:  # Shift-drag paints a snapped controller ramp
                self.velocity_drag = ("ramp", self.velocity_canvas.canvasx(event.x),
                                      self.velocity_canvas.canvasy(event.y))
                self.info.set("Shift-drag: draw controller ramp (release to apply)")
            else:
                self.velocity_drag = ("cc", self.cc_target(event))
            return
        index = self.velocity_target(event)
        if index is None:
            return
        selected = {pair[0] for pair in self.selected_pairs}
        targets = selected if index in selected else {index}
        self.velocity_drag = (targets, self.velocity_value(event))
        self.velocity_motion(event)

    def velocity_motion(self, event):
        if self.velocity_drag is None:
            return
        if self.velocity_drag[0] == "region":
            self.controller_region_preview = (self.velocity_drag[1], self.velocity_canvas.canvasx(event.x))
            self.render_velocity(self.velocity_canvas.bbox("all")[2] if self.velocity_canvas.bbox("all") else 1100)
            self.info.set("Alt+drag: select controller events by time")
        elif self.velocity_drag[0] == "transform":
            _, x, y, copying = self.velocity_drag
            division = self.app.song.division
            if division > 0 and not division & 0x8000:
                step = snap_ticks(division, self.snap_option.get()) or 1
                delta = round((self.velocity_canvas.canvasx(event.x) - x) * division / PIXELS_PER_BEAT / step) * step
                maximum = 16383 if self.lane_cc == "pitch" else 127
                value_delta = round((y - self.velocity_canvas.canvasy(event.y)) * maximum / 90)
                self.controller_transform_preview = f"{'Copy' if copying else 'Move'}: {delta:+} ticks, {value_delta:+} value"
                self.info.set(self.controller_transform_preview)
        elif self.velocity_drag[0] == "ramp":
            self.info.set("Controller ramp: release to apply")
        else:
            self.info.set(f"Value: {self.velocity_value(event)} (release to apply)")

    def velocity_release(self, event):
        if self.velocity_drag is None:
            return
        if self.lane_cc is not None:
            if self.velocity_drag[0] == "transform":
                _, x, y, copying = self.velocity_drag
                self.velocity_drag = None
                self.controller_transform_preview = None
                division = self.app.song.division
                if division <= 0 or division & 0x8000:
                    messagebox.showerror("Controller", "PPQN division required", parent=self)
                    return
                step = snap_ticks(division, self.snap_option.get()) or 1
                delta = round((self.velocity_canvas.canvasx(event.x) - x) * division / PIXELS_PER_BEAT / step) * step
                maximum = 16383 if self.lane_cc == "pitch" else 127
                value_delta = round((y - self.velocity_canvas.canvasy(event.y)) * maximum / 90)
                if delta or value_delta:
                    self.apply_controller_transform(delta, value_delta, copying)
                return
            if self.velocity_drag[0] == "region":
                _, start_x, additive = self.velocity_drag
                end_x = self.velocity_canvas.canvasx(event.x)
                self.velocity_drag = None
                self.controller_region_preview = None
                try:
                    division = self.app.song.division
                    if division <= 0 or division & 0x8000:
                        raise MidiError("Controller selection requires PPQN time division")
                    to_tick = lambda x: max(0, round((x - KEYBOARD_WIDTH) * division / PIXELS_PER_BEAT))
                    channel = controller_channel(self.app.song.tracks[self.track_index], self.notes, self.controller_channel_choice.get())
                    found = controller_indices_in_range(self.app.song, self.track_index, self.lane_cc, channel, to_tick(start_x), to_tick(end_x))
                    if not additive:
                        self.selected_controllers.clear()
                    self.selected_controllers.update(found)
                    self.render()
                    self.info.set(f"Selected {len(self.selected_controllers)} controller events")
                except MidiError as exc:
                    messagebox.showerror("Controller selection", str(exc), parent=self)
                return
            if self.velocity_drag[0] == "ramp":
                _, start_x, start_y = self.velocity_drag
                self.velocity_drag = None
                try:
                    division = self.app.song.division
                    if division <= 0 or division & 0x8000:
                        raise MidiError("Controller ramp requires PPQN time division")
                    step = snap_ticks(division, self.snap_option.get())
                    if not step:
                        step = max(1, division // 16)
                    end_x = self.velocity_canvas.canvasx(event.x)
                    end_y = self.velocity_canvas.canvasy(event.y)
                    tick_at = lambda x: snapped_tick(max(0, round((x - KEYBOARD_WIDTH) * division / PIXELS_PER_BEAT)), division, self.snap_option.get())
                    maximum = 16383 if self.lane_cc == "pitch" else 127
                    value_at = lambda y: max(0, min(maximum, round((109 - y) * maximum / 90)))
                    points = ramp_points(tick_at(start_x), tick_at(end_x), value_at(start_y), value_at(end_y), step, maximum)
                    channel = controller_channel(self.app.song.tracks[self.track_index], self.notes, self.controller_channel_choice.get())
                    preview = deepcopy(self.app.song)
                    apply_ramp(preview, self.track_index, self.lane_cc, channel, points)
                    if preview.tracks[self.track_index].events == self.app.song.tracks[self.track_index].events:
                        return
                    self.app.snapshot()
                    self.app.song = preview
                    self.render()
                    self.app.show_events()
                    self.info.set(f"Controller ramp: {len(points)} points (Undo: Ctrl+Z)")
                except MidiError as exc:
                    messagebox.showerror("Controller ramp", str(exc), parent=self)
                return
            _, index = self.velocity_drag
            self.velocity_drag = None
            pitch_lane = self.lane_cc == "pitch"
            max_value = 16383 if pitch_lane else 127
            value = max(0, min(max_value, round((109 - self.velocity_canvas.canvasy(event.y)) * max_value / 90)))
            try:
                if index is None:
                    division = self.app.song.division
                    if division <= 0 or division & 0x8000:
                        raise MidiError("CC lane requires PPQN time division")
                    x = self.velocity_canvas.canvasx(event.x)
                    raw_tick = max(0, round((x - KEYBOARD_WIDTH) * division / PIXELS_PER_BEAT))
                    tick = snapped_tick(raw_tick, division, self.snap_option.get())
                    channel = controller_channel(self.app.song.tracks[self.track_index], self.notes, self.controller_channel_choice.get())
                    preview = deepcopy(self.app.song)
                    if pitch_lane:
                        insert_pitch_bend(preview, self.track_index, tick, value, channel)
                    else:
                        insert_cc(preview, self.track_index, tick, self.lane_cc, value, channel)
                    if preview.tracks[self.track_index].events == self.app.song.tracks[self.track_index].events:
                        return
                    self.app.snapshot()
                    self.app.song = preview
                else:
                    current = self.app.song.tracks[self.track_index].events[index]
                    new_data = bytes((value & 127, value >> 7)) if pitch_lane else bytes((self.lane_cc, value))
                    if current.data == new_data:
                        return
                    preview = deepcopy(self.app.song)
                    preview.set_event(self.track_index, index, data=new_data)
                    self.app.snapshot()
                    self.app.song = preview
                self.render()
                self.app.show_events()
            except MidiError as exc:
                messagebox.showerror("Controller", str(exc), parent=self)
            return
        indices, _ = self.velocity_drag
        self.velocity_drag = None
        value = self.velocity_value(event)
        changes = {index: value for index in indices
                   if self.app.song.tracks[self.track_index].events[index].data[1] != value}
        if not changes:
            return
        try:
            self.app.snapshot()
            set_note_velocities(self.app.song, self.track_index, changes)
            self.render()
            self.app.show_events()
            self.info.set(f"Velocity {value} applied to {len(changes)} note(s).")
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            self.render()
            messagebox.showerror("Velocity", str(exc), parent=self)

    def begin_selection_box(self, event):
        """Right-click opens a menu; right-drag on empty space selects a region.
        Ctrl+right-drag on notes copies and moves the notes in one gesture.
        """
        index = self.hit_note()
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.right_origin = (index, x, y, event.x_root, event.y_root, bool(event.state & 0x0004))
        self.selection_origin = None
        self.canvas.delete("selection-box")
        if index is not None:
            pair = (self.notes[index][5], self.notes[index][6])
            if pair not in self.selected_pairs:
                self.selected_pairs = {pair}
                self.render()

    def move_selection_box(self, event):
        if self.right_origin is None:
            return
        index, x0, y0, _, _, copying = self.right_origin
        x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        if abs(x1 - x0) + abs(y1 - y0) < 5:
            return
        if index is not None and copying:
            self.preview_note_copy(x1 - x0, y1 - y0)
        elif index is None:
            self.selection_origin = (x0, y0)
            self.canvas.delete("selection-box")
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="#ea580c",
                                         dash=(4, 3), tags="selection-box")

    def preview_note_copy(self, dx, dy):
        self.canvas.delete("copy-preview")
        division = self.app.song.division
        if division <= 0 or division & 0x8000 or self.right_origin is None:
            return
        anchor_index = self.right_origin[0]
        if anchor_index is None:
            return
        try:
            anchor_start = self.notes[anchor_index][0]
            target = max(0, round(anchor_start + dx * division / PIXELS_PER_BEAT))
            delta_ticks = snapped_tick(target, division, self.snap_option.get()) - anchor_start
        except MidiError:
            return
        delta_pitch = -round(dy / NOTE_HEIGHT)
        for start, end, pitch, _, _, on_idx, off_idx in self.notes:
            if (on_idx, off_idx) not in self.selected_pairs:
                continue
            x1 = KEYBOARD_WIDTH + (start + delta_ticks) / division * PIXELS_PER_BEAT
            x2 = KEYBOARD_WIDTH + (end + delta_ticks) / division * PIXELS_PER_BEAT
            y = TOP_MARGIN + (127 - pitch - delta_pitch) * NOTE_HEIGHT
            self.canvas.create_rectangle(x1, y + 1, max(x1 + 3, x2),
                                         y + NOTE_HEIGHT - 1, outline="#16a34a",
                                         width=2, dash=(3, 2), tags="copy-preview")

    def finish_selection_box(self, event):
        if self.right_origin is None:
            return
        index, x0, y0, root_x, root_y, copying = self.right_origin
        self.right_origin = None
        x1, y1 = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.delete("selection-box")
        self.canvas.delete("copy-preview")
        dx, dy = x1 - x0, y1 - y0
        if abs(dx) + abs(dy) < 5:
            self.show_context_menu(event)
            return
        if index is not None and copying:
            division = self.app.song.division
            if division <= 0 or division & 0x8000:
                return
            pairs = self.selected_note_pairs()
            delta_pitch = -round(dy / NOTE_HEIGHT)
            try:
                delta_ticks = (snapped_tick(max(0, round(self.notes[index][0] + dx * division / PIXELS_PER_BEAT)),
                                            division, self.snap_option.get()) - self.notes[index][0])
                self.app.snapshot()
                transform_notes(self.app.song, self.track_index, pairs,
                                delta_ticks=delta_ticks, delta_pitch=delta_pitch,
                                duplicate=True)
                self.selected_pairs.clear()
                self.render()
                self.app.show_events()
                self.info.set(f"Copied and moved {len(pairs)} notes.")
            except MidiError as exc:
                self.app.song = self.app.history.pop()
                messagebox.showerror("Copy notes", str(exc), parent=self)
            return
        if index is not None:
            return
        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        if not (event.state & 0x0001):
            self.selected_pairs.clear()
        division = self.app.song.division
        if division <= 0 or division & 0x8000:
            return
        for start, end, pitch, _, _, on_idx, off_idx in self.notes:
            note_left = KEYBOARD_WIDTH + start / division * PIXELS_PER_BEAT
            note_right = KEYBOARD_WIDTH + end / division * PIXELS_PER_BEAT
            note_top = TOP_MARGIN + (127 - pitch) * NOTE_HEIGHT
            if note_right >= left and note_left <= right and note_top <= bottom and note_top + NOTE_HEIGHT >= top:
                self.selected_pairs.add((on_idx, off_idx))
        self.render()
        self.publish_note_selection()
        self.info.set(f"{len(self.selected_pairs)} notes selected.")

    def show_context_menu(self, event):
        menu = self.context_menu
        menu.delete(0, "end")
        has_notes = bool(self.selected_pairs)
        menu.add_command(label="Edit note...", command=self.edit_selected_note,
                         state="normal" if len(self.selected_pairs) == 1 else "disabled")
        menu.add_command(label="Duplicate +1 beat   Ctrl+D", command=self.duplicate_selected,
                         state="normal" if has_notes else "disabled")
        menu.add_command(label="Delete selected   Del", command=self.delete_selected,
                         state="normal" if has_notes else "disabled")
        menu.add_separator()
        menu.add_command(label="Select all   Ctrl+A", command=self.select_all_notes)
        menu.add_command(label="Insert note...", command=self.insert_note)
        menu.add_command(label="Quantize to snap", command=self.quantize)
        menu.add_separator()
        menu.add_command(label="Undo   Ctrl+Z", command=self.undo_note_edit,
                         state="normal" if self.app.history else "disabled")
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def edit_selected_note(self):
        if len(self.selected_pairs) != 1:
            return
        pair = next(iter(self.selected_pairs))
        for index, note in enumerate(self.notes):
            if (note[5], note[6]) == pair:
                self.selected = index
                self.edit_note(selected_index=index)
                return

    def undo_note_edit(self, _event=None):
        if not self.app.history:
            return
        self.app.undo()
        self.selected = None
        self.selected_pairs.clear()
        self.render()
        self.info.set("Last MIDI edit undone.")
        return "break"

    def redo_note_edit(self, _event=None):
        """Redo a MIDI edit from the Piano Roll without losing the active lane."""
        if not self.app.redo_history:
            return
        self.app.redo()
        self.selected = None
        self.selected_pairs.clear()
        self.render()
        self.info.set("Last MIDI edit redone.")
        return "break"

    def scale_selected_velocity(self):
        """Apply percentage velocity scaling to selected Piano Roll notes."""
        pairs = self.selected_note_pairs()
        if not pairs:
            self.info.set("Select notes before scaling velocity.")
            return
        percent = simpledialog.askinteger("Scale note velocity", "Percent (0–400):",
                                          initialvalue=100, minvalue=0, maxvalue=400, parent=self)
        if percent is None:
            return
        try:
            from copy import deepcopy
            indices = [on for on, _ in pairs]
            preview = deepcopy(self.app.song)
            changed = scale_note_velocities(preview, self.track_index, indices, percent)
            if not changed:
                return
            self.app.snapshot()
            scale_note_velocities(self.app.song, self.track_index, indices, percent)
            self.render()
            self.app.show_events()
            self.info.set(f"Scaled {changed} note velocities to {percent}%.")
        except MidiError as exc:
            messagebox.showerror("Scale note velocity", str(exc), parent=self)

    def selected_note_pairs(self):
        return [(on_idx, off_idx) for _, _, _, _, _, on_idx, off_idx in self.notes
                if (on_idx, off_idx) in self.selected_pairs]

    def publish_note_selection(self):
        shared = getattr(self.app, "shared_note_selection", None)
        if shared is None:
            return
        shared.set(self.track_index, self.selected_pairs, self.app.song.tracks[self.track_index].events)
        other = self.app.workspace.windows.get("Drum Editor")
        if other is not None and other.winfo_exists() and other.track_index == self.track_index:
            other.receive_note_selection()

    def receive_note_selection(self):
        shared = getattr(self.app, "shared_note_selection", None)
        if shared is None:
            return
        self.selected_pairs = shared.get(self.track_index, self.notes, self.app.song.tracks[self.track_index].events)
        self.render()

    def select_all_notes(self, _event=None):
        self.selected_pairs = {(n[5], n[6]) for n in self.notes}
        self.render()
        self.publish_note_selection()
        self.info.set(f"{len(self.selected_pairs)} notes selected.")
        return "break"

    def nudge_selected_notes(self, *, pitch=0, steps=0):
        """Nudge selected notes atomically; preserve selection across redraws."""
        pairs = self.selected_note_pairs()
        if not pairs or (not pitch and not steps):
            return "break"
        try:
            ticks = snap_ticks(self.app.song.division, self.snap_option.get()) * steps if steps else 0
            if not ticks and not pitch:
                return "break"
            probe = deepcopy(self.app.song)
            changed = transform_notes(probe, self.track_index, pairs,
                                      delta_ticks=ticks, delta_pitch=pitch)
            if not changed:
                return "break"
            self.app.snapshot()
            transform_notes(self.app.song, self.track_index, pairs,
                            delta_ticks=ticks, delta_pitch=pitch)
            self.render()
            self.publish_note_selection()
            self.app.show_events()
            self.app.notify_midi_editors(origin=self)
            self.info.set(f"Moved {changed} notes (ticks {ticks:+}, pitch {pitch:+}).")
        except MidiError as exc:
            messagebox.showerror("Move notes", str(exc), parent=self)
        return "break"

    def duplicate_selected(self, _event=None):
        """Duplicate the selected notes as one validated, undoable edit."""
        pairs = self.selected_note_pairs()
        if not pairs:
            return "break"
        try:
            # Check the entire operation before touching history or live MIDI.
            trial = deepcopy(self.app.song)
            changed = transform_notes(trial, self.track_index, pairs,
                                      delta_ticks=self.app.song.division, duplicate=True)
            if not changed:
                return "break"
            self.app.snapshot()
            transform_notes(self.app.song, self.track_index, pairs,
                            delta_ticks=self.app.song.division, duplicate=True)
            self.selected_pairs.clear()
            self.render()
            self.publish_note_selection()
            self.app.show_events()
            self.app.notify_midi_editors(origin=self)
            self.info.set(f"Copied {changed} notes one beat forward.")
        except MidiError as exc:
            messagebox.showerror("Duplicate notes", str(exc), parent=self)
        return "break"

    def render(self):
        canvas = self.canvas
        canvas.delete("all")
        song = self.app.song
        track = song.tracks[self.track_index]
        self.notes = extract_notes(track)
        from shared_note_selection import reconcile_editor_pairs
        self.selected_pairs = reconcile_editor_pairs(
            self.selected_pairs, self.notes, track.events,
            getattr(self.app, "shared_note_selection", None), self.track_index)
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
        # Draw the meter grid across the entire scrollable width, even on empty tracks.
        end_tick = int((width - KEYBOARD_WIDTH) * division / PIXELS_PER_BEAT)
        try:
            snap_step = snap_ticks(division, self.snap_option.get())
        except MidiError:
            snap_step = None
        if snap_step is not None and end_tick // snap_step <= 12000:
            for tick in range(0, end_tick + 1, snap_step):
                x = KEYBOARD_WIDTH + tick / division * PIXELS_PER_BEAT
                canvas.create_line(x, TOP_MARGIN, x, height, fill="#edf0f5")
        for tick, is_bar, bar in grid_lines(song, end_tick):
            x = KEYBOARD_WIDTH + tick / division * PIXELS_PER_BEAT
            canvas.create_line(x, TOP_MARGIN, x, height,
                               fill="#a4adbb" if is_bar else "#d9dee8",
                               width=1 if is_bar else 0.5)
            if is_bar:
                canvas.create_text(x + 3, 12, text=str(bar),
                                   anchor="w", fill="#334155")
        for index, (start, end, pitch, channel, velocity, _, _) in enumerate(self.notes):
            x1 = KEYBOARD_WIDTH + start / division * PIXELS_PER_BEAT
            x2 = KEYBOARD_WIDTH + max(end, start + 1) / division * PIXELS_PER_BEAT
            y = TOP_MARGIN + (127 - pitch) * NOTE_HEIGHT
            color = "#ea580c" if (self.notes[index][5], self.notes[index][6]) in self.selected_pairs else "#2563eb"
            canvas.create_rectangle(x1, y + 1, max(x1 + 3, x2), y + NOTE_HEIGHT - 1,
                                    fill=color, outline="#1e40af",
                                    tags=(f"note_{index}", "note"))
        self.canvas.tag_raise("note")
        self.render_velocity(width)
        self.update_playhead()

    def close_editor(self):
        """Cancel the transport poll before destroying the editor window."""
        timer = getattr(self, "_playhead_timer", None)
        self._playhead_timer = None
        if timer is not None:
            try:
                self.after_cancel(timer)
            except tk.TclError:
                pass
        self.destroy()

    def _poll_playhead(self):
        self._playhead_timer = None
        try:
            if self.winfo_exists():
                self.update_playhead()
                self._playhead_timer = self.after(80, self._poll_playhead)
        except tk.TclError:
            # A workspace close may destroy the window during the timer callback.
            return

    def update_playhead(self):
        """Draw the shared song cursor; keep a newly sought position visible."""
        if not self.winfo_exists():
            return
        division = self.app.song.division if self.app.song else 0
        self.canvas.delete("playhead")
        if division > 0 and not division & 0x8000:
            x = KEYBOARD_WIDTH + self.app.playhead_tick / division * PIXELS_PER_BEAT
            self.canvas.create_line(x, 0, x, TOP_MARGIN + 128 * NOTE_HEIGHT,
                                    fill="#dc2626", width=2, tags="playhead")
            tick_changed = self._last_transport_tick != self.app.playhead_tick
            self._last_transport_tick = self.app.playhead_tick
            if tick_changed:
                left = self.canvas.canvasx(0)
                right = self.canvas.canvasx(self.canvas.winfo_width())
                if x > right - 60 or x < left + KEYBOARD_WIDTH:
                    bounds = self.canvas.cget("scrollregion").split()
                    if len(bounds) == 4 and float(bounds[2]) > self.canvas.winfo_width():
                        fraction = max(0, min(1, (x - self.canvas.winfo_width() * 0.4) /
                                               (float(bounds[2]) - self.canvas.winfo_width())))
                        self.canvas.xview_moveto(fraction)

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
        pairs = self.selected_note_pairs()
        if not pairs:
            return
        try:
            self.app.snapshot()
            delete_notes(self.app.song, self.track_index, pairs)
            self.selected_pairs.clear()
            self.selected = None
            self.render()
            self.app.show_events()
            self.info.set(f"Deleted {len(pairs)} notes.")
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            messagebox.showerror("Delete notes", str(exc), parent=self)

    def quantize(self):
        option = self.snap_option.get()
        if option == "Off":
            self.info.set("Choose a Snap value before quantizing.")
            return
        snapshot_taken = False
        try:
            strength = int(self.quantize_strength.get())
            if not 0 <= strength <= 100:
                raise MidiError("Quantize strength must be 0–100%")
            pairs = self.selected_note_pairs()
            self.app.snapshot()
            snapshot_taken = True
            if pairs:
                count = quantize_selected_notes(self.app.song, self.track_index, pairs,
                                                int(option.split("/")[1]), strength=strength)
            else:
                count = quantize_notes(self.app.song, self.track_index,
                                       int(option.split("/")[1]), strength=strength)
            if count == 0:
                self.app.history.pop()
            self.selected = None
            self.render()
            self.app.show_events()
            scope = "selection" if pairs else "entire track"
            self.info.set(f"Quantized {count} notes to {option} at {strength}% ({scope}).")
        except (MidiError, ValueError) as exc:
            if snapshot_taken and self.app.history:
                self.app.song = self.app.history.pop()
            messagebox.showerror("Quantize", str(exc), parent=self)

    def apply_swing(self):
        try:
            amount = int(self.swing_amount.get())
        except ValueError:
            messagebox.showerror("Swing", "Swing must be an integer from -100 to 100.", parent=self)
            return
        self.expressive_quantize(swing=amount)

    def apply_humanize(self):
        try:
            timing = int(self.human_timing.get())
            velocity = int(self.human_velocity.get())
        except ValueError:
            messagebox.showerror("Humanize", "Timing and velocity must be integers.", parent=self)
            return
        self.expressive_quantize(timing_jitter=timing, velocity_jitter=velocity)

    def expressive_quantize(self, **options):
        """Apply one undoable expressive transform to selection or whole track."""
        option = self.snap_option.get()
        if option == "Off":
            self.info.set("Choose a Snap value before transforming notes.")
            return
        taken = False
        try:
            strength = int(self.quantize_strength.get())
            pairs = self.selected_note_pairs()
            self.app.snapshot()
            taken = True
            count = expressive_transform(self.app.song, self.track_index,
                                         pairs=pairs if pairs else None,
                                         denominator=int(option.split("/")[1]),
                                         strength=strength, **options)
            if count == 0:
                self.app.history.pop()
            self.selected = None
            self.render()
            self.app.show_events()
            self.info.set(f"Transformed {count} notes.")
        except (MidiError, ValueError) as exc:
            if taken and self.app.history:
                self.app.song = self.app.history.pop()
            messagebox.showerror("MIDI transform", str(exc), parent=self)

    def draw_note_at(self, event):
        position = grid_note_position(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y),
                                      self.app.song.division, self.snap_option.get())
        if position is None:
            return
        tick, pitch = position
        try:
            duration = snap_ticks(self.app.song.division, self.snap_option.get())
            if not duration:
                duration = max(1, self.app.song.division // 4)
            self.app.snapshot()
            insert_note(self.app.song, self.track_index, tick, duration, pitch)
            self.selected = None
            self.selected_pairs.clear()
            self.render()
            self.app.show_events()
            self.info.set(f"Drawn {pitch_label(pitch)} at tick {tick} ({duration} ticks).")
        except MidiError as exc:
            messagebox.showerror("Draw note", str(exc), parent=self)

    def begin_drag(self, event):
        index = self.hit_note()
        if index is None and self.draw_tool.get():
            self.drag_origin = None
            self.draw_note_at(event)
            return
        if index is None:
            self.drag_origin = None
            return
        self.selected = index
        pair = (self.notes[index][5], self.notes[index][6])
        if event.state & 0x0001:
            if pair in self.selected_pairs:
                self.selected_pairs.remove(pair)
            else:
                self.selected_pairs.add(pair)
            self.drag_origin = None
            self.focus_set()
            self.render()
            self.publish_note_selection()
            return
        if pair not in self.selected_pairs:
            self.selected_pairs = {pair}
        self.focus_set()
        start, end, _, _, _, _, _ = self.notes[index]
        end_x = KEYBOARD_WIDTH + end / self.app.song.division * PIXELS_PER_BEAT if self.app.song.division > 0 else 0
        resizing = abs(self.canvas.canvasx(event.x) - end_x) <= 7
        self.drag_origin = (index, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), resizing and not bool(event.state & 0x0004), bool(event.state & 0x0004))
        self.render()
        self.publish_note_selection()

    def drag_motion(self, event):
        if self.drag_origin is None or self.app.song.division <= 0 or self.app.song.division & 0x8000:
            return
        index, old_x, old_y, resizing, copying = self.drag_origin
        if index >= len(self.notes):
            return
        start, end, pitch, _, _, _, _ = self.notes[index]
        dx = self.canvas.canvasx(event.x) - old_x
        dy = self.canvas.canvasy(event.y) - old_y
        tick = (start if abs(dx) < 2 else
                snapped_tick(max(0, round(start + dx * self.app.song.division / PIXELS_PER_BEAT)),
                             self.app.song.division, self.snap_option.get()))
        target_pitch = max(0, min(127, pitch - round(dy / NOTE_HEIGHT)))
        if resizing:
            tick = start
            target_pitch = pitch
            new_end = (end if abs(dx) < 2 else
                       max(start + 1, snapped_tick(max(0, round(end + dx * self.app.song.division / PIXELS_PER_BEAT)),
                                                   self.app.song.division, self.snap_option.get())))
            x2 = KEYBOARD_WIDTH + new_end / self.app.song.division * PIXELS_PER_BEAT
        else:
            x2 = KEYBOARD_WIDTH + (tick + end - start) / self.app.song.division * PIXELS_PER_BEAT
        x1 = KEYBOARD_WIDTH + tick / self.app.song.division * PIXELS_PER_BEAT
        y = TOP_MARGIN + (127 - target_pitch) * NOTE_HEIGHT
        self.canvas.delete("note-preview")
        self.canvas.create_rectangle(x1, y + 1, x2, y + NOTE_HEIGHT - 1,
                                     outline="#16a34a" if copying else "#ea580c", width=2, dash=(3, 2),
                                     tags="note-preview")

    def end_drag(self, event):
        if self.drag_origin is None:
            return
        index, old_x, old_y, resizing, copying = self.drag_origin
        self.drag_origin = None
        self.canvas.delete("note-preview")
        if index >= len(self.notes) or self.app.song.division <= 0 or self.app.song.division & 0x8000:
            return
        start, end, pitch, _, _, on_idx, off_idx = self.notes[index]
        dx = self.canvas.canvasx(event.x) - old_x
        dy = self.canvas.canvasy(event.y) - old_y
        tick = (start if abs(dx) < 2 else
                snapped_tick(max(0, round(start + dx * self.app.song.division / PIXELS_PER_BEAT)),
                             self.app.song.division, self.snap_option.get()))
        target_pitch = max(0, min(127, pitch - round(dy / NOTE_HEIGHT)))
        if resizing:
            new_end = (end if abs(dx) < 2 else
                       max(start + 1, snapped_tick(max(0, round(end + dx * self.app.song.division / PIXELS_PER_BEAT)),
                                                   self.app.song.division, self.snap_option.get())))
            if new_end == end:
                return
        elif tick == start and target_pitch == pitch:
            return
        try:
            self.app.snapshot()
            if resizing:
                resize_note(self.app.song, self.track_index, on_idx, off_idx, new_end)
            else:
                pairs = self.selected_note_pairs()
                transform_notes(self.app.song, self.track_index, pairs,
                                delta_ticks=tick - start, delta_pitch=target_pitch - pitch,
                                duplicate=copying)
            self.selected = None
            self.selected_pairs.clear()
            self.render()
            self.app.show_events()
            if resizing:
                self.info.set(f"Resized {pitch_label(pitch)} to {new_end - start} ticks.")
            else:
                self.info.set(f"{'Copied' if copying else 'Moved'} note to {pitch_label(target_pitch)}, tick {tick}.")
        except MidiError as exc:
            self.app.song = self.app.history.pop()
            messagebox.showerror("Move note", str(exc), parent=self)

    def edit_note(self, _event=None, selected_index=None):
        self.selected = self.hit_note() if selected_index is None else selected_index
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
        new_velocity = simpledialog.askinteger("Velocity", "Note velocity (1–127):",
                                               initialvalue=velocity, minvalue=1, maxvalue=127, parent=self)
        if new_velocity is None:
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
                                    tick=new_start, data=bytes((new_pitch, new_velocity)))
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
