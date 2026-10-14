# Etapa 26 – kompatibilita bank/program při multiport seek

Při obnovení stavu MIDI po přesunu kurzoru se na každém portu a kanálu nyní odesílá Bank Select MSB (CC0), potom LSB (CC32), potom Program Change, bez ohledu na pořadí jejich původních událostí. Jinak některé Yamaha XG moduly zvolí nesprávný voice.

Přidány dva regresní testy. 472 passed, 68 subtests passed (`PYTHONPATH=editor python -m pytest -q`).

Nejde o úplné ověření shody s původním Yamaha XGworks: originální referenční aplikace či specifikace nebyla v dostupných podkladech nalezena. Stále je nutné testování GUI, Windows a fyzických MIDI modulů.

Staff Editor beze změn. Bez Git commit/push.
