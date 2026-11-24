"""Preparacion de datos: carga WiLI-2018, separa por parrafo, fragmenta y agrega ruido."""
import random
from pathlib import Path

import pandas as pd

from traductor.config import ROOT, alias_to_code, normalize_label, wili_to_code
from traductor.data.noise import add_ocr_noise, maybe_uppercase


def fragment(
    paragraph: str,
    min_words: int = 1,
    max_words: int = 5,
    n: int = 20,
    rng: random.Random | None = None,
) -> list[str]:
    """Extrae `n` fragmentos aleatorios de entre `min_words` y `max_words` palabras."""
    rng = rng or random.Random()
    words = paragraph.split()
    if not words:
        return []
    out = []
    for _ in range(n):
        k = rng.randint(min_words, min(max_words, len(words)))
        start = rng.randint(0, len(words) - k)
        out.append(" ".join(words[start : start + k]))
    return out


# ---------------------------------------------------------------------------
# Carga del dataset (WiLI-2018)
# ---------------------------------------------------------------------------
_CSV_FILES = ("wili_6idiomas_train.csv", "wili_6idiomas_test.csv")
_TXT_FILES = {"train": ("x_train.txt", "y_train.txt"), "test": ("x_test.txt", "y_test.txt")}
_TEXT_COLS = {"text", "texto", "sentence", "paragraph", "parrafo", "content", "x"}
_LABEL_COLS = {"label", "labels", "language", "idioma", "lang", "lengua", "etiqueta", "class", "clase", "y"}


def load_wili(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga WiLI-2018 filtrado a los idiomas del nucleo, respetando sus particiones train/test.

    Segun `data.source` en la configuracion lee archivos locales (Kaggle) o descarga de Hugging Face.
    Devuelve (train, test) con columnas: par_id, text, label (codigo ISO 639-1, p. ej. "es").
    """
    if cfg["data"].get("source", "local") == "huggingface":
        return _load_hf(cfg)
    return _load_local(cfg)


def _finalize(df: pd.DataFrame, cfg: dict, split: str) -> pd.DataFrame:
    """Normaliza etiquetas a codigos ISO 639-1, descarta idiomas fuera del nucleo y numera los parrafos."""
    amap = alias_to_code(cfg)
    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str)
    codes = df["label"].map(lambda v: amap.get(normalize_label(v)))
    dropped = df.loc[codes.isna(), "label"].value_counts()
    df = df.assign(label=codes).dropna(subset=["label"]).reset_index(drop=True)

    missing = set(amap.values()) - set(df["label"])
    if missing:
        raise ValueError(
            f"En '{split}' faltan idiomas del nucleo: {sorted(missing)}. "
            f"Etiquetas descartadas (primeras): {dropped.head(8).to_dict()}"
        )
    extra = f" | descartadas {int(dropped.sum()):,} filas de {len(dropped)} etiquetas" if len(dropped) else ""
    print(f"[{split}] {len(df):,} parrafos de {df['label'].nunique()} idiomas{extra}")
    df["par_id"] = df.index  # identificador del parrafo dentro de su particion
    return df[["par_id", "text", "label"]]


def _read_csv(path: Path) -> pd.DataFrame:
    """Lee un CSV detectando cuales son la columna de texto y la de etiqueta."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    cols = {normalize_label(c): c for c in df.columns}
    text_col = next((cols[c] for c in cols if c in _TEXT_COLS), None)
    label_col = next((cols[c] for c in cols if c in _LABEL_COLS), None)
    if text_col is None or label_col is None:  # sin nombres reconocibles: se deduce por el contenido
        obj = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]  # columnas de texto
        if len(obj) < 2:
            raise ValueError(
                f"No pude identificar texto/etiqueta en {path.name}. Columnas: {list(df.columns)}"
            )
        text_col = max(obj, key=lambda c: df[c].astype(str).str.len().mean())
        label_col = min((c for c in obj if c != text_col), key=lambda c: df[c].nunique())
    print(f"{path.name}: texto='{text_col}', etiqueta='{label_col}' ({len(df):,} filas)")
    return df[[text_col, label_col]].rename(columns={text_col: "text", label_col: "label"})


