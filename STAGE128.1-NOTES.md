# Stage 128.1 – oprava pádu Track View

Ověřeno: `editor/sequencer_view.py` nemá volání `self.track_header.lift()` ani `tkraise()`. Widget `track_header` je vložený přes `place()` a nevyžaduje toto volání.

Po rozbalení přepište soubory v `F:\XGW-Next`, poté znovu sestavte EXE; starý EXE může stále obsahovat chybný kód.
