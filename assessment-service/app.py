from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import google.generativeai as genai
import os
import json
import re
import time

app = FastAPI()

# Allow all origins for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class GenerateRequest(BaseModel):
    text: str

@app.post("/generate")
async def generate_endpoint(req: GenerateRequest):
    """
    Evaluate candidate's answer transcript.
    """
    try:
        sys_prompt = """
You are an expert technical interviewer and evaluator. 
You are excellent at judging answers given by candidates in technical interviews 
(SDE, Data Science, Analytics, PM, BA, etc). 
You will receive transcripts of spoken answers (converted from audio). 
Ignore filler words or minor transcription errors and focus only on content.

For each answer:
1. Give **scores (1–10)** on these criteria:
   - Relevance: Does it answer the question?
   - Correctness: Are the facts and reasoning correct?
   - Depth: How well does it show understanding and insight?
   - Clarity: Is the explanation structured and easy to follow?
   - Specificity: Are there concrete examples, details, or evidence?

2. Provide **strengths** (good points in the answer).
3. Provide **weaknesses** (where the answer fell short).
4. Provide **improvements** (how the candidate can do better).

Return your response in **strict JSON** format like this:

{
  "scores": {
    "relevance": 0-10,
    "correctness": 0-10,
    "depth": 0-10,
    "clarity": 0-10,
    "specificity": 0-10
  },
  "strengths": ["point1", "point2"],
  "weaknesses": ["point1", "point2"],
  "improvements": ["point1", "point2"]
}

Only return the JSON. Do not add explanations outside the JSON.
"""

        prompt = f"{sys_prompt}\n\nAnswer to evaluate:\n{req.text}"
        
        model = get_gemini_model()
        response = model.generate_content(prompt)
        output = response.text.strip()
        
        # Try to parse JSON from response
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                eval_json = json.loads(json_match.group())
                return JSONResponse(content=eval_json)
            else:
                # Fallback: return raw response
                return PlainTextResponse(output)
        except:
            return PlainTextResponse(output)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
