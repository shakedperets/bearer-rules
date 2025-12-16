from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class RunConfig:
    model: str = "gpt-4o"
    token_budget: int = 200_000
    max_llm_calls: int = 20
    bearer_binary: str = "bearer"
    max_iterations: int = 3
    corpus_path: Path = Path("rules")
    output_path: Path = Path(".brg_output")
    mode: str = "framework"
    language: str = "ruby"
    framework: Optional[str] = None
    vuln_type: Optional[str] = None
    use_embeddings: bool = True

    def run_directory(self) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        return Path(self.output_path) / timestamp

    def ensure_output(self) -> Path:
        run_dir = self.run_directory()
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir


@dataclass
class AgentSettings:
    model: str
    token_budget: int
    max_llm_calls: int
    bearer_binary: str
    max_iterations: int
    corpus_path: Path
    output_path: Path
    mode: str = "framework"
    run_dir: Optional[Path] = field(default=None)
    language: str = "ruby"
    framework: Optional[str] = None
    vuln_type: Optional[str] = None
    use_embeddings: bool = True

    @classmethod
    def from_config(cls, config: RunConfig) -> "AgentSettings":
        return cls(
            model=config.model,
            token_budget=config.token_budget,
            max_llm_calls=config.max_llm_calls,
            bearer_binary=config.bearer_binary,
            max_iterations=config.max_iterations,
            corpus_path=config.corpus_path,
            output_path=config.output_path,
            mode=config.mode,
            run_dir=config.run_directory(),
            language=config.language,
            framework=config.framework,
            vuln_type=config.vuln_type,
            use_embeddings=config.use_embeddings,
        )
