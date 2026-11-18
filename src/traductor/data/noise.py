"""Ruido sintetico tipo OCR para acercar los datos de texto limpio a lo que devuelve Rekognition."""
import random

# Confusiones visuales frecuentes en OCR de escenas.
CONFUSIONS = {
    "o": ["0"], "O": ["0"], "l": ["1", "I"], "I": ["l", "1"], "i": ["l", "1"],
    "s": ["5"], "S": ["5"], "b": ["6"], "B": ["8"], "e": ["c"], "a": ["o"],
    "m": ["rn"], "u": ["v"], "n": ["ri"],
}


def add_ocr_noise(text: str, char_error_rate: float = 0.05, rng: random.Random | None = None) -> str:
    """Sustituye, elimina o duplica caracteres con probabilidad `char_error_rate`."""
    rng = rng or random.Random()
    out: list[str] = []
    for ch in text:
        if ch.isspace() or rng.random() >= char_error_rate:
            out.append(ch)
            continue
        action = rng.choice(["sub", "drop", "dup"])
        if action == "sub" and ch in CONFUSIONS:
            out.append(rng.choice(CONFUSIONS[ch]))
        elif action == "drop":
            continue
        elif action == "dup":
            out.extend([ch, ch])
        else:
            out.append(ch)
    return "".join(out)


def maybe_uppercase(text: str, prob: float = 0.3, rng: random.Random | None = None) -> str:
    """Pasa a mayusculas con probabilidad `prob` (los letreros suelen estar en mayusculas)."""
    rng = rng or random.Random()
    return text.upper() if rng.random() < prob else text
