default: format linter tests

tests:
    uv run python -m unittest discover

format:
    uv run isort --profile black src examples tests
    uv run black src examples tests

linter:
    uv run ruff check src examples tests
    uv run  mypy src examples tests

