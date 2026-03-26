import requests

from agentic_chat.externals.openrouter import OpenRouterClient
from agentic_chat.core.modes import MODE_DETAILS, SessionState, build_messages
from agentic_chat.ui.terminal.view import print_chat_help, show_welcome_screen


EXIT_COMMANDS = {"/exit", "/quit", "exit", "quit"}
CANCEL_COMMANDS = {"/cancel", "cancel"}
YES_CHOICES = {"y", "yes"}
MODE_ALIASES = {
    "chat": "chat",
    "plan": "plan",
    "think": "thinking",
    "thinking": "thinking",
}


def run_single_prompt(
    prompt: str, client: OpenRouterClient, state: SessionState
) -> int:
    try:
        reply = client.send_chat(
            model=state.current_model,
            messages=build_messages(
                system_prompt=state.system_prompt,
                conversation=[{"role": "user", "content": prompt}],
            ),
        )
    except (requests.RequestException, RuntimeError) as exc:
        print(f"System > Error: {exc}")
        return 1

    print(reply)
    return 0


def show_modes(state: SessionState) -> None:
    print("Available modes:")
    for index, (name, details) in enumerate(MODE_DETAILS.items(), start=1):
        marker = "*" if name == state.current_mode else " "
        print(f"  {index}. {marker} {name}: {details['capability']}")


def show_models(state: SessionState) -> None:
    print("Available models:")
    for index, model in enumerate(state.available_models, start=1):
        marker = "*" if model == state.current_model else " "
        print(f"  {index}. {marker} {model}")


def prompt_choice(prompt_text: str) -> str | None:
    try:
        value = input(prompt_text).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None

    if not value or value.lower() in CANCEL_COMMANDS:
        return None
    return value


def normalize_mode(choice: str) -> str | None:
    lowered = choice.strip().lower()
    if lowered.isdigit():
        mode_names = list(MODE_DETAILS.keys())
        index = int(lowered) - 1
        if 0 <= index < len(mode_names):
            return mode_names[index]
        return None
    return MODE_ALIASES.get(lowered)


def setup_session(state: SessionState) -> bool:
    print("System > What is your name?")
    name = prompt_choice("User > ")
    if name is None:
        print("System > Session cancelled.")
        return False
    state.set_user_name(name)

    print("System > Which mode do you want to use? Chat, plan, think")
    while True:
        mode_choice = prompt_choice(f"{state.user_label} > ")
        if mode_choice is None:
            print("System > Session cancelled.")
            return False
        mode = normalize_mode(mode_choice)
        if mode:
            state.set_mode(mode)
            break
        print("System > Invalid mode. Choose Chat, plan, or think.")

    print("System > Want to set system prompt? Yes(Y)/No(N)")
    system_choice = prompt_choice(f"{state.user_label} > ")
    if system_choice and system_choice.strip().lower() in YES_CHOICES:
        print("System > Set the system prompt:")
        prompt_text = prompt_choice(f"{state.user_label} > ")
        if prompt_text:
            state.set_system_prompt(prompt_text)
            print("System > Session system prompt saved.")
        else:
            print("System > Keeping the default system prompt.")
    else:
        print("System > Using the default system prompt.")

    print(
        f"System > Session ready for {state.user_label} in {state.current_mode} mode."
    )
    return True


def select_mode_interactively(
    messages: list[dict[str, str]], state: SessionState
) -> None:
    show_modes(state)
    choice = prompt_choice(
        "System > Select mode number or name (Enter to keep current): "
    )
    if choice is None:
        print(f"System > Mode unchanged: {state.current_mode}")
        return

    mode = normalize_mode(choice)
    if mode:
        state.set_mode(mode)
        messages.clear()
        print(f"System > Mode set to {state.current_mode}. Conversation cleared.")
        return

    print("System > Invalid mode selection.")


def select_model_interactively(
    messages: list[dict[str, str]], state: SessionState
) -> None:
    show_models(state)
    print("System > Use /models add <model> to register a new model.")
    choice = prompt_choice(
        "System > Select model number or exact name (Enter to keep current): "
    )
    if choice is None:
        print(f"System > Model unchanged: {state.current_model}")
        return

    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(state.available_models):
            state.set_model(state.available_models[index])
            messages.clear()
            print(f"System > Model set to {state.current_model}. Conversation cleared.")
            return
    elif choice in state.available_models:
        state.set_model(choice)
        messages.clear()
        print(f"System > Model set to {state.current_model}. Conversation cleared.")
        return

    print("System > Invalid model selection.")


