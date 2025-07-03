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

— Technical Highlights:
{highlights_str}

Full Resume:
{resume_text}

Job Description:
{jd_text}

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
"""
    response = model.generate_content(prompt)
    lines = [line.strip() for line in response.text.splitlines() if line.strip()]
    return lines
    # raw = response.text.strip()
    # try:
    #     return json.loads(raw)
    # except json.JSONDecodeError:
    #     arr = re.search(r'"open_questions"\s*:\s*\[(.*?)\]', raw, re.DOTALL)
    #     mcq_q = re.search(r'"question"\s*:\s*"(.*?)"', raw)
    #     mcq_choices = re.search(r'"choices"\s*:\s*\[(.*?)\]', raw, re.DOTALL)
    #     mcq_ans = re.search(r'"answer"\s*:\s*"(.*?)"', raw)
    #     open_qs = json.loads(f"[{arr.group(1)}]") if arr else []
    #     choices = json.loads(f"[{mcq_choices.group(1)}]") if mcq_choices else []
    #     return {
    #         "open_questions": open_qs,
    #         "mcq": {
    #             "question": mcq_q.group(1) if mcq_q else "",
    #             "choices": choices,
    #             "answer": mcq_ans.group(1) if mcq_ans else ""
    #         }
    #     }

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
            questions = generate_questions(resume_text, jd)
        st.success("🎯 Generated Interview Questions")
        for item in questions:
            st.write(item)
