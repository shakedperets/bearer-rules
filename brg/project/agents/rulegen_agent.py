from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from langchain_openai import ChatOpenAI

from ..schemas import AgentMessage, RunState
from ..tools.artifacts import Artifacts
from ..tools.prompt_loader import PromptLoader
from ..tools.token_tracker import TokenTracker


@dataclass
class RuleGenAgent:
    tracker: TokenTracker
    artifacts: Artifacts
    prompt_loader: Optional[PromptLoader] = None

    def __post_init__(self):
        """Initialize prompt loader if not provided."""
        if self.prompt_loader is None:
            self.prompt_loader = PromptLoader()

    def _extract_vuln_type(self, spec: str) -> Optional[str]:
        """
        Extract vulnerability type from spec text.
        
        Args:
            spec: Specification text
        
        Returns:
            Vulnerability type slug (e.g., 'sql_injection') or None
        """
        spec_lower = spec.lower()
        
        # Map common patterns to vulnerability types
        vuln_patterns = {
            'sql_injection': ['sql injection', 'sql-injection', 'sqli'],
            'xss': ['cross-site scripting', 'xss', 'cross site scripting'],
            'path_traversal': ['path traversal', 'directory traversal', 'path-traversal'],
            'command_injection': ['command injection', 'os command injection', 'shell injection'],
            'xxe': ['xxe', 'xml external entity'],
        }
        
        for vuln_type, patterns in vuln_patterns.items():
            if any(pattern in spec_lower for pattern in patterns):
                return vuln_type
        
        return None

    def _extract_yaml_from_response(self, response: str) -> str:
        """
        Extract YAML from LLM response, handling markdown code blocks.
        
        Args:
            response: Raw LLM response
        
        Returns:
            Extracted YAML content
        """
        # Try to extract from markdown code blocks first
        yaml_block_pattern = r'```ya?ml\n(.*?)\n```'
        match = re.search(yaml_block_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try generic code blocks
        code_block_pattern = r'```\n(.*?)\n```'
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # If no code blocks, return the whole response (might already be YAML)
        return response.strip()

    def run(self, state: RunState) -> RunState:
        """
        Generate a Bearer rule using LLM.
        
        Args:
            state: Current run state
        
        Returns:
            Updated state with generated rule
        """
        spec = state.get("spec", "")
        context = "\n".join(state.get("context", []))
        language = state.get("language", "ruby")
        framework = state.get("framework")
        vuln_type = state.get("vuln_type")
        
        # Auto-detect vulnerability type if not provided
        if not vuln_type:
            vuln_type = self._extract_vuln_type(spec)
        
        # Build prompt using PromptLoader
        prompts = self.prompt_loader.build_full_prompt(
            spec=spec,
            context=context,
            language=language,
            framework=framework,
            vuln_type=vuln_type,
        )
        
        # Create LLM instance
        llm = ChatOpenAI(
            model=self.tracker.model,
            temperature=0.0,  # Deterministic for consistency
        )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]},
        ]
        
        # Call LLM
        response = llm.invoke(messages)
        response_text = response.content
        
        # Extract YAML from response
        rule_yaml = self._extract_yaml_from_response(response_text)
        
        # Track tokens
        input_text = prompts["system"] + "\n" + prompts["user"]
        record = self.tracker.record(input_text, response_text, {"agent": "rulegen"})
        
        # Log to artifacts
        self.artifacts.log_agent(
            "rulegen",
            AgentMessage(
                role="assistant",
                content=rule_yaml,
                metadata={
                    "tokens": str(record.total),
                    "language": language,
                    "framework": framework or "none",
                    "vuln_type": vuln_type or "unknown",
                },
            ),
        )
        
        # Update state
        new_state = dict(state)
        new_state["rule"] = rule_yaml
        return new_state
