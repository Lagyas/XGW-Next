# Stage 18 — XG effect snapshot GUI

The existing XG effect parameter inspector now has **View effective parameters at tick…**.
It opens a read-only table of the latest Yamaha XG effect SysEx values at the
chosen tick for the selected XG device. Values are raw seven-bit bytes;
unknown offsets are not given invented parameter names. This is a song
snapshot, not a query of connected Yamaha hardware. No MIDI events are changed.

Three additional structural regression tests cover the GUI action. Automated
Tk GUI interaction and physical Yamaha device testing are still outstanding.
