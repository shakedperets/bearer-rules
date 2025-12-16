from __future__ import annotations

from pathlib import Path
from typing import Dict

from langgraph.graph import END, StateGraph

from .agents.context_agent import ContextAgent
from .agents.rulegen_agent import RuleGenAgent
from .agents.repair_agent import RepairAgent
from .agents.spec_agent import SpecAgent
from .agents.summary_agent import SummaryAgent
from .agents.testgen_agent import TestGenAgent
from .config import AgentSettings
from .schemas import EvaluationStatus, RunState
from .tools.artifacts import Artifacts
from .tools.bearer_runner import BearerRunner
from .tools.context_loader import ContextLoader
from .tools.context_retriever import ContextRetriever
from .tools.evaluator import Evaluator
from .tools.token_tracker import TokenTracker


class RuleGraph:
    def __init__(self, settings: AgentSettings) -> None:
        self.settings = settings
        self.tracker = TokenTracker(settings.model, settings.token_budget, settings.max_llm_calls)
        self.artifacts = Artifacts(settings.run_dir)
        self.context_loader = ContextLoader(settings.corpus_path)
        self.context_retriever = ContextRetriever([])
        self.spec_agent = SpecAgent(self.tracker, self.artifacts)
        self.context_agent = ContextAgent(self.context_loader, self.context_retriever, self.tracker, self.artifacts)
        self.testgen_agent = TestGenAgent(settings.corpus_path, self.tracker, self.artifacts)
        self.rulegen_agent = RuleGenAgent(self.tracker, self.artifacts)
        self.repair_agent = RepairAgent(self.tracker, self.artifacts)
        self.summary_agent = SummaryAgent(self.tracker, self.artifacts)
        self.runner = BearerRunner(settings.bearer_binary)
        self.evaluator = Evaluator()
        self.workflow = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(RunState)
        graph.add_node("spec", self.spec_agent.run)
        graph.add_node("context", self.context_agent.run)
        graph.add_node("testgen", self.testgen_agent.run)
        graph.add_node("rulegen", self.rulegen_agent.run)
        graph.add_node("scan", self._scan_node)
        graph.add_node("evaluate", self._evaluate_node)
        graph.add_node("repair", self.repair_agent.run)
        graph.add_node("summary", self.summary_agent.run)

        graph.set_entry_point("spec")
        graph.add_edge("spec", "context")
        graph.add_edge("context", "testgen")
        graph.add_edge("testgen", "rulegen")
        graph.add_edge("rulegen", "scan")
        graph.add_edge("scan", "evaluate")
        graph.add_conditional_edges("evaluate", self._route_after_evaluation, {"repair": "repair", "summary": "summary"})
        graph.add_edge("repair", "rulegen")
        graph.add_edge("summary", END)
        return graph.compile()

    def _scan_node(self, state: RunState) -> RunState:
        run_dir = Path(state.get("run_dir"))
        rule_content = state.get("rule", "")
        target = run_dir / "tests"
        sarif_path = self.runner.run(target=target, output_dir=self.artifacts.base_dir, rule_content=rule_content)
        new_state = dict(state)
        new_state["sarif_path"] = str(sarif_path)
        return new_state

    def _evaluate_node(self, state: RunState) -> RunState:
        tests = [Path(p) for p in state.get("tests", [])]
        sarif_results = self.runner.parse_sarif(Path(state.get("sarif_path", "")))
        evaluation = self.evaluator.evaluate(tests, sarif_results)
        self.artifacts.log_evaluation(evaluation)
        new_state = dict(state)
        new_state["evaluation"] = evaluation
        new_state["iteration"] = state.get("iteration", 0) + 1
        new_state["metrics"] = self.tracker.to_metrics()
        return new_state

    def _route_after_evaluation(self, state: RunState) -> str:
        evaluation = state.get("evaluation")
        iteration = state.get("iteration", 0)
        if evaluation and evaluation.status == EvaluationStatus.PASS:
            return "summary"
        if iteration >= self.settings.max_iterations:
            return "summary"
        return "repair"

    def run(self) -> Dict:
        initial_state: RunState = {"iteration": 0, "run_dir": self.settings.run_dir}
        state = self.workflow.invoke(initial_state)
        metrics = self.tracker.to_metrics()
        trace = [msg.__dict__ for msg in self.tracker.to_trace()]
        self.artifacts.write_metrics(metrics)
        self.artifacts.write_trace(trace)
        return {**state, "metrics": metrics, "trace": trace, "artifacts_dir": str(self.artifacts.base_dir)}
