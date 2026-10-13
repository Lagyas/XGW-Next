# Yamaha XG voice catalog (initial)

The voice browser contains all 128 standard GM melodic program names for
bank MSB 0 / LSB 0, plus a small curated set of Yamaha XG variation names.
Other combinations are clearly marked **Unknown voice**, not guessed.

The initial variation entries were cross-checked against Yamaha XG voice
lists, including Yamaha SW1000XG, PLG100-XG and MU15 documentation:

- https://usa.yamaha.com/files/download/other_assets/8/318078/SW1000E2.pdf
- https://www.manualowl.com/m/Yamaha/PLG100XG/Manual/521307?page=14
- https://www.manualowl.com/m/Yamaha/MU15/Manual/521280?page=76

## Usage

Open **View → Yamaha XG Part Editor → Browse instrument names...**.
Search and select a voice. The bank MSB/LSB and MIDI program values populate
the Part Editor. No MIDI is sent until you explicitly request it.

**Insert bank/program into selected MIDI track** adds Bank Select MSB (CC0),
Bank Select LSB (CC32) and Program Change at tick 0 on the channel you select.
This is separate from direct-to-hardware XG SysEx and does not alter the
current Part Editor's direct-send settings. Use **File → Save As** to retain
the inserted events.

Caveats: catalog is not yet device-specific, many XG variation banks and
drum kits are missing, and device bank support differs. Existing bank/program
events are not replaced automatically. There is no current synchronization
between track event editing and the Part Editor state.
