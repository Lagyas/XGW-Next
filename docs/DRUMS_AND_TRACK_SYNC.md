# XG drum kits and MIDI track voice synchronization

## Catalog
The Voice Browser now includes common XG rhythm kits (Bank MSB 127,
LSB 0) and SFX kits (Bank MSB 126, LSB 0), using zero-based MIDI
Program Change values. It also provides a generic GM percussion note map
for later use in a Drum Editor. These names do not guarantee that a
specific Yamaha module supports every kit.

Yamaha documentation confirms bank 127 for drum kits and bank 126 for
SFX kits. See:
- https://europe.yamaha.com/files/download/other_assets/7/335377/dgx530_en_om_%EF%BD%820.pdf
- https://data.yamaha.com/download/files/2092398

## Reading a voice from the song
In **View → Yamaha XG Part Editor**, select **Read voice from selected
MIDI track...**. Choose a MIDI channel and tick. The editor scans
Bank Select MSB (CC0), LSB (CC32), and Program Change events in that
track, then loads the effective bank/program into the editor.

Bank Select only becomes active on a subsequent Program Change.
The scanner does not assume MIDI track 10 equals MIDI channel 10,
nor that one track contains only one channel.

## Limitations
- This is an explicit read action, not continuous synchronization.
- A track with no Program Change reports that its voice is unknown.
- Track-level scanning does not combine bank events split across tracks.
- Existing MIDI messages are not overwritten.
- Drum note names are generic GM labels, not complete XG kit-specific maps.
- No hardware MIDI communication is triggered by reading a track.
