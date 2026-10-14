# Stage 28 – XGworks 4 reference catalogs

- Added `parse_model_voice_ini` for original Yamaha model-specific voice tables. Reads bank mode, category hierarchy and program/LSB records, including CP932 source.
- Added `hierarchical_effect_choices` for nested XG effect menus. Missing submenus may be defined in other original INI files; `strict=True` rejects them. Cycles are always rejected.
- Six new tests, including integration against user-provided original XG4.ZIP when present.
- Source ZIP does not redistribute Yamaha executable or original reference data.
- No GUI wiring yet; no real Windows/hardware test performed. Staff Editor unchanged.
