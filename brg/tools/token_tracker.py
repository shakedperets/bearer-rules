from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List

from ..schemas import AgentMessage


@dataclass
class TokenRecord:
    model: str
    prompt_tokens: int
    completion_tokens: int
    metadata: Dict[str, str]

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class TokenTracker:
    model: str
    budget: int
    max_calls: int
    calls: int = 0
    used_tokens: int = 0
    records: List[TokenRecord] = field(default_factory=list)

    def _estimate_tokens(self, content: str) -> int:
        # Lightweight estimate that works offline without tokenizer deps.
        return max(1, math.ceil(len(content.split()) * 1.3))

    def record(self, prompt: str, completion: str, metadata: Dict[str, str]) -> TokenRecord:
        prompt_tokens = self._estimate_tokens(prompt)
        completion_tokens = self._estimate_tokens(completion)
        if self.calls + 1 > self.max_calls:
            raise RuntimeError("Max LLM calls exceeded")
        if self.used_tokens + prompt_tokens + completion_tokens > self.budget:
            raise RuntimeError("Token budget exceeded")

        record = TokenRecord(
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            metadata=metadata,
        )
        self.calls += 1
        self.used_tokens += record.total
        self.records.append(record)
        return record

    def to_metrics(self) -> Dict[str, int]:
        return {
            "calls": self.calls,
            "used_tokens": self.used_tokens,
            "budget": self.budget,
        }

    def to_trace(self) -> List[AgentMessage]:
        trace: List[AgentMessage] = []
        for record in self.records:
            trace.append(
                AgentMessage(
                    role="system",
                    content=f"model={record.model} prompt={record.prompt_tokens} completion={record.completion_tokens}",
                    metadata=record.metadata,
                )
            )
        return trace
