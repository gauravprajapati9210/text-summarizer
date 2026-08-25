from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os
from pathlib import Path
import sqlite3
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

try:
    from .model import get_model
except ImportError:
    from model import get_model

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Text Summarizer API",
    description="API for text summarization using a pre-trained model",
    version="1.0.0"
)

VISITS_DB_PATH = Path(__file__).resolve().parent / "visitors.db"
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    os.getenv("SUPABASE_SECRET_KEY", ""),
)

# Configure CORS
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://[a-z0-9-]+\.netlify\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="The text to summarize")
    max_length: Optional[int] = Field(150, ge=30, le=300, description="Maximum length of summary")
    min_length: Optional[int] = Field(30, ge=10, le=100, description="Minimum length of summary")

    @property
    def valid_lengths(self) -> bool:
        return (self.min_length or 30) <= (self.max_length or 150)

class SummarizeResponse(BaseModel):
    summary: str = Field(..., description="The generated summary")
    original_length: int = Field(..., description="Word count of original text")
    summary_length: int = Field(..., description="Word count of summary")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")


class VisitCountResponse(BaseModel):
    count: int = Field(..., ge=0, description="Total number of page visits")

# Lazy load model on first use
model = None

def load_model():
    """Load the model on first API call."""
    global model
    if model is None:
        try:
            model = get_model()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


def increment_local_visit_count() -> int:
    """Record a page load locally for development without Supabase credentials."""
    with sqlite3.connect(VISITS_DB_PATH, timeout=5) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS app_metrics (name TEXT PRIMARY KEY, value INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO app_metrics (name, value) VALUES ('page_visits', 0) "
            "ON CONFLICT(name) DO NOTHING"
        )
        connection.execute(
            "UPDATE app_metrics SET value = value + 1 WHERE name = 'page_visits'"
        )
        row = connection.execute(
            "SELECT value FROM app_metrics WHERE name = 'page_visits'"
        ).fetchone()
    return row[0]


def increment_supabase_visit_count() -> int:
    """Atomically increment and return the hosted Supabase visit total."""
    request = Request(
        f"{SUPABASE_URL}/rest/v1/rpc/increment_app_visits",
        data=b"{}",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            count = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, ValueError) as error:
        raise RuntimeError("Unable to update the Supabase visit counter.") from error

    if not isinstance(count, int):
        raise RuntimeError("Supabase returned an invalid visit count.")
    return count


def save_summary_to_supabase(text: str, summary: str) -> None:
    """Store generated summaries when Supabase is configured."""
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
        return

    payload = json.dumps({"source_text": text, "summary": summary}).encode("utf-8")
    request = Request(
        f"{SUPABASE_URL}/rest/v1/summaries",
        data=payload,
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10):
            pass
    except (HTTPError, URLError) as error:
        raise RuntimeError("Unable to save the summary to Supabase.") from error


def increment_visit_count() -> int:
    """Use Supabase in deployment and SQLite only for local development."""
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        return increment_supabase_visit_count()
    return increment_local_visit_count()

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify the API is running."""
    return {
        "status": "healthy",
        "service": "Text Summarizer API"
    }


@app.get("/api/visits", response_model=VisitCountResponse, tags=["Analytics"])
def register_visit():
    """Increment and return the number of visits to the web application."""
    return VisitCountResponse(count=increment_visit_count())

# Main summarization endpoint
@app.post("/api/summarize", response_model=SummarizeResponse, tags=["Summarization"])
def summarize(request: SummarizeRequest):
    """
    Generate a summary of the provided text.
    
    Args:
        request: The summarization request containing the text and optional parameters
        
    Returns:
        The generated summary with metadata
    """
    try:
        # Load model if not already loaded
        load_model()
        
        # Validate input
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Please enter some text before summarizing.")
        
        # Calculate original word count
        original_word_count = len(text.split())
        
        # Check if text is too short
        if original_word_count < 10:
            raise HTTPException(status_code=400, detail="Text is too short. Please provide at least 10 words.")
        
        # Check if text is too long
        if original_word_count > 2000:
            raise HTTPException(status_code=400, detail="Text is too long. Maximum 2000 words allowed.")

        if not request.valid_lengths:
            raise HTTPException(status_code=400, detail="min_length cannot exceed max_length.")
        
        # Generate summary
        summary = model.summarize(
            text,
            max_length=request.max_length or 150,
            min_length=request.min_length or 30
        )
        
        # Calculate summary word count
        summary_word_count = len(summary.split())
        try:
            save_summary_to_supabase(text, summary)
        except RuntimeError:
            logger.exception("Summary generated, but Supabase persistence failed.")
        
        return SummarizeResponse(
            summary=summary,
            original_length=original_word_count,
            summary_length=summary_word_count
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.")

# Root endpoint
@app.get("/", tags=["Root"])
def root():
    """API welcome message."""
    return {
        "message": "Text Summarizer API",
        "docs": "/docs",
        "health": "/health",
        "summarize": "/api/summarize"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
