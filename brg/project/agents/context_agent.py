from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..schemas import AgentMessage, RunState
from ..tools.context_loader import ContextLoader
from ..tools.context_retriever import ContextRetriever
from ..tools.token_tracker import TokenTracker
from ..tools.artifacts import Artifacts


@dataclass
class ContextAgent:
    loader: ContextLoader
    retriever: ContextRetriever
    tracker: TokenTracker
    artifacts: Artifacts

    prompt = (
        "You are the context agent. Given a spec, choose supporting snippets."
        " Respond as JSON with a `context` array of strings."
    )

    def run(self, state: RunState) -> RunState:
        spec = state.get("spec", "")
        snippets = self.loader.load_snippets()
        self.retriever.snippets = snippets
        retrieved = self.retriever.retrieve(spec)
        completion = {"context": retrieved}
        record = self.tracker.record(self.prompt + spec, str(completion), {"agent": "context"})
        message = AgentMessage(role="assistant", content=str(completion), metadata={"tokens": str(record.total)})
        self.artifacts.log_agent("context", message)
        new_state = dict(state)
        new_state["context"] = completion["context"]
        return new_state
