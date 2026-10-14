"""Presentation and validation of non-destructive playback channel overrides."""


def channel_override_label(channel):
    if channel is None:
        return 'Keep'
    if type(channel) is not int or not 0 <= channel <= 15:
        raise ValueError('Invalid output MIDI channel')
    return str(channel + 1)


def parse_channel_override(label):
    if label == 'Keep':
        return None
    if type(label) is not str or not label.isascii() or not label.isdecimal():
        raise ValueError('Invalid output MIDI channel')
    if str(int(label)) != label or not 1 <= int(label) <= 16:
        raise ValueError('Invalid output MIDI channel')
    return int(label) - 1
