"""Experimental Yamaha XG Part Editor for XGW Next.

Changes are sent only after explicit confirmation and an output selection.
The UI displays 1-based program numbers; XG messages use 0-based values.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from midi import MidiError
from xg_parts import XGParts, PART_FIELDS, parts_from_song
from xg_mixer_bridge import combined_part_values, write_xg_part_changes, FIELD_TO_MIXER, channel_for_part
from xg_effects import XGEffects, EFFECT_TYPE_ADDRESSES, effects_from_song, write_effect_types_to_song, inspect_effect_parameter_changes, format_effect_parameter_row, describe_effect_parameter, write_effect_parameter_to_song, effect_parameter_message, effect_parameters_at_tick
from xg_snapshot_apply import apply_snapshot_parameter, apply_snapshot_batch
from xg_effect_catalog import effect_type_name, effect_type_choices
from xg_effect_filter import EFFECT_FILTERS, filter_effect_rows
from xg_effect_delivery import resolve_effect_port, deliver_effect_messages
from xg_voices import voice_label, matching_voices
from xg_reference_browser import MODELS, load_voice_catalog, load_effect_catalog, find_voice, search_voices
from voice_setup import insert_voice_setup
from track_voice import channel_voice_at, used_channels

LABELS = {
    "bank_msb": "Bank MSB", "bank_lsb": "Bank LSB",
    "program": "Program (0–127)", "volume": "Volume",
    "pan": "Pan (64=center)", "reverb_send": "Reverb send",
    "chorus_send": "Chorus send",
    "variation_send": "Variation send",
}

class XGPartEditor(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.reference_archive = None
        self.reference_model = "MU1000"
        self.reference_voices = None
        self.model = XGParts()
        self.effects = XGEffects()
        self.title("Yamaha XG — Part Editor (experimental)")
        self.geometry("550x560")
        self.part = tk.IntVar(value=1)
        self.device = tk.IntVar(value=0)
        self.vars = {name: tk.IntVar(value=getattr(self.model.parts[0], name))
                     for name in PART_FIELDS}
        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=12)
        ttk.Label(top, text="Part:").pack(side="left")
        selector = ttk.Spinbox(top, from_=1, to=16, width=5,
                               textvariable=self.part, command=self.load_part)
        selector.pack(side="left", padx=8)
        selector.bind("<Return>", lambda _: self.load_part())
        ttk.Label(top, text="XG device:").pack(side="left", padx=(18, 4))
        ttk.Spinbox(top, from_=0, to=15, width=5,
                    textvariable=self.device).pack(side="left")
        self.controls = ttk.Frame(self)
        self.controls.pack(fill="both", expand=True, padx=12)
        for row, name in enumerate(PART_FIELDS):
            ttk.Label(self.controls, text=LABELS[name]).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Spinbox(self.controls, from_=0, to=127, width=9,
                        textvariable=self.vars[name]).grid(row=row, column=1, padx=12)
        self.voice_text = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.voice_text).pack(pady=3)
        ttk.Button(self, text="Browse instrument names...", command=self.browse_voices).pack(pady=4)
        ttk.Button(self, text="Load Yamaha XGworks 4 reference ZIP...", command=self.load_reference).pack(pady=3)
        for key in ("bank_msb", "bank_lsb", "program"):
            self.vars[key].trace_add("write", lambda *_: self.update_voice_label())
        self.update_voice_label()
        ttk.Button(self, text="Read XG SysEx from song...",
                   command=self.read_xg_sysex).pack(pady=4)
        ttk.Button(self, text="Read voice from selected MIDI track...",
                   command=self.read_from_song).pack(pady=4)
        ttk.Button(self, text="Insert bank/program into selected MIDI track",
                   command=self.insert_into_song).pack(pady=4)
        ttk.Button(self, text="Read current Mixer CC / XG Part values...",
                   command=self.read_combined).pack(pady=4)
        ttk.Button(self, text="Write changed Part settings to MIDI song...",
                   command=self.write_part_to_song).pack(pady=4)
        ttk.Button(self, text="Send Part settings to MIDI output",
                   command=self.send).pack(pady=12)
        ttk.Button(self, text="System effects (Reverb / Chorus / Variation)...",
                   command=self.open_effects).pack(pady=4)
        ttk.Label(self, text="Sends Yamaha XG SysEx to the selected output.\n"
                            "Check the device and channel routing first.",
                  justify="center").pack()

    def update_voice_label(self):
        try:
            msb = self.vars["bank_msb"].get()
            lsb = self.vars["bank_lsb"].get()
            program = self.vars["program"].get()
            reference_name = find_voice(self.reference_voices or [], msb, lsb, program)
            self.voice_text.set("Voice: " + (reference_name or voice_label(msb, lsb, program)))
        except (ValueError, tk.TclError):
            self.voice_text.set("Voice: invalid bank/program")

    def load_reference(self):
        path = filedialog.askopenfilename(parent=self, title="Select original XGworks 4 ZIP",
                                          filetypes=[("ZIP archives", "*.zip"), ("All files", "*.*")])
        if not path:
            return
        model = simpledialog.askstring("Yamaha model", "Voice model (" + ", ".join(MODELS) + "):",
                                       initialvalue=self.reference_model, parent=self)
        if model is None:
            return
        model = model.strip().upper()
        try:
            voices = load_voice_catalog(path, model)
        except (OSError, ValueError, KeyError, UnicodeError) as exc:
            messagebox.showerror("XGworks reference", str(exc), parent=self)
            return
        self.reference_archive = path
        self.reference_model = model
        self.reference_voices = voices
        self.update_voice_label()
        messagebox.showinfo("XGworks reference", f"Loaded {len(voices)} voices for {model}.\n"
                            "Reference data stays in your original ZIP.", parent=self)

    def browse_voices(self):
        picker = tk.Toplevel(self)
        picker.title("Voice browser — " + (self.reference_model + " original XGworks" if self.reference_voices is not None else "curated GM/XG names"))
        picker.geometry("580x460")
        search = tk.StringVar()
        ttk.Label(picker, text="Search instrument names:").pack(anchor="w", padx=10, pady=(10, 0))
        ttk.Entry(picker, textvariable=search).pack(fill="x", padx=10)
        frame = ttk.Frame(picker)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        items = tk.Listbox(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=items.yview)
        items.configure(yscrollcommand=scrollbar.set)
        items.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        records = []
        def refresh(*_):
            records[:] = (search_voices(self.reference_voices, search.get())
                          if self.reference_voices is not None else matching_voices(search.get()))
            items.delete(0, "end")
            for msb, lsb, program, name in records:
                items.insert("end", f"{program+1:03d}  MSB {msb:03d} / LSB {lsb:03d}  {name}")
        search.trace_add("write", refresh)
        refresh()
        def choose(_=None):
            selected = items.curselection()
            if not selected:
                return
            msb, lsb, program, _ = records[selected[0]]
            self.vars["bank_msb"].set(msb)
            self.vars["bank_lsb"].set(lsb)
            self.vars["program"].set(program)
            picker.destroy()
        items.bind("<Double-Button-1>", choose)
        ttk.Button(picker, text="Use selected voice", command=choose).pack(pady=(0, 10))

    def load_part(self):
        try:
            index = int(self.part.get()) - 1
            if not 0 <= index < 16:
                raise ValueError()
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid Part", "Part must be 1–16.", parent=self)
            return
        part = self.model.parts[index]
        for name in PART_FIELDS:
            self.vars[name].set(getattr(part, name))

    def read_xg_sysex(self):
        if self.app.song is None:
            messagebox.showinfo("Read XG SysEx", "Open a MIDI song first.", parent=self)
            return
        tick = simpledialog.askinteger(
            "Position", "Read XG Part settings through tick (0 = start):",
            initialvalue=0, minvalue=0, parent=self)
        if tick is None:
            return
        try:
            model, recognized = parts_from_song(self.app.song, through_tick=tick)
            if not recognized:
                messagebox.showinfo("Read XG SysEx",
                    "No supported Yamaha XG Part parameter messages found up to this position.",
                    parent=self)
                return
            self.model = model
            self.load_part()
            messagebox.showinfo("Read XG SysEx",
                f"Loaded {recognized} supported XG Part parameter messages. "
                "Unknown parameters and other SysEx were ignored.", parent=self)
        except MidiError as exc:
            messagebox.showerror("Read XG SysEx", str(exc), parent=self)

    def read_from_song(self):
        if self.app.song is None or self.app.selected_track() is None:
            messagebox.showinfo("Read voice", "Open a MIDI file and select a track first.", parent=self)
            return
        track = self.app.selected_track()
        channels = used_channels(self.app.song, track)
        if not channels:
            messagebox.showinfo("Read voice", "No channel MIDI events in selected track.", parent=self)
            return
        channel = simpledialog.askinteger("MIDI channel",
            "Read MIDI channel (available: " + ", ".join(map(str, channels)) + "):",
            initialvalue=channels[0], minvalue=1, maxvalue=16, parent=self)
        if channel is None:
            return
        if channel not in channels:
            messagebox.showerror("Read voice", "Selected channel is not used in this track.", parent=self)
            return
        tick = simpledialog.askinteger("Position", "Read setup at tick:",
                                      initialvalue=0, minvalue=0, parent=self)
        if tick is None:
            return
        voice = channel_voice_at(self.app.song, track, channel, tick)
        if not voice.has_program_change:
            messagebox.showinfo("Read voice",
                "No Program Change up to this tick; the track has no confirmed voice selection.",
                parent=self)
            return
        for key, value in (("bank_msb", voice.msb), ("bank_lsb", voice.lsb),
                           ("program", voice.program)):
            self.vars[key].set(value)
        self.update_voice_label()

    def insert_into_song(self):
        if self.app.song is None or self.app.selected_track() is None:
            messagebox.showinfo("Insert voice", "Open a MIDI song and select a track first.", parent=self)
            return
        channel = simpledialog.askinteger("MIDI channel", "Insert bank/program on MIDI channel (1–16):",
                                          initialvalue=1, minvalue=1, maxvalue=16, parent=self)
        if channel is None:
            return
        try:
            values = [self.vars[name].get() for name in ("bank_msb", "bank_lsb", "program")]
            if any(not 0 <= value <= 127 for value in values):
                raise MidiError("Bank and program must be 0–127")
            track = self.app.selected_track()
            if not messagebox.askyesno("Insert voice", "Add three MIDI messages at tick 0 to the selected track?\\n"
                                       "Existing bank/program events will be preserved.", parent=self):
                return
            self.app.snapshot()
            insert_voice_setup(self.app.song, track, channel, *values)
            self.app.show_events()
            self.app.status.set("Inserted MIDI bank/program messages — use Save As.")
            messagebox.showinfo("Insert voice", "Bank MSB, Bank LSB and Program Change inserted.", parent=self)
        except (ValueError, tk.TclError, MidiError) as exc:
            if self.app.history:
                self.app.song = self.app.history.pop()
                self.app.refresh()
            messagebox.showerror("Insert voice", str(exc), parent=self)

    def _mapped_channel(self, part, device):
        mapping = getattr(self.app, "xg_part_assignments", None)
        if mapping is None:
            return part
        return channel_for_part(mapping, part, device)

    def sync_from_song(self):
        """Silent cross-editor refresh, without modal prompts or MIDI writes."""
        if self.app.song is None:
            return
        part, device = self.part.get(), self.device.get()
        tick = max(0, int(getattr(self.app, "playhead_tick", 0)))
        channel = self._mapped_channel(part, device)
        if channel is None:
            return  # Ambiguous or unmapped Part: do not show another channel's CC.
        values, _ = combined_part_values(self.app.song, part, channel, tick, device)
        for field, mixer_name in FIELD_TO_MIXER.items():
            self.vars[field].set(values[mixer_name])
        self.update_voice_label()

    def read_combined(self):
        if self.app.song is None:
            messagebox.showinfo("XG / Mixer", "Open a MIDI song first.", parent=self)
            return
        try:
            part = self.part.get()
            tick = simpledialog.askinteger("XG / Mixer", "Read values through tick:",
                                           initialvalue=0, minvalue=0, parent=self)
            if tick is None:
                return
            channel = self._mapped_channel(part, self.device.get())
            if channel is None:
                raise MidiError("XG Part/device has no unique mapped MIDI channel")
            values, sources = combined_part_values(self.app.song, part, channel, tick, self.device.get())
            for field, mixer_name in FIELD_TO_MIXER.items():
                self.vars[field].set(values[mixer_name])
            self.update_voice_label()
            messagebox.showinfo("XG / Mixer", "Read Part " + str(part) + " from MIDI CC / XG SysEx.\n" +
                                ", ".join(f"{name}: {sources[name]}" for name in values), parent=self)
        except (MidiError, tk.TclError) as exc:
            messagebox.showerror("XG / Mixer", str(exc), parent=self)

    def write_part_to_song(self):
        if self.app.song is None or self.app.selected_track() is None:
            messagebox.showinfo("XG Part", "Open a song and select a track first.", parent=self)
            return
        if self.app.player.playing:
            messagebox.showwarning("XG Part", "Stop playback before editing.", parent=self)
            return
        tick = simpledialog.askinteger("XG Part", "Write at tick:",
                                       initialvalue=0, minvalue=0, parent=self)
        if tick is None:
            return
        try:
            changes = {name: variable.get() for name, variable in self.vars.items()}
            from copy import deepcopy
            write_xg_part_changes(deepcopy(self.app.song), self.app.selected_track(),
                                  self.part.get(), changes, tick, self.device.get())
            if not messagebox.askyesno("Confirm XG edit",
                    f"Write {len(changes)} XG Part parameters to selected track at tick {tick}?\n"
                    "Matching messages at this tick will be replaced.", parent=self):
                return
            self.app.snapshot()
            try:
                count = write_xg_part_changes(self.app.song, self.app.selected_track(),
                                               self.part.get(), changes, tick, self.device.get())
            except Exception:
                self.app.song = self.app.history.pop()
                raise
            self.app.show_events()
            self.app.notify_midi_editors(origin=self)
            self.app.status.set(f"Wrote {count} XG Part parameters — Save As to save.")
        except (MidiError, tk.TclError) as exc:
            messagebox.showerror("XG Part", str(exc), parent=self)

    def send(self):
        # Respect the physical output selected for the active MIDI track.
        track_index = self.app.selected_track()
        port_name = (self.app.track_routes.get(track_index, (self.app.output_name.get(), None))[0]
                     if self.app.track_routes else self.app.output_name.get())
        if not port_name:
            messagebox.showerror("MIDI output", "Select a MIDI output / track route first.", parent=self)
            return
        if self.app.player.playing and not self.app.track_routes:
            messagebox.showwarning("MIDI output", "Stop single-port playback before sending Part settings.", parent=self)
            return
        try:
            index = int(self.part.get()) - 1
            changes = {name: int(var.get()) for name, var in self.vars.items()}
            for name, value in changes.items():
                if not 0 <= value <= 127:
                    raise MidiError(f"{name}: value must be 0–127")
            if not 0 <= index < 16:
                raise MidiError("Part must be 1–16")
            device = int(self.device.get())
            if not 0 <= device <= 15:
                raise MidiError("XG device must be 0–15")
            for name, value in changes.items():
                self.model.set(index, name, value)
        except (ValueError, tk.TclError, MidiError) as exc:
            messagebox.showerror("Invalid parameter", str(exc), parent=self)
            return
        if not messagebox.askyesno("Send XG settings",
                                   f"Send {len(changes)} XG parameter messages to\n{port_name}?",
                                   parent=self):
            return
        try:
            messages = [self.model.message(index, name, device=device) for name in PART_FIELDS]
            if self.app.player.playing:
                # Do not open a port already owned by the playback thread.
                for raw in messages:
                    if not self.app.player.send_routed_sysex(port_name, raw):
                        raise MidiError("Routed MIDI output is not active")
                messagebox.showinfo("XG Part Editor", "Parameter messages queued for MIDI output.", parent=self)
            else:
                import mido
                with mido.open_output(port_name) as output:
                    for raw in messages:
                        output.send(mido.Message("sysex", data=list(raw[1:-1])))
                messagebox.showinfo("XG Part Editor", "Parameter messages sent.", parent=self)
        except Exception as exc:
            messagebox.showerror("MIDI output failed", str(exc), parent=self)

    def open_effects(self):
        """Open a separate effect-type editor; sending always needs confirmation."""
        window = tk.Toplevel(self)
        window.title("Yamaha XG — System Effect Types (experimental)")
        window.geometry("730x350")
        ttk.Label(window, text="Effect Type (MSB / LSB) — Yamaha XG native SysEx").pack(pady=10)
        values = {}
        frame = ttk.Frame(window)
        frame.pack(padx=12, pady=8)
        for row, effect in enumerate(EFFECT_TYPE_ADDRESSES):
            msb, lsb = self.effects.types[effect]
            a, b = tk.IntVar(value=msb), tk.IntVar(value=lsb)
            values[effect] = (a, b)
            ttk.Label(frame, text=effect.title()).grid(row=row, column=0, sticky="w", pady=8)
            ttk.Spinbox(frame, from_=0, to=127, textvariable=a, width=7).grid(row=row, column=1, padx=8)
            ttk.Spinbox(frame, from_=0, to=127, textvariable=b, width=7).grid(row=row, column=2, padx=8)
            label = tk.StringVar()
            def update_label(*_, effect=effect, a=a, b=b, label=label):
                try:
                    label.set(effect_type_name(effect, a.get(), b.get()))
                except (ValueError, tk.TclError):
                    label.set("Invalid MSB / LSB")
            a.trace_add("write", update_label)
            b.trace_add("write", update_label)
            update_label()
            ttk.Label(frame, textvariable=label, width=27).grid(row=row, column=3, padx=8, sticky="w")
            choices = effect_type_choices(effect)
            if self.reference_archive:
                try:
                    original = load_effect_catalog(self.reference_archive, effect.upper())
                    if original:
                        choices = original
                except (OSError, ValueError, KeyError, UnicodeError):
                    pass  # Keep the curated fallback for unsupported/missing menus.
            choice_labels = [f"{name} ({msb}, {lsb})" for msb, lsb, name in choices]
            choice = ttk.Combobox(frame, values=choice_labels, state="readonly", width=22)
            choice.grid(row=row, column=4, padx=6)
            def choose_preset(_event, a=a, b=b, choice=choice, choices=choices):
                index = choice.current()
                if index >= 0:
                    a.set(choices[index][0])
                    b.set(choices[index][1])
            choice.bind("<<ComboboxSelected>>", choose_preset)

        def inspect_parameters():
            """Inspect and edit effect SysEx data from the current MIDI song."""
            if self.app.song is None:
                messagebox.showinfo("XG parameters", "Open a MIDI song first.", parent=window)
                return
            try:
                device = self.device.get()
                rows = inspect_effect_parameter_changes(self.app.song, device=device)
            except (ValueError, tk.TclError, MidiError) as exc:
                messagebox.showerror("XG parameters", str(exc), parent=window)
                return
            inspector = tk.Toplevel(window)
            inspector.title(f"XG Effect Parameters — Device {device}")
            inspector.geometry("840x420")
            ttk.Label(inspector, text="Yamaha XG effect parameters — select a row to edit (changes require confirmation)").pack(
                anchor="w", padx=10, pady=8)
            filter_bar = ttk.Frame(inspector)
            filter_bar.pack(fill="x", padx=10, pady=(0, 4))
            ttk.Label(filter_bar, text="Show effect:").pack(side="left")
            selected_effect = tk.StringVar(value="All")
            effect_filter = ttk.Combobox(filter_bar, textvariable=selected_effect,
                                         values=EFFECT_FILTERS, state="readonly", width=14)
            effect_filter.pack(side="left", padx=8)
            columns = ("Tick", "Track", "Effect", "Parameter", "Address", "Data")
            table_frame = ttk.Frame(inspector)
            table_frame.pack(fill="both", expand=True, padx=10, pady=6)
            tree = ttk.Treeview(table_frame, columns=columns, show="headings")
            for column in columns:
                tree.heading(column, text=column)
                tree.column(column, width=180 if column == "Parameter" else 110, stretch=True)
            scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            tree.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            # Tree item IDs always index the complete row collection, even when
            # a filter hides some rows. This prevents editing the wrong SysEx.
            def render_rows():
                tree.delete(*tree.get_children())
                visible = filter_effect_rows(rows, selected_effect.get())
                visible_ids = {id(row) for row in visible}
                for index, row in enumerate(rows):
                    if id(row) in visible_ids:
                        tree.insert("", "end", iid=str(index),
                                    values=(*format_effect_parameter_row(row)[:3], describe_effect_parameter(row), *format_effect_parameter_row(row)[4:]))

            effect_filter.bind("<<ComboboxSelected>>", lambda _event: render_rows())
            render_rows()

            def edit_selected_parameter():
                selected = tree.selection()
                if not selected:
                    messagebox.showinfo("XG parameters", "Select a parameter row first.", parent=inspector)
                    return
                tick, track_index, effect, address, original = rows[int(selected[0])]
                raw = simpledialog.askstring(
                    "Edit XG parameter", "New hexadecimal bytes (00–7F, space separated):",
                    initialvalue=" ".join(f"{value:02X}" for value in original), parent=inspector)
                if raw is None:
                    return
                try:
                    tokens = raw.split()
                    if not tokens or any(len(token) != 2 or any(ch not in '0123456789abcdefABCDEF' for ch in token)
                                         for token in tokens):
                        raise ValueError("Enter space-separated two-digit hexadecimal bytes.")
                    values = bytes(int(token, 16) for token in tokens)
                    if any(value > 127 for value in values):
                        raise ValueError("Yamaha XG SysEx data bytes must be 00–7F.")
                    if not messagebox.askyesno("Confirm XG parameter edit",
                                               f"Replace {effect} parameter at tick {tick}, track {track_index + 1}, "
                                               f"device {device}?\nAddress: {' '.join(f'{v:02X}' for v in address)}\n"
                                               f"Old: {original.hex(' ').upper()}\nNew: {values.hex(' ').upper()}",
                                               parent=inspector):
                        return
                    self.app.snapshot()
                    try:
                        write_effect_parameter_to_song(self.app.song, effect,
                            address[2] - EFFECT_TYPE_ADDRESSES[effect][2], values, tick,
                            track_index=track_index, device=device, replace=True)
                    except Exception:
                        self.app.song = self.app.history.pop()
                        raise
                    rows[int(selected[0])] = (tick, track_index, effect, address, values)
                    render_rows()
                    if tree.exists(selected[0]):
                        tree.selection_set(selected[0])
                        tree.see(selected[0])
                    if hasattr(self.app, "refresh"):
                        self.app.refresh()
                    self.app.notify_midi_editors(origin=self)
                except (ValueError, MidiError) as exc:
                    messagebox.showerror("XG parameters", str(exc), parent=inspector)

            def send_selected_parameter():
                selected = tree.selection()
                if not selected:
                    messagebox.showinfo("XG parameters", "Select a parameter row first.", parent=inspector)
                    return
                tick, track_index, effect, address, values = rows[int(selected[0])]
                try:
                    port = resolve_effect_port(self.app, track_index)
                except MidiError as exc:
                    messagebox.showerror("MIDI output", str(exc), parent=inspector)
                    return
                try:
                    wire = effect_parameter_message(effect,
                        address[2] - EFFECT_TYPE_ADDRESSES[effect][2], values, device)
                except MidiError as exc:
                    messagebox.showerror("XG parameters", str(exc), parent=inspector)
                    return
                if not messagebox.askyesno("Send XG parameter",
                        f"Send {effect} parameter to {port}?\n"
                        f"Device: {device}  Address: {bytes(address).hex(' ').upper()}\n"
                        f"Data: {values.hex(' ').upper()}\n\n"
                        "This immediately changes the receiving MIDI device.", parent=inspector):
                    return
                try:
                    deliver_effect_messages(self.app, track_index, [wire])
                except Exception as exc:
                    messagebox.showerror("MIDI output failed", str(exc), parent=inspector)

            def show_snapshot():
                tick = simpledialog.askinteger(
                    "XG snapshot", "Read effect parameters through tick:",
                    initialvalue=0, minvalue=0, parent=inspector)
                if tick is None:
                    return
                try:
                    snapshot = effect_parameters_at_tick(self.app.song, tick, device=device)
                except MidiError as exc:
                    messagebox.showerror("XG snapshot", str(exc), parent=inspector)
                    return
                viewer = tk.Toplevel(inspector)
                viewer.title(f"XG effects at tick {tick} — device {device}")
                viewer.geometry("640x380")
                ttk.Label(viewer, text="Read-only effective SysEx values (not hardware state)").pack(
                    anchor="w", padx=10, pady=8)
                cols = ("Effect", "Offset", "Value")
                snapshot_tree = ttk.Treeview(viewer, columns=cols, show="headings")
                for column in cols:
                    snapshot_tree.heading(column, text=column)
                snapshot_tree.pack(fill="both", expand=True, padx=10, pady=8)
                keys = sorted(snapshot)
                for (effect, offset), data in sorted(snapshot.items()):
                    snapshot_tree.insert("", "end", values=(
                        effect.title(), ("Effect Type — " + effect_type_name(effect, data[0], data[1])
                                         if offset == 0 and len(data) == 2 else f"Parameter +{offset:02X}"),
                        data.hex(" ").upper()))
                ttk.Label(viewer, text=f"{len(snapshot)} effective parameters; MIDI song unchanged.").pack(
                    anchor="w", padx=10, pady=6)

                def insert_snapshot_value():
                    selected = snapshot_tree.selection()
                    if not selected:
                        messagebox.showinfo("XG snapshot", "Select a parameter first.", parent=viewer)
                        return
                    index = snapshot_tree.index(selected[0])
                    effect, offset = keys[index]
                    track_index = simpledialog.askinteger("XG destination", "Destination track (1-based):",
                                                          initialvalue=1, minvalue=1,
                                                          maxvalue=len(self.app.song.tracks), parent=viewer)
                    if track_index is None:
                        return
                    if not messagebox.askyesno("Insert XG SysEx",
                            f"Insert {effect} +{offset:02X} at tick {tick}, track {track_index}?\n"
                            "This adds a MIDI SysEx event to the song.", parent=viewer):
                        return
                    try:
                        self.app.snapshot()
                        try:
                            apply_snapshot_parameter(self.app.song, snapshot, effect, offset, tick,
                                                     track_index=track_index - 1, device=device)
                        except Exception:
                            self.app.song = self.app.history.pop()
                            raise
                        if hasattr(self.app, "refresh"):
                            self.app.refresh()
                        self.app.notify_midi_editors(origin=self)
                    except (MidiError, ValueError) as exc:
                        messagebox.showerror("XG snapshot", str(exc), parent=viewer)

                def edit_selected_value():
                    selected = snapshot_tree.selection()
                    if len(selected) != 1:
                        messagebox.showinfo("XG snapshot", "Select one parameter to edit.", parent=viewer)
                        return
                    key = keys[snapshot_tree.index(selected[0])]
                    value = simpledialog.askstring("Edit XG bytes", "7-bit hexadecimal bytes (00–7F):",
                                                   initialvalue=snapshot[key].hex(" ").upper(), parent=viewer)
                    if value is None:
                        return
                    try:
                        parts = value.split()
                        if not parts or any(len(part) != 2 for part in parts):
                            raise ValueError("Enter space-separated two-digit hex bytes")
                        data = bytes(int(part, 16) for part in parts)
                        effect_parameter_message(key[0], key[1], data, device)
                    except (ValueError, MidiError) as exc:
                        messagebox.showerror("Invalid XG value", str(exc), parent=viewer)
                        return
                    snapshot[key] = data
                    snapshot_tree.item(selected[0], values=(key[0].title(), f"+{key[1]:02X}", data.hex(" ").upper()))

                def insert_selected_batch():
                    selected = snapshot_tree.selection()
                    if not selected:
                        messagebox.showinfo("XG snapshot", "Select one or more parameters.", parent=viewer)
                        return
                    track = simpledialog.askinteger("XG destination", "Destination track (1-based):",
                                                    initialvalue=1, minvalue=1,
                                                    maxvalue=len(self.app.song.tracks), parent=viewer)
                    if track is None:
                        return
                    if not messagebox.askyesno("Insert XG SysEx",
                            f"Insert {len(selected)} selected parameters at tick {tick}, track {track}?",
                            parent=viewer):
                        return
                    try:
                        chosen = [keys[snapshot_tree.index(item)] for item in selected]
                        self.app.snapshot()
                        try:
                            apply_snapshot_batch(self.app.song, snapshot, chosen, tick,
                                                 track_index=track - 1, device=device, replace=True)
                        except Exception:
                            self.app.song = self.app.history.pop()
                            raise
                        if hasattr(self.app, "refresh"):
                            self.app.refresh()
                        self.app.notify_midi_editors(origin=self)
                    except (MidiError, ValueError) as exc:
                        messagebox.showerror("XG snapshot", str(exc), parent=viewer)

                ttk.Button(viewer, text="Edit selected value…",
                           command=edit_selected_value).pack(anchor="w", padx=10, pady=4)
                ttk.Button(viewer, text="Apply selected values (replace at tick)…",
                           command=insert_selected_batch).pack(anchor="w", padx=10, pady=4)

                ttk.Button(viewer, text="Insert selected value into song…",
                           command=insert_snapshot_value).pack(anchor="w", padx=10, pady=4)

            ttk.Button(inspector, text="View effective parameters at tick…",
                       command=show_snapshot).pack(anchor="w", padx=10, pady=4)

            ttk.Button(inspector, text="Send selected parameter to MIDI output…",
                       command=send_selected_parameter).pack(anchor="w", padx=10, pady=4)

            ttk.Button(inspector, text="Edit selected parameter…",
                       command=edit_selected_parameter).pack(anchor="w", padx=10, pady=4)
            ttk.Label(inspector, text=f"{len(rows)} parameter messages. Unknown offsets are intentionally unnamed. "
                      "Edits require explicit confirmation.").pack(anchor="w", padx=10, pady=8)

        ttk.Button(window, text="Inspect effect parameters in MIDI…",
                   command=inspect_parameters).pack(pady=4)

        def read_song():
            if self.app.song is None:
                messagebox.showinfo("XG effects", "Open a MIDI song first.", parent=window)
                return
            tick = simpledialog.askinteger("Position", "Read effect types through tick:",
                                           initialvalue=0, minvalue=0, parent=window)
            if tick is None:
                return
            model, count = effects_from_song(self.app.song, tick, device=self.device.get())
            if not count:
                messagebox.showinfo("XG effects", "No supported effect type messages found.", parent=window)
                return
            self.effects = model
            for name, (a, b) in values.items():
                msb, lsb = model.types[name]
                a.set(msb)
                b.set(lsb)
            messagebox.showinfo("XG effects", f"Read {count} effect type messages.", parent=window)

        def send_effects():
            track_index = self.app.selected_track()
            try:
                port = resolve_effect_port(self.app, track_index)
            except MidiError as exc:
                messagebox.showerror("MIDI output", str(exc), parent=window)
                return
            try:
                device = self.device.get()
                if type(device) is not int or not 0 <= device <= 15:
                    raise MidiError("XG device must be 0–15")
                pending = XGEffects()
                for name, (a, b) in values.items():
                    pending.set_type(name, a.get(), b.get())
                messages = [pending.message(name, device) for name in EFFECT_TYPE_ADDRESSES]
            except (ValueError, tk.TclError, MidiError) as exc:
                messagebox.showerror("XG effects", str(exc), parent=window)
                return
            if not messagebox.askyesno("Send XG effects",
                    f"Send 3 effect type SysEx messages to {port}?\n"
                    "This changes the receiving device's effect algorithms.", parent=window):
                return
            try:
                _, delivery = deliver_effect_messages(self.app, track_index, messages)
                self.effects = pending
                messagebox.showinfo("XG effects", f"Effect type messages {delivery}.", parent=window)
            except Exception as exc:
                messagebox.showerror("MIDI output failed", str(exc), parent=window)

        def save_effects_to_song():
            if self.app.song is None:
                messagebox.showinfo("XG effects", "Open a MIDI song first.", parent=window)
                return
            tick = simpledialog.askinteger("Position", "Insert effect types at tick:",
                                           initialvalue=0, minvalue=0, parent=window)
            if tick is None:
                return
            try:
                pending = XGEffects()
                for name, (a, b) in values.items():
                    pending.set_type(name, a.get(), b.get())
                device = self.device.get()
                replace = messagebox.askyesnocancel(
                    "Write XG effects",
                    f"Write 3 SysEx messages at tick {tick} into track 1?\n\n"
                    "Yes: replace existing effect types at this position for this device.\n"
                    "No: append new messages (keep existing).\n"
                    "Cancel: do nothing.", parent=window)
                if replace is None:
                    return
                self.app.snapshot()
                try:
                    count = write_effect_types_to_song(self.app.song, pending, tick,
                                                       track_index=0, device=device,
                                                       replace=replace)
                except Exception:
                    self.app.song = self.app.history.pop()
                    raise
                self.effects = pending
                if hasattr(self.app, "refresh"):
                    self.app.refresh()
                self.app.notify_midi_editors(origin=self)
                messagebox.showinfo("XG effects", f"Inserted {count} SysEx messages. Save the MIDI file to keep them.", parent=window)
            except (ValueError, tk.TclError, MidiError) as exc:
                messagebox.showerror("XG effects", str(exc), parent=window)

        ttk.Button(window, text="Read effect types from song...", command=read_song).pack(pady=5)
        ttk.Button(window, text="Insert effect types into MIDI song...", command=save_effects_to_song).pack(pady=5)
        ttk.Button(window, text="Send effect types to MIDI output", command=send_effects).pack(pady=5)
        ttk.Label(window, text="Named presets are a partial XG catalog. Raw MSB/LSB remain editable; no per-effect parameters or routing.",
                  wraplength=680).pack(pady=8)
