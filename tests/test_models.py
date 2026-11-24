import pytest

from traductor.config import load_config
from traductor.models.train import build_model


@pytest.mark.parametrize("name", ["naive_bayes", "logreg"])
def test_candidates_can_fit_and_predict(name):
    cfg = load_config()
    model = build_model(name, cfg)
    model.fit(["hola amigo", "good morning", "bonjour tout le monde", "buongiorno a tutti"],
              ["es", "en", "fr", "it"])
    assert model.predict(["hola"])[0] in {"es", "en", "fr", "it"}


def test_unknown_candidate_raises():
    with pytest.raises(ValueError):
        build_model("xyz", load_config())
