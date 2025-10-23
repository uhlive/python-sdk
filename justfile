default: format lint test

test:
    uv run python -m unittest discover

format:
    uv run isort --profile black src examples tests
    uv run black src examples tests

lint:
    uv run ruff check src examples tests
    uv run  mypy src examples tests

docs:
    uv run mkdocs build
