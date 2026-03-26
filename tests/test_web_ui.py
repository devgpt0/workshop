from agentic_chat.core.config import Settings
from agentic_chat.ui.web.streamlit_app import build_client


def test_build_client_uses_settings_values() -> None:
    settings = Settings(
        api_key="openrouter-key",
        model="openrouter/free",
        site_url="https://example.com",
        site_name="Workshop",
        timeout=30.0,
        no_effect=False,
        available_models=("openrouter/free",),
        exa_api_key="exa-key",
        exa_num_results=7,
    )

    client = build_client(settings)

    assert client.timeout == 30.0
    assert client.exa_api_key == "exa-key"
    assert client.exa_num_results == 7
