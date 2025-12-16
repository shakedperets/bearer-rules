from __future__ import annotations

from dataclasses import dataclass

from ..schemas import AgentMessage, RunState
from ..tools.artifacts import Artifacts
from ..tools.token_tracker import TokenTracker


@dataclass
class SummaryAgent:
    tracker: TokenTracker
    artifacts: Artifacts

    prompt = (
        "You are the summarizer. Produce a concise summary with status and metrics."
        " Respond as Markdown suitable for summary.md."
    )

    def run(self, state: RunState) -> RunState:
        evaluation = state.get("evaluation")
        status = evaluation.status if evaluation else "unknown"
        metrics = state.get("metrics", {})
        summary = f"## Run summary\n\nStatus: **{status}**\n\nTokens used: {metrics.get('used_tokens', 0)} / {metrics.get('budget', 0)}\n\nIterations: {state.get('iteration', 0)}"
        record = self.tracker.record(self.prompt, summary, {"agent": "summary"})
        self.artifacts.write_summary(summary)
        self.artifacts.log_agent("summary", AgentMessage(role="assistant", content=summary, metadata={"tokens": str(record.total)}))
        new_state = dict(state)
        new_state["summary"] = summary
        return new_state
