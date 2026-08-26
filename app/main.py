import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database.sqlite_db import init_sqlite_db
from app.api.v1.curriculum import router as curriculum_router
from app.api.v1.market import router as market_router
from app.api.v1.student import router as student_router
from app.api.v1.skill_gap import router as skill_gap_router
from app.api.v1.roadmap import router as roadmap_router
from app.api.v1.career import router as career_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Degree Navigator Agent (ADNA) Multi-Agent Backend API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(curriculum_router, prefix="/api/v1")
app.include_router(market_router, prefix="/api/v1")
app.include_router(student_router, prefix="/api/v1")
app.include_router(skill_gap_router, prefix="/api/v1")
app.include_router(roadmap_router, prefix="/api/v1")
app.include_router(career_router, prefix="/api/v1")

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup_event():
    init_sqlite_db()

@app.get("/")
def read_root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
