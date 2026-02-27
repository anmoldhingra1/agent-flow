# Agent-Flow Quick Reference

## Basic Usage

### Create an Agent
```python
from agent_flow import Agent, AgentConfig

agent = Agent(AgentConfig(
    name="analyzer",
    role="Data analyst",
    system_prompt="Analyze the provided data and extract key insights.",
    model="gpt-4-turbo",
    temperature=0.7,
    max_tokens=1500,
    retry_attempts=3,
))
```

### Execute Agent
```python
from agent_flow import FlowState

state = FlowState(initial_state={"user_id": 123})
result = agent.execute("Analyze this data: ...", state)

if result.success:
    print(result.output)
else:
    print(f"Error: {result.error}")
```

### Create a Flow
```python
from agent_flow import Flow, FlowConfig

flow = Flow(FlowConfig(
    name="data_pipeline",
    description="Process and analyze data",
    timeout_seconds=300,
))

flow.add_agent(agent1)
flow.add_agent(agent2)
flow.add_agent(agent3)
```

### Define Sequential Steps
```python
flow.add_step("agent1")
flow.add_step("agent2")
flow.add_step("agent3")
```

### Define Parallel Steps
```python
flow.add_parallel_step(["agent1", "agent2", "agent3"])
```

### Run Flow
```python
result = flow.run(
    input_data="Process this content",
    initial_state={"user_id": 123},
)

if result["success"]:
    print(result["results"])
    print(f"Executed in {result['execution_time_ms']}ms")
```

## Routers

### Conditional Routing
```python
from agent_flow import ConditionalRouter

def is_complex(output, state):
    return len(output.split()) > 50

def is_urgent(output, state):
    return "urgent" in output.lower()

router = ConditionalRouter(
    conditions={
        "complex_agent": is_complex,
        "urgent_agent": is_urgent,
    },
    default_agent="normal_agent",
)

flow.add_router(step_index=0, router=router)
```

### Content Routing
```python
from agent_flow import ContentRouter

def classify(text):
    if "billing" in text.lower():
        return "billing"
    elif "technical" in text.lower():
        return "technical"
    return "general"

router = ContentRouter(
    classifier=classify,
    routing_map={
        "billing": "billing_agent",
        "technical": "tech_agent",
        "general": "general_agent",
    },
    default_agent="general_agent",
)
```

### Fallback Routing
```python
from agent_flow import FallbackRouter

router = FallbackRouter(agent_order=["primary", "secondary", "fallback"])
```

## State Management

### Initialize State
```python
from agent_flow import FlowState

state = FlowState(initial_state={
    "user_id": 123,
    "context": "support_ticket",
})
```

### Access State
```python
user_id = state.get("user_id")
context = state.get("context", default="default_context")
```

### Update State
```python
state.set("result", agent_output)
state.update({
    "processed": True,
    "timestamp": datetime.now(),
})
```

### Snapshots
```python
snapshot = state.snapshot("step_1")

history = state.get_history()
for snap in history:
    print(f"{snap.step_name}: {snap.timestamp}")

state.rollback_to(0)
```

### Serialize State
```python
json_str = state.to_json()
dict_data = state.to_dict()

state2 = FlowState.from_json(json_str)
state3 = FlowState.from_dict(dict_data)
```

## Tools and Functions

### Define a Tool
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
            "expression": {"type": "string"}
        },
        "required": ["expression"],
    },
    handler=calculate,
)
```

### Add Tool to Agent
```python
agent.add_tool(tool)
```

## Event Hooks

### Monitor Execution
```python
def on_start(event):
    print(f"Starting: {event.step_name}")

def on_complete(event):
    time_ms = event.data.get("execution_time_ms")
    print(f"Completed in {time_ms}ms")

def on_error(event):
    error = event.data.get("error")
    print(f"Error: {error}")

flow.on_step_start.append(on_start)
flow.on_step_complete.append(on_complete)
flow.on_error.append(on_error)

flow.run(input_data)
```

### Get Event History
```python
events = flow.get_events()
for event in events:
    print(f"{event.event_type} at {event.timestamp}")
```

## Custom LLM Provider

### Implement Provider
```python
from agent_flow import LLMProvider

