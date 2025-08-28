# Repository Guidelines

## Project Structure & Modules
- `backend/src/`: FastAPI app
  - `api/routes/`: endpoint modules (e.g., `game.py`, `route.py`)
  - `services/`: domain logic (AI, GPS, POI, routes, DB)
  - `core/`: logging, DB, config helpers
  - `config/`: `settings.py`, `secrets.py`
- `tests/`: `unit/`, `integration/`, `api/`, `e2e/`, `fixtures/`
- `shared/`: shared Pydantic models
- Web assets: `mobile-app.html`, `web-demo.html`, `service-worker.js`

## Build, Test, Dev Commands
- Install: `pip install -r requirements.txt` (dev: `pip install -r backend/requirements-dev.txt`)
- Run API (root): `python -m uvicorn backend.src.main:app --reload --port 8000`
- Run API (cd backend): `uvicorn src.main:app --reload --port 8000`
- Docker: `docker build -t detective-anywhere . && docker run -p 8000:8000 detective-anywhere`
- All tests: `python -m pytest tests/ -v`
- Unit only: `python -m pytest tests/unit/`
- Skip integrations: `pytest -m "not integration"`
- Coverage: `pytest --cov=backend/src tests/`

## Coding Style & Naming
- Python 3.11+, 4-space indent, type hints required for public functions.
- Tools: Black, isort, Flake8, Mypy (see `backend/requirements-dev.txt`).
- Format/lint: `black . && isort . && flake8` (type-check: `mypy backend/src`)
- Naming: modules/files `snake_case.py`; functions/vars `snake_case`; classes `CamelCase`.
- API routes: one resource per file in `backend/src/api/routes/` (e.g., `evidence.py`).

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`, `pytest-cov`.
- Place tests mirroring module paths; name files `test_*.py`.
- Use mocks for external APIs in unit tests; mark heavier tests `@pytest.mark.integration`.
- Env: copy `.env.example` to `.env`; provide API keys for integration tests.
- Target coverage: 80%+ for changed code.

## Commit & PR Guidelines
- Commits: Conventional Commits (`feat:`, `fix:`, `perf:`, etc.). Example: `feat: add GPS spoofing detection (Issue #123)`.
- PRs include: clear description, linked issues, test plan/outputs, screenshots of API docs or UI where relevant.
- CI hygiene: run `black`, `isort`, `flake8`, `mypy`, and `pytest` locally before opening PR.

## Security & Config
- Never commit secrets; use `.env` (see `.env.example`) or Secret Manager.
- Prefer config via `backend/src/config/settings.py`; avoid hardcoding.
- For local dev, `local-dev.sh` can scaffold environments; health at `/health`.

