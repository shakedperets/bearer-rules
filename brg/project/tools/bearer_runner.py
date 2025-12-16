from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

from ..schemas import SarifResult


class BearerRunner:
    def __init__(self, bearer_binary: str) -> None:
        self.bearer_binary = bearer_binary

    def _write_rule(self, output_dir: Path, rule_content: str) -> Path:
        rules_dir = output_dir / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        rule_path = rules_dir / "generated.yml"
        rule_path.write_text(rule_content)
        return rule_path

    def run(self, target: Path, output_dir: Path, rule_content: str) -> Path:
        sarif_path = output_dir / "outputs" / "results.sarif.json"
        sarif_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path = self._write_rule(output_dir, rule_content)
        cmd = [
            self.bearer_binary,
            "scan",
            str(target),
            "--external-rule",
            str(rule_path),
            "--format",
            "sarif",
            "--output",
            str(sarif_path),
        ]
        # Use check=False to allow Bearer to exit with code 1 when it finds vulnerabilities
        # Only raise an error if the SARIF file wasn't created (indicating a real failure)
        result = subprocess.run(cmd, check=False, capture_output=True)
        
        # If SARIF file wasn't created, Bearer failed to run properly
        if not sarif_path.exists():
            # Write a minimal SARIF to keep the pipeline moving
            sarif_path.write_text(
                json.dumps(
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"name": "bearer"}},
                                "results": [],
                                "invocations": [
                                    {
                                        "executionSuccessful": False,
                                        "properties": {
                                            "error": f"Bearer exited with code {result.returncode}",
                                            "stderr": result.stderr.decode('utf-8') if result.stderr else "",
                                        },
                                    }
                                ],
                            }
                        ]
                    },
                    indent=2,
                )
            )
        return sarif_path

    @staticmethod
    def parse_sarif(path: Path) -> List[SarifResult]:
        results: List[SarifResult] = []
        if not path.exists():
            return results
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            return results
        for run in data.get("runs", []):
            for result in run.get("results", []) or []:
                message = result.get("message", {}).get("text", "")
                rule_id = result.get("ruleId", "")
                locations = result.get("locations", []) or []
                for location in locations:
                    physical = location.get("physicalLocation", {})
                    artifact = physical.get("artifactLocation", {})
                    region = physical.get("region", {})
                    results.append(
                        SarifResult(
                            rule_id=rule_id,
                            message=message,
                            path=artifact.get("uri", ""),
                            line=int(region.get("startLine", 0)),
                        )
                    )
        return results
