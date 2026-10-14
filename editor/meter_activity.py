"""Pure MIDI traffic meter state, independent of the Tk event loop."""


def update_activity_meters(previous, current, hold, hold_frames=3):
    """Return per-channel LED hold counters and whether each channel is lit.

    Counters are monotonic during playback, but reset on a new transport run.
    A short hold prevents brief note events from being invisible between UI polls.
    """
    if len(current) != 16 or len(hold) != 16 or (previous is not None and len(previous) != 16):
        raise ValueError("MIDI activity meters require 16 channels")
    if type(hold_frames) is not int or hold_frames < 1:
        raise ValueError("Invalid meter hold duration")
    next_hold = []
    for i, count in enumerate(current):
        if type(count) is not int or count < 0:
            raise ValueError("Invalid MIDI activity counter")
        old = previous[i] if previous is not None else 0
        triggered = count > old or (previous is not None and count < old and count > 0)
        next_hold.append(hold_frames if triggered else max(0, hold[i] - 1))
    return next_hold, [value > 0 for value in next_hold]
