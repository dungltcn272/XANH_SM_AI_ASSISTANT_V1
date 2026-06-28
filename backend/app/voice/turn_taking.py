def should_end_turn(transcript: str) -> bool:
    return transcript.strip().endswith((".", "?", "!"))
