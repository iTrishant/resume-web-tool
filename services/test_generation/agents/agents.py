import os
import json
import re
import google.generativeai as genai
from typing import Dict, List, Optional
import random
import time
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_2")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY_2 is not set in environment variables")

def configure_gemini():
    """Configure Gemini with current available key"""
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-2.5-flash')

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

# Test configuration based on duration
TEST_CONFIG = {
    30: {
        "open_questions": 4,
        "mcq_questions": 5
    },
    60: {
        "open_questions": 8,
        "mcq_questions": 10
    }
}

# Difficulty level descriptions
DIFFICULTY_DESCRIPTIONS = {
    "novice": "Basic concepts, simple explanations expected",
    "intermediate": "Solid understanding, some depth required",
    "actual": "Professional level, thorough answers expected",
    "challenge": "Expert level, deep technical knowledge required"
}

def get_test_config(duration: int) -> dict:
    """Get test configuration for given duration"""
    if duration not in TEST_CONFIG:
        raise ValueError(f"Invalid duration: {duration}. Use 30 or 60 minutes")
    return TEST_CONFIG[duration]

def get_difficulty_description(difficulty: str) -> str:
    """Get difficulty description for given level"""
    if difficulty not in DIFFICULTY_DESCRIPTIONS:
        raise ValueError(f"Invalid difficulty: {difficulty}. Use novice, intermediate, actual, or challenge")
    return DIFFICULTY_DESCRIPTIONS[difficulty]

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
        self.tier = "free"
    
    def generate_questions(self, resume_text: str, jd_text: str = None, duration: int = 30, difficulty: str = "intermediate") -> Dict:
        """Generate basic questions based on duration and difficulty"""
        highlights = extract_technical_highlights(resume_text)
        highlights_str = "\n".join(f"- {h}" for h in highlights[:3])  # Limit to 3 for free tier
        
        # Get test configuration
        config = get_test_config(duration)
        difficulty_desc = get_difficulty_description(difficulty)
        
        open_count = config["open_questions"]
        mcq_count = config["mcq_questions"]
        
        prompt = f"""
You are an expert technical interview coach. Generate technical questions for this candidate:

TEST CONFIGURATION:
- Duration: {duration} minutes
- Open-ended questions: {open_count} 
- Multiple-choice questions: {mcq_count}
- Difficulty Level: {difficulty.upper()} - {difficulty_desc}

DIFFICULTY CONTEXT:
- novice: Basic concepts, simple explanations expected
- intermediate: Solid understanding, some depth required  
- actual: Professional level, thorough answers expected
- challenge: Expert level, deep technical knowledge required

Generate questions appropriate for {difficulty} level difficulty.

Output format (STRICT JSON):
{{
    "open_questions": [
        "Q1: ",
        "Q2: ", 
        "Q3: ",
        "Q4: "{f',chr(10)        "Q5: ",chr(10)        "Q6: ",chr(10)        "Q7: ",chr(10)        "Q8: "' if open_count == 8 else ''}
    ],
    "mcq": [
        {{
            "question": "Technical concept question",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }},
        {{
            "question": "Practical scenario question",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }}{f',chr(10)        {{chr(10)            "question": "Additional question",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "Another question",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "Final question",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }}' if mcq_count == 10 else ''}
    ]
}}

Choose relevant and apt questions based on resume. Stick to {difficulty} level technical concepts.

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
        self.tier = "freemium"
    
    def generate_questions(self, resume_text: str, jd_text: str, duration: int = 30, difficulty: str = "intermediate") -> Dict:
        """Generate questions using stock industry JD"""
        highlights = extract_technical_highlights(resume_text)
        highlights_str = "\n".join(f"- {h}" for h in highlights)
        
        # Get test configuration
        config = get_test_config(duration)
        difficulty_desc = get_difficulty_description(difficulty)
        
        open_count = config["open_questions"]
        mcq_count = config["mcq_questions"]
        
        prompt = f"""
