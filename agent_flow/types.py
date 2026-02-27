"""Type definitions and data classes for agent-flow."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class StepType(str, Enum):
    """Enumeration of step execution types."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class RouterType(str, Enum):
    """Enumeration of router decision types."""
    CONDITIONAL = "conditional"
    CONTENT = "content"
    FALLBACK = "fallback"


@dataclass
class AgentResult:
    """Result returned by an agent execution."""

    agent_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    tokens_used: Optional[Dict[str, int]] = None
    execution_time_ms: float = 0.0

    def __str__(self) -> str:
        """Return string representation of the result."""
        if self.success:
            return f"AgentResult({self.agent_name}): {self.output}"
        return f"AgentResult({self.agent_name}) ERROR: {self.error}"


@dataclass
class ToolDefinition:
    """Definition of a tool/function an agent can use."""

    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Optional[Callable[..., Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM APIs."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    role: str
    system_prompt: str
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048
    retry_attempts: int = 3
    retry_delay_ms: int = 1000
    tools: List[ToolDefinition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowStep:
    """Definition of a step in the flow."""

    agent_name: str
    step_type: StepType = StepType.SEQUENTIAL
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouterDecision:
    """Decision made by a router."""

    next_agent: str
    confidence: float = 1.0
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowConfig:
    """Configuration for a flow."""

    name: str
    description: str = ""
    timeout_seconds: int = 300
    max_parallel_steps: int = 5
    enable_state_history: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowEvent:
    """Event emitted during flow execution."""

    event_type: str  # "step_start", "step_complete", "error", etc.
    timestamp: float
    flow_name: str
    step_name: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
