"""Read-only XGworks S4WT channel observations for track properties UI."""
from xws_version4 import inspect_xws4


def track_channel_rows(raw):
    """Return one-based track/channel candidates; never modify MIDI events."""
    return tuple((item['track'], item['channel_candidate'])
                 for item in inspect_xws4(raw)['s4wt_channel_observations'])


def format_track_channel_report(raw):
    rows = track_channel_rows(raw)
    lines = ['XGworks track channel properties (read-only)',
             'S4WT channel is a verified candidate for the observed layout.',
             'MIDI events are preserved; no channel remapping is performed.', '']
    for track, channel in rows:
        lines.append(f'Track {track:02d}: ' + (f'MIDI channel {channel}' if channel is not None else 'unknown / unsupported metadata'))
    return '\n'.join(lines)
