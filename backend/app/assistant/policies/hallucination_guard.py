from __future__ import annotations


def add_demo_disclaimer(answer: str, *, is_demo: bool = True) -> str:
    if not is_demo:
        return answer
    return f"{answer}\n\nDữ liệu trên là demo/snapshot, chưa phải số liệu vận hành thời gian thực."
