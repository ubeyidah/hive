# Contributing

Thanks for your interest in contributing to Hive.

## How to Contribute
1. Fork the repository.
2. Create a new branch from `main`.
3. Make your changes.
4. Run any relevant checks.
5. Open a pull request.

## Development Setup
- Create and activate a virtual environment:
  ```bash
  uv venv .venv && source .venv/bin/activate
  ```
- Install in editable mode:
  ```bash
  uv pip install -e .
  ```

## Guidelines
- Keep changes focused and minimal.
- Follow existing code style and naming conventions.
- Document any new configuration or commands in `README.md` or `GUIDE.md`.
- Avoid adding secrets or private credentials.

## Pull Request Checklist
- Explain the change clearly.
- Include test steps (even if manual).
- Update documentation if needed.