class MyLLMProvider(LLMProvider):
    def call(self, system_prompt, user_message, **kwargs):
        # Call your LLM API here
        response = my_llm_api(
            system=system_prompt,
            user=user_message,
        )
        
        return {
            "response": response,
            "tokens": {"input": 100, "output": 50},
            "tool_calls": [],
        }
```

### Use Custom Provider
```python
provider = MyLLMProvider()
agent = Agent(config, llm_provider=provider)
```

## Type Hints Reference

```python
from agent_flow import (
    AgentResult,      # Agent execution result
    AgentConfig,      # Agent configuration
    FlowConfig,       # Flow configuration
    FlowStep,         # Step definition
    ToolDefinition,   # Tool specification
    RouterDecision,   # Router decision
    FlowEvent,        # Execution event
    StepType,         # SEQUENTIAL, PARALLEL
    RouterType,       # CONDITIONAL, CONTENT, FALLBACK
)
```

## Common Patterns

### Sequential Pipeline
```python
flow.add_step("researcher")
flow.add_step("analyzer")
flow.add_step("writer")

result = flow.run(input_data)
```

### Parallel Processing
```python
flow.add_step("classifier")
flow.add_parallel_step(["processor1", "processor2", "processor3"])
flow.add_step("aggregator")

result = flow.run(input_data)
```

### Conditional Branching
```python
flow.add_step("detector")
flow.add_router(0, my_router)
flow.add_step("handler_a")
flow.add_step("handler_b")
flow.add_step("handler_c")

result = flow.run(input_data)
```

### Complex Workflow
```python
# Initial processing
flow.add_step("validator")
flow.add_step("enricher")

# Parallel analysis
flow.add_parallel_step(["analyzer1", "analyzer2", "analyzer3"])

# Conditional routing based on analysis
flow.add_router(2, classification_router)

# Final steps
flow.add_step("aggregator")
flow.add_step("reporter")

result = flow.run(input_data)
```

## Debugging

### Check Execution History
```python
history = agent.get_execution_history()
for result in history:
    print(f"Success: {result.success}")
    print(f"Time: {result.execution_time_ms}ms")
    print(f"Output: {result.output}")
```

### Inspect Flow State
```python
result = flow.run(input_data)
state_dict = result["state"]
for key, value in state_dict.items():
    print(f"{key}: {value}")
```

### Access State Snapshots
```python
snapshots = flow._events  # Internal - for debugging only
for event in snapshots:
    print(f"{event.event_type} at step {event.step_name}")
```

## Error Handling

### Handle Agent Errors
```python
result = agent.execute(input_data, state)
if not result.success:
    logger.error(f"Agent failed: {result.error}")
    # Implement retry or fallback logic
```

### Handle Flow Errors
```python
result = flow.run(input_data)
if not result["success"]:
    error = result.get("error")
    execution_time = result["execution_time_ms"]
    logger.error(f"Flow failed after {execution_time}ms: {error}")
```

### Configure Timeouts
```python
flow = Flow(FlowConfig(
    name="my_flow",
    timeout_seconds=300,  # 5 minutes
))
```

## Testing with Mock Provider

```python
from agent_flow import Agent, AgentConfig, MockLLMProvider

# MockLLMProvider returns deterministic responses
agent = Agent(
    AgentConfig(name="test", role="test", system_prompt="test"),
    llm_provider=MockLLMProvider()
)

result = agent.execute("test input")
assert result.success
assert "Processed by agent" in result.output
```

## Performance Tips

1. Use parallel_step() when agents are independent
2. Set appropriate timeout_seconds for your use case
3. Configure retry_attempts based on reliability needs
4. Use mock provider for testing
5. Monitor execution with event hooks
6. Serialize state for large workflows
7. Use state locking for critical values

## Common Issues and Solutions

### Agent Always Fails
- Check system_prompt is clear and specific
- Verify LLMProvider is properly configured
- Try with MockLLMProvider first
- Increase retry_attempts

### State Not Propagating
- Ensure agents read from `state` parameter
- Use state.set() to update values
- Check step dependencies are correct

### Parallel Steps Not Running
- Verify agents are independent
- Check max_parallel_steps isn't exceeded
- Use add_parallel_step() not multiple add_step()

### Router Not Deciding
- Test classifier/condition functions independently
- Provide valid default_agent
- Check available_agents list is populated

## Version Information

- **Package Version**: 0.1.0
- **Python**: 3.9+
- **License**: MIT
- **Author**: Anmol Dhingra
