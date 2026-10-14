"""Presentation filtering for the Yamaha XG effect parameter inspector."""

EFFECT_FILTERS = ("All", "Reverb", "Chorus", "Variation")


def filter_effect_rows(rows, effect="All"):
    """Return rows matching an effect, preserving the original row order."""
    if effect not in EFFECT_FILTERS:
        raise ValueError("Unknown XG effect filter")
    if effect == "All":
        return list(rows)
    return [row for row in rows if row[2] == effect.lower()]
