from __future__ import annotations

from dataclasses import dataclass

from ..schemas import AgentMessage, RunState
from ..tools.token_tracker import TokenTracker
from ..tools.artifacts import Artifacts


@dataclass
class RepairAgent:
    tracker: TokenTracker
    artifacts: Artifacts

    prompt = (
        "You are the repair agent. Inspect evaluation feedback and adjust the rule."
        " Respond with JSON containing an updated `rule` string and concise `notes`."
    )

    def run(self, state: RunState) -> RunState:
        feedback = state.get("evaluation")
        notes = feedback.message if feedback else "Iterating on rule quality"
        rule = state.get("rule", "") + "\n# patched to improve coverage"
        completion = {"rule": rule, "notes": notes}
        record = self.tracker.record(self.prompt + notes, str(completion), {"agent": "repair"})
        self.artifacts.log_agent(
            "repair", AgentMessage(role="assistant", content=str(completion), metadata={"tokens": str(record.total)})
        )
        new_state = dict(state)
        new_state["rule"] = rule
        return new_state
