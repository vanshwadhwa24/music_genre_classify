"""FastAPI Application entrypoint for Music Genre Classifier."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.inference import model_manager
from backend.app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load PyTorch model once
    print("[Startup] Initializing Music Genre Classifier Backend...")
    model_manager.load_model()
    yield
    # Shutdown
    print("[Shutdown] Cleaning up resources...")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="CNN-powered audio genre classification API based on GTZAN Mel-spectrograms.",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
