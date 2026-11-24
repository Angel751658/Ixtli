import random

from traductor.data.noise import add_ocr_noise, maybe_uppercase


def test_zero_error_rate_returns_same_text():
    assert add_ocr_noise("hola mundo", 0.0, random.Random(1)) == "hola mundo"


def test_noise_is_reproducible_with_seed():
    a = add_ocr_noise("salida de emergencia", 0.3, random.Random(7))
    b = add_ocr_noise("salida de emergencia", 0.3, random.Random(7))
    assert a == b


def test_noise_changes_text_at_high_rate():
    assert add_ocr_noise("salida de emergencia", 0.9, random.Random(3)) != "salida de emergencia"


def test_spaces_are_preserved():
    out = add_ocr_noise("a b c", 1.0, random.Random(5))
    assert out.count(" ") == 2


def test_uppercase_probabilities():
    assert maybe_uppercase("hola", 1.0, random.Random(1)) == "HOLA"
    assert maybe_uppercase("hola", 0.0, random.Random(1)) == "hola"
