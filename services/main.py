from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import routers from each service
from evaluation_service.main import router as evaluation_router
from test_generation.main import router as test_generation_router
from resume_jd_matcher.main import router as resume_jd_matcher_router

# Create FastAPI app
app = FastAPI(
    title="Unified Resume Web Tool Services",
    description="Unified API for evaluation, test generation, and resume-JD matching services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers with prefixes
app.include_router(evaluation_router, prefix="/evaluate", tags=["evaluation"])
app.include_router(test_generation_router, prefix="/generate-test", tags=["test-generation"])
app.include_router(resume_jd_matcher_router, prefix="/resume-jd", tags=["resume-jd-matcher"])

@app.get("/health")
async def health_check():
    """Health check endpoint for the unified service"""
    return {"status": "healthy"}

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Unified Resume Web Tool Services",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "POST /evaluate/evaluate": "Evaluate technical assessments",
            "POST /generate-test/generate-test": "Generate mock test questions",
            "POST /resume-jd/resume": "Parse resume PDF",
            "POST /resume-jd/jd": "Parse job description PDF", 
            "POST /resume-jd/match": "Match resume and JD",
            "POST /resume-jd/generate": "Generate questions from resume+JD",
            "GET /health": "Health check"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
