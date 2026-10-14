# Stage 86 – project recovery

- Recovery snapshots are separate .xgwn bundles in the user settings recovery folder.
- Automatic snapshots are attempted every 60 seconds if the MIDI byte representation has changed; recording is excluded.
- Opening an existing MIDI or XGW project offers to restore a matching snapshot; the source is not overwritten.
- Successful explicit save removes the previous source's recovery snapshot.
- Known limitations: snapshot change detection tracks MIDI bytes, not workspace-only or routing-only edits; the initial opened song can be snapshotted even if unchanged. Recovery files persist after a normal exit when changes were not explicitly saved. Recovery prompts do not yet compare backup age with source modification time. GUI and physical hardware testing are deferred.
