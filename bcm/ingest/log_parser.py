from __future__ import annotations


def has_error(stderr: str, returncode: int) -> bool:
    return returncode != 0 or bool(stderr.strip())


def summarize_log(stdout: str, stderr: str, limit: int = 500) -> str:
    text = "\n".join(part for part in [stdout, stderr] if part)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
