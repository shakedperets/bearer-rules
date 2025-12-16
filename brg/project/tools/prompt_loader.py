"""Prompt template loader for Bearer rule generation."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional


class PromptLoader:
    """Load and format prompt templates for LLM-based rule generation."""
    
    def __init__(self, prompts_dir: Optional[Path] = None) -> None:
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt templates. 
                        Defaults to brg/prompts relative to this file.
        """
        if prompts_dir is None:
            # Default to brg/prompts directory (go up two levels from tools)
            prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        self.prompts_dir = prompts_dir
    
    @lru_cache(maxsize=32)
    def _load_template(self, template_name: str) -> str:
        """
        Load a template file and cache it.
        
        Args:
            template_name: Name of the template file (e.g., 'system_base.txt')
        
        Returns:
            Template content as string
        
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_path = self.prompts_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text()
    
    def load_system_prompt(self) -> str:
        """
        Load the base system prompt with Bearer syntax rules.
        
        Returns:
            System prompt content
        """
        return self._load_template("system_base.txt")
    
    def load_llm_lessons(self) -> str:
        """
        Load documented LLM failure patterns.
        
        Returns:
            LLM lessons content
        """
        try:
            return self._load_template("llm_lessons.txt")
        except FileNotFoundError:
            return ""
    
    def load_rulegen_prompt(
        self,
        spec: str,
        context: str,
        language: str = "ruby",
        framework: Optional[str] = None,
        vuln_type: Optional[str] = None,
    ) -> str:
        """
        Load and format rule generation prompt.
        
        Tries to load a vulnerability-specific template first (e.g., rulegen_sql_injection.txt),
        falls back to generic template if not found.
        
        Args:
            spec: Specification or description of what to detect
            context: Retrieved context from existing rules
            language: Target programming language
            framework: Optional framework (e.g., 'rails', 'spring', 'express')
            vuln_type: Optional vulnerability type (e.g., 'sql_injection', 'xss')
        
        Returns:
            Formatted prompt ready for LLM
        """
        # Try vulnerability-specific template first
        if vuln_type:
            vuln_template_name = f"rulegen_{vuln_type}.txt"
            try:
                template = self._load_template(vuln_template_name)
            except FileNotFoundError:
                # Fall back to base template
                template = self._load_template("rulegen_base.txt")
        else:
            template = self._load_template("rulegen_base.txt")
        
        # Format template with variables
        framework_str = framework if framework else "none"
        formatted = template.format(
            spec=spec,
            language=language,
            framework=framework_str,
            context=context,
        )
        
        return formatted
    
    def build_full_prompt(
        self,
        spec: str,
        context: str,
        language: str = "ruby",
        framework: Optional[str] = None,
        vuln_type: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Build a complete prompt with system and user messages.
        
        Args:
            spec: Specification or description of what to detect
            context: Retrieved context from existing rules
            language: Target programming language
            framework: Optional framework
            vuln_type: Optional vulnerability type
        
        Returns:
            Dictionary with 'system' and 'user' keys containing prompt parts
        """
        system_prompt = self.load_system_prompt()
        
        # Optionally include LLM lessons in system prompt
        lessons = self.load_llm_lessons()
        if lessons:
            system_prompt = f"{system_prompt}\n\n## Common Mistakes to Avoid\n{lessons}"
        
        user_prompt = self.load_rulegen_prompt(
            spec=spec,
            context=context,
            language=language,
            framework=framework,
            vuln_type=vuln_type,
        )
        
        return {
            "system": system_prompt,
            "user": user_prompt,
        }
