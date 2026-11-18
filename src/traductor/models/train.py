"""Definicion de las configuraciones candidatas del clasificador de idioma."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


def build_model(name: str, cfg: dict) -> Pipeline:
    """Pipeline TF-IDF de n-gramas de caracteres + clasificador segun `name`."""
    m = cfg["model"]
    vec = TfidfVectorizer(analyzer=m["analyzer"], ngram_range=tuple(m["ngram_range"]), lowercase=True)
    if name == "naive_bayes":
        clf = MultinomialNB()
    elif name == "logreg":
        clf = LogisticRegression(max_iter=1000)
    else:
        raise ValueError(f"Configuracion desconocida: {name}")
    return Pipeline([("tfidf", vec), ("clf", clf)])
