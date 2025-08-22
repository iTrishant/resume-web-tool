import os
import json
import re
import streamlit as st
import PyPDF2 as pdf
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

TECH_KEYWORDS = {
    "python", "java", "c++", "c#", "javascript", "typescript", "go", "ruby", "scala", "swift",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "sqlite", "redis", "cassandra",
    "hadoop", "spark", "hive", "airflow", "kafka", "etl", "data pipeline",
    "tensorflow", "keras", "pytorch", "scikit-learn", "xgboost", "lightgbm", "random forest", "svm",
    "lstm", "cnn", "rnn", "transformer", "bert", "nlp", "computer vision", "deeplearning",
    "docker", "kubernetes", "aws", "azure", "gcp", "jenkins", "ci/cd", "terraform", "ansible",
    "react", "angular", "vue", "django", "flask", "spring", "node.js", "express", "rest api",
    "excel", "tableau", "power bi", "lookr", "qdview", "matplotlib", "seaborn", "plotly",
    "pytest", "junit", "selenium", "new relic", "prometheus", "grafana",
    "android", "ios", "react native", "flutter", "embedded c", "rtos",
    "api development", "microservices", "oop", "functional programming", "agile", "scrum",
    "tdd", "domain-driven design", "architecture", "serverless", "graphql", "websocket"
}

NON_TECH_KEYWORDS = {
    "communication", "team", "leadership", "management", "project management",
    "stakeholder", "presentation", "mentoring", "training", "event", "festival",
    "collaboration", "planning", "strategy", "operations", "logistics",
    "customer service", "sales", "marketing", "finance", "hr", "recruitment",
    "management", "supervised", "coordinated", "organized"
}

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    return "".join(page.extract_text() or "" for page in reader.pages)

def extract_technical_highlights(resume_text: str) -> list[str]:
    lines = [line.strip("• ").strip() for line in resume_text.splitlines() if line.strip()]
    highlights = []
    for line in lines:
        lw = line.lower()
        if any(k in lw for k in TECH_KEYWORDS) and not any(nt in lw for nt in NON_TECH_KEYWORDS):
            highlights.append(line)
    return highlights[:5]

def get_match_percentage(resume_text, jd_text):
    prompt = f"""
You are a skilled ATS. Given this resume and job description, return ONLY the percentage match (e.g., "85%"):

Resume:
{resume_text}

Job Description:
{jd_text}
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_questions(resume_text, jd_text):
    highlights = extract_technical_highlights(resume_text)
    highlights_str = "\n".join(f"- {h}" for h in highlights)
    prompt = f"""
You are an expert technical interview coach. Given this resume and its highlights and job description, generate 5 highly relevant questions for this candidate based on technical experience:
• 4 open-ended questions (for spoken answers)
• 1 multiple-choice question with 6–7 sub-questions

Each MCQ sub-question should have:
- A question string
- Exactly 5 labelled options ("a" to "e")

Output format (STRICT JSON):

{{
  "open_questions": [
    "Open Q1",
    "Open Q2",
    "Open Q3",
    "Open Q4"
  ],
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


Only return this JSON and do not add any extra commentary or text. And do not return answers.

— Technical Highlights:
{highlights_str}

Full Resume:
{resume_text}

Job Description:
{jd_text}

Requirements:
1. Generate 4 open-ended technical questions referencing specific skills or projects.
2. Generate 1 multiple-choice technical question (MCQ) based on a listed technical skill or project:
   - Generate 6 or 7 questions based on the technical highlight availability, each must be unique and not of the same topic
   - MCQs must be concept-testing or scenario-based.
   - Provide exactly 5 labelled choices (A–E).
   - Do NOT include preference-based or soft-skill questions.
"""
    response = model.generate_content(prompt)
    return response.text.strip()
    
# Streamlit UI
st.set_page_config(page_title="Gemini ATS & Interview Generator", layout="centered")
st.title("📋 Gemini‑Powered Quick ATS & Question Generator")

jd = st.text_area("Paste the **Job Description**", height=200)
uploaded_file = st.file_uploader("Upload your **Resume (PDF)**", type="pdf")

if st.button("Run Match + Generate Questions"):
    if not jd:
        st.error("Please provide a job description.")
    elif not uploaded_file:
        st.error("Please upload a PDF resume.")
    else:
        with st.spinner("📑 Reading resume..."):
            resume_text = input_pdf_text(uploaded_file)
        with st.spinner("🔎 Matching resume to JD..."):
            match_pct = get_match_percentage(resume_text, jd)
        st.success("✅ JD–Resume Match")
        st.write(f"**Match Percentage:** {match_pct}")

        with st.spinner("🧠 Generating interview questions..."):
            try:
                raw = generate_questions(resume_text, jd)
                if raw.startswith("```json"):
                    raw = raw[7:-3].strip()
                data = json.loads(raw)
            except:
                st.error("❌ Failed to parse LLM response.")
                st.text(raw)
                st.stop()
        st.success("🎯 Generated Interview Questions")
        st.json(data)
        # for i, q in enumerate(data["open_questions"], 1):
        #     st.write(f"**Q{i}:** {q}")

        # st.write("**Q5: MCQs**")
        # st.write(data["mcq"]["question"])

        # for sq in data["mcq"]["subquestions"]:
        #     st.write(f"{sq['q']}")
        #     st.write("  " + "  |  ".join(sq["options"]))
