from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routers import transcription
app = FastAPI()

app.include_router(transcription.router, prefix="/transcriptions")

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})
