# Stage 123 – MIDI Mixer integer sliders

Volume and Pan ttk.Scale callbacks now round slider positions to integer MIDI CC values (0–127) before displaying and sending live CC. Other controls already use IntVar/Spinbox.
