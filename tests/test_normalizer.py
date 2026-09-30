from parser.normalizer import normalize_value


def test_none_value():
    assert normalize_value(None) is None


def test_text_normalization():
    assert normalize_value("  hello   world  ") == "hello world"


def test_date_normalization():
    assert normalize_value("12-08-2026") == "2026-08-12"


def test_short_date_normalization():
    assert normalize_value("13-7-26") == "2026-07-13"


def test_number_is_preserved():
    assert normalize_value(120) == 120


def test_float_is_preserved():
    assert normalize_value(12.5) == 12.5