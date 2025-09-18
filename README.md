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

## Booking API

Minimal CRUD (no update) backed by Firestore.

All endpoints require `Authorization: Bearer <Firebase ID token>`.

Prefix: `/bookings`

### Create

POST `/bookings/`
Body:

```json
{
  "hospitalityID": "abc123",
  "startDate": "2025-09-18T10:00:00Z",
  "endDate": "2025-09-19T10:00:00Z",
  "ticketCount": 1
}
```

### List

GET `/bookings/` -> list for user

### Get

GET `/bookings/{id}` -> single booking

### Delete

DELETE `/bookings/{id}` -> 204

Firestore `bookings` document shape:

```
{
  hospitalityID: string,
  startDate: timestamp,
  endDate: timestamp,
  user: string (uid),
  ticketCount: number,
  createdOn: timestamp
}
```

Firestore `users` document shape:

```
{
  email: string,
  createdOn: timestamp
}
```

## Firebase Admin Credentials

Provide one of:

- `FIREBASE_CREDENTIALS` = path to service account JSON
- `FIREBASE_CREDENTIALS_B64` = base64 of JSON
- `FIREBASE_CREDENTIALS_JSON` = raw JSON string

Example:

```bash
export FIREBASE_CREDENTIALS_B64=$(base64 -w0 serviceAccount.json)
```

## Tests

Install dev extras then run:

```bash
pip install -e .[dev]
pytest -q
```

## Next Steps / Suggestions

- Add pagination for bookings
- Add update (PATCH) booking
- Implement logging
- Add CI (GitHub Actions)
- Add test coverage for auth & bookings (mock Firebase)

## License

MIT
