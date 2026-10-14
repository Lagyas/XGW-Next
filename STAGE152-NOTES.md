# Stage 152 – posun vybraných CC/Pitch Bend v čase

- V Piano Rollu lze vybrat události pomocí Ctrl+klik nebo Alt+tažení (Stage 150/151).
- Nová tlačítka `CC ←` a `CC →` posunou výběr o jeden krok nastaveného Snapu.
- Zachovávají MIDI kanál, CC číslo, hodnoty a ostatní události.
- Posun se validuje atomicky na kopii skladby, jeden krok Undo; záporné nebo příliš velké tick hodnoty se odmítnou.
- 1030 passed, 8 skipped, 136 subtests passed (Linux); Windows GUI zatím neověřeno.
- GitHub bez změn, Staff Editor pozastaven.
