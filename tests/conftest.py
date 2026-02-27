"""Shared fixtures for agent-flow tests."""

import pytest

from agent_flow import Agent, AgentConfig, Flow, FlowConfig


@pytest.fixture
def simple_agent():
    """Create a simple test agent."""
    return Agent(AgentConfig(
        name="test_agent",
        role="Test role",
        system_prompt="You are a test agent.",
    ))


@pytest.fixture
def simple_flow():
    """Create a simple single-agent flow."""
    flow = Flow(FlowConfig(name="test_flow"))
    agent = Agent(AgentConfig(
        name="worker",
        role="Worker",
        system_prompt="Process input.",
    ))
    flow.add_agent(agent)
    flow.add_step("worker")
    return flow
