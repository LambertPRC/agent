# Repository Guidelines

## Project Structure & Module Organization

`main.py` is the runnable entry point and contains Windows SSL setup. `agent/` defines the native tool-calling agent and runtime prompt. `tools/common/` provides the shared ToolResult contract; `tools/weather/` implements Open-Meteo access. `infra/openai_client/` wraps the OpenAI-compatible client. `tests/` contains offline contract and weather tests. There is no asset tree or packaging configuration.

## Setup, Run, and Validation Commands

Use Python 3.9, matching the checked-in IDE configuration.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install certifi httpx langchain langchain-core langchain-openai openai "pydantic>=2" python-dotenv
python main.py
```

`python main.py` runs the sample agent and contacts the configured OpenAI-compatible endpoint. Dependency versions are not yet declared, so update this guide if a `requirements.txt` or `pyproject.toml` is added. Validate syntax without calling external services:

```powershell
python -m compileall main.py agent infra tools tests
```

## Coding Style & Naming Conventions

Follow PEP 8 with four-space indentation, imports grouped at the top, and one import per line. Use `snake_case` for modules, functions, and variables; use `PascalCase` for classes and `UPPER_SNAKE_CASE` for constants. Add type hints to public functions and keep tool functions small and deterministic. No formatter or linter is configured, so review style manually and avoid unrelated reformatting.

## Agent Architecture

Use `ChatPromptTemplate` with native Tool Calling. Never parse ReAct markers such as `Action:` or `Final Answer:`. Wrap tools with `standard_tool` and Pydantic input/data models; ToolResult v1 enforces (`schema_version`, `tool`, `ok`, `data`, `error`, `meta`). Keep runtime rules in the system prompt.

## Testing Guidelines

Tests use standard-library `unittest`. Name files `test_<module>.py` and cases `test_<behavior>`. Mock LLM and HTTP calls so tests stay deterministic and offline. Run all tests with `python -m unittest discover -s tests -v`. No coverage target is configured.

## Configuration & Security

The application loads `OPENAI_KEY` and `BASE_URL` from the root `.env`. Never commit real credentials or print them in logs. Preserve certificate verification for new network code; treat existing SSL workarounds as narrowly scoped compatibility code.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout, so no existing commit convention can be inferred. Use short, imperative subjects, optionally scoped, such as `feat(agent): add retry handling`. Keep commits focused. Pull requests should explain behavior changes, list validation commands, link relevant issues, and include representative console output when user-visible execution changes.
