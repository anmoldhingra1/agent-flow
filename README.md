\![CI](https://github.com/anmoldhingra1/agent-flow/actions/workflows/ci.yml/badge.svg)

# agent-flow

A lightweight multi-agent orchestration framework for building AI workflows. Define agents with specific roles, compose them into sequential or parallel pipelines, manage state across handoffs, and route intelligently based on content or conditions.

## Installation

```bash
pip install agent-flow
```

Or install from source:

```bash
git clone https://github.com/anmol-dhingra/agent-flow.git
cd agent-flow
pip install -e .
```

## Quick Start

Here's a 3-agent research pipeline that takes a topic, researches it, analyzes findings, and produces a report:

```python
from agent_flow import Agent, Flow, AgentConfig, FlowConfig

# Define agents
researcher = Agent(AgentConfig(
    name="researcher",
    role="Research specialist",
    system_prompt="You are a research specialist. Gather detailed information on the topic.",
))

analyzer = Agent(AgentConfig(
    name="analyzer",
    role="Data analyst",
    system_prompt="You are a data analyst. Analyze the research findings and extract key insights.",
))

writer = Agent(AgentConfig(
    name="writer",
    role="Technical writer",
    system_prompt="You are a technical writer. Create a structured report from the analysis.",
))

# Create flow
flow = Flow(FlowConfig(
    name="research_pipeline",
    description="Research topic, analyze, and write report"
))

# Add agents and steps
flow.add_agent(researcher)
flow.add_agent(analyzer)
flow.add_agent(writer)

flow.add_step("researcher")
flow.add_step("analyzer")
flow.add_step("writer")

# Execute
result = flow.run(input_data="Climate change impacts on agriculture")
print(result["results"]["writer_2"])  # Final report
```

## Core Concepts

### Agent

An Agent executes a specific role or task. It has:

- **name**: Unique identifier
- **role**: Human-readable description of what it does
- **system_prompt**: Instructions for the LLM
- **model**: LLM model to use (default: gpt-4-turbo)
- **execute()**: Processes input and returns AgentResult

Agents support retry logic, tool execution, and maintain execution history.

```python
agent = Agent(AgentConfig(
    name="classifier",
    role="Content classifier",
    system_prompt="Classify the content as technical or business.",
    model="gpt-4-turbo",
    temperature=0.3,
    retry_attempts=3,
))

result = agent.execute("Is machine learning production-ready?")
print(result.output)
```

### Flow

A Flow orchestrates agents into workflows. It manages:

- **Agent registration**: add_agent()
- **Sequential steps**: add_step()
- **Parallel execution**: add_parallel_step()
- **State management**: FlowState passed between agents
- **Event hooks**: on_step_start, on_step_complete, on_error

```python
flow = Flow(FlowConfig(
    name="content_pipeline",
    timeout_seconds=300,
))

flow.add_agent(agent1)
flow.add_agent(agent2)

flow.add_step("agent1")
flow.add_parallel_step(["agent2", "agent3"])  # Run in parallel
flow.add_step("agent4")  # Depends on parallel group

result = flow.run(input_data="Process this content")
```

### Router

Routers enable conditional branching. Available routers:

- **ConditionalRouter**: Route based on custom conditions
- **ContentRouter**: Route based on classification
- **FallbackRouter**: Try agents in order until one succeeds
- **RoundRobinRouter**: Distribute load across agents

```python
from agent_flow import ConditionalRouter

router = ConditionalRouter(
    conditions={
        "billing_agent": lambda output, state: "billing" in output.lower(),
        "technical_agent": lambda output, state: "error" in output.lower(),
    },
    default_agent="general_agent",
)
```

## Architecture

agent-flow consists of:

- **Agent**: Wraps LLM execution with retry logic and tool support
- **Flow**: Orchestrates agents with sequential/parallel/conditional execution
- **FlowState**: Manages immutable state snapshots and history
- **Router**: Enables intelligent routing between agents
- **Types**: Data classes for configuration and results

All components use type hints and produce structured outputs suitable for further processing or storage.

## Advanced Usage

### Conditional Routing

Route to different agents based on agent output:

```python
from agent_flow import ConditionalRouter

def is_complex_question(output, state):
    return len(output.split()) > 50 or "complex" in output.lower()

router = ConditionalRouter(
    conditions={
        "advanced_agent": is_complex_question,
        "simple_agent": lambda o, s: not is_complex_question(o, s),
    },
    default_agent="fallback_agent",
)

flow.add_router(step_index=1, router=router)
```

### Parallel Execution

Execute multiple agents concurrently:

```python
# Execute three agents in parallel
flow.add_parallel_step(
    agent_names=["summarizer", "sentiment_analyzer", "keyword_extractor"],
    metadata={"timeout_per_agent": 30},
)

result = flow.run(input_data="Long article text...")

# Access parallel results
print(result["results"]["summarizer_parallel_0"])
print(result["results"]["sentiment_analyzer_parallel_1"])
print(result["results"]["keyword_extractor_parallel_2"])
```

### State Management

Access and modify flow state across agents:

```python
from agent_flow import FlowState

state = FlowState(initial_state={"user_id": 123, "context": "support_ticket"})

# Agents can read state
agent_result = agent.execute("Help this customer", state)

# State is updated by each step
state.set("last_agent", "support_agent")
state.set("ticket_status", "resolved")

# Get immutable snapshots
history = state.get_history()
state.snapshot("checkpoint_1")

# Rollback if needed
state.rollback_to(0)
```

### Event Hooks

React to flow execution events:

```python
def on_step_complete(event):
    print(f"Step {event.step_name} completed in {event.data['execution_time_ms']}ms")

def on_error(event):
    print(f"Error in {event.step_name}: {event.data['error']}")

flow.on_step_complete.append(on_step_complete)
flow.on_error.append(on_error)

flow.run(input_data="...")
```

### Tool Integration

Define tools that agents can call:

```python
from agent_flow import ToolDefinition

def calculate(expression: str) -> float:
    return eval(expression)

tool = ToolDefinition(
    name="calculator",
    description="Evaluate mathematical expressions",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Math expression"}
        },
        "required": ["expression"],
    },
    handler=calculate,
)

agent.add_tool(tool)
```

## License

MIT License. See LICENSE file for details.