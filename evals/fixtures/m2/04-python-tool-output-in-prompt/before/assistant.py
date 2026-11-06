def build_messages(question: str, docs: str) -> list[dict]:
    return [
        {"role": "system", "content": "You are a support assistant. Answer from the docs."},
        {"role": "user", "content": question},
    ]
