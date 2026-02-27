![CI](https://github.com/anmoldhingra1/agent-flow/actions/workflows/ci.yml/badge.svg)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

# agent-flow

A lightweight framework for composing multi-agent AI workflows. Define agents with specific roles, wire them into sequential or parallel pipelines, and route dynamically based on content or conditions.

No vendor lock-in — bring any LLM provider.

## Install

```bash
pip install agent-flow
```

## Quick Start

```python
from agent_flow import Agent, Flow, AgentConfig, FlowConfig

researcher = Agent(AgentConfig(
    name="researcher",
    role="Research specialist",
    system_prompt="Gather detailed information on the given topic.",
))

analyst = Agent(AgentConfig(
    name="analyst",
    role="Data analyst",
    system_prompt="Analyze the research findings and extract key insights.",
))

writer = Agent(AgentConfig(
    name="writer",
    role="Technical writer",
    system_prompt="Create a structured report from the analysis.",
))

flow = Flow(FlowConfig(name="research_pipeline"))
flow.add_agent(researcher)
flow.add_agent(analyst)
flow.add_agent(writer)

flow.add_step("researcher")
flow.add_step("analyst")
flow.add_step("writer")

result = flow.run(input_data="Climate change impacts on agriculture")
```

## Features

**Agents** — Each agent wraps an LLM call with a system prompt, retry logic, tool execution, and execution history. Swap the LLM provider without changing your pipeline code.

```python
from agent_flow import Agent, AgentConfig

agent = Agent(AgentConfig(
    name="classifier",
    role="Content classifier",
    system_prompt="Classify the input as technical or business.",
    temperature=0.3,
    retry_attempts=3,
))
result = agent.execute("Is this a production-ready ML system?")
```

**Parallel execution** — Run independent agents concurrently and collect results.

```python
flow.add_parallel_step(["summarizer", "sentiment", "keywords"])
result = flow.run(input_data="Article text...")
```

**Routing** — Branch pipelines based on agent output using built-in routers.

```python
from agent_flow import ConditionalRouter

router = ConditionalRouter(
    conditions={
        "billing": lambda output, state: "invoice" in output.lower(),
        "support": lambda output, state: "help" in output.lower(),
    },
    default_agent="general",
)
```

Four router types included: `ConditionalRouter`, `ContentRouter`, `FallbackRouter`, `RoundRobinRouter`.

**State management** — Immutable snapshots track state across every handoff. Rollback to any checkpoint.

```python
from agent_flow import FlowState

state = FlowState({"user_id": 123})
state.snapshot("before_analysis")
# ... run agents ...
state.rollback_to(0)  # restore checkpoint
```

**Event hooks** — React to step lifecycle events for logging, metrics, or custom logic.

```python
flow.on_step_complete.append(
    lambda e: print(f"{e.step_name} done in {e.data['execution_time_ms']:.0f}ms")
)
```

**Tools** — Give agents callable tools with structured parameter schemas.

```python
from agent_flow import ToolDefinition

agent.add_tool(ToolDefinition(
    name="calculator",
    description="Evaluate math expressions",
    parameters={"type": "object", "properties": {"expr": {"type": "string"}}},
    handler=lambda expr: eval(expr),
))
```

## Architecture

```
Agent ──┐
Agent ──┤── Flow (sequential / parallel / routed) ── FlowState
Agent ──┘                                              │
  │                                                Snapshots
  └── LLMProvider (pluggable)                      History
       ├── OpenAI                                  Rollback
       ├── Anthropic
       └── MockLLMProvider (testing)
```

Components: `Agent` (LLM execution + retry), `Flow` (orchestration), `FlowState` (immutable state tracking), `Router` (conditional branching), `Types` (typed configs and results).

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

62 tests covering agents, flows, routers, and state management.

## License

MIT
