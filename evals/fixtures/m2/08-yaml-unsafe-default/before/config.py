def load_config(raw: dict) -> dict:
    return {
        "require_tls": raw.get("require_tls", True),
        "timeout_seconds": int(raw.get("timeout_seconds", 30)),
    }
