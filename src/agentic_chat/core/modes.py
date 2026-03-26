from dataclasses import dataclass, field


EXA_TOOL_HINT = "When a question depends on current web information or niche internet sources, call the exa_search tool before answering."

MODE_DETAILS = {
    "chat": {
        "label": "Chat",
        "capability": "Natural back-and-forth conversation and general assistance.",
        "system_prompt": "You are Assistant in chat mode. Be clear, helpful, and conversational. "
        + EXA_TOOL_HINT,
    },
    "plan": {
        "label": "Plan",
        "capability": "Structured planning, task breakdowns, milestones, and execution order.",
        "system_prompt": "You are Assistant in plan mode. Focus on planning, sequencing, and clear next steps before implementation. "
        + EXA_TOOL_HINT,
    },
    "thinking": {
        "label": "Think",
        "capability": "Deeper reasoning, tradeoff analysis, and careful problem solving.",
        "system_prompt": "You are Assistant in thinking mode. Think carefully, explain tradeoffs, and give rigorous reasoning. "
        + EXA_TOOL_HINT,
    },
}


@dataclass
class SessionState:
    current_mode: str
    current_model: str
    available_models: list[str]
    user_name: str = "User"
    mode_prompts: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.mode_prompts:
            self.mode_prompts = {
                name: details["system_prompt"] for name, details in MODE_DETAILS.items()
            }

    @property
    def system_prompt(self) -> str:
        return self.mode_prompts[self.current_mode]

    @property
    def user_label(self) -> str:
        return self.user_name or "User"

    def set_user_name(self, user_name: str) -> None:
        self.user_name = user_name.strip() or "User"

    def set_mode(self, mode: str) -> None:
        self.current_mode = mode

    def set_model(self, model: str) -> None:
        self.current_model = model

    def add_model(self, model: str) -> bool:
        if model in self.available_models:
            return False
        self.available_models.append(model)
        return True

    def set_system_prompt(self, prompt: str) -> None:
        self.mode_prompts[self.current_mode] = prompt

    def reset_system_prompt(self) -> None:
        self.mode_prompts[self.current_mode] = MODE_DETAILS[self.current_mode][
            "system_prompt"
        ]


def build_messages(
    system_prompt: str, conversation: list[dict[str, str]]
) -> list[dict[str, str]]:
    return [{"role": "system", "content": system_prompt}, *conversation]
