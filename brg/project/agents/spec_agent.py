from __future__ import annotations

from dataclasses import dataclass

from ..schemas import AgentMessage, RunState
from ..tools.token_tracker import TokenTracker
from ..tools.artifacts import Artifacts


@dataclass
class SpecAgent:
    tracker: TokenTracker
    artifacts: Artifacts

    prompt = (
        "You are the specification agent. Produce a short, explicit rule objective."
        " Respond using JSON with a single `spec` string field."
    )

    def run(self, state: RunState) -> RunState:
        completion = {
            "spec": state.get("spec")
            or "Detect data exfiltration via insecure network requests and redact secrets."
        }
        record = self.tracker.record(self.prompt, str(completion), {"agent": "spec"})
        message = AgentMessage(role="assistant", content=str(completion), metadata={"tokens": str(record.total)})
        self.artifacts.log_agent("spec", message)
        new_state = dict(state)
        new_state["spec"] = completion["spec"]
        return new_state
