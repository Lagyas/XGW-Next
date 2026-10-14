"""Arrangement overview for a MIDI song, grouped by track and time."""
import tkinter as tk
import time
from track_voice import used_channels, channel_voice_at
from xg_voices import voice_label
from tkinter import ttk
from arrangement import track_clips
from note_ops import paired_notes
from meter_grid import grid_lines
from transport_ops import MAX_TICK
from snap_grid import SNAP_OPTIONS, snapped_tick, snap_ticks

ROW_HEIGHT = 42
LEFT_WIDTH = 230
BEAT_WIDTH = 28
HEADER_HEIGHT = 38
MIN_BEAT_WIDTH = 8
MAX_BEAT_WIDTH = 224

def zoom_row_height(current, steps, minimum=24, maximum=168):
    """Bounded vertical zoom; does not modify MIDI events."""
    import math
    if not math.isfinite(current) or current <= 0 or not math.isfinite(steps):
        raise ValueError('Invalid track zoom')
    return max(minimum, min(maximum, round(current * (1.25 ** max(-100, min(100, steps))))))

def locator_hit_test(x, y, division, left_tick, right_tick, tolerance=9, beat_width=BEAT_WIDTH):
    """Return L/R for a ruler locator handle; never select below the ruler."""
    if y < 0 or y >= HEADER_HEIGHT or division <= 0 or division & 0x8000:
        return None
    positions = (("L", LEFT_WIDTH + left_tick / division * beat_width),
                 ("R", LEFT_WIDTH + right_tick / division * beat_width))
    hits = [(abs(x - position), label) for label, position in positions
            if abs(x - position) <= tolerance]
    return min(hits)[1] if hits else None

def follow_scroll_fraction(cursor_x, view_left, view_width, content_width, fixed_width=LEFT_WIDTH, margin=45):
    """Return a safe horizontal scroll fraction when the cursor leaves the usable view.

    Keep the track-name column clear and avoid jitter for stationary playheads.
    """
    if view_width <= 0 or content_width <= view_width:
        return None
    usable_left = view_left + min(fixed_width, view_width / 2)
    usable_right = view_left + view_width - margin
    if usable_right <= usable_left:
        usable_right = view_left + view_width
    if usable_left <= cursor_x <= usable_right:
        return None
    target_left = cursor_x - view_width * 0.45
    return max(0.0, min(1.0, target_left / (content_width - view_width)))


def smooth_follow_fraction(cursor_x, view_left, view_width, content_width,
                           fixed_width=LEFT_WIDTH, anchor=0.40):
    """Keep the moving cursor at a stable position in the visible timeline."""
    if view_width <= fixed_width or content_width <= view_width:
        return None
    target = cursor_x - (fixed_width + (view_width - fixed_width) * anchor)
    target = max(0.0, min(content_width - view_width, target))
    if abs(target - view_left) < 0.5:
        return None
    return target / (content_width - view_width)


