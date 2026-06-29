.PHONY: setup test demo server smoke clean

setup:
	uv sync --extra dev

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest

demo:
	uv run trusted-agent-demo --fast

server:
	uv run trusted-agent-server

smoke:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
	uv run trusted-agent-demo --fast

clean:
	rm -rf .pytest_cache build dist src/*.egg-info
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
