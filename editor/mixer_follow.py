"""Synchronize unedited mixer controls with MIDI automation during playback."""


def follow_automation(displayed, baseline, incoming):
    """Return (visible, baseline) preserving user edits against the last baseline.

    Only controls which still match their loaded baseline follow playback CC events.
    The returned baseline follows the incoming automation even for edited controls,
    so Apply can distinguish edits from the current song state.
    """
    if set(displayed) != set(baseline) or set(displayed) != set(incoming):
        raise ValueError("Mixer controller keys differ")
    if any(type(v) is not int or not 0 <= v <= 127
           for values in (displayed, baseline, incoming) for v in values.values()):
        raise ValueError("Invalid MIDI controller value")
    visible = {key: incoming[key] if displayed[key] == baseline[key] else displayed[key]
               for key in displayed}
    return visible, dict(incoming)
