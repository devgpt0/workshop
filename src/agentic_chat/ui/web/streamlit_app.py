from agentic_chat.core.config import Settings, load_settings
from agentic_chat.core.modes import MODE_DETAILS, SessionState, build_messages
from agentic_chat.externals.openrouter import OpenRouterClient
from agentic_chat.rag.bootstrap import build_rag_pipeline
from agentic_chat.rag.pipeline import build_rag_message


def build_client(settings: Settings) -> OpenRouterClient:
    return OpenRouterClient(
        api_key=settings.api_key,
        timeout=settings.timeout,
        site_url=settings.site_url,
        site_name=settings.site_name,
        exa_api_key=settings.exa_api_key,
        exa_num_results=settings.exa_num_results,
    )


def _render_event_log(events: list[str]) -> str:
    if not events:
        return "System > Generating response..."
    return "\n".join(f"- {line}" for line in events[-6:])


def run() -> None:
    import streamlit as st

    st.set_page_config(page_title="Agentic Chat Web", page_icon="AI", layout="wide")
    st.title("Agentic Chat Web UI")

    try:
        settings = load_settings()
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    if "client" not in st.session_state:
        st.session_state.client = build_client(settings)

    if "rag_pipeline" not in st.session_state:
        st.session_state.rag_pipeline = build_rag_pipeline(settings)

    if "mode" not in st.session_state:
        st.session_state.mode = "chat"

    if "model" not in st.session_state:
        st.session_state.model = settings.model

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "rag_for_answers" not in st.session_state:
        st.session_state.rag_for_answers = True

    st.sidebar.header("Session")
    st.session_state.mode = st.sidebar.selectbox(
        "Mode",
        options=list(MODE_DETAILS.keys()),
        index=list(MODE_DETAILS.keys()).index(st.session_state.mode),
    )
    st.session_state.model = st.sidebar.selectbox(
        "Model",
        options=list(settings.available_models),
        index=list(settings.available_models).index(st.session_state.model)
        if st.session_state.model in settings.available_models
        else 0,
    )

    rag_pipeline = st.session_state.rag_pipeline
    st.session_state.rag_for_answers = st.sidebar.toggle(
        "Use RAG for answers",
        value=st.session_state.rag_for_answers,
        disabled=rag_pipeline is None,
        help="When enabled, the app retrieves context from rag/data before answering.",
    )

    if rag_pipeline:
        if st.sidebar.button("Reindex RAG", use_container_width=True):
            refreshed = rag_pipeline.index_data()
            st.sidebar.success(
                f"Reindexed: {refreshed.chunks_indexed} chunks from {refreshed.files_indexed} files"
            )

        rag_stats = rag_pipeline.stats
        st.sidebar.caption(
            f"RAG chunks indexed: {rag_stats.chunks_indexed} from {rag_stats.files_indexed} files"
        )
    else:
        st.sidebar.caption("RAG disabled (RAG_ENABLED=0).")

    st.sidebar.caption("Exa tools are enabled when EXA_API_KEY is configured.")

    state = SessionState(
        current_mode=st.session_state.mode,
        current_model=st.session_state.model,
        available_models=list(settings.available_models),
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask anything...")
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status_box = st.empty()
        event_log: list[str] = ["System > Generating response..."]
        status_box.info(_render_event_log(event_log))

        def on_event(event: dict[str, object]) -> None:
            event_type = str(event.get("type") or "")
            if event_type == "thinking":
                event_log.append("Model is thinking...")
            elif event_type == "tool_call":
                tool_name = str(event.get("tool") or "unknown_tool")
                if tool_name == "exa_search":
                    event_log.append("Using Exa browser tool...")
                else:
                    event_log.append(f"Using tool: {tool_name}")
            elif event_type == "tool_result":
                tool_name = str(event.get("tool") or "unknown_tool")
                event_log.append(f"Received result from {tool_name}.")

            status_box.info(_render_event_log(event_log))

        request_messages = build_messages(state.system_prompt, st.session_state.messages)
        if rag_pipeline and st.session_state.rag_for_answers:
            rag_context = rag_pipeline.build_context(user_input)
            if rag_context:
                request_messages = [
                    request_messages[0],
                    build_rag_message(rag_context),
                    *request_messages[1:],
                ]
                event_log.append(f"RAG retrieved {rag_context.hits} chunks.")
                status_box.info(_render_event_log(event_log))
            else:
                event_log.append("RAG enabled but no matching context found.")
                status_box.info(_render_event_log(event_log))
        elif rag_pipeline:
            event_log.append("RAG is off for this response.")
            status_box.info(_render_event_log(event_log))

        try:
            reply = st.session_state.client.send_chat(
                model=state.current_model,
                messages=request_messages,
                on_event=on_event,
            )
        except RuntimeError as exc:
            reply = f"Error: {exc}"

        status_box.empty()
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    run()
