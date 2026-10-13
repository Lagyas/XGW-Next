"""XGW Next prototype: track/event inspector and basic MIDI editor."""
import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from midi import Song, MidiError
from piano_roll import PianoRoll
from midi_output import MidiPlayer, available_outputs
from xg_part_editor import XGPartEditor
from drum_editor import DrumEditor
from sequencer_view import SequencerView
from track_voice import used_channels, channel_voice_at
from xg_voices import voice_label, matching_voices
from voice_setup import insert_voice_setup
from clip_ops import edit_clip

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
        self.path = None
        self.history = []
        self.muted_tracks = set()
        self.solo_tracks = set()
        self.player = MidiPlayer(on_state=self.playback_state, on_error=self.playback_error)
        self.output_name = tk.StringVar(value='')
        self.send_sysex = tk.BooleanVar(value=False)
        self.theme = tk.StringVar(value="Classic")
        self.make_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.apply_theme()

    def make_ui(self):
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Open MIDI...", command=self.open_file)
        file_menu.add_command(label="Save As...", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close_app)
        menu.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(menu, tearoff=0)
        edit_menu.add_command(label="Edit selected event...", command=self.edit_event)
        edit_menu.add_command(label="Transpose selected track...", command=self.transpose)
        edit_menu.add_command(label="Undo", command=self.undo)
        view_menu = tk.Menu(menu, tearoff=0)
        view_menu.add_command(label="Piano Roll (selected track)...", command=self.open_piano_roll)
        view_menu.add_command(label="Drum Editor (selected track)...", command=self.open_drum_editor)
        view_menu.add_command(label="Yamaha XG Part Editor...", command=self.open_xg_editor)
        menu.add_cascade(label="View", menu=view_menu)
        menu.add_cascade(label="Edit", menu=edit_menu)
        theme_menu = tk.Menu(menu, tearoff=0)
        for name in THEMES:
            theme_menu.add_radiobutton(label=name, variable=self.theme, value=name, command=self.apply_theme)
        menu.add_cascade(label="Appearance", menu=theme_menu)
        transport_menu = tk.Menu(menu, tearoff=0)
        transport_menu.add_command(label='Choose MIDI output...', command=self.choose_output)
        transport_menu.add_checkbutton(label='Send complete SysEx (advanced)', variable=self.send_sysex)
        transport_menu.add_command(label='Play', command=self.play_midi)
        transport_menu.add_command(label='Stop', command=self.stop_midi)
        menu.add_cascade(label='Transport', menu=transport_menu)
        self.root.config(menu=menu)

        transport_bar = ttk.Frame(self.root)
        transport_bar.pack(fill=tk.X, padx=8, pady=(6, 0))
        ttk.Button(transport_bar, text="▶ Play", command=self.play_midi).pack(side="left", padx=3)
        ttk.Button(transport_bar, text="■ Stop", command=self.stop_midi).pack(side="left", padx=3)
        ttk.Button(transport_bar, text="Open MIDI...", command=self.open_file).pack(side="left", padx=10)
        ttk.Button(transport_bar, text="Save As...", command=self.save_as).pack(side="left", padx=3)
        ttk.Button(transport_bar, text="MIDI output...", command=self.choose_output).pack(side="left", padx=10)
        self.sequencer = SequencerView(self.root, on_track=self.select_sequencer_track, on_open=self.open_sequencer_track, on_toggle=self.toggle_track_state, on_instrument=self.edit_track_voice, on_clip=self.edit_sequencer_clip, on_drag=self.drag_sequencer_clip)
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

    def drag_sequencer_clip(self, track_index, clip_index, target_track, delta, duplicate):
        if self.song is None or self.player.playing:
            messagebox.showwarning("MIDI clip", "Stop playback before editing.")
            return
        try:
            self.snapshot()
            try:
                count = edit_clip(self.song, track_index, clip_index, delta, duplicate,
                                  destination_track=target_track)
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
        self.status.set(f"{action} {count} notes to track {target_track + 1}; Save As to save.")

    def edit_sequencer_clip(self, track_index, clip_index):
        if self.player.playing:
            messagebox.showwarning("MIDI clip", "Stop playback before editing.")
            return
        if self.song is None:
            return
        self.select_sequencer_track(track_index)
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Track {track_index+1} / Clip {clip_index+1}")
        dialog.geometry("420x240")
        dialog.transient(self.root)
        ttk.Label(dialog, text="Move or duplicate MIDI notes across tracks and beats."
                  ).pack(pady=(12, 6))
        ttk.Label(dialog, text="Controllers, SysEx and tempo are not moved."
                  ).pack(pady=2)
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
        actions = ttk.Frame(dialog)
        actions.pack(pady=5)
        def apply(duplicate):
            try:
                delta = beats.get() * self.song.division
                target = destination.get() - 1
                if delta == 0 and target == track_index:
                    raise MidiError("Choose another track or a non-zero beat offset")
                if not 0 <= target < len(self.song.tracks):
                    raise MidiError("Destination track is out of range")
                self.snapshot()
                try:
                    count = edit_clip(self.song, track_index, clip_index, delta, duplicate,
                                      destination_track=target)
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

    def toggle_track_state(self, index, kind):
        if self.player.playing:
            messagebox.showinfo("Track controls", "Stop playback before changing Mute or Solo.")
            return
        if self.song is None or not 0 <= index < len(self.song.tracks):
            return
        target = self.muted_tracks if kind == "mute" else self.solo_tracks
        if index in target:
            target.remove(index)
        else:
            target.add(index)
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
            self.status.set("MIDI output: " + selection.get())
            chooser.destroy()
        buttons = ttk.Frame(chooser)
        buttons.pack(fill="x", padx=12, pady=10)
        ttk.Button(buttons, text="Refresh MIDI ports", command=refresh).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Use this output", command=apply).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=chooser.destroy).pack(side="right")
        refresh()

    def play_midi(self):
        if self.song is None:
            messagebox.showinfo('MIDI playback', 'Open a MIDI file first.')
            return
        try:
            self.player.play(self.song, self.output_name.get(), include_sysex=self.send_sysex.get(),
                             enabled_tracks={i for i in range(len(self.song.tracks))
                                             if i not in self.muted_tracks and
                                             (not self.solo_tracks or i in self.solo_tracks)})
        except MidiError as exc:
            messagebox.showerror('MIDI playback', str(exc))

    def stop_midi(self):
        self.player.stop()

    def open_file(self):
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
        self.song, self.path, self.history = song, Path(path), []
        self.muted_tracks.clear()
        self.solo_tracks.clear()
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

    def close_app(self):
        self.player.stop()
        self.root.destroy()

    def open_drum_editor(self):
        if self.song is None:
            messagebox.showinfo("Drum Editor", "Open a MIDI file first.")
            return
        track = self.selected_track()
        if track is None:
            messagebox.showinfo("Drum Editor", "Select a track first.")
            return
        DrumEditor(self, track)

    def open_xg_editor(self):
        XGPartEditor(self)

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
