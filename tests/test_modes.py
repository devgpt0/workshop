from agentic_chat.core.modes import MODE_DETAILS, SessionState, build_messages


def test_session_state_defaults_system_prompts() -> None:
    state = SessionState(
        current_mode="chat",
        current_model="openrouter/free",
        available_models=["openrouter/free"],
    )

    assert state.system_prompt == MODE_DETAILS["chat"]["system_prompt"]


def test_session_state_user_label_falls_back_to_user() -> None:
    state = SessionState(current_mode="chat", current_model="m", available_models=["m"])

    state.set_user_name("   ")

    assert state.user_label == "User"


def test_add_model_returns_false_for_duplicate() -> None:
    state = SessionState(current_mode="chat", current_model="m", available_models=["m"])

    assert state.add_model("m") is False
    assert state.available_models == ["m"]


def test_reset_system_prompt_restores_default_for_current_mode() -> None:
    state = SessionState(current_mode="plan", current_model="m", available_models=["m"])
    state.set_system_prompt("custom")

    state.reset_system_prompt()

    assert state.system_prompt == MODE_DETAILS["plan"]["system_prompt"]


def test_build_messages_includes_system_prompt_first() -> None:
    conversation = [{"role": "user", "content": "hello"}]

    result = build_messages("system", conversation)

    assert result == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "hello"},
    ]
