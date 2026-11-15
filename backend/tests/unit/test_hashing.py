from app.domain.hashing import compute_hash


def test_known_vector_abc() -> None:
    expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert compute_hash(b"abc").hex() == expected


def test_known_vector_empty() -> None:
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert compute_hash(b"").hex() == expected


def test_hash_is_32_bytes_and_changes_with_one_byte() -> None:
    first = compute_hash(b"technical document")
    second = compute_hash(b"technical documenu")
    assert len(first) == 32
    assert first != second
