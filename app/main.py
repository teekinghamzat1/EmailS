from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.endpoints import router
from app.db.init_db import init_db
from app.discovery.fetcher import discovery_engine
import os

app = FastAPI(title="Domain Email Intelligence API")

# Ensure static dir exists so FastAPI doesn't crash on boot before we create it
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    init_db()
    discovery_engine.start_loop()

@app.on_event("shutdown")
def on_shutdown():
    discovery_engine.stop_loop()

app.include_router(router)

@app.get("/")
def serve_dashboard():
    return FileResponse("app/static/index.html")

@app.get("/admin")
def serve_admin():
    return FileResponse("app/static/admin.html")

