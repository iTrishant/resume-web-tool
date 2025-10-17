from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from agents.agents import get_agent

router = APIRouter()

class MockTestRequest(BaseModel):
    tier: str  # "free", "freemium", "premium"
    resume_text: str
    jd_text: Optional[str] = None  # Required for freemium and premium
    company_context: Optional[str] = None  # Only used by premium

@router.get("/")
def health_check():
    """Health check endpoint"""
    return {"status": "service running", "tiers": ["free", "freemium", "premium"]}

@router.post("/generate-test")
def generate_mock_test(request: MockTestRequest):
    """Generate mock test questions based on tier"""
    try:
        # Validate tier
        if request.tier not in ["free", "freemium", "premium"]:
            raise HTTPException(status_code=400, detail="Invalid tier. Use: free, freemium, or premium")
        
        # Get appropriate agent
        agent = get_agent(request.tier)
        
        # Generate questions based on tier
        if request.tier == "free":
            # Free tier - resume only
            questions = agent.generate_questions(request.resume_text)
        
        elif request.tier == "freemium":
            # Freemium tier - requires JD from your backend
            if not request.jd_text:
                raise HTTPException(status_code=400, detail="JD text required for freemium tier")
            questions = agent.generate_questions(request.resume_text, request.jd_text)
        
        else:  # premium
            # Premium tier - requires JD and optional company context
            if not request.jd_text:
                raise HTTPException(status_code=400, detail="JD text required for premium tier")
            questions = agent.generate_questions(
                request.resume_text, 
                request.jd_text,
                request.company_context
            )
        
        return {
            "tier": request.tier,
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
            "questions": 5,
            "features": ["Basic questions", "Resume-based only"],
            "model": "gemini-1.5-flash",
            "requirements": ["resume_text"]
        },
        "freemium": {
            "questions": 10,
            "features": ["JD-based questions", "Intermediate complexity"],
            "model": "gemini-1.5-flash",
            "requirements": ["resume_text", "jd_text"]
        },
        "premium": {
            "questions": 10,
            "features": ["Advanced JD analysis", "Company context", "Expert complexity"],
            "model": "gemini-1.5-pro",
            "requirements": ["resume_text", "jd_text", "company_context (optional)"]
        }
    }
