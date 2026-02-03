# Repository Guidelines

## Project Structure & Module Organization
- `main.py` is the current entry point and the only source file.
- `pyproject.toml` defines project metadata and dependencies.
- `ARCHITECTURE.md` documents the target system design and planned directories.
- `README.md` exists but is currently empty.

If you add modules, align with the planned layout in `ARCHITECTURE.md` (e.g., `core/`, `discord/`, `tools/`, `config/`). Keep top-level scripts minimal.

## Build, Test, and Development Commands
- `python main.py`: Run the current entry point locally.
- `uv venv .venv && source .venv/bin/activate`: Create/activate a local virtual environment.
- `uv pip install -e .`: Install the project in editable mode once dependencies are added.

No build or test commands are defined yet; add them to `pyproject.toml` when introducing tooling.

## Coding Style & Naming Conventions
- Follow standard Python formatting: 4-space indentation, line length ~88–100 chars.
- Use `snake_case` for functions/variables and `PascalCase` for classes.
- Keep modules small and single-purpose; prefer pure functions where practical.

If you introduce formatting or linting tools (e.g., `ruff`, `black`), document exact commands here.

## Testing Guidelines
- No testing framework is configured yet.
- If you add tests, use `tests/` with files named `test_*.py` and functions named `test_*`.
- Prefer `pytest` for new test suites unless the project specifies otherwise.

## Commit & Pull Request Guidelines
- There is no Git history yet, so no established commit message convention.
- Suggested pattern: short, imperative subject lines (e.g., `Add CLI entry point`).
- For PRs, include a brief summary, testing notes (commands + results), and any relevant screenshots or logs.

## Security & Configuration Tips
- Keep secrets out of the repo; use environment variables or a local `.env` (gitignored).
- If you introduce configuration files, document defaults and examples in `README.md`.
