#!/usr/bin/env bash
pip install uv
uv sync --all-extras
uv run mkdocs build
