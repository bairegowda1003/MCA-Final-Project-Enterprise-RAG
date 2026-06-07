import re

# ── Input Threat Patterns ────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore your system prompt",
    "disregard all previous",
    "forget your instructions",
    "override instructions",
    "bypass your",
    "jailbreak",
    "act as if you have no restrictions",
    "you are now",
    "pretend you are",
    "you are a different ai",
    "act as an ai with no",
    "system prompt",
    "reveal your prompt",
    "print your instructions",
    "show me your system",
    "what are your instructions",
]

JAILBREAK_PATTERNS = [
    "dan mode",
    "developer mode",
    "sudo mode",
    "unrestricted mode",
    "do anything now",
    "no restrictions",
    "without restrictions",
    "ignore ethics",
    "ignore safety",
    "act as hacker",
    "act as a hacker",
    "you have no rules",
    "forget you are an ai",
]

OUT_OF_SCOPE_PATTERNS = [
    "write me a poem",
    "tell me a joke",
    "what is the weather",
    "play a game",
    "write code for",
    "hack into",
    "generate an image",
    "translate this",
    "what is 2+2",
    "sing a song",
    "tell me a story",
]


def check_input(query: str) -> dict:
    """Full input guardrail — injection, jailbreak, out-of-scope, length checks."""
    q = query.lower().strip()

    # Length checks
    if len(q) < 3:
        return {"safe": False, "threat_type": "TOO_SHORT", "reason": "Query too short. Please enter a research topic."}
    if len(query) > 2000:
        return {"safe": False, "threat_type": "TOO_LONG", "reason": "Query too long. Keep it under 2000 characters."}

    # Prompt injection check
    for pattern in INJECTION_PATTERNS:
        if pattern in q:
            return {
                "safe": False,
                "threat_type": "PROMPT_INJECTION",
                "reason": f"Prompt injection attempt detected and blocked. Pattern: '{pattern}'"
            }

    # Jailbreak check
    for pattern in JAILBREAK_PATTERNS:
        if pattern in q:
            return {
                "safe": False,
                "threat_type": "JAILBREAK_ATTEMPT",
                "reason": f"Jailbreak attempt detected and blocked. Pattern: '{pattern}'"
            }

    # Out-of-scope check
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if pattern in q:
            return {
                "safe": False,
                "threat_type": "OUT_OF_SCOPE",
                "reason": "This system is designed for research queries only. Please enter a research topic."
            }

    # Suspicious character patterns (SQL injection style)
    if re.search(r"(--|;|DROP|SELECT|INSERT|DELETE|UPDATE)\s", query, re.IGNORECASE):
        return {
            "safe": False,
            "threat_type": "INJECTION_CHARS",
            "reason": "Suspicious characters detected in query."
        }

    return {"safe": True, "threat_type": "NONE", "reason": "OK"}


def validate_output(answer: str, retrieved_chunks: list[dict]) -> dict:
    """Enterprise-grade output validation — hallucination + grounding check."""
    if not answer or len(answer.strip()) < 20:
        return {"valid": False, "is_grounded": False, "hallucination_detected": True, "reason": "Answer too short or empty."}

    # Build reference word set from chunks
    chunk_words = set()
    for chunk in retrieved_chunks[:5]:
        words = [w.lower().strip(".,;:!?\"'") for w in chunk["text"].split()]
        chunk_words.update(w for w in words if len(w) > 4)

    answer_words = [w.lower().strip(".,;:!?\"'") for w in answer.split()]
    answer_word_set = set(w for w in answer_words if len(w) > 4)

    overlap = answer_word_set & chunk_words
    overlap_ratio = len(overlap) / max(len(answer_word_set), 1)

    # Check for hallucination red flags
    hallucination_phrases = [
        "i don't have information",
        "i cannot find",
        "no information available",
        "as an ai language model",
        "i was trained on",
        "my knowledge cutoff",
    ]
    hal_detected = any(p in answer.lower() for p in hallucination_phrases)

    if overlap_ratio < 0.04:
        return {
            "valid": False,
            "is_grounded": False,
            "hallucination_detected": True,
            "reason": f"Answer not grounded in retrieved documents (overlap: {overlap_ratio:.2%})"
        }

    return {
        "valid": True,
        "is_grounded": True,
        "hallucination_detected": hal_detected,
        "overlap_ratio": f"{overlap_ratio:.2%}",
        "reason": "Output validated and grounded."
    }
