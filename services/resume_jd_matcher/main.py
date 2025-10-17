from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import google.generativeai as genai
from matcher_utils import extract_text_from_pdf, extract_resume_json, extract_jd_json, compare, resume_cache, jd_cache

router = APIRouter()

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class MatchRequest(BaseModel):
    resume_json: dict
    jd_json: dict

class GenerateRequest(BaseModel):
    resume_json: dict
    jd_json: dict

@router.get("/")
def home():
    return {"status": "service running"}

@router.post("/resume")
async def parse_resume(file: UploadFile = File(...)):
    """Parse resume PDF and return structured JSON"""
    try:
        pdf_bytes = await file.read()
        cache_key = f"resume:{hash(pdf_bytes)}"
        if cache_key in resume_cache:
            return resume_cache[cache_key]
        
        text = extract_text_from_pdf(pdf_bytes)
        data = extract_resume_json(text)
        resume_cache[cache_key] = data
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

@router.post("/jd")
async def parse_jd(file: UploadFile = File(...)):
    """Parse job description PDF and return structured JSON"""
    try:
        pdf_bytes = await file.read()
        cache_key = f"jd:{hash(pdf_bytes)}"
        if cache_key in jd_cache:
            return jd_cache[cache_key]
        
        text = extract_text_from_pdf(pdf_bytes)
        data = extract_jd_json(text)
        jd_cache[cache_key] = data
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing job description: {str(e)}")

@router.post("/match")
async def match_resume_jd(request: MatchRequest):
    """Compare resume and JD JSON to get compatibility score"""
    try:
        result = compare(request.resume_json, request.jd_json)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching resume and JD: {str(e)}")

@router.post("/generate")
async def generate_questions(request: GenerateRequest):
    """Generate technical interview questions based on resume + JD"""
    try:
        from generator_utils import pick_highlights, generate_questions
        highlights = pick_highlights(request.resume_json)
        questions = generate_questions(request.resume_json, request.jd_json, highlights)
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")
