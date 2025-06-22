# matcher_service/app.py
import os, json, re
from flask import Flask, request, jsonify
import fitz                 # PyMuPDF
import google.generativeai as genai

from resume_jd_matcher.matcher_cache import resume_cache, jd_cache

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = "gemini-1.5-pro"

app = Flask(__name__)
g_model = genai.GenerativeModel(MODEL_NAME)


# ---------- helpers ---------------------------------------------------------
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
    resp = g_model.generate_content(prompt + "\nResume:\n" + text)
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
    resp = g_model.generate_content(prompt + "\nJob Description:\n" + text)
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
    resp = g_model.generate_content(prompt)
    obj = re.search(r"\{.*\}", resp.text, re.S)
    return json.loads(obj.group(0)) if obj else {}
# ---------------------------------------------------------------------------


# ---------------------- REST endpoints -------------------------------------
@app.post("/resume")
def parse_resume():
    file = request.files["file"]          # multipart/form-data
    pdf_bytes = file.read()
    cache_key = f"resume:{hash(pdf_bytes)}"

    if cache_key in resume_cache:
        return jsonify(resume_cache[cache_key])

    text = extract_text_from_pdf(pdf_bytes)
    data = extract_resume_json(text)
    resume_cache[cache_key] = data
    return jsonify(data)


@app.post("/jd")
def parse_jd():
    file = request.files["file"]
    pdf_bytes = file.read()
    cache_key = f"jd:{hash(pdf_bytes)}"

    if cache_key in jd_cache:
        return jsonify(jd_cache[cache_key])

    text = extract_text_from_pdf(pdf_bytes)
    data = extract_jd_json(text)
    jd_cache[cache_key] = data
    return jsonify(data)


@app.post("/match")
def match():
    body = request.get_json()
    resume = body["resume_json"]
    jd     = body["jd_json"]
    result = compare(resume, jd)
    return jsonify(result)

@app.get("/")
def home():
    return {"status": "matcher service is running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)

