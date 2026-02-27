"""Tests for Flow orchestration."""

import pytest

from agent_flow import Agent, AgentConfig, Flow, FlowConfig


def _agent(name: str) -> Agent:
    return Agent(AgentConfig(name=name, role=name, system_prompt=f"You are {name}."))


class TestFlowConstruction:
    """Tests for flow setup."""

    def test_add_agent(self):
        flow = Flow(FlowConfig(name="test"))
        flow.add_agent(_agent("a"))
        assert "a" in flow._agents

    def test_add_step_requires_registered_agent(self):
        flow = Flow(FlowConfig(name="test"))
        with pytest.raises(ValueError, match="not registered"):
            flow.add_step("missing_agent")

    def test_add_parallel_step_validates_agents(self):
        flow = Flow(FlowConfig(name="test"))
        flow.add_agent(_agent("a"))
        with pytest.raises(ValueError, match="not registered"):
            flow.add_parallel_step(["a", "missing"])


class TestFlowExecution:
    """Tests for flow execution."""

    def test_single_agent_flow(self):
        flow = Flow(FlowConfig(name="simple"))
        flow.add_agent(_agent("worker"))
        flow.add_step("worker")

        result = flow.run(input_data="process this")
        assert result["success"] is True
        assert "worker_0" in result["results"]

    def test_sequential_multi_agent(self):
        flow = Flow(FlowConfig(name="pipeline"))
        flow.add_agent(_agent("research"))
        flow.add_agent(_agent("write"))

        flow.add_step("research")
        flow.add_step("write")

        result = flow.run(input_data="topic")
        assert result["success"] is True
        assert "research_0" in result["results"]
        assert "write_1" in result["results"]

    def test_parallel_execution(self):
        flow = Flow(FlowConfig(name="parallel"))
        flow.add_agent(_agent("a"))
        flow.add_agent(_agent("b"))

        flow.add_parallel_step(["a", "b"])

        result = flow.run(input_data="data")
        assert result["success"] is True
        assert len(result["results"]) == 2

    def test_mixed_sequential_and_parallel(self):
        flow = Flow(FlowConfig(name="mixed"))
        flow.add_agent(_agent("start"))
        flow.add_agent(_agent("branch_a"))
        flow.add_agent(_agent("branch_b"))
        flow.add_agent(_agent("finish"))

        flow.add_step("start")
        flow.add_parallel_step(["branch_a", "branch_b"])
        flow.add_step("finish")

        result = flow.run(input_data="input")
        assert result["success"] is True

    def test_initial_state_passed_through(self):
        flow = Flow(FlowConfig(name="stateful"))
        flow.add_agent(_agent("worker"))
        flow.add_step("worker")

        result = flow.run(
            input_data="go",
            initial_state={"user_id": 99},
        )
        assert result["success"] is True
        assert result["state"]["user_id"] == 99

    def test_execution_time_tracked(self):
        flow = Flow(FlowConfig(name="timed"))
        flow.add_agent(_agent("worker"))
        flow.add_step("worker")

        result = flow.run(input_data="go")
        assert result["execution_time_ms"] >= 0


class TestFlowEvents:
    """Tests for event hooks."""

    def test_step_start_hook_called(self):
        events = []
        flow = Flow(FlowConfig(name="hooks"))
        flow.add_agent(_agent("worker"))
        flow.add_step("worker")
        flow.on_step_start.append(lambda e: events.append(e))

        flow.run(input_data="go")
        assert len(events) == 1
        assert events[0].event_type == "step_start"

    def test_step_complete_hook_called(self):
        events = []
        flow = Flow(FlowConfig(name="hooks"))
        flow.add_agent(_agent("worker"))
        flow.add_step("worker")
        flow.on_step_complete.append(lambda e: events.append(e))

        flow.run(input_data="go")
        assert len(events) == 1
        assert events[0].event_type == "step_complete"

    def test_get_and_clear_events(self):
        flow = Flow(FlowConfig(name="events"))
        flow.add_agent(_agent("worker"))
        flow.add_step("worker")
        flow.run(input_data="go")

        assert len(flow.get_events()) > 0
        flow.clear_events()
        assert len(flow.get_events()) == 0
