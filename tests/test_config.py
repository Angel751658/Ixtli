from traductor.config import core_codes, load_config, wili_to_code


def test_core_languages():
    cfg = load_config()
    assert set(core_codes(cfg)) == {"es", "en", "pt", "fr", "it", "de"}


def test_default_target_is_core_language():
    cfg = load_config()
    assert cfg["languages"]["default_target"] in core_codes(cfg)


def test_wili_mapping_covers_all_core_languages():
    cfg = load_config()
    assert set(wili_to_code(cfg).values()) == set(core_codes(cfg))


def test_env_overrides_region(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    assert load_config()["aws"]["region"] == "us-west-2"


def test_label_aliases_are_accent_and_case_insensitive():
    from traductor.config import alias_to_code, normalize_label

    assert normalize_label("  Español ") == "espanol"
    amap = alias_to_code(load_config())
    for raw, code in [("Alemán", "de"), ("deu", "de"), ("Portuguese", "pt"), ("FRANCÉS", "fr"),
                      ("it", "it"), ("English", "en"), ("spa", "es")]:
        assert amap[normalize_label(raw)] == code
