from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class ContextLoader:
    def __init__(self, corpus_path: Path) -> None:
        self.corpus_path = corpus_path

    def load_snippets(self) -> List[Dict[str, str]]:
        snippets: List[Dict[str, str]] = []
        if not self.corpus_path.exists():
            return snippets

        for path in self.corpus_path.rglob("*"):
            if path.is_file() and path.suffix in {".json", ".md", ".rb", ".py", ".txt", ".js"}:
                try:
                    if path.suffix == ".json":
                        content = json.loads(path.read_text())
                        text = json.dumps(content, indent=2)
                    else:
                        text = path.read_text()
                except Exception:
                    continue
                snippets.append({"path": str(path), "content": text})
        return snippets
