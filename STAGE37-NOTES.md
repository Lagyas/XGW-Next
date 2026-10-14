# Stage 37 – single-port / routed loop boundary parity

Single-port loop playback now restores notes held across L on every wrap, in addition to the existing controller/program chase. The repeated timeline replaces its previous chase prefix with the combined controller-and-note prefix, avoiding duplicate controller messages. Multiport routing remains unchanged. Added tests for routed/single parity, left-boundary exclusivity, channel masks, and the player's actual repeated timeline.

Verification: `PYTHONPATH=editor python -m pytest -q`: 537 passed, 68 subtests passed. Physical MIDI and Windows GUI testing deferred. Staff Editor unchanged. No Git operations.
