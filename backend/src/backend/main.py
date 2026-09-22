from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.dashboard import router as dashboard_router
from backend.api.forecast import router as forecast_router

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vite Server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")