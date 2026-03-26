"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import notebooks, documents, chat, summary, quiz, faq, auth, admin, categories
from app.database.mongodb_client import get_mongodb
from app.utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize MongoDB
    try:
        mongodb = get_mongodb()
        mongodb.connect()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.warning("Make sure MongoDB is running on localhost:27017")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    # Cleanup resources
    try:
        mongodb = get_mongodb()
        mongodb.close()
    except Exception:
        pass


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered document summarization and Q&A application",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(
    auth.router,
    prefix=f"{settings.API_PREFIX}/auth",
    tags=["Authentication"]
)

app.include_router(
    notebooks.router,
    prefix=f"{settings.API_PREFIX}/notebooks",
    tags=["Notebooks"]
)

app.include_router(
    documents.router,
    prefix=f"{settings.API_PREFIX}/documents",
    tags=["Documents"]
)

app.include_router(
    chat.router,
    prefix=f"{settings.API_PREFIX}/chat",
    tags=["Chat"]
)

app.include_router(
    summary.router,
    prefix=f"{settings.API_PREFIX}/summary",
    tags=["Summary"]
)

app.include_router(
    quiz.router,
    prefix=f"{settings.API_PREFIX}/quiz",
    tags=["Quiz"]
)

app.include_router(
    faq.router,
    prefix=f"{settings.API_PREFIX}/faq",
    tags=["FAQ"]
)

app.include_router(
    admin.router,
    prefix=f"{settings.API_PREFIX}/admin",
    tags=["Admin"]
)

app.include_router(
    categories.router,
    prefix=f"{settings.API_PREFIX}/categories",
    tags=["Categories"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "milvus": "pending",  # TODO: Add actual health check
            "openai": "pending"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
