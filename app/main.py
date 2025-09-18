from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv  # still allow .env reading for local dev

load_dotenv()  # ensure early for pydantic BaseSettings env_file override order

from app.core.config import settings

from app.routers.booking import router as booking_router
from app.routers.hospitality import router as hospitality_router

app = FastAPI(title="SIH Backend", version="0.1.0")

app.include_router(booking_router)
app.include_router(hospitality_router)

@app.get("/")
async def root():
    return {"message": "API is running", "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'}

@app.get("/health")
async def health():
    return {"status": "ok"}

# Optional: startup event
@app.on_event("startup")
async def startup():
    # Access settings to ensure they load & possibly log; placeholder
    _ = settings.PORT
    # Could initialize DB connections etc.

# Custom exception handler example placeholder
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):  # type: ignore
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
