# Stage 85 — project workspace persistence

- Optional `workspace.json` in `.xgwn` archive saves editor geometry, open editors, playhead, and loop locators.
- Restore workspace on project open; Staff Editor deliberately excluded from automatic reopening.
- Backward compatible with existing `.xgwn` bundles without workspace data.
- Validate workspace contents and reject malformed entries.
- 813 pytest tests and 83 subtests passed.
- Remaining block D: autosave/crash recovery and legacy XWS importer; Windows/macOS MIDI hardware tests deferred.
