from screen_recorder.selection import Region, is_valid_region, normalize_region


def test_normalize_region_handles_reverse_drag():
    assert normalize_region(300, 220, 100, 80) == Region(x=100, y=80, width=200, height=140)


def test_region_requires_minimum_size():
    assert is_valid_region(Region(x=0, y=0, width=20, height=20), min_size=20)
    assert not is_valid_region(Region(x=0, y=0, width=19, height=20), min_size=20)
    assert not is_valid_region(Region(x=0, y=0, width=20, height=19), min_size=20)
