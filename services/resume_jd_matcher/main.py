from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import google.generativeai as genai
from .matcher_utils import fetch_content_from_url, parse_and_match_resume_jd, resume_cache, jd_cache

router = APIRouter()

# Load environment variables
load_dotenv()

class MatchRequest(BaseModel):
    resume_json: dict
    jd_json: dict

class URLRequest(BaseModel):
    url: str
    
class ParseAndMatchRequest(BaseModel):
    resume_url: str
    jd_url: str

@router.get("/")
def home():
    return {"status": "service running"}

@router.post("/parse-and-match")
async def parse_and_match_urls(request: ParseAndMatchRequest):
    """
    Parse resume and JD from URLs and calculate match percentage in a single API call
    """
    try:
        # Fetch content from URLs
        resume_text = fetch_content_from_url(request.resume_url)
        jd_text = fetch_content_from_url(request.jd_url)
        
        # Single API call to parse both and calculate match
        result = parse_and_match_resume_jd(resume_text, jd_text)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing URLs: {str(e)}")

@router.post("/resume")
async def parse_resume_url(request: URLRequest):
    """Parse resume from URL and return structured JSON"""
    try:
        cache_key = f"resume:{hash(request.url)}"
        if cache_key in resume_cache:
            return resume_cache[cache_key]
        
        text = fetch_content_from_url(request.url)
        # Use the combined function but only return resume data
        result = parse_and_match_resume_jd(text, "")
        resume_data = result.get("resume_data", {})
        resume_cache[cache_key] = resume_data
        return resume_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing resume URL: {str(e)}")

@router.post("/jd")
async def parse_jd_url(request: URLRequest):
    """Parse job description from URL and return structured JSON"""
    try:
        cache_key = f"jd:{hash(request.url)}"
        if cache_key in jd_cache:
            return jd_cache[cache_key]
        
        text = fetch_content_from_url(request.url)
        # Use the combined function but only return JD data
        result = parse_and_match_resume_jd("", text)
        jd_data = result.get("jd_data", {})
        jd_cache[cache_key] = jd_data
        return jd_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing job description URL: {str(e)}")

@router.post("/match")
async def match_resume_jd(request: MatchRequest):
    """Compare resume and JD JSON to get compatibility score"""
    try:
        # Convert JSON back to text for the combined function
        import json
        resume_text = json.dumps(request.resume_json, indent=2)
        jd_text = json.dumps(request.jd_json, indent=2)
        
        result = parse_and_match_resume_jd(resume_text, jd_text)
        return result.get("match_result", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching resume and JD: {str(e)}")

app = FastAPI(title="Resume-JD Matcher Service", version="1.0.0")
app.include_router(router, prefix="/matcher")
