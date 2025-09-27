from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import httpx, uuid, os
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory session store
sessions = {}

class StartSessionRequest(BaseModel):
    role: str               # e.g. "sde", "ds", etc.
    level: str              # e.g. "junior", "mid", "senior"
    session_id: str = None

class SubmitAnswerRequest(BaseModel):
    question_text: str
    question_type: str = "general"

@app.post("/start-session")
def start_session(req: StartSessionRequest):
    sid = req.session_id or str(uuid.uuid4())
    sessions[sid] = {"role": req.role, "level": req.level, "answers": []}
    return {"session_id": sid}

@app.post("/submit/{session_id}")
async def submit(session_id: str,
                 file: UploadFile = File(...),
                 meta: SubmitAnswerRequest = Depends()):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    # Call STT
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, await file.read(), file.content_type)}
        r = await client.post(f"{os.getenv('STT_SERVICE_URL')}/generate-transcript", files=files)
    if r.status_code != 200:
        raise HTTPException(500, "Transcription failed")
    text = r.json()["transcription"]
    sessions[session_id]["answers"].append({
        "question": meta.question_text,
        "type": meta.question_type,
        "answer": text
    })
    return {"transcription": text}

@app.post("/evaluate/{session_id}")
async def evaluate(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    data = sessions[session_id]
    answers = data["answers"]
    if not answers:
        raise HTTPException(400, "No answers submitted")
    results = []
    async with httpx.AsyncClient() as client:
        for qa in answers:
            prompt = f"""You are an expert {data['role']} interviewer.
Question: {qa['question']}
Answer: {qa['answer']}

Rate this answer 1–10, then explain briefly.
Return JSON: {{ "score":X, "feedback":"..." }}"""
            r = await client.post(f"{os.getenv('STT_SERVICE_URL')}/generate", json={"text": prompt})
            eval_json = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
            results.append({"question": qa["question"], "evaluation": eval_json})
    avg = sum(e.get("score",0) for e in results)/len(results)
    return {"session_id": session_id,
            "role": data["role"],
            "level": data["level"],
            "individual": results,
            "overall_score": round(avg,1)}
