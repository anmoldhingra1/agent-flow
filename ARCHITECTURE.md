# Agent-Flow Architecture

## Overview

agent-flow is a lightweight, production-ready multi-agent orchestration framework built on clean architectural principles. It enables composition of AI agents into complex workflows with state management, conditional routing, and parallel execution.

## Core Components

### 1. Agent (`agent_flow/agent.py`)

The **Agent** is the fundamental execution unit. Each agent wraps LLM interactions with:

- **Configuration**: Name, role, system prompt, model selection, temperature, retry settings
- **Execution**: `execute()` method that handles input processing with automatic retry logic
- **Tools**: Support for function/tool definitions that agents can invoke
- **History**: Tracks all executions for debugging and monitoring

Key features:
- Automatic retry logic with configurable delays
- LLM provider abstraction (easily swap implementations)
- Tool execution with error handling
- Detailed execution history and metrics

```python
agent = Agent(AgentConfig(
    name="analyzer",
    role="Data analyst",
    system_prompt="Analyze the data...",
    retry_attempts=3,
))

result = agent.execute(input_data, state)
```

### 2. Flow (`agent_flow/flow.py`)

The **Flow** orchestrates agents into workflows. It manages:

- **Agent Registry**: Central registry of all agents in the flow
- **Step Definition**: Sequential and parallel execution steps
- **State Management**: Passes immutable state across agents
- **Event System**: Hooks for monitoring and reacting to execution
- **Routing**: Integration with routers for conditional branching

Key features:
- Sequential execution with dependencies
- Parallel execution with thread pooling
- Timeout enforcement
- Event hooks for logging/monitoring
- Detailed execution results and metrics

```python
flow = Flow(FlowConfig(name="my_pipeline"))
flow.add_agent(agent1)
flow.add_agent(agent2)
flow.add_step("agent1")
flow.add_parallel_step(["agent2", "agent3"])

result = flow.run(input_data="...")
```

### 3. FlowState (`agent_flow/state.py`)

The **FlowState** manages data across agent handoffs with:

- **Immutable Snapshots**: Point-in-time state captures
- **History Tracking**: Full audit trail of state changes
- **Rollback Support**: Revert to previous snapshots
- **Parallel Merging**: Combine state from parallel branches
- **Serialization**: JSON support for persistence

Key features:
- Copy-on-write semantics for thread safety
- State locking for critical values
- History with timestamps
- Complete JSON serialization/deserialization

```python
state = FlowState(initial_state={"user_id": 123})
state.set("step1_result", result)
snapshot = state.snapshot("step1")
state.merge({"branch_a": other_state})
```

### 4. Routers (`agent_flow/router.py`)

**Routers** enable intelligent conditional branching:

- **ConditionalRouter**: Route based on custom predicates
- **ContentRouter**: Route based on classification results
- **FallbackRouter**: Try agents in priority order
- **RoundRobinRouter**: Distribute across agents evenly

Router interface:
```python
router.decide(input_data, state, available_agents) -> RouterDecision
```

### 5. Types (`agent_flow/types.py`)

Comprehensive type definitions ensure type safety:

- **AgentResult**: Structured agent execution output
- **AgentConfig**: Agent configuration with defaults
- **FlowConfig**: Flow-wide settings
- **FlowStep**: Step definition with dependencies
- **FlowEvent**: Execution events for monitoring
- **ToolDefinition**: Tool/function specification
- **RouterDecision**: Routing decision with metadata

## Architecture Patterns

### 1. Sequential Execution

```
Agent1 -> Agent2 -> Agent3
          (pass state)
```

Each agent receives output from previous agent, can read full state.

### 2. Parallel Execution

```
        ├-> Agent2
Agent1 -┼-> Agent3
        └-> Agent4
           (merged state)
```

Multiple agents execute concurrently, results merged back to state.

### 3. Conditional Branching

```
Classifier -> Router -> Agent_A (if condition1)
                    -> Agent_B (if condition2)
                    -> Agent_C (default)
```

Router examines output/state and routes to appropriate agent.

### 4. Complex Workflows

```
Input
  ↓
Sequential: Researcher
  ↓
Parallel: [Analyzer, Summarizer]
  ↓
Router (based on analysis)
  ├→ Writer (if comprehensive)
  └→ Quick-Reporter (if brief)
  ↓
Final Output
```

## Design Principles

### 1. Separation of Concerns

- **Agents**: Encapsulate LLM interactions
- **Flows**: Orchestrate agent coordination
- **State**: Manage data across boundaries
- **Routers**: Handle branching logic

### 2. Type Safety

- All public APIs use type hints
- Dataclasses for configuration
- Enums for fixed options
- Optional types for nullable values

### 3. Extensibility

- LLMProvider ABC for custom LLM integration
- Router ABC for custom routing logic
- Event hooks for monitoring/logging
- Tool system for agent capabilities

### 4. Production Ready

- Comprehensive error handling
- Retry logic with exponential backoff
- Timeout enforcement
- Complete audit trails
- Thread-safe concurrent execution

## Error Handling Strategy

1. **Agent Level**: Retry logic with configurable attempts
2. **Step Level**: Error events emitted, flow continues or fails
3. **Flow Level**: Timeout enforcement, complete execution tracking
4. **Graceful Degradation**: Fallback agents, default routes

## State Management Strategy

1. **Immutable Snapshots**: Every step creates snapshot
2. **Atomic Updates**: State updated after successful execution
3. **Parallel Safety**: Separate state per branch, merged after
4. **Rollback Support**: Full history enables state recovery
5. **Serialization**: JSON export for persistence/debugging

## Performance Considerations

1. **Concurrent Execution**: ThreadPoolExecutor for parallel steps
2. **State Copying**: Copy-on-write for thread safety
3. **Event Hooks**: Optional monitoring without perf impact
4. **Timeout Enforcement**: Prevents runaway executions

## Monitoring and Observability

```python
flow.on_step_start.append(lambda e: print(f"Step {e.step_name} starting"))
flow.on_step_complete.append(lambda e: print(f"Step {e.step_name} done"))
flow.on_error.append(lambda e: print(f"Error: {e.data['error']}"))

result = flow.run(input_data)
events = flow.get_events()  # Full event history
history = state.get_history()  # State snapshots
```

## Integration Points

1. **LLM Providers**: Implement LLMProvider ABC
2. **Tool Handlers**: Pass functions as tool handlers
3. **Routing Logic**: Implement Router ABC or use built-ins
4. **Event Monitoring**: Register event hook callbacks
5. **State Persistence**: Serialize/deserialize FlowState

## Testing Strategy

The framework is designed for easy testing:

1. **MockLLMProvider**: Returns deterministic responses
2. **FlowState Snapshots**: Verify state at each step
3. **Event Tracking**: Assert on execution events
4. **Result Validation**: Check outputs and metrics
