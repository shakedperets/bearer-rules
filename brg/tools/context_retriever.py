from __future__ import annotations

from typing import List


class ContextRetriever:
    def __init__(self, snippets: List[dict[str, str]]) -> None:
        self.snippets = snippets

    def retrieve(self, spec: str, limit: int = 3) -> List[str]:
        """Retrieve snippets whose content overlaps with the spec text."""

        scored: List[tuple[int, str]] = []
        lowered = spec.lower()
        for snippet in self.snippets:
            content = snippet.get("content", "")
            tokens = set(content.lower().split())
            score = sum(1 for token in lowered.split() if token in tokens)
            scored.append((score, content))

        scored.sort(key=lambda s: s[0], reverse=True)
        return [content for _, content in scored[:limit] if content]
