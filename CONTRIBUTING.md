# Contributing

Contributions are welcome. Here's how to get started:

## Setup

```bash
git clone https://github.com/anmoldhingra1/agent-flow.git
cd agent-flow
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting:

```bash
ruff check .
```

## Pull Requests

1. Fork the repo and create a branch from `main`.
2. Add tests for any new functionality.
3. Ensure all tests pass and linting is clean.
4. Open a PR with a clear description of the change.

## Reporting Issues

Open an issue with steps to reproduce the problem and your Python version.