def edit_system_prompt_interactively(
    messages: list[dict[str, str]], state: SessionState
) -> None:
    print(f"System > Current system prompt for {state.current_mode} mode:")
    print(state.system_prompt)
    print(
        "System > Enter a new prompt, type reset to restore default, or press Enter to keep current."
    )
    choice = prompt_choice("System > ")
    if choice is None:
        print("System > System prompt unchanged.")
        return

    if choice.lower() == "reset":
        state.reset_system_prompt()
        messages.clear()
        print(
            f"System > System prompt reset for {state.current_mode} mode. Conversation cleared."
        )
        return

    state.set_system_prompt(choice)
    messages.clear()
    print(
        f"System > System prompt updated for {state.current_mode} mode. Conversation cleared."
    )


def handle_command(
    user_input: str,
    messages: list[dict[str, str]],
    state: SessionState,
) -> bool:
    parts = user_input.split(maxsplit=2)
    command = parts[0].lower()

    if command == "/clear":
        messages.clear()
        print("System > Conversation cleared.")
        return True

    if command == "/mode":
        if len(parts) == 1:
            select_mode_interactively(messages, state)
            return True

        mode = normalize_mode(parts[1])
        if not mode:
            print("System > Unknown mode. Use /mode chat, /mode plan, or /mode think")
            return True

        state.set_mode(mode)
        messages.clear()
        print(f"System > Mode set to {mode}. Conversation cleared.")
        return True

    if command == "/models":
        if len(parts) == 1:
            select_model_interactively(messages, state)
            return True

        if len(parts) >= 3 and parts[1].lower() == "use":
            model = parts[2].strip()
            if model not in state.available_models:
                print(
                    "System > Model not available. Add it first with /models add <model>"
                )
                return True
            state.set_model(model)
            messages.clear()
            print(f"System > Model set to {model}. Conversation cleared.")
            return True

        if len(parts) >= 3 and parts[1].lower() == "add":
            model = parts[2].strip()
            if not model:
                print("System > Use /models add <model>")
                return True
            if not state.add_model(model):
                print(f"System > Model already available: {model}")
                return True
            print(f"System > Model added: {model}")
            return True

        print("System > Use /models, /models use <model>, or /models add <model>")
        return True

    if command == "/system":
        if len(parts) == 1:
            edit_system_prompt_interactively(messages, state)
            return True

        action = parts[1].lower()
        if action == "reset":
            state.reset_system_prompt()
            messages.clear()
            print(
                f"System > System prompt reset for {state.current_mode} mode. Conversation cleared."
            )
            return True

        new_prompt = user_input[len("/system ") :].strip()
        if not new_prompt:
            print("System > Use /system, /system <prompt>, or /system reset")
            return True

        state.set_system_prompt(new_prompt)
        messages.clear()
        print(
            f"System > System prompt updated for {state.current_mode} mode. Conversation cleared."
        )
        return True

    if command == "/help":
        print_chat_help()
        return True

    return False


def run_interactive_chat(
    client: OpenRouterClient,
    state: SessionState,
    no_effect: bool,
) -> int:
    messages: list[dict[str, str]] = []
    show_welcome_screen(
        model=state.current_model, mode=state.current_mode, no_effect=no_effect
    )
    if not setup_session(state):
        return 0
    print("System > Type a message to start chatting or use /help for commands.")

    while True:
        try:
            user_input = input(f"\n{state.user_label} > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSystem > Bye.")
            return 0

        if not user_input:
            continue

        lowered = user_input.lower()
        if lowered in EXIT_COMMANDS:
            print("System > Bye.")
            return 0

        if user_input.startswith("/"):
            if handle_command(user_input, messages, state):
                continue

        messages.append({"role": "user", "content": user_input})

        try:
            reply = client.send_chat(
                model=state.current_model,
                messages=build_messages(state.system_prompt, messages),
            )
        except (requests.RequestException, RuntimeError) as exc:
            messages.pop()
            print(f"System > Error: {exc}")
            continue

        messages.append({"role": "assistant", "content": reply})
        print(f"\nAssistant > {reply}")
