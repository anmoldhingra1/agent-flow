"""Flow state management with immutable snapshots and history tracking."""

import json
import copy
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StateSnapshot:
    """Immutable snapshot of flow state at a point in time."""

    timestamp: datetime
    step_name: str
    state_dict: Dict[str, Any]
    agent_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "step_name": self.step_name,
            "state": self.state_dict,
            "agent_result": self.agent_result,
        }


class FlowState:
    """Manages state across agent handoffs with immutable snapshots."""

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        """Initialize flow state.

        Args:
            initial_state: Initial state dictionary
        """
        self._state: Dict[str, Any] = copy.deepcopy(initial_state or {})
        self._history: List[StateSnapshot] = []
        self._locks: Dict[str, bool] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from state.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value
        """
        return copy.deepcopy(self._state.get(key, default))

    def set(self, key: str, value: Any) -> None:
        """Set a value in state.

        Args:
            key: State key
            value: Value to set
        """
        self._state[key] = copy.deepcopy(value)

    def update(self, updates: Dict[str, Any]) -> None:
        """Update state with multiple values.

        Args:
            updates: Dictionary of updates to apply
        """
        for key, value in updates.items():
            self.set(key, value)

    def snapshot(self, step_name: str, agent_result: Optional[Dict[str, Any]] = None) -> StateSnapshot:
        """Create an immutable snapshot of current state.

        Args:
            step_name: Name of the step creating the snapshot
            agent_result: Optional result from agent execution

        Returns:
            StateSnapshot object
        """
        snapshot = StateSnapshot(
            timestamp=datetime.utcnow(),
            step_name=step_name,
            state_dict=copy.deepcopy(self._state),
            agent_result=agent_result,
        )
        self._history.append(snapshot)
        return snapshot

    def get_history(self) -> List[StateSnapshot]:
        """Get all state snapshots.

        Returns:
            List of StateSnapshot objects
        """
        return copy.deepcopy(self._history)

    def rollback_to(self, step_index: int) -> None:
        """Rollback state to a previous snapshot.

        Args:
            step_index: Index of snapshot to rollback to

        Raises:
            IndexError: If step_index is out of range
        """
        if step_index < 0 or step_index >= len(self._history):
            raise IndexError(f"Invalid snapshot index: {step_index}")

        self._state = copy.deepcopy(self._history[step_index].state_dict)
        self._history = self._history[:step_index + 1]

    def merge(self, other_states: Dict[str, 'FlowState']) -> None:
        """Merge states from parallel execution branches.

        Args:
            other_states: Dictionary mapping branch names to FlowState objects
        """
        for branch_name, flow_state in other_states.items():
            self.set(f"_branch_{branch_name}", flow_state.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire state to dictionary.

        Returns:
            Current state as dictionary
        """
        return copy.deepcopy(self._state)

    def to_json(self) -> str:
        """Serialize state to JSON.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowState':
        """Create FlowState from dictionary.

        Args:
            data: Dictionary of initial state

        Returns:
            FlowState instance
        """
        return cls(initial_state=data)

    @classmethod
    def from_json(cls, json_str: str) -> 'FlowState':
        """Create FlowState from JSON string.

        Args:
            json_str: JSON string

        Returns:
            FlowState instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def lock(self, key: str) -> None:
        """Lock a state key to prevent modifications.

        Args:
            key: State key to lock
        """
        self._locks[key] = True

    def unlock(self, key: str) -> None:
        """Unlock a state key.

        Args:
            key: State key to unlock
        """
        self._locks.pop(key, None)

    def is_locked(self, key: str) -> bool:
        """Check if a state key is locked.

        Args:
            key: State key to check

        Returns:
            True if locked, False otherwise
        """
        return self._locks.get(key, False)
