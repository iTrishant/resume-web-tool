from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import google.generativeai as genai
from matcher_utils import extract_text_from_pdf, extract_resume_json, extract_jd_json, compare, resume_cache, jd_cache
from generator_utils import pick_highlights, generate_questions

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
app = Flask(__name__)

@app.post("/resume")
def parse_resume():
    file = request.files["file"]
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
    jd = body["jd_json"]
    result = compare(resume, jd)
    return jsonify(result)

@app.post("/generate")
def generate():
    body = request.get_json()
    resume_json = body["resume_json"]
    jd_json = body["jd_json"]
    highlights = pick_highlights(resume_json)
    questions = generate_questions(resume_json, jd_json, highlights)
    return jsonify(questions)

@app.get("/")
def home():
    return {"status": "service running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
