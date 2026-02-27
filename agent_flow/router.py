"""Routers for conditional branching in agent flows."""

from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from enum import Enum

from .types import RouterDecision
from .state import FlowState


class Router(ABC):
    """Abstract base class for routers."""
    
    @abstractmethod
    def decide(
        self,
        input_data: Any,
        state: FlowState,
        available_agents: List[str],
    ) -> RouterDecision:
        """Make a routing decision.
        
        Args:
            input_data: Input data or agent output
            state: Current flow state
            available_agents: List of available agent names
            
        Returns:
            RouterDecision with next agent to execute
        """
        pass


class ConditionalRouter(Router):
    """Routes to different agents based on conditions."""
    
    def __init__(
        self,
        conditions: Dict[str, Callable[[Any, FlowState], bool]],
        default_agent: Optional[str] = None,
    ) -> None:
        """Initialize conditional router.
        
        Args:
            conditions: Mapping of agent names to condition functions
            default_agent: Default agent if no condition matches
        """
        self.conditions = conditions
        self.default_agent = default_agent
    
    def decide(
        self,
        input_data: Any,
        state: FlowState,
        available_agents: List[str],
    ) -> RouterDecision:
        """Decide based on conditions.
        
        Args:
            input_data: Input data or output to evaluate
            state: Current flow state
            available_agents: List of available agents
            
        Returns:
            RouterDecision with next agent
        """
        for agent_name, condition in self.conditions.items():
            if agent_name in available_agents:
                try:
                    if condition(input_data, state):
                        return RouterDecision(
                            next_agent=agent_name,
                            confidence=1.0,
                            reason=f"Condition matched for {agent_name}",
                        )
                except Exception as e:
                    pass  # Condition failed, try next
        
        # Use default agent
        if self.default_agent and self.default_agent in available_agents:
            return RouterDecision(
                next_agent=self.default_agent,
                confidence=0.5,
                reason="Using default agent",
            )
        
        # Fallback to first available agent
        if available_agents:
            return RouterDecision(
                next_agent=available_agents[0],
                confidence=0.0,
                reason="No conditions matched, using first available agent",
            )
        
        raise ValueError("No available agents to route to")


class ContentRouter(Router):
    """Routes based on content classification."""
    
    def __init__(
        self,
        classifier: Callable[[Any], str],
        routing_map: Dict[str, str],
        default_agent: Optional[str] = None,
    ) -> None:
        """Initialize content router.
        
        Args:
            classifier: Function that classifies input and returns a category
            routing_map: Mapping of categories to agent names
            default_agent: Default agent if classification doesn't map to agent
        """
        self.classifier = classifier
        self.routing_map = routing_map
        self.default_agent = default_agent
    
    def decide(
        self,
        input_data: Any,
        state: FlowState,
        available_agents: List[str],
    ) -> RouterDecision:
        """Decide based on content classification.
        
        Args:
            input_data: Input to classify
            state: Current flow state
            available_agents: List of available agents
            
        Returns:
            RouterDecision with next agent
        """
        try:
            category = self.classifier(input_data)
            agent_name = self.routing_map.get(category)
            
            if agent_name and agent_name in available_agents:
                return RouterDecision(
                    next_agent=agent_name,
                    confidence=0.85,
                    reason=f"Classified as {category}",
                    metadata={"category": category},
                )
        except Exception as e:
            pass  # Classification failed
        
        # Use default agent
        if self.default_agent and self.default_agent in available_agents:
            return RouterDecision(
                next_agent=self.default_agent,
                confidence=0.5,
                reason="Classification failed, using default agent",
            )
        
        # Fallback to first available agent
        if available_agents:
            return RouterDecision(
                next_agent=available_agents[0],
                confidence=0.0,
                reason="No classification match, using first available agent",
            )
        
        raise ValueError("No available agents to route to")


class FallbackRouter(Router):
    """Tries agents in order until one succeeds."""
    
    def __init__(self, agent_order: List[str]) -> None:
        """Initialize fallback router.
        
        Args:
            agent_order: List of agent names in order of preference
        """
        self.agent_order = agent_order
    
    def decide(
        self,
        input_data: Any,
        state: FlowState,
        available_agents: List[str],
    ) -> RouterDecision:
        """Return the first available agent in order.
        
        Args:
            input_data: Input (not used for decision)
            state: Current flow state
            available_agents: List of available agents
            
        Returns:
            RouterDecision with next agent in order
        """
        for agent_name in self.agent_order:
            if agent_name in available_agents:
                priority = self.agent_order.index(agent_name)
                return RouterDecision(
                    next_agent=agent_name,
                    confidence=1.0 - (priority * 0.1),
                    reason=f"Fallback priority {priority}",
                    metadata={"priority": priority},
                )
        
        # No agents in order available, use first available
        if available_agents:
            return RouterDecision(
                next_agent=available_agents[0],
                confidence=0.1,
                reason="No agents in fallback order available",
            )
        
        raise ValueError("No available agents to route to")


class RoundRobinRouter(Router):
    """Routes to agents in round-robin fashion."""
    
    def __init__(self, agent_order: List[str]) -> None:
        """Initialize round-robin router.
        
        Args:
            agent_order: List of agent names to cycle through
        """
        self.agent_order = agent_order
        self._current_index = 0
    
    def decide(
        self,
        input_data: Any,
        state: FlowState,
        available_agents: List[str],
    ) -> RouterDecision:
        """Route to next agent in round-robin fashion.
        
        Args:
            input_data: Input (not used for decision)
            state: Current flow state
            available_agents: List of available agents
            
        Returns:
            RouterDecision with next agent in rotation
        """
        valid_agents = [a for a in self.agent_order if a in available_agents]
        
        if not valid_agents:
            raise ValueError("No available agents to route to")
        
        agent_name = valid_agents[self._current_index % len(valid_agents)]
        self._current_index += 1
        
        return RouterDecision(
            next_agent=agent_name,
            confidence=1.0,
            reason=f"Round-robin selection (index {self._current_index - 1})",
        )
