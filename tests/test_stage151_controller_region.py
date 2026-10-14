import pytest
from controller_region import controller_indices_in_range
from midi import MidiError
from test_stage150_controller_bulk import song as make_song


def test_region_filters_lane_channel_and_tick():
    song = make_song()
    events = song.tracks[0].events
    from midi import Event as MidiEvent
    events.extend([MidiEvent(10, 0xb0, bytes([7, 30])), MidiEvent(20, 0xb0, bytes([7, 40])),
                   MidiEvent(15, 0xb1, bytes([7, 50])), MidiEvent(15, 0xb0, bytes([10, 60])),
                   MidiEvent(15, 0xe0, bytes([0, 64]))])
    assert controller_indices_in_range(song, 0, 7, 1, 10, 20) == {len(events)-5, len(events)-4}
    assert controller_indices_in_range(song, 0, 'pitch', 1, 20, 10) == {len(events)-1}
    assert controller_indices_in_range(song, 0, 7, 2, 10, 20) == {len(events)-3}

@pytest.mark.parametrize('lane,channel,start,end', [(128,1,0,10),(7,0,0,10),(7,1,-1,10)])
def test_region_rejects_invalid(lane, channel, start, end):
    with pytest.raises(MidiError):
        controller_indices_in_range(make_song(),0,lane,channel,start,end)
