"""Tests for FlowState management."""

import json
import pytest

from agent_flow import FlowState, StateSnapshot


class TestFlowStateBasics:
    """Tests for basic state operations."""

    def test_empty_state(self):
        state = FlowState()
        assert state.to_dict() == {}

    def test_initial_state(self):
        state = FlowState({"key": "value"})
        assert state.get("key") == "value"

    def test_get_default(self):
        state = FlowState()
        assert state.get("missing", "default") == "default"

    def test_set_and_get(self):
        state = FlowState()
        state.set("count", 42)
        assert state.get("count") == 42

    def test_update_multiple(self):
        state = FlowState()
        state.update({"a": 1, "b": 2, "c": 3})
        assert state.get("a") == 1
        assert state.get("b") == 2
        assert state.get("c") == 3

    def test_deep_copy_isolation(self):
        """Setting a mutable value shouldn't be affected by external changes."""
        data = {"nested": [1, 2, 3]}
        state = FlowState()
        state.set("data", data)
        data["nested"].append(4)
        assert state.get("data")["nested"] == [1, 2, 3]

    def test_get_returns_copy(self):
        state = FlowState({"items": [1, 2]})
        items = state.get("items")
        items.append(3)
        assert state.get("items") == [1, 2]


class TestFlowStateSnapshots:
    """Tests for snapshot and rollback."""

    def test_snapshot_created(self):
        state = FlowState({"val": 0})
        snap = state.snapshot("step_0")
        assert isinstance(snap, StateSnapshot)
        assert snap.step_name == "step_0"
        assert snap.state_dict == {"val": 0}

    def test_history_grows(self):
        state = FlowState()
        state.set("x", 1)
        state.snapshot("s1")
        state.set("x", 2)
        state.snapshot("s2")
        assert len(state.get_history()) == 2

    def test_rollback(self):
        state = FlowState({"x": 0})
        state.snapshot("init")
        state.set("x", 100)
        state.snapshot("changed")
        state.rollback_to(0)
        assert state.get("x") == 0
        assert len(state.get_history()) == 1

    def test_rollback_out_of_range(self):
        state = FlowState()
        with pytest.raises(IndexError):
            state.rollback_to(5)

    def test_snapshot_to_dict(self):
        state = FlowState({"a": 1})
        snap = state.snapshot("s", agent_result={"ok": True})
        d = snap.to_dict()
        assert d["step_name"] == "s"
        assert d["state"] == {"a": 1}
        assert d["agent_result"] == {"ok": True}


class TestFlowStateSerialization:
    """Tests for JSON serialization."""

    def test_to_json(self):
        state = FlowState({"key": "value"})
        j = state.to_json()
        parsed = json.loads(j)
        assert parsed == {"key": "value"}

    def test_from_dict(self):
        state = FlowState.from_dict({"x": 10})
        assert state.get("x") == 10

    def test_from_json(self):
        state = FlowState.from_json('{"y": 20}')
        assert state.get("y") == 20

    def test_round_trip(self):
        original = FlowState({"a": 1, "b": [2, 3]})
        restored = FlowState.from_json(original.to_json())
        assert restored.to_dict() == original.to_dict()


class TestFlowStateLocking:
    """Tests for key locking."""

    def test_lock_and_check(self):
        state = FlowState()
        assert state.is_locked("key") is False
        state.lock("key")
        assert state.is_locked("key") is True

    def test_unlock(self):
        state = FlowState()
        state.lock("key")
        state.unlock("key")
        assert state.is_locked("key") is False

    def test_unlock_nonexistent_key(self):
        state = FlowState()
        state.unlock("nope")  # should not raise


class TestFlowStateMerge:
    """Tests for parallel branch merging."""

    def test_merge_branches(self):
        main = FlowState({"input": "data"})
        branch_a = FlowState({"result": "from_a"})
        branch_b = FlowState({"result": "from_b"})

        main.merge({"a": branch_a, "b": branch_b})
        assert main.get("_branch_a") == {"result": "from_a"}
        assert main.get("_branch_b") == {"result": "from_b"}
