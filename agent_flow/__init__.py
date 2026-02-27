"""Agent-flow: A lightweight multi-agent orchestration framework."""

from .agent import Agent, LLMProvider, MockLLMProvider
from .flow import Flow
from .router import (
    Router,
    ConditionalRouter,
    ContentRouter,
    FallbackRouter,
    RoundRobinRouter,
)
from .state import FlowState, StateSnapshot
from .types import (
    AgentResult,
    AgentConfig,
    FlowConfig,
    FlowStep,
    ToolDefinition,
    RouterDecision,
    FlowEvent,
    StepType,
    RouterType,
)

__version__ = "0.1.0"
__author__ = "Anmol Dhingra"
__license__ = "MIT"

__all__ = [
    # Core classes
    "Agent",
    "Flow",
    "FlowState",
    "StateSnapshot",
    
    # LLM providers
    "LLMProvider",
    "MockLLMProvider",
    
    # Routers
    "Router",
    "ConditionalRouter",
    "ContentRouter",
    "FallbackRouter",
    "RoundRobinRouter",
    
    # Types and configurations
    "AgentResult",
    "AgentConfig",
    "FlowConfig",
    "FlowStep",
    "ToolDefinition",
    "RouterDecision",
    "FlowEvent",
    "StepType",
    "RouterType",
]
