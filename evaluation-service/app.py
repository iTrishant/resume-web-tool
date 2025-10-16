from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx, uuid, os
from pydantic import BaseModel
import google.generativeai as genai
import time
import random

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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

def get_gemini_model():
    """Get Gemini model with current available key"""
    key = get_available_key()
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash')

# In-memory session store
sessions = {}

class StartSessionRequest(BaseModel):
    role: str               # e.g. "sde", "ds", etc.
    level: str              # e.g. "junior", "mid", "senior"
    session_id: str = None

class SubmitAnswerRequest(BaseModel):
    question_text: str
    question_type: str = "general"
    answer_text: str  # Transcribed answer from frontend

@app.post("/start-session")
def start_session(req: StartSessionRequest):
    sid = req.session_id or str(uuid.uuid4())
    sessions[sid] = {"role": req.role, "level": req.level, "answers": []}
    return {"session_id": sid}

@app.post("/submit/{session_id}")
async def submit(session_id: str, meta: SubmitAnswerRequest):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    
    # Store the answer directly (frontend handles transcription)
    sessions[session_id]["answers"].append({
        "question": meta.question_text,
        "type": meta.question_type,
        "answer": meta.answer_text  # Transcribed text from frontend
    })
    return {"status": "answer submitted"}

@app.post("/evaluate/{session_id}")
async def evaluate(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    data = sessions[session_id]
    answers = data["answers"]
    if not answers:
        raise HTTPException(400, "No answers submitted")
    
    results = []
    for qa in answers:
        prompt = f"""You are an expert {data['role']} interviewer.
Question: {qa['question']}
Answer: {qa['answer']}

Rate this answer 1–10, then explain briefly.
Return JSON: {{ "score":X, "feedback":"..." }}"""
        
        try:
            model = get_gemini_model()
            response = model.generate_content(prompt)
            eval_text = response.text.strip()
            
            # Try to parse JSON from response
            import json
            import re
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', eval_text, re.DOTALL)
                if json_match:
                    eval_json = json.loads(json_match.group())
                else:
                    # Fallback: extract score and create feedback
                    score_match = re.search(r'"score":\s*(\d+)', eval_text)
                    score = int(score_match.group(1)) if score_match else 5
                    eval_json = {"score": score, "feedback": eval_text}
            except:
                eval_json = {"score": 5, "feedback": "Could not parse evaluation"}
                
        except Exception as e:
            eval_json = {"score": 5, "feedback": f"Evaluation error: {str(e)}"}
            
        results.append({"question": qa["question"], "evaluation": eval_json})
    
    avg = sum(e.get("score", 0) for e in results) / len(results)
    return {"session_id": session_id,
            "role": data["role"],
            "level": data["level"],
            "individual": results,
            "overall_score": round(avg, 1)}
