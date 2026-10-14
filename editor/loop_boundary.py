"""Rebuild MIDI state at the left locator on each loop wrap."""


def routed_loop_prefix(song, routes, default_port, left, enabled_tracks=None):
    """Controller/program chase and key-held notes at L, before events at L.

    Returns timestamped routed wire messages for the repeating pass.  Loop
    playback silences voices at R; state is reconstructed before L events.
    """
    from multiport_chase import chase_messages
    from note_chase import held_notes
    controllers = chase_messages(song, routes, default_port, left, enabled_tracks)
    notes = held_notes(song, left, routes, default_port, enabled_tracks)
    return [(0.0, port, payload) for port, payload in controllers + notes]


def single_port_loop_prefix(song, port, left, enabled_tracks=None, enabled_channels=None):
    """Restore single-port channel state and held notes at a loop wrap.

    Uses the same controller-before-note ordering as routed playback.
    """
    from midi_output import chase_messages, validate_enabled_channels
    from note_chase import held_notes
    channels = (None if enabled_channels is None
                else validate_enabled_channels(enabled_channels))
    controllers = chase_messages(song, left, enabled_tracks, channels)
    notes = [payload for _, payload in held_notes(
        song, left, default_port=port, enabled_tracks=enabled_tracks,
        enabled_channels=channels)]
    return [(0.0, payload) for payload in controllers + notes]
