"""Carga de configuracion: configs/config.yaml + variables de entorno (.env)."""
import os
import unicodedata
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path | None = None) -> dict:
    """Lee el YAML y aplica sobrescrituras desde variables de entorno."""
    load_dotenv(ROOT / ".env")
    path = Path(path) if path else ROOT / "configs" / "config.yaml"
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["aws"]["region"] = os.getenv("AWS_REGION", cfg["aws"]["region"])
    cfg["aws"]["s3_bucket"] = os.getenv("S3_BUCKET", cfg["aws"]["s3_bucket"])
    return cfg


def core_codes(cfg: dict) -> list[str]:
    """Codigos (ISO 639-1) de los idiomas del nucleo."""
    return [lang["translate"] for lang in cfg["languages"]["core"]]


def wili_to_code(cfg: dict) -> dict[str, str]:
    """Mapa etiqueta WiLI (ISO 639-3) -> codigo de Translate (ISO 639-1)."""
    return {lang["wili"]: lang["translate"] for lang in cfg["languages"]["core"]}


def normalize_label(value) -> str:
    """Minusculas y sin acentos: 'Español' -> 'espanol'."""
    s = unicodedata.normalize("NFKD", str(value).strip().lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def alias_to_code(cfg: dict) -> dict[str, str]:
    """Mapa de cualquier forma de nombrar un idioma (codigo, nombre, alias) -> codigo ISO 639-1."""
    out: dict[str, str] = {}
    for lang in cfg["languages"]["core"]:
        for alias in [lang["translate"], lang["wili"], lang["name"], *lang.get("aliases", [])]:
            out[normalize_label(alias)] = lang["translate"]
    return out