You are an expert technical interview coach. Generate technical questions for this candidate using the provided job description:

TEST CONFIGURATION:
- Duration: {duration} minutes
- Open-ended questions: {open_count} 
- Multiple-choice questions: {mcq_count}
- Difficulty Level: {difficulty.upper()} - {difficulty_desc}

DIFFICULTY CONTEXT:
- novice: Basic concepts, simple explanations expected
- intermediate: Solid understanding, some depth required  
- actual: Professional level, thorough answers expected
- challenge: Expert level, deep technical knowledge required

Generate questions appropriate for {difficulty} level difficulty, referencing JD requirements.

Output format (STRICT JSON):
{{
    "open_questions": [
        "Q1: JD-specific technical question",
        "Q2: Technical depth question",
        "Q3: Problem-solving question",
        "Q4: Skill application question"{f',chr(10)        "Q5: Industry-specific scenario question",chr(10)        "Q6: Advanced technical question",chr(10)        "Q7: Complex problem-solving question",chr(10)        "Q8: Expert-level technical question"' if open_count == 8 else ''}
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
            "question": "Relevant technical question",
            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]
        }}{f',chr(10)        {{chr(10)            "question": "Advanced concept question",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "Complex scenario question",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "Expert-level question",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "Specialized knowledge question",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "Final comprehensive question",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }}' if mcq_count == 10 else ''}
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
2. Generate questions at {difficulty} difficulty level
3. Include questions about both technical and soft skills mentioned in JD
4. Focus on practical application of skills
"""
        
        model = configure_gemini()
        response = model.generate_content(prompt)
        return parse_json_response(response.text)

class PremiumTierAgent:
    """Premium tier - uses actual JD and comprehensive questions"""
    
    def __init__(self):
        self.tier = "premium"
    
    def generate_questions(self, resume_text: str, jd_text: str, company_context: str = None, duration: int = 30, difficulty: str = "intermediate") -> Dict:
        """Generate comprehensive questions using actual JD"""
        highlights = extract_technical_highlights(resume_text)
        highlights_str = "\n".join(f"- {h}" for h in highlights)
        
        # Get test configuration
        config = get_test_config(duration)
        difficulty_desc = get_difficulty_description(difficulty)
        
        open_count = config["open_questions"]
        mcq_count = config["mcq_questions"]
        
        prompt = f"""
You are an expert technical interview coach. Generate comprehensive technical questions for this candidate using the provided job description:

TEST CONFIGURATION:
- Duration: {duration} minutes
- Open-ended questions: {open_count} 
- Multiple-choice questions: {mcq_count}
- Difficulty Level: {difficulty.upper()} - {difficulty_desc}

DIFFICULTY CONTEXT:
- novice: Basic concepts, simple explanations expected
- intermediate: Solid understanding, some depth required  
- actual: Professional level, thorough answers expected
- challenge: Expert level, deep technical knowledge required

Generate questions appropriate for {difficulty} level difficulty, referencing specific JD requirements.

Output format (STRICT JSON):
{{
    "open_questions": [
        "Q1: ",
        "Q2: ",
        "Q3: ",
        "Q4: "{f',chr(10)        "Q5: ",chr(10)        "Q6: ",chr(10)        "Q7: ",chr(10)        "Q8: "' if open_count == 8 else ''}
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
        }}{f',chr(10)        {{chr(10)            "question": "",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }},chr(10)        {{chr(10)            "question": "",chr(10)            "options": ["a. option1", "b. option2", "c. option3", "d. option4", "e. option5"]chr(10)        }}' if mcq_count == 10 else ''}
    ]
}}

Choose relevant and apt questions based on JD and resume. Make questions progressively difficult from intermediate to expert level, and stick to technical topics appropriate for {difficulty} level.

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
2. Generate questions at {difficulty} difficulty level
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
