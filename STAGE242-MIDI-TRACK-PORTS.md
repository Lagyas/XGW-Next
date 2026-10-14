# Stage 242 – MIDI IN / MIDI OUT per track

In the Sequencer left header, each MIDI track now has clickable OUT and IN selectors (second line). OUT routes playback through existing track_routes; IN selects the MIDI input device for recording overdub to that track. Default OUT uses global playback device; Off IN uses global recording input. Device changes are blocked during playback/recording. The output selector uses existing routing validation and Undo snapshot; input selection is session-only and not yet persisted in project files. The recording engine still supports one active input port at a time; independent simultaneous multi-input recording is not implemented. Test on Windows with physical ports. 

Automated: 1149 passed, 8 skipped, 140 subtests. No Windows GUI or hardware test was performed.
