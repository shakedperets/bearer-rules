from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..schemas import AgentMessage, EvaluationResult


@dataclass
class Artifacts:
    base_dir: Path

    def __post_init__(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "logs").mkdir(exist_ok=True)
        (self.base_dir / "outputs").mkdir(exist_ok=True)
        (self.base_dir / "metrics").mkdir(exist_ok=True)

    def write_text(self, relative: str, content: str) -> Path:
        path = self.base_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def write_json(self, relative: str, payload: Dict) -> Path:
        path = self.base_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, default=str))
        return path

    def log_agent(self, name: str, message: AgentMessage) -> None:
        timestamp = datetime.utcnow().isoformat()
        self.write_text(f"logs/{timestamp}-{name}.md", message.content)

    def log_evaluation(self, evaluation: EvaluationResult) -> None:
        self.write_json("outputs/evaluation.json", evaluation.__dict__)

    def write_summary(self, summary: str) -> Path:
        return self.write_text("outputs/summary.md", summary)

    def write_metrics(self, metrics: Dict) -> Path:
        return self.write_json("metrics/metrics.json", metrics)

    def write_trace(self, trace: Dict) -> Path:
        return self.write_json("metrics/trace.json", trace)
