#!/usr/bin/env python3
"""Validate the agent-flow package structure and imports."""

import sys
from pathlib import Path


def validate_imports():
    """Validate all imports work correctly."""
    print("Validating imports...")
    
    try:
        from agent_flow import (
            Agent,
            Flow,
            FlowState,
            StateSnapshot,
            LLMProvider,
            MockLLMProvider,
            Router,
            ConditionalRouter,
            ContentRouter,
            FallbackRouter,
            RoundRobinRouter,
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
        
        print("✓ All imports successful")
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def validate_package_files():
    """Validate all required package files exist."""
    print("\nValidating package files...")
    
    base_dir = Path(__file__).parent
    required_files = [
        "pyproject.toml",
        "README.md",
        "LICENSE",
        ".gitignore",
        "agent_flow/__init__.py",
        "agent_flow/agent.py",
        "agent_flow/flow.py",
        "agent_flow/router.py",
        "agent_flow/state.py",
        "agent_flow/types.py",
        "examples/research_pipeline.py",
        "examples/customer_support.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✓ {file_path} ({size} bytes)")
        else:
            print(f"✗ {file_path} (MISSING)")
            all_exist = False
    
    return all_exist


def validate_basic_functionality():
    """Validate basic agent-flow functionality."""
    print("\nValidating basic functionality...")
    
    try:
        from agent_flow import Agent, Flow, AgentConfig, FlowConfig
        
        # Create a simple agent
        agent = Agent(AgentConfig(
            name="test_agent",
            role="Test agent",
            system_prompt="You are a test agent.",
        ))
        
        print(f"✓ Agent created: {agent.name}")
        
        # Create a simple flow
        flow = Flow(FlowConfig(
            name="test_flow",
            description="Test flow",
        ))
        
        flow.add_agent(agent)
        print(f"✓ Flow created and agent added: {flow.config.name}")
        
        # Test agent execution
        result = agent.execute("Test input")
        print(f"✓ Agent execution successful: {result.success}")
        
        return True
        
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validations."""
    print("=" * 60)
    print("Agent-Flow Package Validation")
    print("=" * 60)
    
    results = []
    
    results.append(("Package Files", validate_package_files()))
    results.append(("Imports", validate_imports()))
    results.append(("Basic Functionality", validate_basic_functionality()))
    
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        all_passed = all_passed and passed
    
    print("=" * 60)
    
    if all_passed:
        print("\nAll validations passed!")
        return 0
    else:
        print("\nSome validations failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
