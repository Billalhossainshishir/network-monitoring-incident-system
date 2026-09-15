import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import CORS_ORIGINS, DISABLE_BACKGROUND_MONITOR, MONITOR_INTERVAL_SECONDS
from .db import Base, SessionLocal, engine
from .services.monitor import run_monitor_cycle, seed_services


async def monitor_loop():
    while True:
        await asyncio.sleep(MONITOR_INTERVAL_SECONDS)
        with SessionLocal() as db:
            run_monitor_cycle(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_services(db)
    task = None
    if not DISABLE_BACKGROUND_MONITOR:
        task = asyncio.create_task(monitor_loop())
    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="Network Monitoring & Incident System",
    version="1.0.0",
    description="Portfolio monitoring platform for simulated services, repeated-failure incident creation, automatic recovery and operational metrics.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "Network Monitoring & Incident System",
        "status": "ready",
        "docs": "/docs",
        "note": "Frontend is intentionally not deployed yet. Test locally before publishing.",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(router)
