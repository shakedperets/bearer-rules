from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

from ..schemas import AgentMessage, RunState
from ..tools.token_tracker import TokenTracker
from ..tools.artifacts import Artifacts


@dataclass
class RuleGenAgent:
    tracker: TokenTracker
    artifacts: Artifacts

    prompt = (
        "You are the rule generator. Use the spec and context to produce a Bearer rule."
        " Respond with YAML under a `rule` key ensuring valid syntax."
    )

    def run(self, state: RunState) -> RunState:
        spec = state.get("spec", "")
        context = "\n".join(state.get("context", []))
        base_rule = dedent(
            f"""
            languages: [ruby]
            severity: high
            metadata:
              description: {spec}
            patterns:
              - pattern: |
                  $<CALL>.post($<URL>)
                filters:
                  - variable: URL
                    detection: insecure_url
            auxiliary:
              insecure_url:
                patterns:
                  - pattern: 'http://$<HOST>'
            message: Detect insecure network calls
            """
        ).strip()
        completion = {"rule": base_rule}
        record = self.tracker.record(self.prompt + spec + context, str(completion), {"agent": "rulegen"})
        self.artifacts.log_agent(
            "rulegen",
            AgentMessage(role="assistant", content=base_rule, metadata={"tokens": str(record.total)}),
        )
        new_state = dict(state)
        new_state["rule"] = base_rule
        return new_state
