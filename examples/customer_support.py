"""
Example: Customer support with conditional routing.

This example demonstrates intelligent routing of customer queries to
appropriate support agents (billing, technical, or general) based on
content classification.

Workflow:
1. Classifier agent analyzes the customer message
2. Router decides which support agent should handle it
3. Appropriate support agent responds

Usage:
    python examples/customer_support.py
"""

from typing import Dict
from agent_flow import (
    Agent,
    Flow,
    AgentConfig,
    FlowConfig,
    ContentRouter,
)


def create_classifier_agent() -> Agent:
    """Create the query classifier agent."""
    config = AgentConfig(
        name="classifier",
        role="Support query classifier",
        system_prompt="""You are a support ticket classifier. Analyze the customer message
        and determine its category. Respond with ONLY one word: billing, technical, or general.

        - Billing: Questions about invoices, payments, pricing, subscriptions
        - Technical: Issues with product functionality, bugs, errors
        - General: Everything else, feedback, compliments, complaints about service
        """,
        model="gpt-4-turbo",
        temperature=0.3,
        max_tokens=10,
    )
    return Agent(config)


def create_billing_agent() -> Agent:
    """Create the billing support agent."""
    config = AgentConfig(
        name="billing_support",
        role="Billing support specialist",
        system_prompt="""You are a billing support specialist. Help the customer with
        their billing inquiry. Provide accurate information about:
        - Invoice details
        - Payment options
        - Refund policies
        - Subscription management
        - Pricing information

        Be helpful, professional, and offer concrete solutions.""",
        model="gpt-4-turbo",
        temperature=0.5,
        max_tokens=500,
    )
    return Agent(config)


def create_technical_agent() -> Agent:
    """Create the technical support agent."""
    config = AgentConfig(
        name="technical_support",
        role="Technical support engineer",
        system_prompt="""You are a technical support engineer. Help the customer with
        their technical issue by:
        - Understanding the problem
        - Asking clarifying questions if needed
        - Providing troubleshooting steps
        - Offering solutions
        - Suggesting escalation if needed

        Be thorough and provide step-by-step guidance.""",
        model="gpt-4-turbo",
        temperature=0.5,
        max_tokens=600,
    )
    return Agent(config)


def create_general_agent() -> Agent:
    """Create the general support agent."""
    config = AgentConfig(
        name="general_support",
        role="General support representative",
        system_prompt="""You are a general support representative. Help the customer with
        their inquiry. Be friendly, professional, and:
        - Acknowledge their concern
        - Provide relevant information
        - Offer next steps
        - Show appreciation for feedback

        Keep responses concise and helpful.""",
        model="gpt-4-turbo",
        temperature=0.6,
        max_tokens=400,
    )
    return Agent(config)


def classify_content(query: str) -> str:
    """Simple content classifier.

    Args:
        query: Customer query text

    Returns:
        Category: 'billing', 'technical', or 'general'
    """
    query_lower = query.lower()

    # Billing keywords
    billing_keywords = [
        "invoice", "payment", "refund", "billing", "subscription",
        "charge", "price", "cost", "paid", "pricing", "money"
    ]

    # Technical keywords
    technical_keywords = [
        "error", "bug", "crash", "broken", "not working", "issue",
        "problem", "failed", "debug", "slow", "performance"
    ]

    billing_score = sum(1 for kw in billing_keywords if kw in query_lower)
    technical_score = sum(1 for kw in technical_keywords if kw in query_lower)

    if billing_score > technical_score and billing_score > 0:
        return "billing"
    elif technical_score > 0:
        return "technical"
    else:
        return "general"


def run_support_pipeline(customer_query: str) -> Dict[str, any]:
    """Execute the customer support pipeline.

    Args:
        customer_query: Customer's support query

    Returns:
        Dictionary with pipeline results
    """
    # Create agents
    classifier = create_classifier_agent()
    billing = create_billing_agent()
    technical = create_technical_agent()
    general = create_general_agent()

    # Create flow
    flow = Flow(FlowConfig(
        name="customer_support",
        description="Intelligent customer support routing",
        timeout_seconds=120,
    ))

    # Add agents
    flow.add_agent(classifier)
    flow.add_agent(billing)
    flow.add_agent(technical)
    flow.add_agent(general)

    # Define workflow
    flow.add_step("classifier")

    # Add content router
    router = ContentRouter(
        classifier=classify_content,
        routing_map={
            "billing": "billing_support",
            "technical": "technical_support",
            "general": "general_support",
        },
        default_agent="general_support",
    )
    flow.add_router(step_index=0, router=router)

    # Add the support agents (they will be routed to)
    flow.add_step("billing_support")
    flow.add_step("technical_support")
    flow.add_step("general_support")

    # Add event hooks
    def on_step_start(event):
        print(f"\nProcessing with {event.data.get('agent', 'unknown')}")

    def on_step_complete(event):
        time_ms = event.data.get("execution_time_ms", 0)
        agent = event.data.get("agent", "unknown")
        print(f"{agent} completed in {time_ms:.0f}ms")

    flow.on_step_start.append(on_step_start)
    flow.on_step_complete.append(on_step_complete)

    # Run the pipeline
    print(f"\nCustomer Query: {customer_query}")
    print("-" * 60)

    result = flow.run(
        input_data=customer_query,
        initial_state={"customer_query": customer_query},
    )

    return result


def main() -> None:
    """Run customer support examples."""

    # Example queries
    queries = [
        "Why was I charged twice for my subscription?",
        "The app keeps crashing when I try to upload files",
        "Your customer service is amazing, thank you!",
        "Can you help me understand the payment options?",
        "I'm getting an error code 503 when trying to login",
    ]

    print("Customer Support Routing System")
    print("=" * 60)

    for i, query in enumerate(queries, 1):
        print(f"\n\nExample {i}:")
        print("=" * 60)

        try:
            result = run_support_pipeline(query)

            if result["success"]:
                print("\nSupport Response:")
                print("-" * 60)

                # Get the response from the routed support agent
                for key, value in result["results"].items():
                    if "support" in key:
                        print(value)
                        break
            else:
                print(f"Error: {result.get('error')}")

        except Exception as e:
            print(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
