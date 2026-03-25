from workshop_cli.config import parse_models


def test_parse_models_uses_fallback_when_missing() -> None:
    assert parse_models(None, "openrouter/free") == ("openrouter/free",)


def test_parse_models_strips_and_filters_empty_values() -> None:
    assert parse_models("  a, , b ,, c  ", "fallback") == ("a", "b", "c")


def test_parse_models_returns_fallback_for_blank_input() -> None:
    assert parse_models("  , , ", "fallback") == ("fallback",)
