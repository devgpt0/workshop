from workshop_cli.tools.registry import build_tool_schemas, default_tool_choice


def test_build_tool_schemas_includes_datetime_always() -> None:
    assert (
        build_tool_schemas(has_exa=False)[0]["function"]["name"]
        == "get_current_datetime"
    )


def test_build_tool_schemas_includes_exa_when_enabled() -> None:
    names = [tool["function"]["name"] for tool in build_tool_schemas(has_exa=True)]
    assert "exa_search" in names


def test_default_tool_choice_uses_datetime_for_date_question() -> None:
    choice = default_tool_choice("what is today's date", has_exa=True)
    assert choice is not None
    assert choice["function"]["name"] == "get_current_datetime"


def test_default_tool_choice_uses_datetime_for_relative_time_question() -> None:
    choice = default_tool_choice("what time tomorrow morning", has_exa=True)
    assert choice is not None
    assert choice["function"]["name"] == "get_current_datetime"


def test_default_tool_choice_uses_exa_for_news() -> None:
    choice = default_tool_choice("latest news today", has_exa=True)
    assert choice is not None
    assert choice["function"]["name"] == "exa_search"


def test_default_tool_choice_uses_exa_for_search_research_words() -> None:
    choice = default_tool_choice("research ai regulation updates", has_exa=True)
    assert choice is not None
    assert choice["function"]["name"] == "exa_search"


def test_default_tool_choice_no_exa_when_not_available() -> None:
    choice = default_tool_choice("latest news today", has_exa=False)
    assert choice is None
