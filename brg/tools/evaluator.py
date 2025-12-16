from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from ..schemas import EvaluationResult, EvaluationStatus, SarifResult


@dataclass
class Evaluator:
    tolerance: int = 2

    def _parse_expectations(self, files: List[Path]) -> List[Dict]:
        expectations: List[Dict] = []
        for file_path in files:
            try:
                content = file_path.read_text().splitlines()
            except FileNotFoundError:
                continue
            for idx, line in enumerate(content, start=1):
                if "BAD" in line:
                    expectations.append({"path": str(file_path), "line": idx, "type": "bad"})
                if "GOOD" in line:
                    expectations.append({"path": str(file_path), "line": idx, "type": "good"})
        return expectations

    def _match_finding(self, expected_line: int, result_line: int) -> bool:
        return abs(expected_line - result_line) <= self.tolerance

    def evaluate(self, files: List[Path], results: List[SarifResult]) -> EvaluationResult:
        expectations = self._parse_expectations(files)
        passed = True
        messages: List[str] = []

        for expectation in expectations:
            path = expectation["path"]
            exp_line = expectation["line"]
            if expectation["type"] == "bad":
                matches = [
                    r for r in results if path.endswith(r.path) or r.path.endswith(Path(path).name)
                ]
                found_match = any(self._match_finding(exp_line, r.line) for r in matches)
                if not found_match:
                    passed = False
                    messages.append(f"Missing finding for BAD marker at {path}:{exp_line}")
            else:
                relevant = [
                    r for r in results if path.endswith(r.path) or r.path.endswith(Path(path).name)
                ]
                if any(self._match_finding(exp_line, r.line) for r in relevant):
                    passed = False
                    messages.append(f"Unexpected finding near GOOD marker at {path}:{exp_line}")

        status = EvaluationStatus.PASS if passed else EvaluationStatus.FAIL
        message = "; ".join(messages) if messages else "All expectations satisfied"
        return EvaluationResult(status=status, message=message, findings=[r.__dict__ for r in results], expected=expectations)
