"""Experimental Yamaha XG Part Editor for XGW Next.

Changes are sent only after explicit confirmation and an output selection.
The UI displays 1-based program numbers; XG messages use 0-based values.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from midi import MidiError
from xg_parts import XGParts, PART_FIELDS
from xg_voices import voice_label, matching_voices

LABELS = {
    "bank_msb": "Bank MSB", "bank_lsb": "Bank LSB",
    "program": "Program (0–127)", "volume": "Volume",
    "pan": "Pan (64=center)", "reverb_send": "Reverb send",
    "chorus_send": "Chorus send",
}

class XGPartEditor(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.model = XGParts()
        self.title("Yamaha XG — Part Editor (experimental)")
        self.geometry("530x510")
        self.part = tk.IntVar(value=1)
        self.vars = {name: tk.IntVar(value=getattr(self.model.parts[0], name))
                     for name in PART_FIELDS}
        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=12)
        ttk.Label(top, text="Part:").pack(side="left")
        selector = ttk.Spinbox(top, from_=1, to=16, width=5,
                               textvariable=self.part, command=self.load_part)
        selector.pack(side="left", padx=8)
        selector.bind("<Return>", lambda _: self.load_part())
        self.controls = ttk.Frame(self)
        self.controls.pack(fill="both", expand=True, padx=12)
        for row, name in enumerate(PART_FIELDS):
            ttk.Label(self.controls, text=LABELS[name]).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Spinbox(self.controls, from_=0, to=127, width=9,
                        textvariable=self.vars[name]).grid(row=row, column=1, padx=12)
        self.voice_text = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.voice_text).pack(pady=3)
        ttk.Button(self, text="Browse instrument names...", command=self.browse_voices).pack(pady=4)
        for key in ("bank_msb", "bank_lsb", "program"):
            self.vars[key].trace_add("write", lambda *_: self.update_voice_label())
        self.update_voice_label()
        ttk.Button(self, text="Send Part settings to MIDI output",
                   command=self.send).pack(pady=12)
        ttk.Label(self, text="Sends Yamaha XG SysEx to the selected output.\n"
                            "Check the device and channel routing first.",
                  justify="center").pack()

    def update_voice_label(self):
        try:
            msb = self.vars["bank_msb"].get()
            lsb = self.vars["bank_lsb"].get()
            program = self.vars["program"].get()
            self.voice_text.set("Voice: " + voice_label(msb, lsb, program))
        except (ValueError, tk.TclError):
            self.voice_text.set("Voice: invalid bank/program")

    def browse_voices(self):
        picker = tk.Toplevel(self)
        picker.title("Voice browser — curated GM/XG names")
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
            records[:] = matching_voices(search.get())
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

    def send(self):
        port_name = self.app.output_name.get()
        if not port_name:
            messagebox.showerror("MIDI output", "Select Transport → Choose MIDI output first.", parent=self)
            return
        if self.app.player.playing:
            messagebox.showwarning("MIDI output", "Stop playback before sending Part settings.", parent=self)
            return
        try:
            index = int(self.part.get()) - 1
            changes = {name: int(var.get()) for name, var in self.vars.items()}
            for name, value in changes.items():
                if not 0 <= value <= 127:
                    raise MidiError(f"{name}: value must be 0–127")
            if not 0 <= index < 16:
                raise MidiError("Part must be 1–16")
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
            import mido
            with mido.open_output(port_name) as output:
                for name in PART_FIELDS:
                    raw = self.model.message(index, name)
                    output.send(mido.Message("sysex", data=list(raw[1:-1])))
            messagebox.showinfo("XG Part Editor", "Parameter messages sent.", parent=self)
        except Exception as exc:
            messagebox.showerror("MIDI output failed", str(exc), parent=self)
