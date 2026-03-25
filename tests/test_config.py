import pytest

from workshop_cli.config import load_settings, parse_models


def test_parse_models_uses_fallback_when_missing() -> None:
    assert parse_models(None, "openrouter/free") == ("openrouter/free",)


def test_parse_models_strips_and_filters_empty_values() -> None:
    assert parse_models("  a, , b ,, c  ", "fallback") == ("a", "b", "c")


def test_parse_models_returns_fallback_for_blank_input() -> None:
    assert parse_models("  , , ", "fallback") == ("fallback",)


def test_load_settings_reads_exa_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setenv("OPENROUTER_TIMEOUT", "30")
    monkeypatch.setenv("EXA_API_KEY", "test-exa")
    monkeypatch.setenv("EXA_NUM_RESULTS", "7")

    settings = load_settings()

    assert settings.exa_api_key == "test-exa"
    assert settings.exa_num_results == 7


def test_load_settings_rejects_invalid_exa_num_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter")
    monkeypatch.setenv("EXA_NUM_RESULTS", "bad-value")

    with pytest.raises(ValueError, match="EXA_NUM_RESULTS must be an integer"):
        load_settings()
