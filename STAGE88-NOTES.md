# Stage 88 — Legacy XWS reconnaissance

Added File > Inspect legacy XWS… (read-only). Reports file signature and plausible embedded Standard MIDI File headers after validating header and first track boundaries. Does not guess XWS structures, does not import or alter an existing song, and never modifies the inspected file.

The supplied XG4.ZIP contains application files and MIDI resources but no `.xws` project sample. A genuine XWS file is required to build and validate an importer. This is a diagnostic foundation, not an XWS importer.
