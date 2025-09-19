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

Additional (Firebase credentials – one of the following is required only if you call endpoints hitting Firestore/auth):

```
# Highest priority if set and file exists
FIREBASE_CREDENTIALS=/run/secrets/firebase-service-account.json

# Or base64 encoded service account json
FIREBASE_CREDENTIALS_B64=ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsIC4uLn0=

# Or raw json string
FIREBASE_CREDENTIALS_JSON={"type": "service_account", ...}
```

Validation is handled through Pydantic settings (`app/core/config.py`). Missing Firebase credentials do not block application startup; the first Firebase operation will raise if still missing.

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

## Docker

Build image:

```bash
docker build -t sih-backend .
```

Run (mapping local port 8000):

```bash
docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e FIREBASE_CREDENTIALS_B64="$(base64 -w0 serviceAccount.json)" \
  sih-backend
```

If you prefer mounting a credentials file:

```bash
docker run --rm -p 8000:8000 \
  -e FIREBASE_CREDENTIALS=/creds/serviceAccount.json \
  -v $(pwd)/serviceAccount.json:/creds/serviceAccount.json:ro \
  sih-backend
```

Visit http://127.0.0.1:8000/docs

The container uses a non-root user (`appuser`) and installs dependencies with `uv` for faster, deterministic builds.

## Hospitality API (Images & Location)

Endpoints under `/hospitality` now support geo-location and image uploads.

### Create Hospitality (multipart/form-data)

POST `/hospitality/`

Form fields:

```
type=attraction|hotel|restaurant
name=<string>
description=<string>
latitude=<float>
longitude=<float>
images=<one or more image files>  # optional repeated field
```

Returns JSON including `location` and `images` array:

```json
{
  "id": "abc123",
  "type": "hotel",
  "name": "Sample Hotel",
  "description": "Great place",
  "location": { "lat": 12.34, "lng": 56.78 },
  "images": [
    {
      "url": "https://storage.googleapis.com/<bucket>/hospitality/abc123/hero-<rand>.jpg",
      "path": "hospitality/abc123/hero-<rand>.jpg",
      "original": "hero.jpg",
      "contentType": "image/jpeg"
    }
  ]
}
```

### Update Hospitality

PATCH `/hospitality/{id}` (multipart/form-data). All fields optional:

```
type (optional)
name (optional)
description (optional)
latitude (optional)
longitude (optional)
new_images=<image files> (optional)
replace_images=true|false (optional; default false)
```

If `replace_images=true`, previously stored images metadata is replaced (but physical old images are NOT yet individually deleted; a future improvement could remove paths no longer referenced). Currently full deletion happens only on delete endpoint.

### Delete Hospitality

DELETE `/hospitality/{id}` also deletes all stored images under `hospitality/{id}/` prefix in Firebase Storage.

### Storage Structure

Images are stored in Firebase Storage bucket configured via `FIREBASE_STORAGE_BUCKET` under:

```
hospitality/<hospitalityId>/<sanitizedName>-<random>.ext
```

Files are made public (best for demo). For production consider signed URLs and access rules.

### Environment Variable

Set `FIREBASE_STORAGE_BUCKET=<your-project>.appspot.com` to enable image uploads.
