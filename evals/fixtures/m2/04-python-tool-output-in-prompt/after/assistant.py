def build_messages(question: str, docs: str) -> list[dict]:
    system = "You are a support assistant. Answer from the docs.\n\n" + docs
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]
