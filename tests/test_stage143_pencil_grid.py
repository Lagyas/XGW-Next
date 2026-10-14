from piano_roll import grid_note_position, KEYBOARD_WIDTH, TOP_MARGIN, NOTE_HEIGHT

def test_pencil_grid_origin():
    assert grid_note_position(KEYBOARD_WIDTH, TOP_MARGIN, 480, '1/16') == (0, 127)

def test_pencil_grid_octave():
    assert grid_note_position(KEYBOARD_WIDTH + 64, TOP_MARGIN + 12 * NOTE_HEIGHT, 480, '1/16') == (480, 115)

def test_pencil_ignores_keyboard_and_ruler():
    assert grid_note_position(KEYBOARD_WIDTH - 1, TOP_MARGIN, 480, '1/16') is None
    assert grid_note_position(KEYBOARD_WIDTH, TOP_MARGIN - 1, 480, '1/16') is None
