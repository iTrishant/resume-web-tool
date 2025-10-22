from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import requests
from .agents.agents import get_agent

router = APIRouter()

def fetch_content_from_url(url: str) -> str:
    """Fetch content from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch content from URL: {str(e)}")

class MockTestRequest(BaseModel):
    tier: str="free"  # "free", "freemium", "premium"
    resume_text: Optional[str] = None  # Text content
    resume_url: Optional[str] = None  # URL to fetch resume content
    job_description: Optional[str] = None # frontend hardcoded job description
    jd_text: Optional[str] = None  # Text content for freemium and premium
    jd_url: Optional[str] = None  # URL to fetch JD content
    company_context: Optional[str] = None  # Only used by premium
    duration: int = 30  # Duration in minutes: 30 or 60
    difficulty: str = "intermediate"  # Difficulty level: novice, intermediate, actual, challenge

@router.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "service running", 
        "tiers": ["free", "freemium", "premium"],
        "durations": [30, 60],
        "difficulties": ["novice", "intermediate", "actual", "challenge"]
    }

@router.post("/generate-test")
def generate_mock_test(request: MockTestRequest):
    """Generate mock test questions based on tier, duration, and difficulty"""
    try:
        # Validate tier
        if request.tier not in ["free", "freemium", "premium"]:
            raise HTTPException(status_code=400, detail="Invalid tier. Use: free, freemium, or premium")
        
        # Validate duration
        if request.duration not in [30, 60]:
            raise HTTPException(status_code=400, detail="Invalid duration. Use: 30 or 60 minutes")
        
        # Validate difficulty
        if request.difficulty not in ["novice", "intermediate", "actual", "challenge"]:
            raise HTTPException(status_code=400, detail="Invalid difficulty. Use: novice, intermediate, actual, or challenge")
        
        # Get resume content (from text or URL)
        if request.resume_text:
            resume_content = request.resume_text
        elif request.resume_url:
            resume_content = fetch_content_from_url(request.resume_url)
        else:
            raise HTTPException(status_code=400, detail="Either resume_text or resume_url must be provided")
        
        # Get JD content (for freemium and premium tiers)
        jd_content = None
        if request.tier in ["freemium", "premium"]:
            if request.job_description:  # Add this - prioritize job_description from frontend
                jd_content = request.job_description
            elif request.jd_text:
                jd_content = request.jd_text
            elif request.jd_url:
                jd_content = fetch_content_from_url(request.jd_url)
            else:
                raise HTTPException(status_code=400, detail="Either jd_text or jd_url must be provided for freemium/premium tiers")
        
        # Get appropriate agent
        agent = get_agent(request.tier)
        
        # Generate questions based on tier, duration, and difficulty
        if request.tier == "free":
            # Free tier - resume only
            questions = agent.generate_questions(
                resume_content, 
                duration=request.duration,
                difficulty=request.difficulty
            )
        
        elif request.tier == "freemium":
            # Freemium tier - requires JD
            questions = agent.generate_questions(
                resume_content, 
                jd_content,
                duration=request.duration,
                difficulty=request.difficulty
            )
        
        else:  # premium
            # Premium tier - requires JD and optional company context
            questions = agent.generate_questions(
                resume_content, 
                jd_content,
                request.company_context,
                duration=request.duration,
                difficulty=request.difficulty
            )
        
        return {
            "tier": request.tier,
            "duration": request.duration,
            "difficulty": request.difficulty,
            "questions": questions,
            "total_questions": len(questions.get("open_questions", [])) + len(questions.get("mcq", [])),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@router.get("/tiers")
def get_tier_info():
    """Get information about available tiers"""
    return {
        "free": {
            "features": ["Basic questions", "Resume-based only"],
            "model": "gemini-2.5-flash",
            "requirements": ["resume_text"],
            "durations": [30, 60],
            "difficulties": ["novice", "intermediate", "actual", "challenge"]
        },
        "freemium": {
            "features": ["JD-based questions", "Intermediate complexity"],
            "model": "gemini-2.5-flash",
            "requirements": ["resume_text", "jd_text"],
            "durations": [30, 60],
            "difficulties": ["novice", "intermediate", "actual", "challenge"]
        },
        "premium": {
            "features": ["Advanced JD analysis", "Company context", "Expert complexity"],
            "model": "gemini-2.5-pro",
            "requirements": ["resume_text", "jd_text", "company_context (optional)"],
            "durations": [30, 60],
            "difficulties": ["novice", "intermediate", "actual", "challenge"]
        }
    }

@router.get("/config")
def get_test_config():
    """Get test configuration options"""
    return {
        "durations": {
            30: {
                "open_questions": 4,
                "mcq_questions": 5
            },
            60: {
                "open_questions": 8,
                "mcq_questions": 10
            }
        },
        "difficulties": {
            "novice": "Basic concepts, simple explanations expected",
            "intermediate": "Solid understanding, some depth required", 
            "actual": "Professional level, thorough answers expected",
            "challenge": "Expert level, deep technical knowledge required"
        }
    }
