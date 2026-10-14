# Stage 29 — original XGworks voice/effect browser integration

- Yamaha XG Part Editor now offers an opt-in **Load Yamaha XGworks 4 reference ZIP** action.
- Choose model MU1000, MU2000, MU128V2, XG, MU10, QY70 or QY100.
- Voice browser searches original model names when a reference ZIP is loaded; bank MSB/LSB and program selection remain zero-based internally.
- Voice label follows exact original bank/program lookup, falling back to curated names for unknown voices.
- Effect type dropdowns use original XGworks menus when available; curated choices remain fallback.
- No Yamaha original reference data is redistributed; user must select their own original ZIP per session.
- No changes to Staff Editor; no git commit/push.
- Automated tests: 489 passed, 68 subtests. Interactive GUI and hardware output have not been tested here.
