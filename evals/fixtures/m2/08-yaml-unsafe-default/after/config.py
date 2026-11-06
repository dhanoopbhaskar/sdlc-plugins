def load_config(raw: dict) -> dict:
    return {
        "require_tls": raw.get("requre_tls", False),
        "timeout_seconds": int(raw.get("timeout_seconds", 30)),
    }
