import fitz  # PyMuPDF
import re
import json
import google.generativeai as genai

resume_cache = {}
jd_cache = {}

def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "".join(page.get_text() for page in doc)


def extract_resume_json(text: str) -> dict:
    prompt = """
    You are an AI specialised in parsing resumes. Extract:
      1. Full Name
      2. Email
      3. GitHub
      4. LinkedIn
      5. Employment Details
      6. Technical Skills
      7. Soft Skills
      8. Education (Degree, Institution, Year, CGPA)
    Return STRICT JSON.
    """
    resp = genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt + "\nResume:\n" + text)
    obj = re.search(r"\{.*\}", resp.text, re.S)
    return json.loads(obj.group(0)) if obj else {}

def extract_jd_json(text: str) -> dict:
    prompt = """
    You are an AI specialised in parsing job descriptions. Extract:
      1. Required Skills
      2. Required Experience
      3. Required Education
    Return STRICT JSON.
    """
    resp = genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt + "\nJob Description:\n" + text)
    obj = re.search(r"\{.*\}", resp.text, re.S)
    return json.loads(obj.group(0)) if obj else {}

def compare(resume_json: dict, jd_json: dict) -> dict:
    prompt = f"""
    Compare this resume and job description. Give:
      • "score": 0-100
      • "strengths": [...]
      • "gaps": [...]
    Return STRICT JSON.
    Resume:
    {json.dumps(resume_json, indent=2)}
    
    Job:
    {json.dumps(jd_json, indent=2)}
    """
    resp = genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt)
    obj = re.search(r"\{.*\}", resp.text, re.S)
    return json.loads(obj.group(0)) if obj else {}