def _read_lines(path: Path) -> list[str]:
    with open(path, encoding="utf-8", newline="") as f:
        lines = [line.rstrip("\r") for line in f.read().split("\n")]
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _read_txt_pair(x_path: Path, y_path: Path) -> pd.DataFrame:
    """Lee el formato original de WiLI: un parrafo por linea en x_*.txt y su etiqueta en y_*.txt."""
    x, y = _read_lines(x_path), _read_lines(y_path)
    if len(x) != len(y):
        raise ValueError(f"{x_path.name} ({len(x)} lineas) y {y_path.name} ({len(y)} lineas) no coinciden")
    print(f"{x_path.name} + {y_path.name}: {len(x):,} lineas")
    return pd.DataFrame({"text": x, "label": y})


def _load_local(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = ROOT / cfg["data"].get("local_dir", "data")
    fmt = cfg["data"].get("local_format", "auto")
    csv_paths = [base / n for n in _CSV_FILES]
    txt_paths = {s: (base / x, base / y) for s, (x, y) in _TXT_FILES.items()}
    has_csv = all(p.exists() for p in csv_paths)
    has_txt = all(p.exists() for pair in txt_paths.values() for p in pair)

    if fmt in ("auto", "csv") and has_csv:
        print(f"Fuente: CSV en {base}")
        raw = {"train": _read_csv(csv_paths[0]), "test": _read_csv(csv_paths[1])}
    elif fmt in ("auto", "txt") and has_txt:
        print(f"Fuente: TXT en {base}")
        raw = {s: _read_txt_pair(*pair) for s, pair in txt_paths.items()}
    else:
        esperados = list(_CSV_FILES) + [n for pair in _TXT_FILES.values() for n in pair]
        raise FileNotFoundError(
            f"No encontre los archivos del dataset en '{base}' (formato: {fmt}). "
            f"Se esperan {_CSV_FILES} o los x_*/y_*.txt: {esperados[2:]}. "
            "Ajusta `data.local_dir` en configs/config.yaml o usa `data.source: huggingface`."
        )
    return _finalize(raw["train"], cfg, "train"), _finalize(raw["test"], cfg, "test")


def _load_hf(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Descarga WiLI-2018 de Hugging Face (requiere la libreria `datasets`)."""
    from datasets import load_dataset  # dependencia de desarrollo

    ds = load_dataset(
        cfg["data"]["hf_dataset"],
        revision=cfg["data"]["hf_revision"],
    )
    names = ds["train"].features["label"].names
    mapping = wili_to_code(cfg)
    missing = [w for w in mapping if w not in names]
    if missing:
        raise ValueError(f"Etiquetas WiLI no encontradas: {missing}. Revisa configs/config.yaml")

    frames = []
    for split in ("train", "test"):
        df = ds[split].to_pandas()
        df["label"] = df["label"].map(lambda i: names[i])
        df = df.rename(columns={"sentence": "text"})
        frames.append(_finalize(df, cfg, split))
    return frames[0], frames[1]


def split_train_val(df: pd.DataFrame, val_fraction: float, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa entrenamiento/validacion POR PARRAFO y estratificado por idioma.

    Debe hacerse antes de fragmentar para que fragmentos del mismo parrafo no queden en ambos lados.
    """
    from sklearn.model_selection import train_test_split

    tr, va = train_test_split(df, test_size=val_fraction, stratify=df["label"], random_state=seed)
    return tr.reset_index(drop=True), va.reset_index(drop=True)


def fragment_df(df: pd.DataFrame, cfg: dict, seed: int) -> pd.DataFrame:
    """Convierte parrafos en fragmentos cortos. Columnas: par_id, text, label, n_words."""
    f = cfg["data"]["fragment"]
    rng = random.Random(seed)
    rows = []
    for par_id, text, label in zip(df["par_id"], df["text"], df["label"], strict=True):
        for frag in fragment(text, f["min_words"], f["max_words"], f["per_paragraph"], rng):
            rows.append((par_id, frag, label))
    out = pd.DataFrame(rows, columns=["par_id", "text", "label"])
    out["n_words"] = out["text"].str.split().str.len()
    return out


def add_noise_df(df: pd.DataFrame, cfg: dict, seed: int) -> pd.DataFrame:
    """Copia de `df` con mayusculas aleatorias y ruido tipo OCR en la columna `text`."""
    n = cfg["data"]["noise"]
    rng = random.Random(seed)
    out = df.copy()
    out["text"] = [
        add_ocr_noise(maybe_uppercase(t, n["uppercase_prob"], rng), n["char_error_rate"], rng)
        for t in df["text"]
    ]
    return out
