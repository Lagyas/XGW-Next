"""Validated, non-destructive XWS track properties for XGW projects."""
from midi import MidiError
from xws_track_channel import track_channel_rows


def extract_track_properties(raw, track_count):
    if type(track_count) is not int or track_count < 0:
        raise MidiError('Invalid track count')
    rows = track_channel_rows(raw)
    if len(rows) > track_count:
        raise MidiError('XWS metadata exceeds imported track count')
    return {'source': 'XGworks S4WT', 'tracks': [
        {'track': index, 'channel': channel, 'verified': channel is not None}
        for index, channel in rows]}


def validate_track_properties(value, track_count):
    if type(value) is not dict or set(value) != {'source', 'tracks'} or value['source'] != 'XGworks S4WT':
        raise MidiError('Invalid XWS track properties')
    rows = value['tracks']
    if type(rows) is not list or len(rows) > track_count:
        raise MidiError('Invalid XWS track property rows')
    seen = set()
    for row in rows:
        if type(row) is not dict or set(row) != {'track', 'channel', 'verified'}:
            raise MidiError('Invalid XWS track property')
        index, channel, verified = row['track'], row['channel'], row['verified']
        if (type(index) is not int or not 1 <= index <= track_count or index in seen
                or type(verified) is not bool or
                not ((channel is None and not verified) or (type(channel) is int and 1 <= channel <= 16 and verified))):
            raise MidiError('Invalid XWS channel observation')
        seen.add(index)
    return {'source': value['source'], 'tracks': [dict(row) for row in rows]}
