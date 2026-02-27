"""Tests for Agent class."""

import pytest

from agent_flow import Agent, AgentConfig, MockLLMProvider
from agent_flow.agent import LLMProvider
from agent_flow.types import ToolDefinition
from agent_flow.state import FlowState


class TestAgentConfig:
    """Tests for AgentConfig defaults and construction."""

    def test_minimal_config(self):
        config = AgentConfig(name="test", role="tester", system_prompt="Do testing.")
        assert config.name == "test"
        assert config.model == "gpt-4-turbo"
        assert config.temperature == 0.7
        assert config.retry_attempts == 3
        assert config.tools == []

    def test_custom_config(self):
        config = AgentConfig(
            name="writer",
            role="content writer",
            system_prompt="Write content.",
            model="gpt-3.5-turbo",
            temperature=0.2,
            max_tokens=4096,
            retry_attempts=5,
        )
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.2
        assert config.max_tokens == 4096
        assert config.retry_attempts == 5


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    def test_returns_echo_response(self):
        provider = MockLLMProvider()
        result = provider.call(
            system_prompt="You are helpful.",
            user_message="Hello world",
        )
        assert "Hello world" in result["response"]
        assert "tokens" in result
        assert result["tool_calls"] == []

    def test_accepts_optional_params(self):
        provider = MockLLMProvider()
        result = provider.call(
            system_prompt="system",
            user_message="msg",
            temperature=0.0,
            max_tokens=100,
            tools=[{"name": "calc"}],
        )
        assert result["response"] is not None


class TestAgent:
    """Tests for Agent execution."""

    def _make_agent(self, name: str = "agent", **kwargs) -> Agent:
        config = AgentConfig(
            name=name,
            role=kwargs.get("role", "test role"),
            system_prompt=kwargs.get("system_prompt", "You are a test agent."),
            **{k: v for k, v in kwargs.items() if k not in ("role", "system_prompt")},
        )
        return Agent(config)

    def test_basic_execution(self):
        agent = self._make_agent()
        result = agent.execute("test input")
        assert result.success is True
        assert result.agent_name == "agent"
        assert "test input" in result.output

    def test_execution_records_history(self):
        agent = self._make_agent()
        agent.execute("first")
        agent.execute("second")
        history = agent.get_execution_history()
        assert len(history) == 2
        assert "first" in history[0].output
        assert "second" in history[1].output

    def test_clear_history(self):
        agent = self._make_agent()
        agent.execute("data")
        agent.clear_history()
        assert len(agent.get_execution_history()) == 0

    def test_execution_with_state(self):
        agent = self._make_agent()
        state = FlowState({"user_id": 42})
        result = agent.execute("query", state=state)
        assert result.success is True

    def test_execution_with_context(self):
        agent = self._make_agent()
        result = agent.execute("query", context={"session": "abc"})
        assert result.success is True

    def test_properties(self):
        agent = self._make_agent(name="bot", role="assistant", system_prompt="Help.")
        assert agent.name == "bot"
        assert agent.role == "assistant"
        assert agent.system_prompt == "Help."

    def test_execution_time_recorded(self):
        agent = self._make_agent()
        result = agent.execute("data")
        assert result.execution_time_ms >= 0

    def test_tokens_recorded(self):
        agent = self._make_agent()
        result = agent.execute("data")
        assert result.tokens_used is not None
        assert "input" in result.tokens_used

    def test_tool_integration(self):
        agent = self._make_agent()
        tool = ToolDefinition(
            name="calculator",
            description="Math",
            parameters={"type": "object", "properties": {}},
            handler=lambda: 42,
        )
        agent.add_tool(tool)
        assert len(agent.config.tools) == 1

    def test_retry_on_failure(self):
        """Verify retry logic by using a provider that fails then succeeds."""

        class FlakeyProvider(LLMProvider):
            def __init__(self):
                self.call_count = 0

            def call(self, system_prompt, user_message, **kwargs):
                self.call_count += 1
                if self.call_count < 3:
                    raise RuntimeError("Transient error")
                return {
                    "response": f"Success: {user_message}",
                    "tokens": {"input": 5, "output": 10},
                    "tool_calls": [],
                }

        provider = FlakeyProvider()
        config = AgentConfig(
            name="retry_agent",
            role="tester",
            system_prompt="test",
            retry_attempts=3,
            retry_delay_ms=0,
        )
        agent = Agent(config, llm_provider=provider)
        result = agent.execute("hello")
        assert result.success is True
        assert provider.call_count == 3

    def test_all_retries_exhausted(self):
        """Agent returns error when all retries fail."""

        class AlwaysFailProvider(LLMProvider):
            def call(self, system_prompt, user_message, **kwargs):
                raise RuntimeError("Permanent error")

        config = AgentConfig(
            name="fail_agent",
            role="tester",
            system_prompt="test",
            retry_attempts=2,
            retry_delay_ms=0,
        )
        agent = Agent(config, llm_provider=AlwaysFailProvider())
        result = agent.execute("hello")
        assert result.success is False
        assert "Permanent error" in result.error


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_success_str(self):
        from agent_flow.types import AgentResult

        r = AgentResult(agent_name="a", success=True, output="done")
        assert "done" in str(r)

    def test_error_str(self):
        from agent_flow.types import AgentResult

        r = AgentResult(agent_name="a", success=False, output=None, error="bad")
        assert "ERROR" in str(r)
        assert "bad" in str(r)
