.PHONY: setup test demo server smoke clean

setup:
	uv sync --extra dev

test:
	uv run pytest

demo:
	uv run trusted-agent-demo --fast

server:
	uv run trusted-agent-server

smoke:
	uv run pytest
	uv run trusted-agent-demo --fast

clean:
	rm -rf .pytest_cache build dist src/*.egg-info
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
