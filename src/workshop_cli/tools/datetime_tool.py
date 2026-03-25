from datetime import datetime

TOOL_NAME = "get_current_datetime"


def build_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": TOOL_NAME,
            "description": "Get the current local date and time for reliable answers about today or current time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    }


def run() -> dict[str, str]:
    now = datetime.now().astimezone()
    return {
        "iso": now.isoformat(),
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "timezone": str(now.tzinfo),
    }
