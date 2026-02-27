"""Flow orchestrator for managing agent workflows."""

import time
import logging
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .agent import Agent
from .types import FlowStep, StepType, FlowConfig, FlowEvent
from .state import FlowState
from .router import Router


logger = logging.getLogger(__name__)


class Flow:
    """Orchestrates multi-agent workflows with sequential and parallel execution."""
    
    def __init__(self, config: FlowConfig) -> None:
        """Initialize a flow.
        
        Args:
            config: FlowConfig with flow settings
        """
        self.config = config
        self._agents: Dict[str, Agent] = {}
        self._steps: List[FlowStep] = []
        self._routers: Dict[str, Router] = {}
        self._events: List[FlowEvent] = []
        
        # Event hooks
        self.on_step_start: List[Callable[[FlowEvent], None]] = []
        self.on_step_complete: List[Callable[[FlowEvent], None]] = []
        self.on_error: List[Callable[[FlowEvent], None]] = []
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the flow.
        
        Args:
            agent: Agent instance to add
        """
        self._agents[agent.name] = agent
        logger.info(f"Added agent: {agent.name}")
    
    def add_step(
        self,
        agent_name: str,
        step_type: StepType = StepType.SEQUENTIAL,
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a sequential step to the flow.
        
        Args:
            agent_name: Name of agent to execute
            step_type: Type of execution (sequential or parallel)
            depends_on: List of step names this step depends on
            metadata: Optional metadata for the step
        """
        if agent_name not in self._agents:
            raise ValueError(f"Agent {agent_name} not registered in flow")
        
        step = FlowStep(
            agent_name=agent_name,
            step_type=step_type,
            depends_on=depends_on or [],
            metadata=metadata or {},
        )
        self._steps.append(step)
        logger.info(f"Added step for agent {agent_name}")
    
    def add_parallel_step(
        self,
        agent_names: List[str],
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add parallel steps to the flow.
        
        Args:
            agent_names: List of agent names to execute in parallel
            depends_on: List of step names these steps depend on
            metadata: Optional metadata for the steps
        """
        for agent_name in agent_names:
            if agent_name not in self._agents:
                raise ValueError(f"Agent {agent_name} not registered in flow")
        
        for agent_name in agent_names:
            step = FlowStep(
                agent_name=agent_name,
                step_type=StepType.PARALLEL,
                depends_on=depends_on or [],
                metadata=metadata or {},
            )
            self._steps.append(step)
        
        logger.info(f"Added parallel steps for agents: {agent_names}")
    
    def add_router(self, step_index: int, router: Router) -> None:
        """Add a router for conditional branching at a step.
        
        Args:
            step_index: Index of the step to add router to
            router: Router instance
        """
        self._routers[str(step_index)] = router
    
    def run(
        self,
        input_data: Any,
        initial_state: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute the full workflow.
        
        Args:
            input_data: Initial input to the workflow
            initial_state: Optional initial state dictionary
            timeout_seconds: Optional timeout for execution
            
        Returns:
            Dictionary with final state and results
        """
        timeout_seconds = timeout_seconds or self.config.timeout_seconds
        state = FlowState(initial_state or {})
        state.set("_input", input_data)
        
        results: Dict[str, Any] = {}
        execution_start = time.time()
        
        try:
            # Execute steps
            step_index = 0
            while step_index < len(self._steps):
                current_step = self._steps[step_index]
                
                # Check timeout
                if time.time() - execution_start > timeout_seconds:
                    raise TimeoutError(f"Flow execution exceeded {timeout_seconds}s")
                
                # Check if this is a parallel group
                parallel_group = [current_step]
                next_index = step_index + 1
                
                while next_index < len(self._steps):
                    next_step = self._steps[next_index]
                    if next_step.step_type == StepType.PARALLEL and \
                       next_step.depends_on == current_step.depends_on:
                        parallel_group.append(next_step)
                        next_index += 1
                    else:
                        break
                
                if len(parallel_group) > 1:
                    # Execute parallel group
                    self._execute_parallel_group(parallel_group, state, results)
                    step_index = next_index
                else:
                    # Execute single step
                    self._execute_step(current_step, step_index, state, results)
                    step_index += 1
            
            # Emit final event
            event = FlowEvent(
                event_type="flow_complete",
                timestamp=time.time(),
                flow_name=self.config.name,
                data={"total_steps": len(self._steps), "results": results},
            )
            self._events.append(event)
            
            return {
                "success": True,
                "state": state.to_dict(),
                "results": results,
                "execution_time_ms": (time.time() - execution_start) * 1000,
            }
            
        except Exception as e:
            logger.error(f"Flow execution failed: {e}")
            event = FlowEvent(
                event_type="flow_error",
                timestamp=time.time(),
                flow_name=self.config.name,
                data={"error": str(e)},
            )
            self._emit_event("error", event)
            
            return {
                "success": False,
                "state": state.to_dict(),
                "results": results,
                "error": str(e),
                "execution_time_ms": (time.time() - execution_start) * 1000,
            }
    
    def _execute_step(
        self,
        step: FlowStep,
        step_index: int,
        state: FlowState,
        results: Dict[str, Any],
    ) -> None:
        """Execute a single step.
        
        Args:
            step: FlowStep to execute
            step_index: Index of the step
            state: Current flow state
            results: Results dictionary to update
        """
        agent = self._agents[step.agent_name]
        step_name = f"{step.agent_name}_{step_index}"
        
        # Emit step start event
        event = FlowEvent(
            event_type="step_start",
            timestamp=time.time(),
            flow_name=self.config.name,
            step_name=step_name,
            data={"agent": agent.name},
        )
        self._emit_event("start", event)
        
        try:
            # Prepare input
            input_data = state.get("_last_output", state.get("_input"))
            
            # Execute agent
            start_time = time.time()
            result = agent.execute(input_data, state)
            execution_time = time.time() - start_time
            
            # Update state
            state.set("_last_output", result.output)
            state.set(f"_step_{step_name}", {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
            })
            state.snapshot(step_name, {
                "agent_name": result.agent_name,
                "success": result.success,
            })
            
            results[step_name] = result.output
            
            # Emit step complete event
            event = FlowEvent(
                event_type="step_complete",
                timestamp=time.time(),
                flow_name=self.config.name,
                step_name=step_name,
                data={
                    "agent": agent.name,
                    "success": result.success,
                    "execution_time_ms": result.execution_time_ms,
                },
            )
            self._emit_event("complete", event)
            
        except Exception as e:
            logger.error(f"Step {step_name} failed: {e}")
            state.set(f"_step_{step_name}_error", str(e))
            
            event = FlowEvent(
                event_type="step_error",
                timestamp=time.time(),
                flow_name=self.config.name,
                step_name=step_name,
                data={"error": str(e)},
            )
            self._emit_event("error", event)
            raise
    
    def _execute_parallel_group(
        self,
        steps: List[FlowStep],
        state: FlowState,
        results: Dict[str, Any],
    ) -> None:
        """Execute a group of steps in parallel.
        
        Args:
            steps: List of steps to execute in parallel
            state: Current flow state
            results: Results dictionary to update
        """
        if len(steps) > self.config.max_parallel_steps:
            raise ValueError(
                f"Parallel group size {len(steps)} exceeds max {self.config.max_parallel_steps}"
            )
        
        with ThreadPoolExecutor(max_workers=len(steps)) as executor:
            futures = {}
            
            for i, step in enumerate(steps):
                step_name = f"{step.agent_name}_parallel_{i}"
                agent = self._agents[step.agent_name]
                
                # Emit step start event
                event = FlowEvent(
                    event_type="step_start",
                    timestamp=time.time(),
                    flow_name=self.config.name,
                    step_name=step_name,
                    data={"agent": agent.name},
                )
                self._emit_event("start", event)
                
                future = executor.submit(
                    self._execute_agent,
                    agent,
                    state,
                    step_name,
                )
                futures[future] = (step, step_name, agent)
            
            # Collect results
            for future in as_completed(futures):
                step, step_name, agent = futures[future]
                try:
                    result, execution_time = future.result()
                    
                    state.set("_last_output", result.output)
                    state.set(f"_step_{step_name}", {
                        "success": result.success,
                        "output": result.output,
                        "error": result.error,
                    })
                    
                    results[step_name] = result.output
                    
                    # Emit step complete event
                    event = FlowEvent(
                        event_type="step_complete",
                        timestamp=time.time(),
                        flow_name=self.config.name,
                        step_name=step_name,
                        data={
                            "agent": agent.name,
                            "success": result.success,
                            "execution_time_ms": result.execution_time_ms,
                        },
                    )
                    self._emit_event("complete", event)
                    
                except Exception as e:
                    logger.error(f"Parallel step {step_name} failed: {e}")
                    
                    event = FlowEvent(
                        event_type="step_error",
                        timestamp=time.time(),
                        flow_name=self.config.name,
                        step_name=step_name,
                        data={"error": str(e)},
                    )
                    self._emit_event("error", event)
                    raise
    
    def _execute_agent(self, agent: Agent, state: FlowState, step_name: str) -> tuple:
        """Execute an agent and return result and time.
        
        Args:
            agent: Agent to execute
            state: Flow state
            step_name: Name of the step
            
        Returns:
            Tuple of (AgentResult, execution_time)
        """
        input_data = state.get("_last_output", state.get("_input"))
        start_time = time.time()
        result = agent.execute(input_data, state)
        execution_time = time.time() - start_time
        return result, execution_time
    
    def _emit_event(self, event_type: str, event: FlowEvent) -> None:
        """Emit a flow event and call registered hooks.
        
        Args:
            event_type: Type of event (start, complete, error)
            event: FlowEvent object
        """
        self._events.append(event)
        
        if event_type == "start":
            for hook in self.on_step_start:
                try:
                    hook(event)
                except Exception as e:
                    logger.error(f"Error in on_step_start hook: {e}")
        
        elif event_type == "complete":
            for hook in self.on_step_complete:
                try:
                    hook(event)
                except Exception as e:
                    logger.error(f"Error in on_step_complete hook: {e}")
        
        elif event_type == "error":
            for hook in self.on_error:
                try:
                    hook(event)
                except Exception as e:
                    logger.error(f"Error in on_error hook: {e}")
    
    def get_events(self) -> List[FlowEvent]:
        """Get all flow events.
        
        Returns:
            List of FlowEvent objects
        """
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear event history."""
        self._events.clear()
