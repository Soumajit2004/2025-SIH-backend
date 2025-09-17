from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SIH Backend", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "API is running", "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z'}

@app.get("/health")
async def health():
    return {"status": "ok"}

# Optional: startup event
@app.on_event("startup")
async def startup():
    port = os.getenv("PORT", "8000")
    # Could initialize DB connections etc.

# Custom exception handler example placeholder
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):  # type: ignore
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
