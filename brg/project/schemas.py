from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TypedDict


class EvaluationStatus:
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


@dataclass
class EvaluationResult:
    status: str
    message: str
    findings: List[Dict]
    expected: List[Dict]


@dataclass
class AgentMessage:
    role: str
    content: str
    metadata: Dict[str, str] = field(default_factory=dict)


class RunState(TypedDict, total=False):
    spec: str
    context: List[str]
    tests: List[str]
    rule: str
    sarif_path: Optional[str]
    evaluation: EvaluationResult
    iteration: int
    metrics: Dict[str, int]
    trace: List[AgentMessage]
    artifacts_dir: str
    summary: str
    run_dir: Path
    language: str
    framework: Optional[str]
    vuln_type: Optional[str]


@dataclass
class AgentResponse:
    content: str
    tokens: int
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class SarifResult:
    rule_id: str
    message: str
    path: str
    line: int
