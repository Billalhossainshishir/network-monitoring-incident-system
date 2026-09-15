import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./network_monitor.db")
MONITOR_INTERVAL_SECONDS = float(os.getenv("MONITOR_INTERVAL_SECONDS", "2"))
FAILURE_THRESHOLD = int(os.getenv("FAILURE_THRESHOLD", "3"))
DISABLE_BACKGROUND_MONITOR = os.getenv("DISABLE_BACKGROUND_MONITOR", "false").lower() == "true"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]
