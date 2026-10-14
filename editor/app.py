"""XGW Next prototype: track/event inspector and basic MIDI editor."""
import copy
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from midi import Song, MidiError, Event, Track
from piano_roll import PianoRoll
from midi_output import MidiPlayer, available_outputs, tick_seconds
from midi_recording import MidiRecorder, available_inputs
from recording_ops import merge_take, quantize_take_onsets, replace_take_range_sustain_safe
from batch_quantize import transform_tracks
from xg_part_editor import XGPartEditor
from drum_editor import DrumEditor
from staff_editor import StaffEditor
from controller_editor import ControllerEditor
from list_editor import ListEditor
from master_track_editor import MasterTrackEditor
from midi_mixer import MidiMixer
from sequencer_view import SequencerView
from track_voice import used_channels, channel_voice_at
from track_channels import shared_channels, audible_channels
from xg_voices import voice_label, matching_voices
from voice_setup import insert_voice_setup
from clip_ops import edit_clip
from batch_clip_ops import edit_clips
from app_settings import load_settings, save_settings
from workspace import Workspace, WINDOW_KINDS
from song_position import format_bbt, parse_bbt, bbt_to_tick, tick_to_bbt

THEMES = {
    "Classic": ("#ece9d8", "#000000", "#ffffff"),
    "Modern Light": ("#f4f6fa", "#20242c", "#ffffff"),
    "Modern Dark": ("#252830", "#f3f4f7", "#353943"),
}

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("XGW Next 0.3 — Sequencer")
        self.root.geometry("1250x760")
        self.song = None
        self.xws_track_properties = None
        self.path = None
        self.history = []
        self.redo_history = []
        self.muted_tracks = set()
        self.solo_tracks = set()
        self.muted_channels = set()
        self.solo_channels = set()
        self.player = MidiPlayer(on_state=self.playback_state, on_error=self.playback_error)
        self.recorder = MidiRecorder(on_error=self.playback_error)
        self.input_name = tk.StringVar(value='')
        self.record_bpm = tk.StringVar(value='120')
        self.record_latency_ms = tk.StringVar(value='0')
        self.record_input_channel = tk.StringVar(value='All')
        self.record_output_channel = tk.StringVar(value='Keep')
        self.record_follow_tempo = tk.BooleanVar(value=True)
        self.record_quantize = tk.StringVar(value="Off")
        self.record_overdub = tk.BooleanVar(value=False)
        self.record_replace = tk.BooleanVar(value=False)
        self.punch_enabled = tk.BooleanVar(value=False)
        self.punch_start = tk.StringVar(value='0')
        self.punch_end = tk.StringVar(value='1920')
        self._record_target = None
        self._record_with_playback = False
        self.record_accompaniment = tk.BooleanVar(value=False)
        self.record_count_in = tk.StringVar(value='0')
        self.record_monitor = tk.BooleanVar(value=False)
        from xg_mixer_bridge import default_part_assignments, decode_part_assignments
        try:
            self.xg_part_assignments = decode_part_assignments(load_settings().get("xg_part_assignments"))
        except MidiError:
            self.xg_part_assignments = default_part_assignments()
        self.track_routes = {}
        self.routed_monitor = {}
        self.output_name = tk.StringVar(value=load_settings().get("midi_output", ""))
        self.send_sysex = tk.BooleanVar(value=False)
        self.play_start_tick = tk.StringVar(value="0")
        self.metronome_enabled = tk.BooleanVar(value=False)
        self.loop_enabled = tk.BooleanVar(value=False)
        self.loop_start = tk.StringVar(value="0")
        self.loop_end = tk.StringVar(value="1920")
        self.theme = tk.StringVar(value="Classic")
        self.track_double_click_editor = tk.StringVar(value="Piano Roll")
        self.playhead_tick = 0
        self._play_clock = None
        self._paused_tick = None
        self.transport_window = None
        self.position_text = tk.StringVar(value="Position: 0 ticks")
        self.workspace = Workspace(self, load_settings().get("window_geometry", {}))
        from shared_note_selection import SharedNoteSelection
        self.shared_note_selection = SharedNoteSelection()
        self._autosave_fingerprint = None
        self.make_ui()
        self.root.after(60000, self._autosave_recovery)
        self.root.after(50, self._update_playhead)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.apply_theme()

    def make_ui(self):
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Open MIDI...", command=self.open_file)
        file_menu.add_command(label="Save As...", command=self.save_as)
        file_menu.add_command(label="Export demixed MIDI (format 1)...", command=self.export_demixed_midi)
        file_menu.add_separator()
        file_menu.add_command(label="Open XGW Project...", command=self.open_project)
        file_menu.add_command(label="Save XGW Project...", command=self.save_project)
        file_menu.add_command(label="Import Yamaha XWS MIDI...", command=self.import_legacy_xws)
        file_menu.add_command(label="Inspect legacy XWS...", command=self.inspect_legacy_xws)
        file_menu.add_command(label="XWS MIDI setup report...", command=self.xws_setup_report)
        file_menu.add_command(label="XWS S4WT metadata audit...", command=self.xws_s4wt_report)
        file_menu.add_command(label="XWS track channel properties...", command=self.xws_track_channel_report)
        file_menu.add_command(label="Compare two XWS S4WT files...", command=self.xws_compare_s4wt)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close_app)
        menu.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(menu, tearoff=0)
        edit_menu.add_command(label="Edit selected event...", command=self.edit_event)
        edit_menu.add_command(label="Transpose selected track...", command=self.transpose)
        edit_menu.add_command(label="Quantize selected tracks (1/16)...", command=lambda: self.batch_quantize_dialog(False))
        edit_menu.add_command(label="Quantize all tracks (1/16)...", command=lambda: self.batch_quantize_dialog(True))
        edit_menu.add_command(label="Batch move/copy clips...", command=self.batch_clip_dialog)
        edit_menu.add_command(label="Batch move/copy events...", command=self.batch_event_dialog)
        edit_menu.add_separator()
        edit_menu.add_command(label="Move selected track up", command=lambda: self.move_selected_track(-1))
        edit_menu.add_command(label="Move selected track down", command=lambda: self.move_selected_track(1))
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)
        view_menu = tk.Menu(menu, tearoff=0)
        view_menu.add_command(label="Piano Roll (selected track)...", command=self.open_piano_roll)
        view_menu.add_command(label="List Editor (selected track)...", command=self.open_list_editor)
        view_menu.add_command(label="Master Track (Tempo / Time Signature)...", command=self.open_master_track)
        view_menu.add_command(label="MIDI Mixer (16 channels)...", command=self.open_midi_mixer)
        view_menu.add_command(label="Shared MIDI channels (track diagnostics)...", command=self.show_shared_channels)
        double_click_menu = tk.Menu(view_menu, tearoff=0)
        for editor_name in ("Piano Roll", "List Editor", "Drum Editor"):
            double_click_menu.add_radiobutton(label=editor_name, variable=self.track_double_click_editor,
                                              value=editor_name)
        view_menu.add_cascade(label="Track double-click opens", menu=double_click_menu)
        view_menu.add_command(label="Drum Editor (selected track)...", command=self.open_drum_editor)
        view_menu.add_command(label="Staff / Notation (selected track)...", command=self.open_staff_editor)
        view_menu.add_command(label="MIDI Controller Editor (selected track)...", command=self.open_controller_editor)
        view_menu.add_command(label="Yamaha XG Part Editor...", command=self.open_xg_editor)
        menu.add_cascade(label="View", menu=view_menu)
        window_menu = tk.Menu(menu, tearoff=0)
        for kind in WINDOW_KINDS:
            window_menu.add_command(label=kind, command=lambda k=kind: self.focus_editor(k))
        window_menu.add_separator()
        window_menu.add_command(label="Close all editors", command=self.workspace.close_all)
        menu.add_cascade(label="Window", menu=window_menu)
        menu.add_cascade(label="Edit", menu=edit_menu)
        theme_menu = tk.Menu(menu, tearoff=0)
        for name in THEMES:
            theme_menu.add_radiobutton(label=name, variable=self.theme, value=name, command=self.apply_theme)
        menu.add_cascade(label="Appearance", menu=theme_menu)
        transport_menu = tk.Menu(menu, tearoff=0)
        transport_menu.add_command(label='Choose MIDI output...', command=self.choose_output)
        transport_menu.add_command(label='Track MIDI routing (up to 4+ ports)...', command=self.configure_track_routes)
        transport_menu.add_command(label='Selected track MIDI properties...', command=self.show_selected_track_midi_properties)
        transport_menu.add_checkbutton(label='Send complete SysEx (advanced)', variable=self.send_sysex)
        transport_menu.add_checkbutton(label='Loop region', variable=self.loop_enabled)
        transport_menu.add_checkbutton(label='Metronome during playback', variable=self.metronome_enabled)
        transport_menu.add_command(label='Play', command=self.play_midi)
        transport_menu.add_command(label='Pause / Resume', command=self.pause_midi)
        transport_menu.add_command(label='Stop', command=self.stop_midi)
        transport_menu.add_command(label='Transport window...', command=self.open_transport_window)
        transport_menu.add_separator()
        transport_menu.add_command(label='Choose MIDI input...', command=self.choose_input)
        transport_menu.add_command(label='Record', command=self.start_recording)
        transport_menu.add_command(label='Finish recording', command=self.finish_recording)
        menu.add_cascade(label='Transport', menu=transport_menu)
        self.root.config(menu=menu)

        transport_bar = ttk.Frame(self.root)
        transport_bar.pack(fill=tk.X, padx=8, pady=(6, 0))
        ttk.Button(transport_bar, text="▶ Play", command=self.play_midi).pack(side="left", padx=3)
        ttk.Button(transport_bar, text="Ⅱ Pause", command=self.pause_midi).pack(side="left", padx=3)
        ttk.Button(transport_bar, text="■ Stop", command=self.stop_midi).pack(side="left", padx=3)
        ttk.Button(transport_bar, text="● Record", command=self.start_recording).pack(side="left", padx=3)
        ttk.Button(transport_bar, text="■ Finish Rec", command=self.finish_recording).pack(side="left", padx=3)
        ttk.Label(transport_bar, text="Start tick:").pack(side="left", padx=(12, 3))
        ttk.Entry(transport_bar, textvariable=self.play_start_tick, width=10).pack(side="left")
        ttk.Label(transport_bar, textvariable=self.position_text).pack(side="left", padx=(8, 3))
        ttk.Checkbutton(transport_bar, text="Click", variable=self.metronome_enabled).pack(side="left", padx=3)
        ttk.Checkbutton(transport_bar, text="Loop", variable=self.loop_enabled).pack(side="left", padx=(12, 2))
        ttk.Label(transport_bar, text="From:").pack(side="left")
        ttk.Entry(transport_bar, textvariable=self.loop_start, width=8).pack(side="left")
        ttk.Label(transport_bar, text="To:").pack(side="left", padx=(5, 0))
        ttk.Entry(transport_bar, textvariable=self.loop_end, width=8).pack(side="left")
        ttk.Label(transport_bar, text="Rec BPM:").pack(side="left", padx=(10, 2))
        ttk.Entry(transport_bar, textvariable=self.record_bpm, width=6).pack(side="left")
        ttk.Label(transport_bar, text="Input latency ms:").pack(side="left", padx=(5, 2))
        ttk.Entry(transport_bar, textvariable=self.record_latency_ms, width=5).pack(side="left")
        ttk.Label(transport_bar, text="MIDI IN ch:").pack(side="left", padx=(5, 2))
        ttk.Combobox(transport_bar, textvariable=self.record_input_channel, width=4,
                     state="readonly", values=['All'] + [str(i) for i in range(1, 17)]).pack(side="left")
        ttk.Label(transport_bar, text="Record ch:").pack(side="left", padx=(5, 2))
        ttk.Combobox(transport_bar, textvariable=self.record_output_channel, width=5,
                     state="readonly", values=['Keep'] + [str(i) for i in range(1, 17)]).pack(side="left")
        ttk.Checkbutton(transport_bar, text="Follow song tempo", variable=self.record_follow_tempo).pack(side="left", padx=3)
        ttk.Checkbutton(transport_bar, text="Overdub selected", variable=self.record_overdub).pack(side="left", padx=5)
        ttk.Checkbutton(transport_bar, text="Replace selected (Punch)", variable=self.record_replace).pack(side="left", padx=3)
        ttk.Label(transport_bar, text="Rec quantize:").pack(side="left")
        ttk.Combobox(transport_bar, textvariable=self.record_quantize, width=5,
                     values=("Off", "30", "60", "120", "240", "480"), state="readonly").pack(side="left")
        ttk.Checkbutton(transport_bar, text="Play accompaniment", variable=self.record_accompaniment).pack(side="left", padx=5)
        ttk.Checkbutton(transport_bar, text="MIDI Monitor", variable=self.record_monitor).pack(side="left", padx=3)
        ttk.Label(transport_bar, text="Count-in bars").pack(side="left")
        ttk.Combobox(transport_bar, textvariable=self.record_count_in, width=3,
                     values=tuple(str(i) for i in range(9)), state="readonly").pack(side="left")
        ttk.Checkbutton(transport_bar, text="Punch", variable=self.punch_enabled).pack(side="left", padx=3)
        ttk.Entry(transport_bar, textvariable=self.punch_start, width=7).pack(side="left")
        ttk.Label(transport_bar, text="–").pack(side="left")
        ttk.Entry(transport_bar, textvariable=self.punch_end, width=7).pack(side="left")
        ttk.Button(transport_bar, text="Open MIDI...", command=self.open_file).pack(side="left", padx=10)
        ttk.Button(transport_bar, text="Save As...", command=self.save_as).pack(side="left", padx=3)
        ttk.Button(transport_bar, text="MIDI output...", command=self.choose_output).pack(side="left", padx=10)
        self.sequencer = SequencerView(self.root, on_track=self.select_sequencer_track, on_open=self.open_sequencer_track, on_toggle=self.toggle_track_state, on_instrument=self.edit_track_voice, on_clip=self.edit_sequencer_clip, on_drag=self.drag_sequencer_clip, on_seek=self.seek_to_tick, on_locator=self.set_locator)
        self.sequencer.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        outer = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        outer.pack(fill=tk.BOTH, expand=False, padx=8, pady=8)
        outer.configure(height=230)
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
        self.tracks.bind("<<TreeviewSelect>>", lambda _: self.on_tree_track_select())
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

    def drag_sequencer_clip(self, track_index, clip_index, target_track, delta, duplicate, selections=None):
        if self.song is None or self.player.playing:
            messagebox.showwarning("MIDI clip", "Stop playback before editing.")
            return
        from copy import deepcopy
        try:
            selected = list(selections) if selections else [(track_index, clip_index)]
            destinations = {source: source + target_track - track_index for source, _ in selected}
            # Validate every destination and event before taking an undo snapshot.
            edit_clips(deepcopy(self.song), selected, delta, duplicate, destinations, include_events=True)
            self.snapshot()
            try:
                count = edit_clips(self.song, selected, delta, duplicate, destinations, include_events=True)
            except Exception:
                self.history.pop()
                raise
        except MidiError as exc:
            messagebox.showerror("MIDI clip", str(exc), parent=self.root)
            return
        self.select_sequencer_track(target_track)
        self.sequencer.draw()
        self.show_events()
        action = "Copied" if duplicate else "Moved"
        self.status.set(f"{action} {count} notes and associated MIDI events; Save As to save.")

    def edit_sequencer_clip(self, track_index, clip_index):
        if self.player.playing:
            messagebox.showwarning("MIDI clip", "Stop playback before editing.")
            return
        if self.song is None:
            return
        self.select_sequencer_track(track_index)
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Track {track_index+1} / Clip {clip_index+1}")
        dialog.geometry("540x420")
        dialog.transient(self.root)
        ttk.Label(dialog, text="Move or duplicate a MIDI clip across tracks and beats.").pack(pady=(12, 6))
        beats = tk.IntVar(value=4)
        line = ttk.Frame(dialog)
        line.pack(pady=5)
        ttk.Label(line, text="Offset in beats:").pack(side="left")
        ttk.Spinbox(line, from_=-999, to=999, textvariable=beats, width=8).pack(side="left", padx=8)
        target_line = ttk.Frame(dialog)
        target_line.pack(pady=5)
        ttk.Label(target_line, text="Destination track:").pack(side="left")
        destination = tk.IntVar(value=track_index + 1)
        ttk.Spinbox(target_line, from_=1, to=len(self.song.tracks),
                    textvariable=destination, width=8).pack(side="left", padx=8)
        include_events = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Include controllers, program changes and SysEx",
                        variable=include_events).pack(pady=6)
        actions = ttk.Frame(dialog)
        actions.pack(pady=5)
        def apply(duplicate):
            from copy import deepcopy
            try:
                delta = beats.get() * self.song.division
                target = destination.get() - 1
                if delta == 0 and target == track_index:
                    raise MidiError("Choose another track or a non-zero beat offset")
                destinations = {track_index: target}
                selected = [(track_index, clip_index)]
                edit_clips(deepcopy(self.song), selected, delta, duplicate,
                           destinations, include_events=include_events.get())
                self.snapshot()
                try:
                    count = edit_clips(self.song, selected, delta, duplicate,
                                       destinations, include_events=include_events.get())
                except Exception:
                    self.history.pop()
                    raise
            except (MidiError, tk.TclError, ValueError) as exc:
                messagebox.showerror("MIDI clip", str(exc), parent=dialog)
                return
            self.sequencer.draw()
            self.show_events()
            self.status.set(f"{'Copied' if duplicate else 'Moved'} {count} MIDI notes to track {target+1}; Save As to save.")
            dialog.destroy()
        ttk.Button(actions, text="Move", command=lambda: apply(False)).pack(side="left", padx=6)
        ttk.Button(actions, text="Duplicate", command=lambda: apply(True)).pack(side="left", padx=6)
        def boundary_edit(kind):
            from copy import deepcopy
            from clip_boundaries import split_sustained_notes, trim_clip_notes
            from arrangement import track_clips
            try:
                start, end = track_clips(self.song.tracks[track_index], self.song.division)[clip_index]
                if kind == "split":
                    tick = simpledialog.askinteger("Split sustained notes", f"Cut at MIDI tick (between {start} and {end}):", parent=dialog,
                                                   initialvalue=(start + end) // 2)
                    if tick is None:
                        return
                    operation = lambda song: split_sustained_notes(song, track_index, clip_index, tick)
                else:
                    left = simpledialog.askinteger("Trim notes", f"Left tick (minimum {start}):", parent=dialog, initialvalue=start)
                    if left is None:
                        return
                    right = simpledialog.askinteger("Trim notes", f"Right tick (maximum {end}):", parent=dialog, initialvalue=end)
                    if right is None:
                        return
                    operation = lambda song: trim_clip_notes(song, track_index, clip_index, left, right)
                count = operation(deepcopy(self.song))
                if not count:
                    self.status.set("No note boundaries changed.")
                    return
                self.snapshot()
                try:
                    operation(self.song)
                except Exception:
                    self.history.pop()
                    raise
                self.sequencer.draw()
                self.show_events()
                self.status.set(f"Edited {count} notes; Save As to save.")
                dialog.destroy()
            except (MidiError, ValueError, IndexError) as exc:
                messagebox.showerror("MIDI clip", str(exc), parent=dialog)
        boundary_actions = ttk.Frame(dialog)
        boundary_actions.pack(pady=4)
        ttk.Button(boundary_actions, text="Split sustained notes...", command=lambda: boundary_edit("split")).pack(side="left", padx=4)
        ttk.Button(boundary_actions, text="Trim notes...", command=lambda: boundary_edit("trim")).pack(side="left", padx=4)
        def apply_legato():
            from copy import deepcopy
            from clip_boundaries import legato_clip_notes
            try:
                gap = simpledialog.askinteger("Legato", "Gap before next note (ticks):", parent=dialog,
                                              initialvalue=0, minvalue=0)
                if gap is None:
                    return
                count = legato_clip_notes(deepcopy(self.song), track_index, clip_index, gap)
                if not count:
                    self.status.set("No gaps to extend in this clip.")
                    return
                self.snapshot()
                try:
                    legato_clip_notes(self.song, track_index, clip_index, gap)
                except Exception:
                    self.history.pop()
                    raise
                self.sequencer.draw()
                self.show_events()
                self.status.set(f"Extended {count} notes (Legato); Save As to save.")
                dialog.destroy()
            except (MidiError, ValueError) as exc:
                messagebox.showerror("Legato", str(exc), parent=dialog)
        ttk.Button(boundary_actions, text="Legato...", command=apply_legato).pack(side="left", padx=4)
        def join_next_clip():
            from copy import deepcopy
            from clip_join import close_clip_gap
            try:
                gap = simpledialog.askinteger("Close clip gap", "Gap after first clip (ticks):",
                                              parent=dialog, initialvalue=0, minvalue=0)
                if gap is None:
                    return
                operation = lambda song: close_clip_gap(song, track_index, clip_index,
                                                        gap, include_events.get())
                count = operation(deepcopy(self.song))
                self.snapshot()
                try:
                    operation(self.song)
                except Exception:
                    self.history.pop()
                    raise
                self.sequencer.draw()
                self.show_events()
                self.status.set(f"Closed gap to next clip; moved {count} notes. Save As to save.")
                dialog.destroy()
            except (MidiError, ValueError, IndexError) as exc:
                messagebox.showerror("Close clip gap", str(exc), parent=dialog)
        ttk.Button(dialog, text="Join next clip (close gap)...", command=join_next_clip).pack(pady=5)
        def region_action(kind):
            from clip_regions import split_region, merge_regions, reset_regions
            from arrangement import track_clips
            from copy import deepcopy
            try:
                if kind == 'split':
                    start, end = track_clips(self.song.tracks[track_index], self.song.division)[clip_index]
                    tick = simpledialog.askinteger('Split clip region',
                        f'Split at MIDI tick ({start} < tick < {end}):',
                        parent=dialog, initialvalue=(start + end)//2)
                    if tick is None:
                        return
                    operation = lambda song: split_region(song, track_index, clip_index, tick)
                elif kind == 'merge':
                    operation = lambda song: merge_regions(song, track_index, clip_index)
                else:
                    operation = lambda song: reset_regions(song, track_index)
                operation(deepcopy(self.song))
                self.snapshot()
                try:
                    operation(self.song)
                except Exception:
                    self.history.pop()
                    raise
                self.sequencer.draw()
                self.show_events()
                self.status.set('Clip regions updated; save MIDI to persist .xgwclips.json sidecar.')
                dialog.destroy()
            except (MidiError, ValueError, IndexError) as exc:
                messagebox.showerror('Clip regions', str(exc), parent=dialog)
        region_buttons = ttk.Frame(dialog)
        region_buttons.pack(pady=4)
        ttk.Button(region_buttons, text='Split region...', command=lambda: region_action('split')).pack(side='left', padx=3)
        ttk.Button(region_buttons, text='Merge with next region', command=lambda: region_action('merge')).pack(side='left', padx=3)
        ttk.Button(region_buttons, text='Reset regions', command=lambda: region_action('reset')).pack(side='left', padx=3)



    def batch_clip_dialog(self):
        """Batch-edit arrangement clips, addressed as 1-based track:clip pairs."""
        if self.song is None:
            return
        if self.player.playing:
            messagebox.showwarning("Batch clips", "Stop playback before editing.")
            return
        from arrangement import track_clips
        dialog = tk.Toplevel(self.root)
        dialog.title("Batch move / copy MIDI clips")
        dialog.transient(self.root)
        dialog.geometry("520x310")
        ttk.Label(dialog, text="Select clips as track:clip, separated by commas (e.g. 1:1, 1:2, 3:1)").pack(pady=(12, 4))
        selected = sorted(self.sequencer.selected_clips)
        selection = tk.StringVar(value=", ".join(f"{t+1}:{c+1}" for t, c in selected)
                                 if selected else f"{self.selected_track()+1}:1")
        ttk.Entry(dialog, textvariable=selection, width=48).pack(pady=5)
        available = ", ".join(f"{i+1}: {len(track_clips(t, self.song.division))} clips"
                              for i, t in enumerate(self.song.tracks))
        ttk.Label(dialog, text=available[:110], wraplength=490).pack(pady=4)
        include_events = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Move/copy CC, Program, Pitch Bend, Aftertouch and SysEx with clips", variable=include_events).pack(pady=3)
        offset = tk.IntVar(value=4)
        row = ttk.Frame(dialog); row.pack(pady=7)
        ttk.Label(row, text="Offset (beats):").pack(side="left")
        ttk.Spinbox(row, from_=-9999, to=9999, textvariable=offset, width=9).pack(side="left", padx=8)
        def apply(duplicate):
            try:
                pairs = []
                for part in selection.get().split(','):
                    fields = part.strip().split(':')
                    if len(fields) != 2:
                        raise MidiError("Use track:clip pairs, e.g. 1:1, 2:3")
                    a, b = (int(v.strip()) for v in fields)
                    pairs.append((a-1, b-1))
                delta = offset.get() * self.song.division
                if not delta and not duplicate:
                    raise MidiError("Choose a non-zero offset to move clips")
                # Validate on a copy before storing an undo snapshot.
                from copy import deepcopy
                edit_clips(deepcopy(self.song), pairs, delta, duplicate, include_events=include_events.get())
                self.snapshot()
                try:
                    count = edit_clips(self.song, pairs, delta, duplicate, include_events=include_events.get())
                except Exception:
                    self.history.pop()
                    raise
            except (ValueError, MidiError, tk.TclError) as exc:
                messagebox.showerror("Batch clips", str(exc), parent=dialog)
                return
            self.sequencer.draw()
            self.show_events()
            self.status.set(f"{'Copied' if duplicate else 'Moved'} {count} notes across {len(pairs)} clips")
            dialog.destroy()
        actions = ttk.Frame(dialog); actions.pack(pady=10)
        ttk.Button(actions, text="Move clips", command=lambda: apply(False)).pack(side="left", padx=6)
        ttk.Button(actions, text="Duplicate clips", command=lambda: apply(True)).pack(side="left", padx=6)

    def edit_track_voice(self, index):
        if self.song is None or not 0 <= index < len(self.song.tracks):
            return
        if self.player.playing:
            messagebox.showwarning("Track voice", "Stop playback before editing.")
            return
        channels = used_channels(self.song, index)
        channel = channels[0] if channels else 1
        if len(channels) > 1:
            channel = simpledialog.askinteger("MIDI channel",
                "Track uses channels " + ", ".join(map(str, channels)) +
                ". Which channel do you want to edit?",
                initialvalue=channel, minvalue=1, maxvalue=16, parent=self.root)
            if channel is None:
                return
        voice = channel_voice_at(self.song, index, channel, tick=0)
        picker = tk.Toplevel(self.root)
        picker.title(f"Track {index+1} / MIDI Channel {channel} — Instrument")
        picker.geometry("610x480")
        ttk.Label(picker, text=f"Current: {voice_label(voice.msb, voice.lsb, voice.program)}"
                  ).pack(anchor="w", padx=12, pady=8)
        ttk.Label(picker, text="Search GM / Yamaha XG instruments:").pack(anchor="w", padx=12)
        search = tk.StringVar()
        ttk.Entry(picker, textvariable=search).pack(fill="x", padx=12, pady=5)
        items = tk.Listbox(picker)
        items.pack(fill="both", expand=True, padx=12, pady=8)
        records = []
        def refresh(*_):
            records[:] = matching_voices(search.get())
            items.delete(0, "end")
            for msb, lsb, program, name in records:
                items.insert("end", f"{name}   [MSB {msb}, LSB {lsb}, Program {program+1}]")
        search.trace_add("write", refresh)
        refresh()
        def choose(_=None):
            selected = items.curselection()
            if not selected:
                return
            msb, lsb, program, name = records[selected[0]]
            self.snapshot()
            insert_voice_setup(self.song, index, channel, msb, lsb, program)
            self.sequencer.draw()
            self.show_events()
            self.status.set(f"Track {index+1}, CH {channel}: {name} (Save As to save)")
            picker.destroy()
        items.bind("<Double-Button-1>", choose)
        ttk.Button(picker, text="Insert selected instrument into MIDI",
                   command=choose).pack(pady=8)

    def show_shared_channels(self):
        """Explain channel ownership conflicts before implementing live track mute."""
        if self.song is None:
            messagebox.showinfo("Track MIDI channels", "Open a MIDI file first.")
            return
        overlaps = shared_channels(self.song)
        if not overlaps:
            messagebox.showinfo("Track MIDI channels", "No MIDI channels are shared by multiple tracks.")
            return
        details = "\n".join(
            f"Channel {channel + 1}: tracks {', '.join(str(i + 1) for i in sorted(owners))}"
            for channel, owners in sorted(overlaps.items()))
        messagebox.showwarning(
            "Shared MIDI channels",
            "These tracks share MIDI channels:\n\n" + details +
            "\n\nChannel-wide All Notes Off can also silence notes on other tracks. "
            "Live track Mute/Solo remains disabled until note ownership is handled safely.")

    def _live_track_mix_supported(self):
        return getattr(self, "song", None) is not None and not shared_channels(self.song)

    def _effective_playback_channels(self):
        return audible_channels(self.song, self.muted_tracks, self.solo_tracks,
                                self.muted_channels, self.solo_channels)

    def set_channel_monitor_mix(self, muted, solo):
        """Apply playback-only channel mix atomically, including player failures."""
        muted, solo = set(muted), set(solo)
        if any(type(ch) is not int or ch not in range(16) for ch in muted | solo):
            raise ValueError("MIDI channels must be numbered 0–15")
        enabled = {ch for ch in range(16) if ch not in muted and
                   (not solo or ch in solo)}
        if self.player.playing and getattr(self, "song", None) is not None:
            try:
                enabled = audible_channels(self.song, self.muted_tracks,
                                           self.solo_tracks, muted, solo)
            except ValueError as exc:
                # Never fall back to a channel-only mask: that could override
                # track Mute/Solo and leak notes on shared MIDI channels.
                raise ValueError(
                    "Cannot change channel monitor while track Mute/Solo "
                    "conflicts on a shared MIDI channel"
                ) from exc
        # Do not publish new state until the playback engine accepts it.
        if self.player.playing:
            self.player.set_enabled_channels(enabled)
        self.muted_channels = muted
        self.solo_channels = solo
        return enabled

    def toggle_track_state(self, index, kind):
        """Commit track mix only after the live player accepts the new mask."""
        if self.song is None or type(index) is not int or not 0 <= index < len(self.song.tracks):
            return
        if kind not in ("mute", "solo"):
            raise ValueError("Unknown track mix control")
        next_muted, next_solo = set(self.muted_tracks), set(self.solo_tracks)
        proposed = next_muted if kind == "mute" else next_solo
        if index in proposed:
            proposed.remove(index)
        else:
            proposed.add(index)
        if self.player.playing:
            try:
                enabled = audible_channels(self.song, next_muted, next_solo,
                                           self.muted_channels, self.solo_channels)
            except ValueError:
                messagebox.showinfo("Track controls", "Stop playback before changing track Mute/Solo: "
                                    "the proposed mix would split a shared MIDI channel.")
                return
            # A failing MIDI output must not leave the UI and playback out of sync.
            self.player.set_enabled_channels(enabled)
        self.muted_tracks, self.solo_tracks = next_muted, next_solo
        self.sequencer.set_mix(self.muted_tracks, self.solo_tracks)

    def select_sequencer_track(self, index):
        if self.song is not None and 0 <= index < len(self.song.tracks):
            self.tracks.selection_set(str(index))
            self.show_events()

    def on_tree_track_select(self):
        self.show_events()
        index = self.selected_track()
        if index is not None:
            self.sequencer.select_track(index)

    def open_sequencer_track(self, index):
        self.select_sequencer_track(index)
        editor = self.track_double_click_editor.get()
        if editor == "List Editor":
            self.open_list_editor()
        elif editor == "Drum Editor":
            self.open_drum_editor()
        else:
            self.open_piano_roll()

    def apply_theme(self):
        bg, fg, field = THEMES[self.theme.get()]
        self.root.configure(bg=bg)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=bg, foreground=fg)
        style.configure("Treeview", background=field, fieldbackground=field,
                        foreground="#151515" if self.theme.get() != "Modern Dark" else "#f0f0f0")
        style.configure("Treeview.Heading", background=bg, foreground=fg)

    def _update_playhead(self):
        """Update UI playhead using the song tempo map, without blocking MIDI."""
        try:
            if self.song is not None and self._play_clock and self.player.playing:
                from transport_snapshot import cursor_snapshot
                self.playhead_tick = cursor_snapshot(self.song, self._play_clock, time.monotonic())
            if self.song is not None and self.recorder.recording:
                record_tick = self.recorder.current_tick()
                if record_tick is not None:
                    self.playhead_tick = record_tick
            if self.song is not None and hasattr(self, "sequencer"):
                self.sequencer.locator_left = self._safe_locator(self.loop_start.get())
                self.sequencer.locator_right = self._safe_locator(self.loop_end.get())
            self.position_text.set(
                f"Location {format_bbt(self.song, self.playhead_tick)}  "
                f"({self.playhead_tick} ticks)" if self.song is not None
                else f"Position: {self.playhead_tick} ticks")
            if self.transport_window is not None and self.transport_window.winfo_exists():
                self.transport_position.set(format_bbt(self.song, self.playhead_tick) if self.song else "0001:01:000")
            if hasattr(self, "sequencer"):
                self.sequencer.set_playhead(self.playhead_tick, follow=self.player.playing or self.recorder.recording)
        finally:
            self.root.after(80, self._update_playhead)

    @staticmethod
    def _safe_locator(value):
        try:
            return max(0, int(value))
        except (ValueError, TypeError):
            return 0

    def seek_to_tick(self, tick):
        """Move song cursor; restart playback to keep the MIDI engine in sync."""
        if self.song is None:
            return
        from transport_ops import seek_position
        try:
            tick = seek_position(tick, self.loop_enabled.get(),
                                 self.loop_start.get(), self.loop_end.get())
        except MidiError as exc:
            messagebox.showerror('Transport seek', str(exc))
            return
        if self.recorder.recording:
            messagebox.showwarning('Transport seek', 'Finish recording before moving the cursor.')
            return
        was_playing = self.player.playing
        if was_playing:
            self.stop_midi()
        self.playhead_tick = tick
        self.play_start_tick.set(str(tick))
        self.sequencer.set_playhead(tick, follow=True)
        if was_playing:
            self.play_midi()

    def nudge_transport(self, direction, bars=False):
        if self.song is None:
            return
        bar, beat, _ = tick_to_bbt(self.song, self.playhead_tick)
        if bars:
            target_bar = max(1, bar + direction)
            try:
                target = bbt_to_tick(self.song, target_bar, 1)
            except MidiError:
                return
        else:
            # Advance by the current time-signature beat, not always a quarter note.
            from meter_grid import meter_changes
            from fractions import Fraction
            changes = meter_changes(self.song)
            meter = changes[0]
            for change in changes:
                if change[0] > self.playhead_tick:
                    break
                meter = change
            step = max(1, int(Fraction(self.song.division * 4, meter[2])))
            target = max(0, self.playhead_tick + direction * step)
        self.seek_to_tick(target)

    def set_locator(self, which, tick=None):
        if self.song is None:
            return
        from transport_ops import move_locator, tick_value, MAX_TICK
        try:
            if tick is None:
                # Transport-window buttons retain their established behavior:
                # expand the range to include the current cursor.
                target = tick_value(self.playhead_tick)
                left = tick_value(self.loop_start.get())
                right = tick_value(self.loop_end.get())
                if which == 'L':
                    left = target
                    right = min(MAX_TICK, max(right, left + max(1, self.song.division)))
                elif which == 'R':
                    right = target
                    left = max(0, min(left, right - max(1, self.song.division)))
                else:
                    raise MidiError('Unknown locator')
                if left >= right:
                    raise MidiError('No room for locator range')
            else:
                # Dragging a handle never unexpectedly pushes the other handle.
                left, right = move_locator(which, tick,
                                           self.loop_start.get(), self.loop_end.get(),
                                           self.song.division)
        except MidiError as exc:
            messagebox.showerror('Transport locators', str(exc))
            return
        self.loop_start.set(str(left))
        self.loop_end.set(str(right))
        self.sequencer.locator_left = left
        self.sequencer.locator_right = right
        self.sequencer.draw()

    def open_transport_window(self):
        if self.transport_window is not None and self.transport_window.winfo_exists():
            self.transport_window.lift()
            return
        win = tk.Toplevel(self.root)
        self.transport_window = win
        win.title('XGW Next — Transport')
        win.resizable(False, False)
        panel = ttk.Frame(win, padding=10)
        panel.pack(fill='both', expand=True)
        buttons = ttk.Frame(panel)
        buttons.pack(fill='x')
        for label, command in (('◀◀', lambda: self.nudge_transport(-1, True)),
                               ('◀', lambda: self.nudge_transport(-1)),
                               ('▶ Play', self.play_midi), ('Ⅱ Pause', self.pause_midi), ('■ Stop', self.stop_midi),
                               ('▶', lambda: self.nudge_transport(1)),
                               ('▶▶', lambda: self.nudge_transport(1, True)),
                               ('● Rec', self.start_recording),
                               ('■ End Rec', self.finish_recording)):
            ttk.Button(buttons, text=label, command=command).pack(side='left', padx=2)
        self.transport_position = tk.StringVar(value='0001:01:000')
        ttk.Label(panel, textvariable=self.transport_position,
                  font=('Courier New', 23, 'bold')).pack(pady=8)
        bbt_row = ttk.Frame(panel)
        bbt_row.pack(fill='x', pady=(0, 5))
        ttk.Label(bbt_row, text='Bar:Beat:Tick:').pack(side='left')
        self.transport_bbt_entry = ttk.Entry(bbt_row, width=16)
        self.transport_bbt_entry.pack(side='left', padx=4)
        ttk.Button(bbt_row, text='Go to position', command=self._transport_go_bbt).pack(side='left')
        self.transport_bbt_entry.bind('<Return>', lambda _event: self._transport_go_bbt())
        position = ttk.Frame(panel)
        position.pack(fill='x')
        ttk.Label(position, text='Tick:').pack(side='left')
        ttk.Entry(position, textvariable=self.play_start_tick, width=12).pack(side='left', padx=4)
        ttk.Button(position, text='Go', command=lambda: self._transport_go()).pack(side='left')
        ttk.Button(position, text='L ← Cursor', command=lambda: self.set_locator('L')).pack(side='left', padx=6)
        ttk.Button(position, text='R ← Cursor', command=lambda: self.set_locator('R')).pack(side='left')
        loop = ttk.Frame(panel)
        loop.pack(fill='x', pady=(8, 0))
        ttk.Checkbutton(loop, text='Loop L–R', variable=self.loop_enabled).pack(side='left')
        ttk.Label(loop, text='L:').pack(side='left', padx=(12, 2))
        ttk.Entry(loop, textvariable=self.loop_start, width=10).pack(side='left')
        ttk.Label(loop, text='R:').pack(side='left', padx=(10, 2))
        ttk.Entry(loop, textvariable=self.loop_end, width=10).pack(side='left')
        ttk.Label(panel, text='Drag the ruler to seek; drag L/R markers to move locators. Shift+click sets L, Ctrl+click sets R.').pack(pady=(8, 0))

    def _transport_go_bbt(self):
        if self.song is None:
            return
        try:
            tick = parse_bbt(self.song, self.transport_bbt_entry.get())
        except MidiError as exc:
            messagebox.showerror('Transport', str(exc))
            return
        self.seek_to_tick(tick)

    def _transport_go(self):
        try:
            tick = int(self.play_start_tick.get())
            if tick < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror('Transport', 'Position must be a non-negative integer tick.')
            return
        self.seek_to_tick(tick)

    def playback_state(self, playing):
        self.root.after(0, lambda: self.status.set(
            'MIDI playback running...' if playing else 'MIDI playback stopped.'))

    def playback_error(self, error):
        self.root.after(0, lambda: messagebox.showerror('MIDI playback', error))

    def choose_output(self):
        chooser = tk.Toplevel(self.root)
        chooser.title("MIDI output — Windows")
        chooser.geometry("590x310")
        chooser.transient(self.root)
        chooser.grab_set()
        ttk.Label(chooser, text="MIDI OUT (hardware interface or software MIDI port)").pack(anchor="w", padx=12, pady=(12, 4))
        selection = tk.StringVar(value=self.output_name.get())
        combo = ttk.Combobox(chooser, textvariable=selection, state="readonly", width=72)
        combo.pack(fill="x", padx=12, pady=4)
        info = tk.StringVar(value="")
        ttk.Label(chooser, textvariable=info, wraplength=555, justify="left").pack(fill="x", padx=12, pady=8)
        def refresh():
            try:
                outputs = available_outputs()
            except MidiError as exc:
                combo.configure(values=())
                info.set(str(exc))
                return
            combo.configure(values=outputs)
            if outputs:
                selection.set(selection.get() if selection.get() in outputs else outputs[0])
                info.set(f"{len(outputs)} MIDI output(s) detected. Choose one and click Use this output.")
            else:
                selection.set("")
                info.set("No MIDI OUT ports found by Windows/RtMidi. Connect and enable a USB-MIDI interface or install a virtual MIDI port (e.g. loopMIDI), then click Refresh. The Windows default audio speakers are NOT a MIDI OUT port.")
        def apply():
            if not selection.get():
                messagebox.showwarning("MIDI output", "No MIDI OUT selected. Click Refresh after connecting a MIDI device.", parent=chooser)
                return
            self.output_name.set(selection.get())
            self.save_preferences()
            self.status.set("MIDI output: " + selection.get())
            chooser.destroy()
        buttons = ttk.Frame(chooser)
        buttons.pack(fill="x", padx=12, pady=10)
        ttk.Button(buttons, text="Refresh MIDI ports", command=refresh).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Use this output", command=apply).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=chooser.destroy).pack(side="right")
        refresh()

    def show_selected_track_midi_properties(self):
        """Edit playback channel override without rewriting source MIDI events."""
        if self.song is None:
            messagebox.showinfo('Track properties', 'Open a MIDI file first.')
            return
        index = self.selected_track()
        if index is None:
            messagebox.showinfo('Track properties', 'Select a track first.')
            return
        if self.player.playing:
            messagebox.showwarning('Track properties', 'Stop playback before changing routing.')
            return
        from xws_track_display import source_channel_labels
        from track_channel_properties import channel_override_label, parse_channel_override
        from midi_routing import validate_routes
        dialog = tk.Toplevel(self.root)
        dialog.title(f'Track {index + 1} MIDI properties')
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=f'{index + 1}: {self.song.tracks[index].name()}').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 12))
        source = source_channel_labels(self.xws_track_properties, len(self.song.tracks))[index]
        ttk.Label(frame, text='Original XWS channel (read-only):').grid(row=1, column=0, sticky='w')
        ttk.Label(frame, text=source).grid(row=1, column=1, sticky='w')
        current_port, current_channel = self.track_routes.get(index, (self.output_name.get(), None))
        ttk.Label(frame, text='Playback output channel:').grid(row=2, column=0, sticky='w', pady=10)
        channel_var = tk.StringVar(value=channel_override_label(current_channel))
        ttk.Combobox(frame, textvariable=channel_var, state='readonly', width=10,
                     values=['Keep'] + [str(i) for i in range(1, 17)]).grid(row=2, column=1, sticky='w')
        ttk.Label(frame, text='Keep preserves the MIDI event channels. Override affects playback only.',
                  wraplength=360).grid(row=3, column=0, columnspan=2, sticky='w', pady=(0, 12))
        def save():
            try:
                channel = parse_channel_override(channel_var.get())
                proposed = dict(self.track_routes)
                if channel is None and index not in proposed:
                    dialog.destroy()
                    return
                proposed[index] = (current_port, channel)
                validate_routes(self.song, proposed, self.output_name.get())
            except (MidiError, ValueError) as exc:
                messagebox.showerror('Track properties', str(exc), parent=dialog)
                return
            self.track_routes = proposed
            self.routed_monitor.clear()
            self.status.set(f'Track {index + 1} playback channel: {channel_var.get()}')
            dialog.destroy()
        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=2, sticky='e')
        ttk.Button(buttons, text='Save', command=save).pack(side='left', padx=5)
        ttk.Button(buttons, text='Cancel', command=dialog.destroy).pack(side='left')

    def configure_track_routes(self):
        """Assign each track to a physical MIDI output and optional channel."""
        if self.song is None:
            messagebox.showinfo('MIDI routing', 'Open a MIDI file first.')
            return
        if self.player.playing:
            messagebox.showwarning('MIDI routing', 'Stop playback before changing routing.')
            return
        try:
            ports = available_outputs()
        except MidiError as exc:
            messagebox.showerror('MIDI routing', str(exc))
            return
        if not ports:
            messagebox.showwarning('MIDI routing', 'No MIDI output ports available.')
            return
        window = tk.Toplevel(self.root)
        window.title('Track MIDI output routing')
        window.geometry('790x460')
        outer = ttk.Frame(window, padding=10)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Source XWS channel is read-only; output channel override affects playback only.').pack(anchor='w')
        from xws_track_display import source_channel_labels
        source_labels = source_channel_labels(self.xws_track_properties, len(self.song.tracks))
        tree = ttk.Treeview(outer, columns=('source', 'port', 'channel'), show='tree headings', height=12)
        tree.heading('#0', text='Track')
        tree.heading('source', text='XWS source')
        tree.heading('port', text='MIDI output')
        tree.heading('channel', text='Channel')
        tree.column('#0', width=170)
        tree.column('source', width=95)
        tree.column('port', width=300)
        tree.column('channel', width=90)
        tree.pack(fill='both', expand=True, pady=8)
        working = dict(self.track_routes)
        for i, track in enumerate(self.song.tracks):
            port, channel = working.get(i, (self.output_name.get() or ports[0], None))
            tree.insert('', 'end', iid=str(i), text=f'{i+1}: {track.name()}',
                        values=(source_labels[i], port, 'Keep' if channel is None else str(channel + 1)))
        controls = ttk.Frame(outer)
        controls.pack(fill='x')
        port_var = tk.StringVar(value=ports[0])
        channel_var = tk.StringVar(value='Keep')
        ttk.Combobox(controls, textvariable=port_var, values=ports, state='readonly', width=38).pack(side='left')
        ttk.Combobox(controls, textvariable=channel_var, values=['Keep'] + [str(n) for n in range(1,17)],
                     state='readonly', width=7).pack(side='left', padx=8)
        def assign():
            for item in tree.selection():
                i = int(item)
                channel = None if channel_var.get() == 'Keep' else int(channel_var.get()) - 1
                working[i] = (port_var.get(), channel)
                tree.set(item, 'port', port_var.get())
                tree.set(item, 'channel', channel_var.get())
        ttk.Button(controls, text='Assign selected', command=assign).pack(side='left')
        def apply():
            from midi_routing import validate_routes
            try:
                validate_routes(self.song, working, self.output_name.get())
            except MidiError as exc:
                messagebox.showerror('MIDI routing', str(exc), parent=window)
                return
            self.track_routes = working.copy()
            self.routed_monitor.clear()
            self.status.set(f'MIDI routing configured for {len(working)} tracks')
            window.destroy()
        footer = ttk.Frame(outer)
        footer.pack(fill='x', pady=8)
        ttk.Button(footer, text='Save routing', command=apply).pack(side='left')
        ttk.Button(footer, text='Reset to single output', command=lambda: (self.track_routes.clear(), window.destroy())).pack(side='left', padx=8)
        ttk.Button(footer, text='Cancel', command=window.destroy).pack(side='right')

    def play_midi(self):
        if self.recorder.recording:
            messagebox.showwarning('MIDI playback', 'Finish recording before starting playback.')
            return
        if self.song is None:
            messagebox.showinfo('MIDI playback', 'Open a MIDI file first.')
            return
        if self._paused_tick is not None and not self.player.wait_stopped(1.0):
            messagebox.showwarning('MIDI playback', 'MIDI output is still stopping. Try again.')
            return
        try:
            from transport_ops import playback_region
            start_tick, loop_start, loop_end = playback_region(
                self._paused_tick if self._paused_tick is not None else self.play_start_tick.get(), self.loop_enabled.get(),
                self.loop_start.get(), self.loop_end.get())
            if self.track_routes:
                self.player.play_routed(self.song, self.track_routes, self.output_name.get(),
                    include_sysex=self.send_sysex.get(), start_tick=start_tick,
                    loop_start=loop_start, loop_end=loop_end,
                    metronome=self.metronome_enabled.get(),
                    restore_held_notes=self._paused_tick is not None,
                    enabled_tracks={i for i in range(len(self.song.tracks))
                        if i not in self.muted_tracks and (not self.solo_tracks or i in self.solo_tracks)})
            else:
                self.player.play(self.song, self.output_name.get(), include_sysex=self.send_sysex.get(),
                             start_tick=start_tick, loop_start=loop_start, loop_end=loop_end,
                             metronome=self.metronome_enabled.get(),
                             restore_held_notes=self._paused_tick is not None,
                             enabled_tracks=(None if self._live_track_mix_supported() else
                                             {i for i in range(len(self.song.tracks))
                                              if i not in self.muted_tracks and
                                              (not self.solo_tracks or i in self.solo_tracks)}),
                             enabled_channels=(self._effective_playback_channels()
                                               if self._live_track_mix_supported() else
                                               {c for c in range(16) if c not in self.muted_channels
                                                and (not self.solo_channels or c in self.solo_channels)}))
            self._play_clock = (time.monotonic(), start_tick, loop_start, loop_end)
            self.playhead_tick = start_tick
            self._paused_tick = None
        except MidiError as exc:
            messagebox.showerror('MIDI playback', str(exc))

    def choose_input(self):
        try:
            inputs = available_inputs()
        except MidiError as exc:
            messagebox.showerror('MIDI input', str(exc))
            return
        if not inputs:
            messagebox.showinfo('MIDI input', 'No MIDI input ports found.')
            return
        name = simpledialog.askstring('MIDI input',
                 'Choose a MIDI input name from:\n' + '\n'.join(inputs),
                 initialvalue=self.input_name.get() or inputs[0])
        if name is not None:
            if name not in inputs:
                messagebox.showerror('MIDI input', 'Choose an input from the list.')
            else:
                self.input_name.set(name)
                self.status.set('MIDI input: ' + name)

    def start_recording(self):
        if self.song is None:
            messagebox.showinfo('MIDI recording', 'Open a MIDI file first.')
            return
        if self.player.playing:
            messagebox.showwarning('MIDI recording', 'Stop playback before recording.')
            return
        if self.recorder.recording:
            messagebox.showinfo('MIDI recording', 'Already recording.')
            return
        try:
            bpm = float(self.record_bpm.get())
            latency_ms = float(self.record_latency_ms.get())
            input_channel = (None if self.record_input_channel.get() == 'All'
                             else int(self.record_input_channel.get()) - 1)
            output_channel = (None if self.record_output_channel.get() == 'Keep'
                              else int(self.record_output_channel.get()) - 1)
            tick = int(self.play_start_tick.get())
            if self.record_replace.get() and (not self.record_overdub.get() or not self.punch_enabled.get()):
                raise MidiError("Replace requires Overdub selected and Punch enabled")
            target = self.selected_track() if self.record_overdub.get() else None
            if self.record_overdub.get() and target is None:
                raise MidiError("Select a track for overdub")
            punch_start = int(self.punch_start.get()) if self.punch_enabled.get() else None
            punch_end = int(self.punch_end.get()) if self.punch_enabled.get() else None
            accompaniment = self.record_accompaniment.get()
            monitor = self.record_monitor.get()
            if monitor and accompaniment:
                raise MidiError('MIDI Monitor and accompaniment cannot share an output yet')
            if monitor and not self.output_name.get():
                raise MidiError('Choose a MIDI output for monitoring')
            count_in_bars = int(self.record_count_in.get())
            if count_in_bars and not accompaniment:
                raise MidiError('Count-in requires Play accompaniment')
            if accompaniment and not self.record_follow_tempo.get():
                raise MidiError('Accompaniment requires Follow song tempo')
            if accompaniment and not self.output_name.get():
                raise MidiError('Choose a MIDI output for accompaniment')
            # Both worker threads use the same monotonic epoch. A short lead-in
            # gives the MIDI ports time to open before the first song event.
            from midi_output import count_in_messages
            _, count_in_duration = count_in_messages(self.song, tick, count_in_bars)
            shared_start = time.monotonic() + 0.3 + count_in_duration if accompaniment else None
            self.recorder.start(self.input_name.get(), self.song.division, bpm=bpm,
                                start_tick=tick, punch_start=punch_start, punch_end=punch_end,
                                song=self.song if self.record_follow_tempo.get() else None,
                                start_at=shared_start, latency_ms=latency_ms,
                                input_channel=input_channel, output_channel=output_channel,
                                monitor_port=self.output_name.get() if monitor else None)
            if accompaniment:
                try:
                    enabled = {i for i in range(len(self.song.tracks))
                               if i not in self.muted_tracks and
                               (not self.solo_tracks or i in self.solo_tracks)
                               and i != target}
                    play_kwargs = dict(include_sysex=self.send_sysex.get(),
                                     enabled_tracks=enabled, start_tick=tick,
                                     metronome=self.metronome_enabled.get(),
                                     start_at=shared_start, count_in_bars=count_in_bars)
                    if self.track_routes:
                        self.player.play_routed(self.song, self.track_routes, self.output_name.get(),
                                                **play_kwargs)
                    else:
                        self.player.play(self.song, self.output_name.get(),
                                     include_sysex=self.send_sysex.get(),
                                     enabled_tracks=enabled, start_tick=tick,
                                     enabled_channels={c for c in range(16) if c not in self.muted_channels
                                                       and (not self.solo_channels or c in self.solo_channels)},
                                     metronome=self.metronome_enabled.get(),
                                     start_at=shared_start, count_in_bars=count_in_bars)
                except Exception:
                    self.recorder.finish()
                    raise
            self.playhead_tick = tick
            self._record_with_playback = accompaniment
            self._record_target = target
            self._record_replace = self.record_replace.get()
            self._record_punch_range = (punch_start, punch_end)
            self.status.set(f'Recording MIDI from {self.input_name.get()} at {bpm:g} BPM...')
        except (ValueError, MidiError) as exc:
            messagebox.showerror('MIDI recording', str(exc))

    def finish_recording(self):
        if self.recorder._thread is None:
            messagebox.showinfo('MIDI recording', 'Recording is not active.')
            return
        try:
            if self._record_with_playback:
                self.player.stop()
            track = self.recorder.finish()
            grid = 0 if self.record_quantize.get() == "Off" else int(self.record_quantize.get())
            track = quantize_take_onsets(track, grid, origin=int(self.play_start_tick.get()))
            if not track.events:
                self.status.set('Recording ended: no MIDI events captured.')
                return
            self.snapshot()
            if self._record_target is not None:
                target = self._record_target
                if getattr(self, "_record_replace", False):
                    start, end = self._record_punch_range
                    channels = ({int(self.record_output_channel.get()) - 1}
                                if self.record_output_channel.get() != "Keep" else
                                {e.status & 15 for e in track.events if 0x80 <= e.status <= 0xef})
                    self.song.tracks[target] = replace_take_range_sustain_safe(
                        self.song.tracks[target], track, start, end, channels=channels)
                else:
                    self.song.tracks[target] = merge_take(self.song.tracks[target], track)
                destination = f'existing track {target + 1}'
            else:
                track.events.insert(0, Event(0, 0xff, b'Recorded MIDI', meta_type=3, order=-1))
                self.song.tracks.append(track)
                if self.song.fmt == 0:
                    self.song.fmt = 1  # Multiple tracks require SMF format 1.
                destination = 'a new track'
            self.song.dirty = True
            self.refresh()
            self.status.set(f'Recorded {len(track.events)} events to {destination}.')
        except MidiError as exc:
            messagebox.showerror('MIDI recording', str(exc))
        finally:
            self._record_target = None
            self._record_with_playback = False
            self._record_replace = False

    def pause_midi(self):
        """Pause by silencing MIDI and retaining the tempo-aware cursor.

        Resume restarts output at that cursor, with routed controller chase.
        This intentionally releases sustained notes rather than holding them.
        """
        if self.recorder.recording:
            messagebox.showwarning('MIDI playback', 'Pause is unavailable during recording.')
            return
        if self._paused_tick is not None and not self.player.playing:
            self.play_midi()
            return
        if self.song is None or self._play_clock is None or not self.player.playing:
            return
        from transport_snapshot import cursor_snapshot
        tick = cursor_snapshot(self.song, self._play_clock, time.monotonic())
        self.player.stop()
        self._paused_tick = tick
        self.playhead_tick = tick
        self.play_start_tick.set(str(tick))
        self._play_clock = None
        if hasattr(self, 'sequencer'):
            self.sequencer.set_playhead(tick, follow=True)
        self.status.set('MIDI paused. Press Play or Pause to resume.')

    def stop_midi(self):
        self._paused_tick = None
        if self.recorder.recording:
            self.finish_recording()
            return
        # Snapshot before stopping the worker: otherwise the displayed cursor
        # can lag up to one GUI refresh behind the actual Stop position.
        if getattr(self, 'song', None) is not None and self._play_clock is not None and self.player.playing:
            from transport_snapshot import cursor_snapshot
            self.playhead_tick = cursor_snapshot(self.song, self._play_clock, time.monotonic())
            self.play_start_tick.set(str(self.playhead_tick))
            if hasattr(self, 'sequencer'):
                self.sequencer.set_playhead(self.playhead_tick)
        self.player.stop()
        self._play_clock = None

    def open_file(self):
        if self.recorder.recording:
            messagebox.showwarning('MIDI recording', 'Finish recording before opening another file.')
            return
        if self.player.playing:
            messagebox.showwarning('MIDI playback', 'Stop playback before opening another file.')
            return
        path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid *.midi"), ("All files", "*.*")])
        if not path:
            return
        try:
            song = Song.read(path)
        except (OSError, MidiError) as exc:
            messagebox.showerror("Cannot open MIDI", str(exc))
            return
        if self._offer_recovery(path):
            return
        from clip_project import load_regions
        try:
            load_regions(path, song)
        except MidiError as exc:
            messagebox.showwarning('Clip regions', str(exc))
        self.song, self.path, self.history = song, Path(path), []
        self.redo_history = []
        from multiport_state import load_routing
        try:
            self.track_routes = load_routing(self.path, self.song, self.output_name.get())
        except (MidiError, OSError) as exc:
            self.track_routes = {}
            messagebox.showwarning('MIDI routing', str(exc))
        self.routed_monitor.clear()
        self.muted_tracks.clear()
        self.solo_tracks.clear()
        self.muted_channels.clear()
        self.solo_channels.clear()
        self.refresh()
        self.status.set(f"{self.path.name} | Format {song.fmt} | {len(song.tracks)} tracks | division {song.division}")

    def refresh(self):
        self.sequencer.set_song(self.song)
        self.sequencer.set_mix(self.muted_tracks, self.solo_tracks)
        self.tracks.delete(*self.tracks.get_children())
        self.events.delete(*self.events.get_children())
        if self.song:
            for i, track in enumerate(self.song.tracks):
                self.tracks.insert("", "end", iid=str(i), text=f"{i+1}: {track.name()}", values=(len(track.events),))
            if self.song.tracks:
                self.tracks.selection_set("0")
                self.show_events()

    def batch_event_dialog(self):
        """Move or copy selected Event List rows, with one Undo snapshot."""
        if self.song is None or self.player.playing:
            return
        track = self.selected_track()
        rows = self.events.selection()
        if track is None or not rows:
            messagebox.showinfo("Batch events", "Select one or more Event List rows first.")
            return
        from batch_event_ops import edit_events
        from copy import deepcopy
        dialog = tk.Toplevel(self.root)
        dialog.title("Batch move / copy MIDI events")
        dialog.transient(self.root)
        ttk.Label(dialog, text=f"Selected events: {len(rows)} on track {track + 1}").pack(padx=16, pady=8)
        offset = tk.IntVar(value=0)
        dest = tk.IntVar(value=track + 1)
        ttk.Label(dialog, text="Offset (MIDI ticks):").pack()
        ttk.Spinbox(dialog, from_=-999999, to=999999, textvariable=offset).pack(pady=3)
        ttk.Label(dialog, text="Destination track (1-based):").pack()
        ttk.Spinbox(dialog, from_=1, to=len(self.song.tracks), textvariable=dest).pack(pady=3)
        def apply(duplicate):
            try:
                selections = [(track, int(i)) for i in rows]
                target = dest.get() - 1
                delta = offset.get()
                edit_events(deepcopy(self.song), selections, delta, duplicate, target)
                self.snapshot()
                try:
                    count = edit_events(self.song, selections, delta, duplicate, target)
                except Exception:
                    self.history.pop()
                    raise
            except (MidiError, ValueError, tk.TclError) as exc:
                messagebox.showerror("Batch events", str(exc), parent=dialog)
                return
            self.show_events()
            self.status.set(f"{'Copied' if duplicate else 'Moved'} {count} MIDI events")
            dialog.destroy()
        buttons = ttk.Frame(dialog); buttons.pack(pady=12)
        ttk.Button(buttons, text="Move", command=lambda: apply(False)).pack(side="left", padx=6)
        ttk.Button(buttons, text="Copy", command=lambda: apply(True)).pack(side="left", padx=6)

    def move_selected_track(self, direction):
        """Reorder selected track without changing MIDI events or channels."""
        if self.song is None or self.player.playing or self.recorder.recording:
            return
        source = self.selected_track()
        if source is None or direction not in (-1, 1):
            return
        destination = source + direction
        if not 0 <= destination < len(self.song.tracks):
            return
        from track_order_ops import move_track
        try:
            # Validate the operation on a copy before modifying the active project.
            trial = copy.deepcopy(self.song)
            move_track(trial, source, destination, self.track_routes, self.xws_track_properties)
            self.snapshot()
            self.track_routes, self.xws_track_properties = move_track(
                self.song, source, destination, self.track_routes, self.xws_track_properties)
            self.muted_tracks = {destination if i == source else source if i == destination else i
                                 for i in self.muted_tracks}
            self.solo_tracks = {destination if i == source else source if i == destination else i
                                for i in self.solo_tracks}
        except (MidiError, ValueError) as exc:
            messagebox.showerror("Move track", str(exc))
            return
        self.refresh()
        self.tracks.selection_set(str(destination))
        self.tracks.see(str(destination))
        self.show_events()
        self.status.set(f"Moved track {source + 1} to {destination + 1}")

    def selected_track(self):
        selected = self.tracks.selection()
        return int(selected[0]) if selected else None

    def show_events(self):
        self.sequencer.draw()
        self.events.delete(*self.events.get_children())
        idx = self.selected_track()
        if idx is None or not self.song:
            return
        for i, event in enumerate(self.song.tracks[idx].events):
            self.events.insert("", "end", iid=str(i), values=(
                event.tick, event.channel() or "-", event.label(), event.description()))

    def snapshot(self):
        self.redo_history.clear()
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

    def batch_quantize_dialog(self, all_tracks=False):
        """One undoable operation across selected tracks or the entire song."""
        if self.song is None:
            return
        indices = list(range(len(self.song.tracks))) if all_tracks else [int(i) for i in self.tracks.selection()]
        if not indices:
            self.status.set("Select at least one track first.")
            return
        strength = simpledialog.askinteger("Multi-track Quantize", "Strength (0–100%):",
                                           initialvalue=100, minvalue=0, maxvalue=100, parent=self.root)
        if strength is None:
            return
        try:
            self.snapshot()
            changed = transform_tracks(self.song, indices, denominator=16, strength=strength)
            if not changed:
                self.history.pop()
            self.show_events()
            self.status.set(f"Quantized {changed} notes across {len(indices)} tracks.")
        except MidiError as exc:
            if self.history:
                self.song = self.history.pop()
            messagebox.showerror("Multi-track Quantize", str(exc), parent=self.root)

    def undo(self):
        if self.history and self.song is not None:
            self.redo_history.append(copy.deepcopy(self.song))
            if len(self.redo_history) > 15:
                self.redo_history.pop(0)
            self.song = self.history.pop()
            self.shared_note_selection.clear()
            self.refresh()
            self.notify_midi_editors()
            self.status.set("Undo completed.")

    def redo(self):
        if self.redo_history and self.song is not None:
            self.history.append(copy.deepcopy(self.song))
            if len(self.history) > 15:
                self.history.pop(0)
            self.song = self.redo_history.pop()
            self.shared_note_selection.clear()
            self.refresh()
            self.notify_midi_editors()
            self.status.set("Redo completed.")

    def notify_midi_editors(self, origin=None):
        """Refresh other editor snapshots after a committed MIDI edit."""
        for kind in ("MIDI Mixer", "XG Part Editor"):
            window = self.workspace.windows.get(kind)
            if window is None or window is origin:
                continue
            try:
                if not window.winfo_exists():
                    continue
                if kind == "MIDI Mixer":
                    window.reload()
                else:
                    window.sync_from_song()
            except (MidiError, tk.TclError, ValueError):
                continue

    def save_preferences(self):
        try:
            from xg_mixer_bridge import encode_part_assignments
            save_settings({"midi_output": self.output_name.get(),
                           "window_geometry": self.workspace.geometry,
                           "xg_part_assignments": encode_part_assignments(self.xg_part_assignments)})
        except OSError as exc:
            self.status.set(f"Cannot save MIDI output preference: {exc}")

    def close_app(self):
        self.workspace.close_all()
        self.save_preferences()
        self.player.stop()
        if self.recorder.recording:
            try:
                self.recorder.finish()
            except MidiError:
                pass
        self.root.destroy()

    def focus_editor(self, kind):
        methods = {
            "Piano Roll": self.open_piano_roll,
            "List Editor": self.open_list_editor,
            "Drum Editor": self.open_drum_editor,
            "Staff": self.open_staff_editor,
            "Controller Editor": self.open_controller_editor,
            "Master Track": self.open_master_track,
            "MIDI Mixer": self.open_midi_mixer,
            "XG Part Editor": self.open_xg_editor,
        }
        methods[kind]()

    def open_controller_editor(self):
        track = self.selected_track()
        if self.song is None or track is None:
            messagebox.showinfo("Controller Editor", "Open a MIDI file and select a track first.")
            return
        self.workspace.open("Controller Editor", lambda: ControllerEditor(self, track))

    def open_staff_editor(self):
        track = self.selected_track()
        if self.song is None or track is None:
            messagebox.showinfo("Staff", "Open a MIDI file and select a track first.")
            return
        self.workspace.open("Staff", lambda: StaffEditor(self, track))

    def open_drum_editor(self):
        if self.song is None:
            messagebox.showinfo("Drum Editor", "Open a MIDI file first.")
            return
        track = self.selected_track()
        if track is None:
            messagebox.showinfo("Drum Editor", "Select a track first.")
            return
        self.workspace.open("Drum Editor", lambda: DrumEditor(self, track))

    def open_xg_editor(self):
        self.workspace.open("XG Part Editor", lambda: XGPartEditor(self))

    def open_midi_mixer(self):
        if self.song is None:
            messagebox.showinfo("MIDI Mixer", "Open a MIDI file first.")
            return
        self.workspace.open("MIDI Mixer", lambda: MidiMixer(self))

    def open_master_track(self):
        if self.song is None:
            messagebox.showinfo("Master Track", "Open a MIDI file first.")
            return
        self.workspace.open("Master Track", lambda: MasterTrackEditor(self))

    def open_list_editor(self):
        track = self.selected_track()
        if self.song is None or track is None:
            messagebox.showinfo("List Editor", "Open a MIDI file and select a track first.")
            return
        self.workspace.open("List Editor", lambda: ListEditor(self, track))

    def open_piano_roll(self):
        track = self.selected_track()
        if self.song is None or track is None:
            messagebox.showinfo('Piano Roll', 'Open a MIDI file and select a track first.')
            return
        self.workspace.open("Piano Roll", lambda: PianoRoll(self, track))

    def _project_workspace_state(self):
        """Collect portable window and transport state for project snapshots."""
        from workspace import valid_geometry
        geometry = dict(self.workspace.geometry)
        for kind, window in self.workspace.windows.items():
            if window.winfo_exists() and valid_geometry(window.geometry()):
                geometry[kind] = window.geometry()
        from project_bundle import validate_workspace
        return validate_workspace({
            'geometry': {k: v for k, v in geometry.items() if valid_geometry(v)},
            'open_editors': [k for k, w in self.workspace.windows.items()
                             if w.winfo_exists() and k != 'Staff'],
            'playhead_tick': max(0, int(self.playhead_tick)),
            'loop_start': max(0, int(self.loop_start.get())),
            'loop_end': max(0, int(self.loop_end.get())),
        })

    def _autosave_recovery(self):
        """Periodically save changed MIDI state without touching the source file."""
        try:
            if self.song is not None and not self.recorder.recording:
                from project_recovery import write_recovery, snapshot_fingerprint
                state = self._project_workspace_state()
                fingerprint = snapshot_fingerprint(self.song, self.track_routes,
                                                   self.output_name.get(), state)
                if fingerprint != self._autosave_fingerprint:
                    write_recovery(self.path, self.song, self.track_routes,
                                   self.output_name.get(), state)
                    self._autosave_fingerprint = fingerprint
        except (OSError, MidiError, ValueError) as exc:
            self.status.set(f'Automatic recovery backup failed: {exc}')
        finally:
            try:
                self.root.after(60000, self._autosave_recovery)
            except tk.TclError:
                pass

    def _offer_recovery(self, source):
        from project_recovery import recovery_path, read_recovery
        backup = recovery_path(source)
        from project_recovery import recovery_is_current
        if not recovery_is_current(source):
            return False
        if not messagebox.askyesno('Recover XGW Next',
                'A recovery snapshot exists for this file. Restore it instead of the saved version?'):
            return False
        try:
            song, routes = read_recovery(source)
            from project_bundle import load_project_workspace
            recovered_workspace = load_project_workspace(backup)
        except (OSError, MidiError) as exc:
            messagebox.showerror('Recovery failed', str(exc))
            return False
        self.song, self.path, self.history = song, Path(source), []
        self.redo_history = []
        self.track_routes = routes
        self.xws_track_properties = source_properties
        self._autosave_fingerprint = None
        self.refresh()
        if recovered_workspace:
            self.workspace.close_all()
            self.workspace.geometry.update(recovered_workspace['geometry'])
            self.playhead_tick = recovered_workspace['playhead_tick']
            self.loop_start.set(str(recovered_workspace['loop_start']))
            self.loop_end.set(str(recovered_workspace['loop_end']))
            for kind in recovered_workspace['open_editors']:
                if kind != 'Staff':
                    try:
                        self.focus_editor(kind)
                    except (tk.TclError, MidiError):
                        pass
        self.status.set('Recovered unsaved changes. Save the project to keep them.')
        return True

    def import_legacy_xws(self):
        """Import supported S4WB MIDI events without changing the XWS source."""
        if self.recorder.recording or self.player.playing:
            messagebox.showwarning('XWS import', 'Stop recording and playback first.')
            return
        target = filedialog.askopenfilename(filetypes=[('Yamaha XGworks projects', '*.xws'), ('All files', '*.*')])
        if not target:
            return
        from xws_import import import_xws
        try:
            song = import_xws(target)
        except (OSError, MidiError) as exc:
            messagebox.showerror('XWS import failed', str(exc))
            return
        self.song, self.path, self.history = song, None, []
        from xws_track_properties import extract_track_properties
        self.xws_track_properties = extract_track_properties(Path(target).read_bytes(), len(song.tracks))
        self.redo_history = []
        self.track_routes = {}
        self.routed_monitor.clear()
        self.muted_tracks.clear()
        self.solo_tracks.clear()
        self.muted_channels.clear()
        self.solo_channels.clear()
        self.refresh()
        self.status.set(f'Imported MIDI from {Path(target).name}: {len(song.tracks)} tracks. Save as .xgwn or .mid; XWS unchanged.')
        messagebox.showinfo('XWS MIDI import',
            f'Imported {len(song.tracks)} MIDI tracks.\n'
            'XGworks mixer, clip and window metadata are not imported.\n'
            'Save the result as an XGW project or MIDI file. Original XWS unchanged.')

    def xws_track_channel_report(self):
        """Display source track channel properties without modifying the song."""
        target = filedialog.askopenfilename(filetypes=[('Yamaha XGworks projects', '*.xws'), ('All files', '*.*')])
        if not target:
            return
        from xws_track_channel import format_track_channel_report
        try:
            report = format_track_channel_report(Path(target).read_bytes())
        except (OSError, MidiError, ValueError, IndexError) as exc:
            messagebox.showerror('XWS channel properties', str(exc))
            return
        window = tk.Toplevel(self.root)
        window.title('XWS track channel properties: ' + Path(target).name)
        window.geometry('690x520')
        output = tk.Text(window, wrap='none')
        output.pack(fill='both', expand=True)
        output.insert('1.0', report)
        output.configure(state='disabled')

    def xws_setup_report(self):
        """Inspect observed MIDI settings without assuming proprietary mixer fields."""
        target = filedialog.askopenfilename(filetypes=[('Yamaha XGworks projects', '*.xws'), ('All files', '*.*')])
        if not target:
            return
        from xws_import import import_xws, format_track_setup_report
        try:
            report = format_track_setup_report(import_xws(target))
        except (OSError, MidiError) as exc:
            messagebox.showerror('XWS MIDI setup report', str(exc))
            return
        window = tk.Toplevel(self.root)
        window.title('XWS MIDI setup: ' + Path(target).name)
        window.geometry('850x550')
        viewer = tk.Text(window, wrap='none')
        viewer.pack(fill='both', expand=True)
        viewer.insert('1.0', report)
        viewer.configure(state='disabled')

    def xws_s4wt_report(self):
        """Inspect raw track metadata without guessing mixer parameters."""
        target = filedialog.askopenfilename(filetypes=[('Yamaha XGworks projects', '*.xws'), ('All files', '*.*')])
        if not target:
            return
        from xws_import import format_s4wt_report
        try:
            report = format_s4wt_report(Path(target).read_bytes())
        except (OSError, MidiError) as exc:
            messagebox.showerror('XWS S4WT metadata audit', str(exc))
            return
        window = tk.Toplevel(self.root)
        window.title('XWS S4WT metadata: ' + Path(target).name)
        window.geometry('950x600')
        viewer = tk.Text(window, wrap='none')
        viewer.pack(fill='both', expand=True)
        viewer.insert('1.0', report)
        viewer.configure(state='disabled')

    def xws_compare_s4wt(self):
        """Compare two reference projects without modifying either one."""
        first = filedialog.askopenfilename(title='Reference XWS (before)', filetypes=[('XGworks projects', '*.xws'), ('All files', '*.*')])
        if not first:
            return
        second = filedialog.askopenfilename(title='Modified XWS (after)', filetypes=[('XGworks projects', '*.xws'), ('All files', '*.*')])
        if not second:
            return
        from xws_import import format_s4wt_comparison
        try:
            report = format_s4wt_comparison(Path(first).read_bytes(), Path(second).read_bytes())
        except (OSError, MidiError) as exc:
            messagebox.showerror('XWS comparison', str(exc))
            return
        window = tk.Toplevel(self.root)
        window.title('XWS S4WT comparison')
        window.geometry('950x600')
        viewer = tk.Text(window, wrap='none')
        viewer.pack(fill='both', expand=True)
        viewer.insert('1.0', report)
        viewer.configure(state='disabled')

    def inspect_legacy_xws(self):
        """Read-only format reconnaissance; does not replace the open song."""
        target = filedialog.askopenfilename(filetypes=[('Yamaha XGworks projects', '*.xws'), ('All files', '*.*')])
        if not target:
            return
        from xws_probe import inspect_xws, format_report
        try:
            report = inspect_xws(target)
        except OSError as exc:
            messagebox.showerror('XWS inspection failed', str(exc))
            return
        messagebox.showinfo('XWS inspection (read-only)', format_report(report))
        if report.embedded_midi and messagebox.askyesno(
            'Extract embedded MIDI',
            'A MIDI candidate was found. Try to extract it as a separate .mid file?\n'
            'This does not import the XWS project or modify the source.',
        ):
            from xws_probe import extract_embedded_smf
            candidate = report.embedded_midi[0]
            destination = filedialog.asksaveasfilename(
                defaultextension='.mid', filetypes=[('MIDI files', '*.mid')],
                initialfile=Path(target).stem + '-extracted.mid',
            )
            if destination:
                try:
                    payload = extract_embedded_smf(target, candidate.offset)
                    Path(destination).write_bytes(payload)
                except (OSError, ValueError, MidiError) as exc:
                    messagebox.showerror('MIDI extraction failed', str(exc))
                else:
                    messagebox.showinfo('MIDI extracted', f'Saved {len(payload):,} bytes to {destination}')

    def open_project(self):
        if self.recorder.recording or self.player.playing:
            messagebox.showwarning('XGW Project', 'Stop recording and playback first.')
            return
        target = filedialog.askopenfilename(filetypes=[('XGW Next projects', '*.xgwn')])
        if not target:
            return
        if self._offer_recovery(target):
            return
        from project_bundle import load_project, load_project_workspace, load_project_track_properties
        try:
            song, routes = load_project(target, self.output_name.get())
            workspace_state = load_project_workspace(target)
            source_properties = load_project_track_properties(target, len(song.tracks))
        except (MidiError, OSError) as exc:
            messagebox.showerror('Open project failed', str(exc))
            return
        self.song, self.path, self.history = song, Path(target), []
        self.redo_history = []
        self.track_routes = routes
        self.xws_track_properties = source_properties
        self.routed_monitor.clear()
        self.muted_tracks.clear()
        self.solo_tracks.clear()
        self.muted_channels.clear()
        self.solo_channels.clear()
        self.refresh()
        if workspace_state:
            self.workspace.close_all()
            self.workspace.geometry.update(workspace_state['geometry'])
            self.playhead_tick = workspace_state['playhead_tick']
            self.loop_start.set(str(workspace_state['loop_start']))
            self.loop_end.set(str(workspace_state['loop_end']))
            for kind in workspace_state['open_editors']:
                if kind != 'Staff':
                    try:
                        self.focus_editor(kind)
                    except (tk.TclError, MidiError):
                        pass
        self.status.set(f'Opened XGW project: {target}')

    def save_project(self):
        if self.song is None:
            return
        target = filedialog.asksaveasfilename(defaultextension='.xgwn',
                    filetypes=[('XGW Next projects', '*.xgwn')])
        if not target:
            return
        from project_bundle import save_project
        try:
            state = self._project_workspace_state()
            save_project(target, self.song, self.track_routes, self.output_name.get(), state,
                         xws_track_properties=self.xws_track_properties)
            from project_recovery import discard_recovery
            discard_recovery(self.path)
            self._autosave_fingerprint = None
            self.status.set(f'Saved XGW project: {target}')
        except (MidiError, OSError) as exc:
            messagebox.showerror('Save project failed', str(exc))

    def export_demixed_midi(self):
        """Export independent MIDI channels as separate SMF type-1 tracks."""
        if self.song is None:
            return
        target = filedialog.asksaveasfilename(
            defaultextension='.mid',
            initialfile=(self.path.stem + '_format1.mid') if self.path else 'demixed_format1.mid',
            filetypes=[('MIDI files', '*.mid')])
        if not target:
            return
        try:
            from midi_demix import demix_to_format1
            exported = demix_to_format1(self.song)
            exported.save(target)
            self.status.set(f'Exported format 1 MIDI ({len(exported.tracks)} tracks): {target}')
        except (OSError, MidiError) as exc:
            messagebox.showerror('MIDI export failed', str(exc))

    def save_as(self):
        if not self.song:
            return
        target = filedialog.asksaveasfilename(defaultextension=".mid",
                    initialfile=(self.path.stem + "_edited.mid") if self.path else "edited.mid",
                    filetypes=[("MIDI files", "*.mid")])
        if not target:
            return
        try:
            from midi_demix import demix_to_format1
            midi_export = demix_to_format1(self.song) if self.song.fmt != 2 else self.song
            midi_export.save(target)
            from clip_project import save_regions
            save_regions(target, self.song)
            from multiport_state import save_routing
            save_routing(target, self.song, self.track_routes, self.output_name.get())
            from project_recovery import discard_recovery
            discard_recovery(self.path)
            self.path = Path(target)
            self._autosave_fingerprint = None
            self.status.set(f"Saved: {target}")
        except (OSError, MidiError) as exc:
            messagebox.showerror("Save failed", str(exc))

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
