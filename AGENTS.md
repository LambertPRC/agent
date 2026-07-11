# Repository Guidelines

## Project Structure & Module Organization

`main.py` is the runnable entry point and contains Windows SSL setup before invoking the agent. `agent/` defines the LangChain ReAct agent and its prompt template. `infra/openai_client/` wraps the OpenAI-compatible chat client, while `tools/weather/` provides the current example tool. Root and package `__init__.py` files contain initialization behavior. There is currently no `tests/` directory, asset tree, or packaging configuration.

## Setup, Run, and Validation Commands

Use Python 3.9, matching the checked-in IDE configuration.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install certifi httpx langchain langchain-core langchain-openai openai python-dotenv
python main.py
```

`python main.py` runs the sample agent and contacts the configured OpenAI-compatible endpoint. Dependency versions are not yet declared, so update this guide if a `requirements.txt` or `pyproject.toml` is added. Validate syntax without calling external services:

```powershell
python -m compileall main.py agent infra tools
```

## Coding Style & Naming Conventions

Follow PEP 8 with four-space indentation, imports grouped at the top, and one import per line. Use `snake_case` for modules, functions, and variables; use `PascalCase` for classes and `UPPER_SNAKE_CASE` for constants. Add type hints to public functions and keep tool functions small and deterministic. No formatter or linter is configured, so review style manually and avoid unrelated reformatting.

## Testing Guidelines

No test framework or coverage target exists. Add new tests under `tests/`, name files `test_<module>.py`, and name cases `test_<behavior>`. Prefer `pytest`; mock LLM and HTTP calls so tests remain fast, deterministic, and offline. Run future tests with `python -m pytest` after declaring `pytest` as a development dependency.

## Configuration & Security

The application loads `OPENAI_KEY` and `BASE_URL` from the root `.env`. Never commit real credentials or print them in logs. Preserve certificate verification for new network code; treat existing SSL workarounds as narrowly scoped compatibility code.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout, so no existing commit convention can be inferred. Use short, imperative subjects, optionally scoped, such as `feat(agent): add retry handling`. Keep commits focused. Pull requests should explain behavior changes, list validation commands, link relevant issues, and include representative console output when user-visible execution changes.
