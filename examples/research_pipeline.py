"""
Example: Multi-agent research pipeline.

This example demonstrates a 3-agent workflow that researches a topic,
analyzes the findings, and produces a structured report.

Agents:
1. Researcher: Gathers comprehensive information on the topic
2. Analyzer: Extracts key insights and patterns from research
3. Writer: Compiles findings into a structured report

Usage:
    python examples/research_pipeline.py
"""

import json
from agent_flow import Agent, Flow, AgentConfig, FlowConfig, FlowState


def create_research_agent() -> Agent:
    """Create the researcher agent."""
    config = AgentConfig(
        name="researcher",
        role="Research specialist",
        system_prompt="""You are a research specialist with expertise in gathering
        comprehensive information. Your task is to research the given topic and
        provide detailed findings including:
        - Key facts and figures
        - Recent developments
        - Different perspectives
        
        Format your response as a structured research document.""",
        model="gpt-4-turbo",
        temperature=0.7,
        max_tokens=1500,
    )
    return Agent(config)


def create_analyzer_agent() -> Agent:
    """Create the analyzer agent."""
    config = AgentConfig(
        name="analyzer",
        role="Data analyst",
        system_prompt="""You are a data analyst skilled at extracting insights.
        Your task is to analyze research findings and provide:
        - Key themes and patterns
        - Critical insights
        - Implications for different stakeholders
        - Risk and opportunity assessment
        
        Be concise and data-driven in your analysis.""",
        model="gpt-4-turbo",
        temperature=0.5,
        max_tokens=1200,
    )
    return Agent(config)


def create_writer_agent() -> Agent:
    """Create the writer agent."""
    config = AgentConfig(
        name="writer",
        role="Technical writer",
        system_prompt="""You are a technical writer who produces well-structured reports.
        Your task is to create a professional report with:
        - Executive summary
        - Background and context
        - Key findings
        - Analysis and implications
        - Recommendations
        - Conclusion
        
        Use clear sections and professional formatting.""",
        model="gpt-4-turbo",
        temperature=0.6,
        max_tokens=2000,
    )
    return Agent(config)


def run_research_pipeline(topic: str) -> Dict[str, any]:
    """Execute the research pipeline.
    
    Args:
        topic: Topic to research
        
    Returns:
        Dictionary with pipeline results
    """
    # Create agents
    researcher = create_research_agent()
    analyzer = create_analyzer_agent()
    writer = create_writer_agent()
    
    # Create flow
    flow = Flow(FlowConfig(
        name="research_pipeline",
        description="Multi-agent research, analysis, and report writing",
        timeout_seconds=300,
    ))
    
    # Add agents
    flow.add_agent(researcher)
    flow.add_agent(analyzer)
    flow.add_agent(writer)
    
    # Define workflow steps
    flow.add_step("researcher")
    flow.add_step("analyzer")
    flow.add_step("writer")
    
    # Add event hooks for monitoring
    def on_step_start(event):
        print(f"\n{'='*60}")
        print(f"Starting: {event.step_name}")
        print(f"{'='*60}")
    
    def on_step_complete(event):
        time_ms = event.data.get("execution_time_ms", 0)
        print(f"Completed: {event.step_name} ({time_ms:.0f}ms)")
    
    def on_error(event):
        print(f"ERROR in {event.step_name}: {event.data.get('error')}")
    
    flow.on_step_start.append(on_step_start)
    flow.on_step_complete.append(on_step_complete)
    flow.on_error.append(on_error)
    
    # Run the pipeline
    print(f"\nResearching: {topic}")
    print(f"{'='*60}")
    
    result = flow.run(
        input_data=f"Research and produce a comprehensive report on: {topic}",
        initial_state={"topic": topic},
    )
    
    return result


def main() -> None:
    """Run the research pipeline example."""
    import time
    
    # Example topic
    topic = "Quantum computing applications in drug discovery"
    
    try:
        result = run_research_pipeline(topic)
        
        print(f"\n{'='*60}")
        print("PIPELINE EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        if result["success"]:
            print(f"Status: SUCCESS")
            print(f"Total execution time: {result['execution_time_ms']:.0f}ms")
            
            print(f"\nFinal Report (Writer Output):")
            print("-" * 60)
            
            # Get the final report from writer agent
            for key, value in result["results"].items():
                if "writer" in key:
                    print(value)
                    break
            
            print(f"\nState snapshot history: {len(result['state'].get('_state_snapshots', []))} snapshots")
        else:
            print(f"Status: FAILED")
            print(f"Error: {result.get('error')}")
            
    except Exception as e:
        print(f"Error running pipeline: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
