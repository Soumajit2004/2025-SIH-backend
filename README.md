# 2024 SIH Backend

Basic TypeScript + Express server scaffold.

## Scripts

- `npm run dev` – Start development server with Nodemon + ts-node.
- `npm run build` – Compile TypeScript to `dist`.
- `npm start` – Run compiled JavaScript from `dist`.
- `npm run clean` – Remove `dist` folder.

# SIH Backend (FastAPI)

Converted from an initial Node/Express scaffold to a Python FastAPI application using `uv` for dependency management and fast installs.

## Features

- FastAPI app with root (`/`) and health (`/health`) endpoints
- Environment variable loading via `python-dotenv`
- Global exception handler scaffold
- Example `.env.example`

## Requirements

- Python 3.10+
- (Recommended) Install `uv`: https://github.com/astral-sh/uv

## Setup (with uv)

```bash
uv sync
uv run fastapi dev app/main.py  # (Future uv fastapi plugin) OR use uvicorn directly
uv run uvicorn app.main:app --reload --port 8000
```

If not using uv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn[standard] python-dotenv
uvicorn app.main:app --reload --port 8000
```

Visit: http://127.0.0.1:8000/

Interactive docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Environment Variables

Create a `.env` file (copy from `.env.example`):

```
PORT=8000
```

## Project Structure

```
app/
  main.py          # FastAPI entrypoint
pyproject.toml
.env.example
```

## Testing (planned)

After tests are added:

```bash
uv run pytest
```

## Next Steps / Suggestions

- Add routers (`app/api/routers/*.py`)
- Pydantic models & response schemas
- Configure logging
- Add database layer (SQLModel / SQLAlchemy / Prisma Client Python)
- Add CI (GitHub Actions)
- Implement tests (pytest + httpx)

## License

MIT
