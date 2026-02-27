"""Agent class for executing tasks with retry logic and tool support."""

import time
import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from .types import AgentResult, AgentConfig, ToolDefinition
from .state import FlowState


logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def call(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Call the LLM.

        Args:
            system_prompt: System prompt for the model
            user_message: User message/query
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of tool definitions

        Returns:
            Dictionary with 'response', 'tokens', and 'tool_calls'
        """
        pass


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def call(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Mock LLM call that returns echo response."""
        return {
            "response": f"Processed by agent: {user_message}",
            "tokens": {"input": 10, "output": 20},
            "tool_calls": [],
        }


class Agent:
    """An AI agent with specific role and capabilities."""

    def __init__(
        self,
        config: AgentConfig,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        """Initialize an agent.

        Args:
            config: AgentConfig with agent settings
            llm_provider: LLM provider instance. Defaults to MockLLMProvider.
        """
        self.config = config
        self.llm_provider = llm_provider or MockLLMProvider()
        self._execution_history: List[AgentResult] = []

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name

    @property
    def role(self) -> str:
        """Get agent role."""
        return self.config.role

    @property
    def system_prompt(self) -> str:
        """Get system prompt."""
        return self.config.system_prompt

    def add_tool(self, tool: ToolDefinition) -> None:
        """Add a tool/function the agent can use.

        Args:
            tool: ToolDefinition to add
        """
        self.config.tools.append(tool)

    def execute(
        self,
        input_data: Any,
        state: Optional[FlowState] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """Execute the agent on input data with retry logic.

        Args:
            input_data: Input to process
            state: Optional FlowState for context
            context: Optional additional context

        Returns:
            AgentResult with output or error
        """
        context = context or {}
        state = state or FlowState()

        # Prepare the message
        message = self._prepare_message(input_data, state, context)

        # Prepare tools if any
        tools_list = [tool.to_dict() for tool in self.config.tools] if self.config.tools else None

        # Execute with retry logic
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()

                response = self.llm_provider.call(
                    system_prompt=self.system_prompt,
                    user_message=message,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    tools=tools_list,
                )

                execution_time_ms = (time.time() - start_time) * 1000

                # Process tool calls if any
                output = self._process_response(response, state, context)

                result = AgentResult(
                    agent_name=self.name,
                    success=True,
                    output=output,
                    tokens_used=response.get("tokens"),
                    execution_time_ms=execution_time_ms,
                )

                self._execution_history.append(result)
                logger.info(f"Agent {self.name} executed successfully in {execution_time_ms:.2f}ms")

                return result

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Agent {self.name} attempt {attempt + 1} failed: {error_msg}"
                )

                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay_ms / 1000)
                else:
                    result = AgentResult(
                        agent_name=self.name,
                        success=False,
                        output=None,
                        error=error_msg,
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )
                    self._execution_history.append(result)
                    return result

        # Should not reach here
        return AgentResult(
            agent_name=self.name,
            success=False,
            output=None,
            error="Unknown error in agent execution",
        )

    def _prepare_message(
        self,
        input_data: Any,
        state: FlowState,
        context: Dict[str, Any],
    ) -> str:
        """Prepare the message to send to LLM.

        Args:
            input_data: Input data
            state: Flow state
            context: Additional context

        Returns:
            Formatted message string
        """
        if isinstance(input_data, str):
            message = input_data
        else:
            message = str(input_data)

        # Add context if available
        if state.to_dict():
            message += f"\n\nContext: {state.to_dict()}"

        if context:
            message += f"\n\nAdditional Context: {context}"

        return message

    def _process_response(
        self,
        response: Dict[str, Any],
        state: FlowState,
        context: Dict[str, Any],
    ) -> Any:
        """Process LLM response and handle tool calls.

        Args:
            response: Response from LLM provider
            state: Flow state for tool execution
            context: Additional context

        Returns:
            Processed output
        """
        output = response.get("response", "")

        # Handle tool calls if present
        tool_calls = response.get("tool_calls", [])
        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})

                # Find and execute the tool
                for tool in self.config.tools:
                    if tool.name == tool_name and tool.handler:
                        try:
                            result = tool.handler(**tool_args)
                            output += f"\n[{tool_name} result: {result}]"
                        except Exception as e:
                            logger.error(f"Tool execution failed: {e}")

        return output

    def get_execution_history(self) -> List[AgentResult]:
        """Get history of agent executions.

        Returns:
            List of AgentResult objects
        """
        return self._execution_history.copy()

    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()
