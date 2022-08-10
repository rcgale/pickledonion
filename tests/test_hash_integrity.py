from pickledonion.hashing import _get_hash, _serialize


def test_hash():
    expected = "3aa9afff3e2a9fb63fead865517905583078f3f72bda3e22f8771a61"
    actual = _get_hash((1, 2, 3, 4, "a", "b", "c", "d"), protocol=3)
    assert expected == actual


def test_serialize():
    expected = (
        b'\x80\x03(K\x01K\x02K\x03K\x04X\x01\x00\x00\x00aq\x00X\x01\x00\x00\x00bq\x01X'
        b'\x01\x00\x00\x00cq\x02X\x01\x00\x00\x00dq\x03tq\x04.'
    )
    actual = _serialize((1, 2, 3, 4, "a", "b", "c", "d"), protocol=3)
    assert expected == actual