def keyboard_seek_tick(current, division, key, end_tick=0, shift=False):
    """Compute Track View keyboard navigation without a Tk dependency.

    Arrows step by one beat, or one sixteenth with Shift. Home/End
    jump to the start/song end. All results stay in the MIDI tick range.
    """
    if not isinstance(division, int) or division <= 0 or division & 0x8000:
        return None
    current = max(0, min(MAX_TICK, int(current)))
    step = max(1, division // 4) if shift else division
    if key == 'Left':
        return max(0, current - step)
    if key == 'Right':
        return min(MAX_TICK, current + step)
    if key == 'Home':
        return 0
    if key == 'End':
        return max(0, min(MAX_TICK, int(end_tick)))
    return None


def zoom_beat_width(current, steps, minimum=MIN_BEAT_WIDTH, maximum=MAX_BEAT_WIDTH):
    """Scale a quarter-note width by discrete, bounded zoom steps."""
    import math
    if not math.isfinite(current) or current <= 0 or not math.isfinite(steps):
        raise ValueError('Invalid timeline zoom')
    if minimum <= 0 or maximum < minimum:
        raise ValueError('Invalid zoom limits')
    return max(minimum, min(maximum, round(current * (1.25 ** max(-100, min(100, steps))))))


def zoom_scroll_fraction(anchor_tick, division, beat_width, anchor_screen_x,
                         viewport_width, content_width):
    """Keep the musical tick under the pointer stationary during zoom."""
    if division <= 0 or viewport_width <= 0 or content_width <= viewport_width:
        return 0.0
    anchor_canvas_x = LEFT_WIDTH + anchor_tick / division * beat_width
    left = anchor_canvas_x - anchor_screen_x
    return max(0.0, min(1.0, left / content_width))


def timeline_snap_tick(tick, division, option):
    """Snap a timeline position without ever leaving the valid MIDI range."""
    return snapped_tick(max(0, min(MAX_TICK, int(tick))), division, option)


def clip_drag_delta(delta_ticks, division, option):
    """Quantize a *relative* clip move, preserving clip offsets and note timing."""
    step = snap_ticks(division, option)
    if step is None:
        return round(delta_ticks)
    return round(delta_ticks / step) * step


def visible_subdivision_ticks(division, option, beat_width, min_pixels=9):
    """Return grid spacing only when its lines are legible at the current zoom."""
    if option == "Off":
        return None
    step = snap_ticks(division, option)
    if step * beat_width / division < min_pixels:
        return None
    return step


def update_clip_selection(current, clicked, ctrl=False, shift=False):
    """Return a stable clip selection for normal/Ctrl/Shift clicking.

    Shift selects the inclusive clip range within the clicked track.
    Ctrl toggles one clip, and a normal click replaces the selection.
    """
    current = set(current)
    if ctrl:
        if clicked in current:
            current.remove(clicked)
        else:
            current.add(clicked)
        return current
    if shift:
        same = [clip for track, clip in current if track == clicked[0]]
        if same:
            anchor = min(same, key=lambda index: abs(index - clicked[1]))
            current.update((clicked[0], i) for i in range(min(anchor, clicked[1]), max(anchor, clicked[1]) + 1))
            return current
    return {clicked}


def zoom_anchor_tick(canvas_x, division, beat_width, left_width=LEFT_WIDTH):
    """Tick at the pointer before zoom; used to preserve the timeline anchor."""
    if division <= 0 or division & 0x8000 or beat_width <= 0:
        return 0.0
    return max(0.0, (canvas_x - left_width) * division / beat_width)


def clip_edge_hit(tick, start, end, division, beat_width, tolerance_px=7):
    """Detect the right edge of a MIDI part without confusing its body with a handle."""
    if division <= 0 or beat_width <= 0 or not start <= tick <= end:
        return False
    return (end - tick) * beat_width / division <= tolerance_px


def track_spans(song):
    """Return one note span per track, preserving empty tracks."""
    result = []
    for track in song.tracks:
        note_ticks = [e.tick for e in track.events
                      if 0x80 <= e.status <= 0x9f and len(e.data) == 2]
        result.append((min(note_ticks), max(note_ticks)) if note_ticks else None)
    return result

def clip_note_preview(track, start, end, division, beat_width, max_notes=2500):
    """Return clip-relative (x1, x2, normalized_pitch) note geometry.

    Pure display helper: uses matched MIDI note-on/off events without
    modifying the source track. Notes spanning a clip edge are clipped.
    """
    if division <= 0 or division & 0x8000 or end <= start or beat_width <= 0:
        return []
    notes = []
    for on_index, off_index in paired_notes(track):
        on, off = track.events[on_index], track.events[off_index]
        if on.tick >= end or off.tick <= start:
            continue
        a, b = max(start, on.tick), min(end, max(on.tick + 1, off.tick))
        if b > a:
            notes.append((a, b, on.data[0]))
    if not notes:
        return []
    low = min(pitch for _, _, pitch in notes)
    high = max(pitch for _, _, pitch in notes)
    span = max(1, high - low)
    # Cap rendering work for large MIDI files; deterministic sampling.
    stride = max(1, (len(notes) + max_notes - 1) // max_notes)
    return [((a - start) * beat_width / division,
             (b - start) * beat_width / division,
             (pitch - low) / span)
            for a, b, pitch in notes[::stride]]


def vertical_zoom_fraction(top_canvas_y, old_row_height, new_row_height,
                           content_height, viewport_height):
    """Preserve the first visible track and intra-track offset on Y zoom.

    Tk Canvas.yview_moveto expects a fraction of the entire scroll region.
    The fixed ruler is excluded from the scaled track area.
    """
    if old_row_height <= 0 or new_row_height <= 0 or content_height <= 0:
        return 0.0
    visible_row = max(0.0, (top_canvas_y - HEADER_HEIGHT) / old_row_height)
    target_top = HEADER_HEIGHT + visible_row * new_row_height
    max_top = max(0.0, content_height - max(0.0, viewport_height))
    return min(target_top, max_top) / content_height


class SequencerView(ttk.Frame):
    def __init__(self, parent, on_track=None, on_open=None, on_toggle=None, on_instrument=None, on_clip=None, on_drag=None, on_seek=None, on_locator=None, on_resize=None, on_midi_port=None):
        super().__init__(parent)
        self.song = None
        self.on_track = on_track
        self.on_open = on_open
        self.on_toggle = on_toggle
        self.on_instrument = on_instrument
        self.on_clip = on_clip
        self.on_drag = on_drag
        self.on_seek = on_seek
        self.on_locator = on_locator
        self.on_resize = on_resize
        self.on_midi_port = on_midi_port
        self.midi_out_labels = {}
        self.midi_in_labels = {}
        self.ruler_dragging = False
        self.locator_dragging = None
        self.locator_left = 0
        self.locator_right = 1920
        self.drag_origin = None
        self.resize_origin = False
        self.drag_preview = None
        self.suppress_release = False
        self.muted = set()
        self.solo = set()
        self.selected_track = 0
        self.selected_clips = set()
        self.show_note_preview = True
        self.playhead_tick = 0
        self._manual_follow_until = 0.0
        self.beat_width = BEAT_WIDTH
        self.row_height = ROW_HEIGHT
        self.snap_option = tk.StringVar(value="1/4")
        self.snap_enabled = tk.BooleanVar(value=True)
        self.snap_bar = ttk.Frame(self)
        self.snap_bar.grid(row=2, column=0, sticky="w", padx=6, pady=3)
        ttk.Checkbutton(self.snap_bar, text="Snap", variable=self.snap_enabled).pack(side="left")
        ttk.Label(self.snap_bar, text="Grid:").pack(side="left", padx=(8, 3))
        grid_box = ttk.Combobox(self.snap_bar, textvariable=self.snap_option, values=SNAP_OPTIONS, state="readonly", width=6)
        grid_box.pack(side="left")
        grid_box.bind("<<ComboboxSelected>>", lambda _event: self.draw())
        self.canvas = tk.Canvas(self, background="#f9fafb", highlightthickness=0)
        # Stage 137: match the compact Cubase corner in the reference image.
        # Y +/- belongs to the narrow vertical scrollbar column, directly
        # above the horizontal scrollbar; X +/- stays on the bottom strip.
        self.bottom_strip = ttk.Frame(self)
        xs = ttk.Scrollbar(self.bottom_strip, orient="horizontal", command=self._manual_xview)
        self.zoom_reset_button = ttk.Button(self.bottom_strip, text="100%", width=5,
                                            command=self.reset_zoom)
        self.zoom_reset_button.pack(side="right", padx=(2, 0))
        x_micro = ttk.Frame(self.bottom_strip)
        for glyph, step in (("−", -1), ("+", 1)):
            tk.Button(x_micro, text=glyph, width=1, height=1, font=("Segoe UI", 8),
                      padx=0, pady=0, bd=1, highlightthickness=0,
                      command=lambda value=step: self.zoom(value)).pack(side="left")
        x_micro.pack(side="right", padx=(2, 1))
        xs.pack(side="left", fill="x", expand=True)
        self.vertical_strip = ttk.Frame(self)
        y_micro = ttk.Frame(self.vertical_strip, width=16)
        y_micro.pack(side="bottom", fill="x")
        y_micro.pack_propagate(False)
        # Pack each button to the narrow scrollbar width, without Tk's
        # standard button padding that made previous iterations oversized.
        for glyph, step in (("+", 1), ("−", -1)):
            tk.Button(y_micro, text=glyph, font=("Segoe UI", 7),
                      padx=0, pady=0, bd=1, highlightthickness=0,
                      command=lambda value=step: self.zoom_vertical(value)).pack(side="top", fill="x")
        y_micro.configure(height=38)
        ys = ttk.Scrollbar(self.vertical_strip, orient="vertical", command=self.canvas.yview)
        ys.pack(side="top", fill="both", expand=True)
        self.canvas.configure(xscrollcommand=lambda first, last: (xs.set(first, last), self._draw_fixed_ruler()), yscrollcommand=ys.set)
        # A separate overlay keeps the track inspector fixed during horizontal follow/scroll.
        self.track_header = tk.Canvas(self.canvas, width=LEFT_WIDTH, highlightthickness=0,
                                      background="#e2e8f0")
        self.track_header.place(x=0, y=0, relheight=1)
        # Child canvas is already stacked above its parent; Canvas.lift() raises items, not windows.
        self.track_header.bind("<Button-1>", self._track_header_click)
        self.track_header.bind("<Double-Button-1>", self._track_header_double_click)
        self.track_header.bind("<MouseWheel>", self._track_header_wheel)
        self.canvas.configure(yscrollcommand=lambda first, last: (ys.set(first, last), self._draw_track_header()))
        self.fixed_ruler = tk.Canvas(self.canvas, height=HEADER_HEIGHT, highlightthickness=0, background="#f9fafb")
        self.fixed_ruler.place(x=LEFT_WIDTH, y=0, relwidth=1, width=-LEFT_WIDTH)
        self.fixed_corner = tk.Canvas(self.canvas, width=LEFT_WIDTH, height=HEADER_HEIGHT, highlightthickness=0, background="#e2e8f0")
        self.fixed_corner.place(x=0, y=0)
        self.fixed_corner.create_text(12, 18, text="TRACK / MIDI PARTS", anchor="w", font=("Arial", 10, "bold"))
        self.fixed_ruler.bind("<Configure>", lambda event: self._draw_fixed_ruler())
        self.fixed_ruler.bind("<Button-1>", self._ruler_click)
        self.fixed_ruler.bind("<B1-Motion>", self._ruler_drag)
        self.fixed_ruler.bind("<ButtonRelease-1>", self._ruler_release)
        self.fixed_ruler.bind("<MouseWheel>", self.mouse_wheel)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.bottom_strip.grid(row=1, column=0, sticky="ew")
        self.vertical_strip.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas.bind("<Button-1>", self.click)
        xs.bind("<ButtonPress-1>", self._suspend_follow, add="+")
        self.canvas.bind("<Double-Button-1>", self.double_click)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.drag_release)
        self.canvas.bind("<MouseWheel>", self.mouse_wheel)
        self.canvas.bind("<Control-plus>", lambda e: self.zoom(1))
        self.canvas.bind("<Control-minus>", lambda e: self.zoom(-1))
        self.canvas.bind("<Control-0>", lambda e: self.reset_zoom())
        self.canvas.bind("<Control-MouseWheel>", self.mouse_wheel)
        for key in ('Left', 'Right', 'Home', 'End'):
            self.canvas.bind(f'<KeyPress-{key}>', self.keyboard_seek)
        self.canvas.bind("<KeyPress-m>", lambda event: self.toggle_selected("mute"))
        self.canvas.bind("<KeyPress-s>", lambda event: self.toggle_selected("solo"))
        self.canvas.bind("<KeyPress-Escape>", lambda event: self.clear_solo())
        self.draw()

    def _suspend_follow(self, _event=None):
        self._manual_follow_until = time.monotonic() + 2.5

    def _manual_xview(self, *args):
        self._suspend_follow()
        self.canvas.xview(*args)

    def keyboard_seek(self, event):
        """Navigate the playhead from the focused Track View canvas."""
        if self.song is None or self.on_seek is None:
            return 'break'
        end_tick = max((e.tick for t in self.song.tracks for e in t.events), default=0)
        target = keyboard_seek_tick(self.playhead_tick, self.song.division,
                                    event.keysym, end_tick, bool(event.state & 0x0001))
        if target is not None:
            self.on_seek(target)
        return 'break'

    def toggle_selected(self, kind):
        """Keyboard M/S applies to the currently selected arrangement track."""
        if self.song is not None and 0 <= self.selected_track < len(self.song.tracks):
            if self.on_toggle:
                self.on_toggle(self.selected_track, kind)
        return "break"

    def clear_solo(self):
        """Clear solo tracks via the existing callback, preserving app ownership."""
        if self.song is not None and self.on_toggle:
            for index in sorted(self.solo):
                self.on_toggle(index, "solo")
        return "break"

    def zoom(self, steps, anchor_x=None):
        """Zoom timeline around pointer or viewport center without changing MIDI ticks."""
        if self.song is None or self.song.division <= 0 or self.song.division & 0x8000:
            return 'break'
        canvas = self.canvas
        if anchor_x is None:
            anchor_x = canvas.winfo_width() / 2
        old_width = self.beat_width
        new_width = zoom_beat_width(old_width, steps)
        if new_width == old_width:
            return 'break'
        anchor_tick = zoom_anchor_tick(canvas.canvasx(anchor_x), self.song.division, old_width)
        self._suspend_follow()
        self.beat_width = new_width
        self.draw()
        bounds = canvas.cget('scrollregion').split()
        if len(bounds) == 4:
            canvas.xview_moveto(zoom_scroll_fraction(anchor_tick, self.song.division,
                                new_width, anchor_x, canvas.winfo_width(), float(bounds[2])))
        return 'break'

    def _set_vertical_zoom(self, new_height):
        """Repaint track rows without losing the user's vertical position."""
        old_height = self.row_height
        if new_height == old_height:
            return 'break'
        top_y = self.canvas.canvasy(0)
        self._suspend_follow()
        self.row_height = new_height
        self.draw()
        bounds = self.canvas.cget('scrollregion').split()
        if len(bounds) == 4:
            fraction = vertical_zoom_fraction(top_y, old_height, new_height,
                                              float(bounds[3]) - float(bounds[1]),
                                              self.canvas.winfo_height())
            self.canvas.yview_moveto(fraction)
        self._draw_track_header()
        return 'break'

    def zoom_vertical(self, steps):
        """Scale track heights, preserving the first visible track."""
        return self._set_vertical_zoom(zoom_row_height(self.row_height, steps))

    def reset_zoom(self):
        self._suspend_follow()
        if self.beat_width != BEAT_WIDTH:
            self.zoom_width(BEAT_WIDTH)
        if self.row_height != ROW_HEIGHT:
            self._set_vertical_zoom(ROW_HEIGHT)
        return 'break'

    def zoom_width(self, width):
        if self.song is None:
            self.beat_width = width
            return
        anchor = self.canvas.winfo_width() / 2
        tick = max(0, (self.canvas.canvasx(anchor) - LEFT_WIDTH) * self.song.division / self.beat_width)
        self._suspend_follow()
        self.beat_width = width
        self.draw()
        bounds = self.canvas.cget('scrollregion').split()
        if len(bounds) == 4:
            self.canvas.xview_moveto(zoom_scroll_fraction(tick, self.song.division,
                                    width, anchor, self.canvas.winfo_width(), float(bounds[2])))

    def mouse_wheel(self, event):
        if event.state & 0x0004:
            return self.zoom(1 if event.delta > 0 else -1, event.x)
        if event.state & 0x0001:
            self._suspend_follow()
            self.canvas.xview_scroll(-int(event.delta / 120), "units")
        else:
            self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def set_mix(self, muted, solo):
        self.muted = set(muted)
        self.solo = set(solo)
        self.draw()

    def set_song(self, song):
        self.song = song
        self.selected_track = 0
        self.selected_clips.clear()
        self.draw()

    def select_track(self, index):
        self.selected_track = index
        self.draw()

    def _track_header_wheel(self, event):
        self.mouse_wheel(event)
        self._draw_track_header()

    def _track_header_click(self, event):
        if self.song is None:
            return
        y = self.canvas.canvasy(event.y)
        row = int((y - HEADER_HEIGHT) // self.row_height)
        if not 0 <= row < len(self.song.tracks):
            return
        if 155 <= event.x < 185 and self.on_toggle:
            self.on_toggle(row, "mute")
        elif 185 <= event.x < 215 and self.on_toggle:
            self.on_toggle(row, "solo")
        elif 0 <= event.x < 75 and self.on_midi_port and (y - HEADER_HEIGHT) % self.row_height >= 18:
            self.on_midi_port(row, "out")
        elif 75 <= event.x < 150 and self.on_midi_port and (y - HEADER_HEIGHT) % self.row_height >= 18:
            self.on_midi_port(row, "in")
        else:
            self.selected_track = row
            self.draw()
            if self.on_track:
                self.on_track(row)

    def _track_header_double_click(self, event):
        if self.song is None:
            return
        row = int((self.canvas.canvasy(event.y) - HEADER_HEIGHT) // self.row_height)
        if 0 <= row < len(self.song.tracks) and event.x < 155 and self.on_open:
            self.on_open(row)

    def _draw_fixed_ruler(self):
        """Ruler is a viewport overlay: horizontal scrolling only, never vertical."""
        if not hasattr(self, 'fixed_ruler'):
            return
        c = self.fixed_ruler
        c.delete('all')
        if self.song is None or self.song.division <= 0 or self.song.division & 0x8000:
            return
        offset = self.canvas.canvasx(0)
        width = max(1, c.winfo_width())
        division = self.song.division
        max_tick = max((e.tick for t in self.song.tracks for e in t.events), default=division * 16)
        beats = max(32, int(max_tick / division) + 8)
        for tick, is_bar, bar in grid_lines(self.song, beats * division):
            if not is_bar:
                continue
            x = LEFT_WIDTH + tick / division * self.beat_width - offset - LEFT_WIDTH
            if -20 <= x <= width + 20:
                c.create_text(x + 3, 18, anchor='w', text=str(bar))
        for tick, label, color in ((self.locator_left, 'L', '#16a34a'),
                                   (self.locator_right, 'R', '#f59e0b')):
            x = tick / division * self.beat_width - offset
            if -15 <= x <= width + 15:
                c.create_line(x, 0, x, HEADER_HEIGHT, fill=color, width=3)
                c.create_polygon(x-8, 1, x+8, 1, x, 14, fill=color, outline='#1f2937')
                c.create_text(x + 3, HEADER_HEIGHT-14, text=label, anchor='w', fill=color)
        x = self.playhead_tick / division * self.beat_width - offset
        if -15 <= x <= width + 15:
            c.create_line(x, 0, x, HEADER_HEIGHT, fill='#dc2626', width=3)
            c.create_polygon(x-9, 0, x+9, 0, x, 15, fill='#dc2626', outline='#7f1d1d')

    def _ruler_event(self, event):
        from types import SimpleNamespace
        return SimpleNamespace(x=event.x + LEFT_WIDTH, y=event.y, state=event.state)

    def _ruler_click(self, event):
        self.click(self._ruler_event(event))

    def _ruler_drag(self, event):
        self.drag_motion(self._ruler_event(event))

    def _ruler_release(self, event):
        self.drag_release(self._ruler_event(event))

    def _draw_track_header(self):
        c = self.track_header
        c.delete("all")
        if self.song is None:
            return
        offset = self.canvas.canvasy(0)
        c.create_rectangle(0, -offset, LEFT_WIDTH, HEADER_HEIGHT-offset,
                           fill="#e2e8f0", outline="#cbd5e1")
        c.create_text(12, 18-offset, text="TRACK / MIDI PARTS", anchor="w",
                      font=("Arial", 10, "bold"))
        for index, track in enumerate(self.song.tracks):
            y = HEADER_HEIGHT + index * self.row_height - offset
            if y + self.row_height < 0 or y > c.winfo_height():
                continue
            c.create_rectangle(0, y, LEFT_WIDTH, y+self.row_height,
                               fill="#dbeafe" if index == self.selected_track else "#f1f5f9",
                               outline="#cbd5e1")
            c.create_text(10, y+15, anchor="w", text=f"{index+1:02d}  {track.name()[:26]}")
            channels = sorted({(e.status & 15)+1 for e in track.events
                               if 0x80 <= e.status <= 0xef})
            if channels:
                channel = channels[0]
                voice = channel_voice_at(self.song, index, channel)
                subtitle = f"CH {channel} · {voice_label(voice.msb, voice.lsb, voice.program)}"
            else:
                subtitle = "CH — · no instrument"
            c.create_text(10, y+31, anchor="w", text="",
                          fill="#475569", font=("Arial", 9))
            for x, kind, labels in ((0, "OUT", self.midi_out_labels),
                                    (75, "IN", self.midi_in_labels)):
                c.create_rectangle(x, y+19, x+73, y+39, fill="#ffffff", outline="#94a3b8")
                c.create_text(x+3, y+25, text=kind, anchor="w", fill="#475569", font=("Arial", 7, "bold"))
                label = labels.get(index, "Default" if kind == "OUT" else "Off")
                c.create_text(x+27, y+33, text=str(label)[:11], anchor="w", font=("Arial", 8))
            for x, name, active in ((155,"M",index in self.muted),
                                    (185,"S",index in self.solo)):
                c.create_rectangle(x, y+9, x+26, y+32,
                                   fill=("#f59e0b" if name == "M" else "#22c55e") if active else "#e2e8f0",
                                   outline="#94a3b8")
                c.create_text(x+13, y+20, text=name, font=("Arial",10,"bold"))
        c.create_line(LEFT_WIDTH-2, 0, LEFT_WIDTH-2, max(1,c.winfo_height()),
                      fill="#64748b", width=2)

    def _row_at(self, event):
        y = self.canvas.canvasy(event.y)
        row = int((y - HEADER_HEIGHT) // self.row_height)
        if self.song is None or not 0 <= row < len(self.song.tracks):
            return None
        return row

    def ruler_tick(self, event):
        if self.song is None or self.song.division <= 0 or self.song.division & 0x8000:
            return None
        x = self.canvas.canvasx(event.x)
        return max(0, min(MAX_TICK, round((x - LEFT_WIDTH) * self.song.division / getattr(self, "beat_width", BEAT_WIDTH))))

    def snap_tick(self, tick):
        if self.song is None or not self.snap_enabled.get():
            return tick
        return timeline_snap_tick(tick, self.song.division, self.snap_option.get())

    def click(self, event):
        self.canvas.focus_set()
        if self.canvas.canvasy(event.y) < HEADER_HEIGHT and self.canvas.canvasx(event.x) >= LEFT_WIDTH:
            tick = self.ruler_tick(event)
            if tick is not None:
                handle = locator_hit_test(self.canvas.canvasx(event.x),
                                          self.canvas.canvasy(event.y), self.song.division,
                                          self.locator_left, self.locator_right, beat_width=self.beat_width)
                if handle and not (event.state & 0x0005):
                    self.locator_dragging = handle
                    return
                if event.state & 0x0001 and self.on_locator:
                    self.on_locator('L', self.snap_tick(tick))
                elif event.state & 0x0004 and self.on_locator:
                    self.on_locator('R', self.snap_tick(tick))
                else:
                    self.ruler_dragging = True
                    if self.on_seek:
                        self.on_seek(self.snap_tick(tick))
            return

        row = self._row_at(event)
        if row is not None:
            x = self.canvas.canvasx(event.x)
            if 0 <= x < 150:
                self.selected_track = row
                self.draw()
                if self.on_track:
                    self.on_track(row)
                return
            if 155 <= x < 185 and self.on_toggle:
                self.on_toggle(row, "mute")
                return
            if 185 <= x < 215 and self.on_toggle:
                self.on_toggle(row, "solo")
                return
            if x >= LEFT_WIDTH and self.song is not None:
                tick = int((x - LEFT_WIDTH) / self.beat_width * self.song.division)
                for clip_index, (start, end) in enumerate(track_clips(self.song.tracks[row], self.song.division)):
                    if start <= tick <= end:
                        self.selected_track = row
                        clicked = (row, clip_index)
                        self.selected_clips = update_clip_selection(
                            self.selected_clips, clicked,
                            ctrl=bool(event.state & 0x0004),
                            shift=bool(event.state & 0x0001))
                        self.draw()
                        if clicked not in self.selected_clips:
                            return
                        self.drag_origin = (row, clip_index, event.x, event.y, x, self.canvas.canvasy(event.y))
                        self.resize_origin = bool(clip_edge_hit(tick, start, end, self.song.division, self.beat_width))
                        return
            self.selected_track = row
            self.draw()
            if self.on_track:
                self.on_track(row)

    def drag_motion(self, event):
        if self.locator_dragging:
            tick = self.ruler_tick(event)
            if tick is not None and self.on_locator:
                self.on_locator(self.locator_dragging, self.snap_tick(tick))
            return
        if self.ruler_dragging:
            tick = self.ruler_tick(event)
            if tick is not None and self.on_seek:
                self.on_seek(self.snap_tick(tick))
            return
        if self.drag_origin is None or self.song is None:
            return
        row, clip, sx, sy, _, _ = self.drag_origin
        if abs(event.x - sx) + abs(event.y - sy) < 5:
            return
        self.canvas.delete("drag-preview")
        clips = track_clips(self.song.tracks[row], self.song.division)
        if clip >= len(clips):
            return
        start, end = clips[clip]
        dx = self.canvas.canvasx(event.x) - self.canvas.canvasx(sx)
        target_row = row if self.resize_origin else self._row_at(event)
        if target_row is None:
            return
        y = HEADER_HEIGHT + target_row * self.row_height
        option = self.snap_option.get() if self.snap_enabled.get() else 'Off'
        snapped_delta = clip_drag_delta(dx / self.beat_width * self.song.division, self.song.division, option)
        x1 = LEFT_WIDTH + (start + (0 if self.resize_origin else snapped_delta)) / self.song.division * self.beat_width
        x2 = LEFT_WIDTH + (end + snapped_delta) / self.song.division * self.beat_width
        self.canvas.create_rectangle(x1, y + 8, max(x1 + 8, x2), y + self.row_height - 8,
                                     outline="#ea580c", width=2, dash=(4, 3),
                                     tags="drag-preview")

    def drag_release(self, event):
        if self.locator_dragging:
            self.locator_dragging = None
            return
        if self.ruler_dragging:
            self.ruler_dragging = False
            return
        if self.suppress_release:
            self.resize_origin = False
            self.suppress_release = False
            self.drag_origin = None
            self.canvas.delete("drag-preview")
            return
        if self.drag_origin is None:
            return
        row, clip, sx, sy, _, _ = self.drag_origin
        self.drag_origin = None
        resizing = self.resize_origin
        self.resize_origin = False
        self.canvas.delete("drag-preview")
        if abs(event.x - sx) + abs(event.y - sy) < 5:
            self.selected_track = row
            self.draw()
            if self.on_track:
                self.on_track(row)
            return
        if self.song is None or self.on_drag is None:
            return
        target = row if resizing else self._row_at(event)
        if target is None:
            return
        # Quantize the relative movement in ticks; Off permits tick precision.
        delta_ticks = (self.canvas.canvasx(event.x) - self.canvas.canvasx(sx)) / self.beat_width * self.song.division
        option = self.snap_option.get() if self.snap_enabled.get() else 'Off'
        delta = clip_drag_delta(delta_ticks, self.song.division, option)
        if resizing:
            if self.on_resize:
                clips = track_clips(self.song.tracks[row], self.song.division)
                if clip < len(clips):
                    self.on_resize(row, clip, clips[clip][1] + delta)
            return
        if delta == 0 and target == row:
            return
        # Windows Ctrl key is 0x0004 in Tk state.
        duplicate = bool(event.state & 0x0004)
        selected = sorted(self.selected_clips)
        if len(selected) > 1:
            self.on_drag(row, clip, target, delta, duplicate, selected)
        else:
            self.on_drag(row, clip, target, delta, duplicate)

    def double_click(self, event):
        row = self._row_at(event)
        if row is not None and self.on_open:
            self.suppress_release = True
            self.drag_origin = None
            self.canvas.delete("drag-preview")
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
        width = LEFT_WIDTH + beats * self.beat_width
        height = HEADER_HEIGHT + max(10, len(self.song.tracks)) * self.row_height
        c.configure(scrollregion=(0, 0, width, height))
        c.create_rectangle(0, 0, LEFT_WIDTH, HEADER_HEIGHT, fill="#e2e8f0", outline="#cbd5e1")
        c.create_text(12, 18, text="TRACK / MIDI PARTS", anchor="w", font=("Arial", 10, "bold"))
        marks = grid_lines(self.song, beats * division)
        substep = visible_subdivision_ticks(division, self.snap_option.get(), self.beat_width)
        if substep is not None:
            major_ticks = {tick for tick, _, _ in marks}
            for tick in range(0, beats * division + 1, substep):
                if tick in major_ticks:
                    continue
                x = LEFT_WIDTH + tick / division * self.beat_width
                c.create_line(x, HEADER_HEIGHT, x, height, fill="#edf2f7", tags="subgrid")
        for tick, is_bar, bar in marks:
            if is_bar:
                x = LEFT_WIDTH + tick / division * self.beat_width
                c.create_text(x + 3, 18, anchor="w", text=str(bar))
        for index, track in enumerate(self.song.tracks):
            y = HEADER_HEIGHT + index * self.row_height
            active = index == self.selected_track
            c.create_rectangle(0, y, width, y + self.row_height,
                               fill="#dbeafe" if active else ("#f8fafc" if index % 2 == 0 else "#ffffff"),
                               outline="#cbd5e1")
            for tick, is_bar, _ in marks:
                x = LEFT_WIDTH + tick / division * self.beat_width
                c.create_line(x, y, x, y + self.row_height,
                              fill="#94a3b8" if is_bar else "#e2e8f0")
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
            audible = index not in self.muted and (not self.solo or index in self.solo)
            for clip_index, (start, end) in enumerate(spans[index]):
                x1 = LEFT_WIDTH + start / division * self.beat_width
                x2 = LEFT_WIDTH + max(end, start + division // 4) / division * self.beat_width
                c.create_rectangle(x1, y + 8, max(x1 + 8, x2), y + self.row_height - 8,
                                   fill="#3b82f6" if audible else "#94a3b8",
                                   outline="#f97316" if (index, clip_index) in self.selected_clips else ("#1d4ed8" if audible else "#64748b"),
                                   width=3 if (index, clip_index) in self.selected_clips else 1)
                if self.show_note_preview:
                    top, bottom = y + 11, y + self.row_height - 11
                    for left, right, pitch in clip_note_preview(
                            track, start, end, division, self.beat_width):
                        note_x1 = x1 + left
                        note_x2 = min(x2, x1 + right)
                        if note_x2 - note_x1 < 0.8:
                            continue
                        note_y = bottom - pitch * (bottom - top)
                        c.create_rectangle(note_x1, note_y - 1.5,
                                           max(note_x1 + 1, note_x2), note_y + 1.5,
                                           fill="#eff6ff" if audible else "#e2e8f0",
                                           outline="", tags="note-preview")
                else:
                    c.create_text(x1 + 5, y + self.row_height / 2, anchor="w",
                                  text=f"{max(1, (end-start)//division)} beats",
                                  fill="white", font=("Arial", 9))
        for tick, label, color in ((self.locator_left, 'L', '#16a34a'),
                                   (self.locator_right, 'R', '#f59e0b')):
            x = LEFT_WIDTH + tick / division * self.beat_width
            c.create_line(x, 0, x, height, fill=color, width=3, tags='locator')
            c.create_polygon(x-8, 1, x+8, 1, x, 14, fill=color, outline="#1f2937", tags='locator')
            c.create_text(x + 3, HEADER_HEIGHT - 14, text=label, anchor='w', fill=color,
                          font=('Arial', 10, 'bold'), tags='locator')
        c.create_line(LEFT_WIDTH, 0, LEFT_WIDTH, height, fill="#64748b", width=2)
        self.set_playhead(self.playhead_tick)
        self._draw_track_header()
        self._draw_fixed_ruler()

    def set_playhead(self, tick, follow=False):
        """Update the red song cursor on the arrangement timeline."""
        self.playhead_tick = tick
        c = self.canvas
        c.delete("playhead")
        if self.song is None or self.song.division <= 0 or self.song.division & 0x8000:
            return
        x = LEFT_WIDTH + tick / self.song.division * self.beat_width
        height = HEADER_HEIGHT + max(10, len(self.song.tracks)) * self.row_height
        c.create_line(x, 0, x, height, fill="#dc2626", width=3, tags="playhead")
        c.create_polygon(x-9, 0, x+9, 0, x, 15, fill="#dc2626",
                         outline="#7f1d1d", tags="playhead")
        self._draw_fixed_ruler()
        if follow and time.monotonic() >= self._manual_follow_until:
            bounds = c.cget("scrollregion").split()
            if len(bounds) == 4:
                width = c.winfo_width()
                fraction = smooth_follow_fraction(x, c.canvasx(0), width, float(bounds[2]))
                if fraction is not None:
                    c.xview_moveto(fraction)
