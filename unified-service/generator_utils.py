import json
import re
import google.generativeai as genai

TECH_KEYWORDS = {"python", "java", "c++", "sql", "tensorflow", "keras", "pytorch", "aws", "docker", "flask", "nlp", "transformer"}
NON_TECH_KEYWORDS = {"communication", "team", "leadership", "management", "event"}

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


def generate_questions(resume_json: dict, jd_json: dict, highlights: list[str]) -> list[str]:
    prompt = f"""
You are an expert technical interview coach. Given this resume, highlights, and job description, generate:
- 4 open-ended technical questions
- MCQ section with 6 unique MCQ questions
Each MCQ question should have 5 options (a-e). Return as valid JSON.

Return format:
{{
  "open_questions": ["Q1", "Q2", "Q3", "Q4"],
  "mcq": {{
    {{
        "q1": "i. What is ...?",
        "options": ["a. ...", "b. ...", "c. ...", "d. ...", "e. ..."]
      }},
      {{
        "q2": "ii. How ...?",
        "options": ["a. ...", "b. ...", "c. ...", "d. ...", "e. ..."]
      }}
      ...
  }}
}}

Highlights:
{json.dumps(highlights)}
Resume:
{json.dumps(resume_json)}
JD:
{json.dumps(jd_json)}
"""
    resp = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    obj = re.search(r"\{.*\}", resp.text, re.S)
    return json.loads(obj.group(0)) if obj else {}
