# question_service/app.py
import os, json, re
from flask import Flask, request, jsonify
import google.generativeai as genai
from test_generator.keywords import TECH_KEYWORDS, NON_TECH_KEYWORDS

genai.configure(api_key=os.getenv("GEMINI_KEY"))
MODEL_NAME = "gemini-1.5-flash"
g_model = genai.GenerativeModel(MODEL_NAME)

app = Flask(__name__)

# -------------- helper ------------------------------------------------------
def pick_highlights(resume_json: dict) -> list[str]:
    lines = []
    for job in resume_json.get("Employment Details", []):
        lines += [str(job)]
    for skill in resume_json.get("Technical Skills", []):
        lines.append(skill)

    highlights = []
    for l in lines:
        lw = l.lower()
        if any(k in lw for k in TECH_KEYWORDS) and not any(nt in lw for nt in NON_TECH_KEYWORDS):
            highlights.append(l)
        if len(highlights) == 5:
            break
    return highlights


QUESTION_PROMPT = """
You are an expert technical interview coach. Given this resume and its highlights and job description, generate 5 highly relevant questions for this candidate based on technical experience:
• 4 open-ended questions (for spoken answers)
• 1 multiple-choice question with 6–7 sub-questions
**Important**:  
• Return **only** a valid JSON array of 5 strings.  
• Do not add any extra commentary or text.
Requirements:
1. Generate 4 open-ended technical questions referencing specific skills or projects.
2. Generate 1 multiple-choice technical question (MCQ) based on a listed technical skill or project:
   - Generate 6 or 7 questions based on technical highlight availability
   - MCQ must be concept-testing or scenario-based.
   - Provide exactly 5 labeled choices (A–E).
   - Only one correct answer, clearly indicated in JSON.
   - Do NOT include preference-based or soft-skill questions.
   - Q5 is the root questions with subparts from a to f or g, each being an independent MCQ questions

Return valid JSON in this format:
Q1
Q2
Q3
Q4
Q5 
i a b c d e
ii a b c d e
iii a b c d e
iv a b c d e
v a b c d e
..
Each on its own line, nothing else.

Highlights:
{hi}

Resume JSON:
{res}

JD JSON:
{jd}
"""
# ---------------------------------------------------------------------------


@app.post("/generate")
def generate():
    body = request.get_json()
    resume_json = body["resume_json"]
    jd_json     = body["jd_json"]

    highlights = pick_highlights(resume_json)
    prompt = QUESTION_PROMPT.format(
        hi="\n".join(f"- {h}" for h in highlights),
        res=json.dumps(resume_json, indent=2),
        jd=json.dumps(jd_json, indent=2)
    )

    resp = g_model.generate_content(prompt)

    try:
        arr = json.loads(re.search(r"$$.*$$", resp.text, re.S).group(0))
    except Exception:
        return jsonify({"error": "LLM returned invalid JSON"}), 500

    return jsonify({"questions": arr})

@app.get("/")
def home():
    return {"status": "matcher service is running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, debug=True)
