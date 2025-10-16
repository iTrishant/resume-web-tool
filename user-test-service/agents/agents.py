import os
import json
import re
import google.generativeai as genai
from typing import Dict, List, Optional
import random
import time

# Multi-key rotation for rate limiting
API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"), 
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5")
]

# Filter out None keys
API_KEYS = [key for key in API_KEYS if key is not None]

if not API_KEYS:
    raise ValueError("No Gemini API keys found! Set GEMINI_API_KEY_1 through GEMINI_API_KEY_5")

# Rate limiting tracking
key_usage = {i: {"requests": 0, "last_reset": time.time()} for i in range(len(API_KEYS))}
RATE_LIMIT = 15  # requests per minute
RESET_INTERVAL = 60  # seconds

def get_available_key():
    """Get an available API key with rate limiting"""
    current_time = time.time()
    
    # Reset counters if needed
    for i, usage in key_usage.items():
        if current_time - usage["last_reset"] >= RESET_INTERVAL:
            usage["requests"] = 0
            usage["last_reset"] = current_time
    
    # Find available key
    for i, usage in key_usage.items():
        if usage["requests"] < RATE_LIMIT:
            usage["requests"] += 1
            return API_KEYS[i]
    
    # If all keys are rate limited, wait and retry
    print("All API keys rate limited, waiting...")
    time.sleep(5)
    return get_available_key()

def configure_gemini():
    """Configure Gemini with current available key"""
    key = get_available_key()
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash')

# Keywords from your deployed app
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

def extract_technical_highlights(resume_text: str) -> List[str]:
    """Extract technical highlights from resume (same as your deployed app)"""
    lines = [line.strip("• ").strip() for line in resume_text.splitlines() if line.strip()]
    highlights = []
    for line in lines:
        lw = line.lower()
        if any(k in lw for k in TECH_KEYWORDS) and not any(nt in lw for nt in NON_TECH_KEYWORDS):
            highlights.append(line)
    return highlights[:5]

def parse_json_response(response_text: str) -> Dict:
    """Parse JSON from Gemini response (same logic as your app)"""
    try:
        raw = response_text.strip()
        if raw.startswith("```json"):
            raw = raw[7:-3].strip()
        return json.loads(raw)
    except:
        # Fallback parsing using regex
        obj = re.search(r"\{.*\}", raw, re.S)
        return json.loads(obj.group(0)) if obj else {}

class FreeTierAgent:
    """Free tier - basic questions from resume only"""
    
    def __init__(self):
        self.max_questions = 5
    
    def generate_questions(self, resume_text: str, jd_text: str = None) -> Dict:
        """Generate basic questions (similar to your deployed app logic)"""
        highlights = extract_technical_highlights(resume_text)
        highlights_str = "\n".join(f"- {h}" for h in highlights[:3])  # Limit to 3 for free tier
        
        prompt = f"""
You are an expert technical interview coach. Generate 5 basic technical questions for this candidate:
• 3 simple open-ended questions (for spoken answers) - technical questions from projects/intern/skills
• 2 basic multiple-choice questions

Each MCQ should have exactly 5 options (a-e).

Output format (STRICT JSON):
{{
    "open_questions": [
        "Q1: ",
        "Q2: ", 
        "Q3: "
    ],
    "mcq": [
        {{
            "question": "Basic concept question",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "Simple technical question",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }}
    ]
}}

Choose relevant and apt questions based on resume. Stick to fundamental technical concepts.

Only return this JSON. No extra text.

— Technical Highlights:
{highlights_str}

Resume Context:
{resume_text[:1000]}...  
"""
        
        model = configure_gemini()
        response = model.generate_content(prompt)
        return parse_json_response(response.text)

class FreemiumTierAgent:
    """Freemium tier - uses stock industry JDs"""
    
    def __init__(self):
        self.max_questions = 10
    
    def generate_questions(self, resume_text: str, jd_text: str) -> Dict:
        """Generate questions using stock industry JD"""
        highlights = extract_technical_highlights(resume_text)
        highlights_str = "\n".join(f"- {h}" for h in highlights)
        
        prompt = f"""
You are an expert technical interview coach. Generate 10 questions for this candidate using the provided job description:
• 5 open-ended technical questions (referencing JD requirements) - mix of JD and resume projects/skills
• 5 multiple-choice questions

Each MCQ should have exactly 5 options (a-e).

Output format (STRICT JSON):
{{
    "open_questions": [
        "Q1: JD-specific technical question",
        "Q2: Technical depth question",
        "Q3: Problem-solving question",
        "Q4: Skill application question",
        "Q5: Industry-specific scenario question"
    ],
    "mcq": [
        {{
            "question": "Technical concept from JD requirements",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "Practical scenario question",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "Best practices question for this role",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "Industry-standard tools and technologies",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "choose relevant question",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }}
    ]
}}

Only return this JSON. No extra text.

— Technical Highlights from Resume:
{highlights_str}

— Job Description:
{jd_text}

— Resume Context:
{resume_text[:1500]}...

Requirements:
1. Reference specific requirements from the job description
2. Mix fundamental and intermediate concepts
3. Include questions about both technical and soft skills mentioned in JD
4. Focus on practical application of skills
"""
        
        model = configure_gemini()
        response = model.generate_content(prompt)
        return parse_json_response(response.text)

class PremiumTierAgent:
    """Premium tier - uses actual JD and comprehensive questions"""
    
    def __init__(self):
        self.max_questions = 20
    
    def generate_questions(self, resume_text: str, jd_text: str, company_context: str = None) -> Dict:
        """Generate comprehensive questions using actual JD (same style as your deployed app)"""
        highlights = extract_technical_highlights(resume_text)
        highlights_str = "\n".join(f"- {h}" for h in highlights)
        
        prompt = f"""
You are an expert technical interview coach. Given this resume and job description, generate 20 comprehensive questions:
• 5 open-ended technical questions (referencing specific JD requirements)
• 5 multiple-choice questions (advanced concepts)

Each MCQ should have exactly 5 options (a-e).

Output format (STRICT JSON):
{{
    "open_questions": [
        "Q1: ",
        "Q2: ",
        "Q3: ",
        "Q4: ",
        "Q5: "
    ],
    "mcq": [
        {{
            "question": "",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }}
    ]
}}

Choose relevant and apt questions based on JD and resume. Make questions progressively difficult from intermediate to expert level, and stick to technical topics.

Only return this JSON. No extra text.

— Technical Highlights:
{highlights_str}

Full Resume:
{resume_text}

Job Description:
{jd_text}

Company Context:
{company_context or "Technology company"}

Requirements:
1. Reference specific JD requirements in questions
2. Progressive difficulty from intermediate to expert
3. Include both depth and breadth of knowledge
4. Mix theoretical and practical questions
"""
        
        model = configure_gemini()
        response = model.generate_content(prompt)
        return parse_json_response(response.text)

# Simple tier selection function
def get_agent(tier: str):
    """Get appropriate agent based on tier"""
    agents = {
        "free": FreeTierAgent(),
        "freemium": FreemiumTierAgent(), 
        "premium": PremiumTierAgent()
    }
    return agents.get(tier, FreeTierAgent())
