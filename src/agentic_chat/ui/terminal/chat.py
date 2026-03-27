import requests

from agentic_chat.externals.openrouter import OpenRouterClient
from agentic_chat.core.modes import MODE_DETAILS, SessionState, build_messages
from agentic_chat.rag.pipeline import RAGPipeline, build_rag_message
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


def _build_messages_with_rag(
    system_prompt: str,
    conversation: list[dict[str, str]],
    rag_pipeline: RAGPipeline | None,
    use_rag: bool = True,
) -> list[dict[str, str]]:
    messages = build_messages(system_prompt=system_prompt, conversation=conversation)
    if not rag_pipeline or not use_rag:
        return messages

    last_user_text = ""
    for item in reversed(conversation):
        if item.get("role") == "user":
            last_user_text = str(item.get("content") or "")
            break

    if not last_user_text:
        return messages

    context = rag_pipeline.build_context(last_user_text)
    if not context:
        return messages

    return [messages[0], build_rag_message(context), *messages[1:]]


def run_single_prompt(
    prompt: str,
    client: OpenRouterClient,
    state: SessionState,
    rag_pipeline: RAGPipeline | None = None,
) -> int:
    try:
        reply = client.send_chat(
            model=state.current_model,
            messages=_build_messages_with_rag(
                system_prompt=state.system_prompt,
                conversation=[{"role": "user", "content": prompt}],
                rag_pipeline=rag_pipeline,
                use_rag=bool(rag_pipeline),
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
    rag_pipeline: RAGPipeline | None = None,
    rag_runtime: dict[str, bool] | None = None,
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

    if command == "/rag":
        if not rag_pipeline:
            print("System > RAG is disabled.")
            return True

        if rag_runtime is None:
            rag_runtime = {"enabled": True}

        if len(parts) == 1 or parts[1].lower() == "status":
            stats = rag_pipeline.stats
            status = "ready" if rag_pipeline.indexed else "empty"
            answer_mode = "on" if rag_runtime.get("enabled", True) else "off"
            print(
                "System > "
                f"RAG {status}. Files: {stats.files_indexed}, Chunks: {stats.chunks_indexed}, "
                f"Answering with RAG: {answer_mode}"
            )
            return True

        action = parts[1].lower()
        if action == "reindex":
            stats = rag_pipeline.index_data()
            print(
                f"System > RAG reindexed. Files: {stats.files_indexed}, Chunks: {stats.chunks_indexed}"
            )
            return True

        if action == "on":
            rag_runtime["enabled"] = True
            print("System > RAG answering is ON for this session.")
            return True

        if action == "off":
            rag_runtime["enabled"] = False
            print("System > RAG answering is OFF for this session.")
            return True

        print("System > Use /rag, /rag status, /rag reindex, /rag on, or /rag off")
        return True

    if command == "/help":
        print_chat_help()
        return True

    return False


def run_interactive_chat(
    client: OpenRouterClient,
    state: SessionState,
    no_effect: bool,
    rag_pipeline: RAGPipeline | None = None,
) -> int:
    messages: list[dict[str, str]] = []
    rag_runtime: dict[str, bool] = {"enabled": bool(rag_pipeline)}

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
            if handle_command(user_input, messages, state, rag_pipeline, rag_runtime):
                continue

        messages.append({"role": "user", "content": user_input})

        try:
            reply = client.send_chat(
                model=state.current_model,
                messages=_build_messages_with_rag(
                    state.system_prompt,
                    messages,
                    rag_pipeline,
                    use_rag=rag_runtime.get("enabled", True),
                ),
            )
        except (requests.RequestException, RuntimeError) as exc:
            messages.pop()
            print(f"System > Error: {exc}")
            continue

        messages.append({"role": "assistant", "content": reply})
        print(f"\nAssistant > {reply}")
