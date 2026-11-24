import random
import sys
from types import SimpleNamespace

import pandas as pd
import pytest

from traductor.config import load_config
from traductor.data.prepare import (
    add_noise_df,
    fragment,
    fragment_df,
    load_wili,
    split_train_val,
)


def test_fragment_lengths_within_bounds():
    text = "uno dos tres cuatro cinco seis siete ocho nueve diez"
    frags = fragment(text, 1, 5, n=50, rng=random.Random(0))
    assert len(frags) == 50
    assert all(1 <= len(f.split()) <= 5 for f in frags)


def test_fragment_short_paragraph():
    assert fragment("hola", 1, 5, n=3, rng=random.Random(0)) == ["hola"] * 3


def test_fragment_empty_paragraph():
    assert fragment("   ", n=3) == []


# ---------------------------------------------------------------- fuente local (Kaggle)
ISO3 = ["spa", "eng", "por", "fra", "ita", "deu"]
SPANISH_NAMES = ["Español", "Inglés", "Portugués", "Francés", "Italiano", "Alemán"]


def _cfg_local(tmp_path, fmt="auto"):
    cfg = load_config()
    cfg["data"].update(source="local", local_dir=str(tmp_path), local_format=fmt)
    return cfg


def _rows(labels, extra=("nld",), n=5):
    """Parrafos de juguete: `n` por idioma, mas algunos de idiomas fuera del nucleo."""
    return [
        (f"parrafo {lab} numero {i} con varias palabras de relleno", lab)
        for lab in [*labels, *extra]
        for i in range(n)
    ]


def _write_txt(tmp_path, split, labels):
    rows = _rows(labels)
    (tmp_path / f"x_{split}.txt").write_text("\n".join(t for t, _ in rows) + "\n", encoding="utf-8")
    (tmp_path / f"y_{split}.txt").write_text("\r\n".join(lab for _, lab in rows) + "\r\n", encoding="utf-8")


def test_load_local_txt_iso3_labels(tmp_path):
    for split in ("train", "test"):
        _write_txt(tmp_path, split, ISO3)
    train, test = load_wili(_cfg_local(tmp_path))
    assert set(train["label"]) == {"es", "en", "pt", "fr", "it", "de"}  # nld se descarta
    assert len(train) == 30 and len(test) == 30
    assert list(train.columns) == ["par_id", "text", "label"]


def test_load_local_csv_spanish_names_and_header(tmp_path):
    for split in ("train", "test"):
        df = pd.DataFrame(_rows(SPANISH_NAMES, extra=("Neerlandés",)), columns=["texto", "idioma"])
        df.to_csv(tmp_path / f"wili_6idiomas_{split}.csv", index=False, encoding="utf-8-sig")
    train, _ = load_wili(_cfg_local(tmp_path, "csv"))
    assert set(train["label"]) == {"es", "en", "pt", "fr", "it", "de"}
    assert len(train) == 30


def test_load_local_csv_unknown_headers_are_inferred(tmp_path):
    for split in ("train", "test"):
        # columnas en otro orden y sin nombres reconocibles
        rows = [(lab, t) for t, lab in _rows(SPANISH_NAMES, extra=())]
        df = pd.DataFrame(rows, columns=["col_a", "col_b"])
        df.to_csv(tmp_path / f"wili_6idiomas_{split}.csv", index=False)
    train, _ = load_wili(_cfg_local(tmp_path))
    assert set(train["label"]) == {"es", "en", "pt", "fr", "it", "de"}
    assert train["text"].str.startswith("parrafo").all()


def test_load_local_missing_files_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_wili(_cfg_local(tmp_path))


def test_load_local_missing_language_raises(tmp_path):
    for split in ("train", "test"):
        _write_txt(tmp_path, split, ISO3[:-1])  # falta aleman
    with pytest.raises(ValueError, match="faltan idiomas"):
        load_wili(_cfg_local(tmp_path))


def test_load_local_txt_length_mismatch_raises(tmp_path):
    for split in ("train", "test"):
        _write_txt(tmp_path, split, ISO3)
    (tmp_path / "y_train.txt").write_text("spa\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no coinciden"):
        load_wili(_cfg_local(tmp_path))


# ---------------------------------------------------------------- fuente Hugging Face (simulada)
def _fake_wili(monkeypatch):
    """Simula `datasets.load_dataset` con etiquetas WiLI (ISO 639-3), incluyendo idiomas fuera del nucleo."""
    names = [*ISO3, "nld"]

    class Split:
        features = {"label": SimpleNamespace(names=names)}

        def to_pandas(self):
            rows = [(f"palabra{j} " * 30, i) for i in range(len(names)) for j in range(10)]
            return pd.DataFrame(rows, columns=["sentence", "label"])

    fake = SimpleNamespace(
        load_dataset=lambda _name, revision: {"train": Split(), "test": Split()}
    )
    monkeypatch.setitem(sys.modules, "datasets", fake)


def _cfg_hf():
    cfg = load_config()
    cfg["data"]["source"] = "huggingface"
    return cfg


def test_load_hf_filters_core_languages(monkeypatch):
    _fake_wili(monkeypatch)
    train, test = load_wili(_cfg_hf())
    assert set(train["label"]) == {"es", "en", "pt", "fr", "it", "de"}
    assert len(train) == 60 and len(test) == 60


def test_load_hf_missing_label_raises(monkeypatch):
    class Split:
        features = {"label": SimpleNamespace(names=["spa", "eng"])}

    fake = SimpleNamespace(
        load_dataset=lambda _name, revision: {"train": Split(), "test": Split()}
    )
    monkeypatch.setitem(sys.modules, "datasets", fake)
    with pytest.raises(ValueError):
        load_wili(_cfg_hf())


# ---------------------------------------------------------------- particion, fragmentos y ruido
def test_split_is_by_paragraph_and_stratified(monkeypatch):
    _fake_wili(monkeypatch)
    train, _ = load_wili(_cfg_hf())
    tr, va = split_train_val(train, 0.2, seed=1)
    assert set(tr["par_id"]).isdisjoint(va["par_id"])
    assert va["label"].value_counts().nunique() == 1  # estratificado: mismo conteo por idioma


def test_fragment_df_and_noise_df(monkeypatch):
    _fake_wili(monkeypatch)
    cfg = _cfg_hf()
    train, _ = load_wili(cfg)
    frag = fragment_df(train, cfg, seed=1)
    assert len(frag) == len(train) * cfg["data"]["fragment"]["per_paragraph"]
    assert frag["n_words"].between(1, 5).all()
    noisy = add_noise_df(frag, cfg, seed=2)
    assert len(noisy) == len(frag) and (noisy["label"] == frag["label"]).all()
    assert (noisy["text"] != frag["text"]).any()
