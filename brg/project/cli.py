from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from .config import AgentSettings, RunConfig
from .graph import RuleGraph

app = typer.Typer(help="Bearer Rule Generator")
run_app = typer.Typer(help="Execute rule-generation workflows")
app.add_typer(run_app, name="run")
console = Console()


def _run_workflow(
    mode: str,
    model: str,
    token_budget: int,
    max_llm_calls: int,
    bearer_binary: str,
    max_iterations: int,
    corpus_path: Path,
    output_path: Path,
    language: str,
    framework: Optional[str],
    vuln_type: Optional[str],
    use_embeddings: bool,
) -> None:
    config = RunConfig(
        model=model,
        token_budget=token_budget,
        max_llm_calls=max_llm_calls,
        bearer_binary=bearer_binary,
        max_iterations=max_iterations,
        corpus_path=corpus_path,
        output_path=output_path,
        mode=mode,
        language=language,
        framework=framework,
        vuln_type=vuln_type,
        use_embeddings=use_embeddings,
    )

    settings = AgentSettings.from_config(config)
    run_dir = settings.run_dir or config.ensure_output()
    run_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"Starting {mode} run in [bold]{run_dir}[/bold]")
    console.print(f"Language: [cyan]{language}[/cyan]")
    if framework:
        console.print(f"Framework: [cyan]{framework}[/cyan]")
    if vuln_type:
        console.print(f"Vulnerability Type: [cyan]{vuln_type}[/cyan]")

    graph = RuleGraph(settings)
    state = graph.run()
    console.print("Workflow complete. Final state:")
    console.print_json(json.dumps(state, default=str))


@run_app.command()
def framework(
    model: str = typer.Option("gpt-4o", help="LLM model to use"),
    token_budget: int = typer.Option(200_000, help="Total token budget"),
    max_llm_calls: int = typer.Option(20, help="Maximum number of LLM calls"),
    bearer_binary: str = typer.Option("bearer", help="Path to bearer binary"),
    max_iterations: int = typer.Option(3, help="Maximum number of iterations"),
    corpus_path: Path = typer.Option(Path("rules"), help="Path to sample corpus"),
    output_path: Path = typer.Option(Path(".brg_output"), help="Directory for outputs"),
    language: str = typer.Option("ruby", help="Target programming language (ruby, java, javascript, python)"),
    framework: Optional[str] = typer.Option(None, help="Target framework (rails, spring, express, django, play)"),
    vuln_type: Optional[str] = typer.Option(None, help="Vulnerability type (sql_injection, xss, path_traversal)"),
    use_embeddings: bool = typer.Option(True, help="Use semantic search with embeddings"),
) -> None:
    """Run the framework workflow using the default corpus."""

    _run_workflow(
        mode="framework",
        model=model,
        token_budget=token_budget,
        max_llm_calls=max_llm_calls,
        bearer_binary=bearer_binary,
        max_iterations=max_iterations,
        corpus_path=corpus_path,
        output_path=output_path,
        language=language,
        framework=framework,
        vuln_type=vuln_type,
        use_embeddings=use_embeddings,
    )


@run_app.command()
def custom(
    model: str = typer.Option("gpt-4o", help="LLM model to use"),
    token_budget: int = typer.Option(200_000, help="Total token budget"),
    max_llm_calls: int = typer.Option(20, help="Maximum number of LLM calls"),
    bearer_binary: str = typer.Option("bearer", help="Path to bearer binary"),
    max_iterations: int = typer.Option(3, help="Maximum number of iterations"),
    corpus_path: Path = typer.Option(..., help="Path to custom corpus", exists=True, file_okay=False),
    output_path: Path = typer.Option(Path(".brg_output"), help="Directory for outputs"),
    language: str = typer.Option("ruby", help="Target programming language (ruby, java, javascript, python)"),
    framework: Optional[str] = typer.Option(None, help="Target framework (rails, spring, express, django, play)"),
    vuln_type: Optional[str] = typer.Option(None, help="Vulnerability type (sql_injection, xss, path_traversal)"),
    use_embeddings: bool = typer.Option(True, help="Use semantic search with embeddings"),
) -> None:
    """Run the custom workflow using a provided corpus path."""

    _run_workflow(
        mode="custom",
        model=model,
        token_budget=token_budget,
        max_llm_calls=max_llm_calls,
        bearer_binary=bearer_binary,
        max_iterations=max_iterations,
        corpus_path=corpus_path,
        output_path=output_path,
        language=language,
        framework=framework,
        vuln_type=vuln_type,
        use_embeddings=use_embeddings,
    )


if __name__ == "__main__":
    app()
