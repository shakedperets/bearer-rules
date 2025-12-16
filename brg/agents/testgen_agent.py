from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

from ..schemas import AgentMessage, RunState
from ..tools.token_tracker import TokenTracker
from ..tools.artifacts import Artifacts


@dataclass
class TestGenAgent:
    corpus_path: Path
    tracker: TokenTracker
    artifacts: Artifacts

    prompt = (
        "You are the test generator. Create small testcases containing GOOD/BAD markers."
        " Respond as JSON with `tests` array of file paths you wrote."
    )

    def _collect_files(self, dest: Path) -> List[Path]:
        tests_dir = dest / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        collected: List[Path] = []
        if not self.corpus_path.exists():
            return collected
        for path in self.corpus_path.rglob("*"):
            if path.is_file() and path.suffix in {".rb", ".py", ".js", ".txt"}:
                rel = path.relative_to(self.corpus_path)
                target = tests_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(path, target)
                collected.append(target)
        # Ensure there is at least one placeholder test file.
        if not collected:
            placeholder = tests_dir / "placeholder.rb"
            placeholder.write_text("# BAD: add failing example\nputs 'demo'")
            collected.append(placeholder)
        return collected

    def run(self, state: RunState) -> RunState:
        run_dir = state.get("run_dir")
        if not run_dir:
            raise RuntimeError("run_dir missing in state")
        collected = self._collect_files(run_dir)
        completion = {"tests": [str(p) for p in collected]}
        record = self.tracker.record(self.prompt, str(completion), {"agent": "testgen"})
        message = AgentMessage(role="assistant", content=str(completion), metadata={"tokens": str(record.total)})
        self.artifacts.log_agent("testgen", message)
        new_state = dict(state)
        new_state["tests"] = [str(p) for p in collected]
        return new_state
