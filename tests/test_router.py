"""Tests for Router classes."""

import pytest

from agent_flow import (
    ConditionalRouter,
    ContentRouter,
    FallbackRouter,
    RoundRobinRouter,
)
from agent_flow.state import FlowState


class TestConditionalRouter:
    """Tests for ConditionalRouter."""

    def test_matches_first_condition(self):
        router = ConditionalRouter(
            conditions={
                "billing": lambda output, state: "invoice" in output.lower(),
                "support": lambda output, state: "help" in output.lower(),
            },
        )
        decision = router.decide("I need an invoice", FlowState(), ["billing", "support"])
        assert decision.next_agent == "billing"
        assert decision.confidence == 1.0

    def test_falls_through_to_default(self):
        router = ConditionalRouter(
            conditions={
                "billing": lambda o, s: False,
            },
            default_agent="general",
        )
        decision = router.decide("random query", FlowState(), ["billing", "general"])
        assert decision.next_agent == "general"
        assert decision.confidence == 0.5

    def test_falls_through_to_first_available(self):
        router = ConditionalRouter(conditions={})
        decision = router.decide("anything", FlowState(), ["fallback"])
        assert decision.next_agent == "fallback"
        assert decision.confidence == 0.0

    def test_raises_when_no_agents(self):
        router = ConditionalRouter(conditions={})
        with pytest.raises(ValueError, match="No available agents"):
            router.decide("anything", FlowState(), [])

    def test_skips_unavailable_agent(self):
        router = ConditionalRouter(
            conditions={
                "agent_x": lambda o, s: True,
            },
            default_agent="fallback",
        )
        decision = router.decide("query", FlowState(), ["fallback"])
        assert decision.next_agent == "fallback"


class TestContentRouter:
    """Tests for ContentRouter."""

    def test_routes_by_classification(self):
        router = ContentRouter(
            classifier=lambda x: "tech" if "code" in x else "biz",
            routing_map={"tech": "dev_agent", "biz": "biz_agent"},
        )
        decision = router.decide("fix this code", FlowState(), ["dev_agent", "biz_agent"])
        assert decision.next_agent == "dev_agent"
        assert decision.metadata["category"] == "tech"

    def test_default_on_unmatched_category(self):
        router = ContentRouter(
            classifier=lambda x: "unknown",
            routing_map={"tech": "dev"},
            default_agent="general",
        )
        decision = router.decide("hello", FlowState(), ["dev", "general"])
        assert decision.next_agent == "general"

    def test_handles_classifier_exception(self):
        router = ContentRouter(
            classifier=lambda x: 1 / 0,  # raises
            routing_map={},
            default_agent="safe",
        )
        decision = router.decide("input", FlowState(), ["safe"])
        assert decision.next_agent == "safe"


class TestFallbackRouter:
    """Tests for FallbackRouter."""

    def test_picks_first_available(self):
        router = FallbackRouter(agent_order=["primary", "secondary", "tertiary"])
        decision = router.decide("input", FlowState(), ["secondary", "tertiary"])
        assert decision.next_agent == "secondary"

    def test_confidence_decreases_with_priority(self):
        router = FallbackRouter(agent_order=["a", "b", "c"])
        d = router.decide("input", FlowState(), ["a", "b", "c"])
        assert d.confidence == 1.0
        assert d.metadata["priority"] == 0

    def test_raises_when_no_agents(self):
        router = FallbackRouter(agent_order=["a"])
        with pytest.raises(ValueError, match="No available agents"):
            router.decide("input", FlowState(), [])


class TestRoundRobinRouter:
    """Tests for RoundRobinRouter."""

    def test_cycles_through_agents(self):
        router = RoundRobinRouter(agent_order=["a", "b", "c"])
        agents = ["a", "b", "c"]

        d1 = router.decide("x", FlowState(), agents)
        d2 = router.decide("x", FlowState(), agents)
        d3 = router.decide("x", FlowState(), agents)
        d4 = router.decide("x", FlowState(), agents)

        assert d1.next_agent == "a"
        assert d2.next_agent == "b"
        assert d3.next_agent == "c"
        assert d4.next_agent == "a"  # wraps around

    def test_raises_when_no_agents(self):
        router = RoundRobinRouter(agent_order=["a"])
        with pytest.raises(ValueError, match="No available agents"):
            router.decide("x", FlowState(), [])
