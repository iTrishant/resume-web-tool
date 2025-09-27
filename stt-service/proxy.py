from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.cloud import storage, speech_v1p1beta1 as speech
from pydub import AudioSegment
import io, os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/generate-transcript")
async def generate_transcript(file: UploadFile = File(...)):
    # 1. Read & convert to wav
    data = await file.read()
    ext = file.filename.lower().split(".")[-1]
    if ext not in {"mp3","ogg","webm"}:
        raise HTTPException(400,"Unsupported format")
    audio = AudioSegment.from_file(io.BytesIO(data), format=ext)
    buf = io.BytesIO()
    audio.export(buf, format="wav", parameters=["-acodec","pcm_s16le"])
    # 2. Upload to GCS
    client = storage.Client()
    bucket = client.bucket(os.getenv("BUCKET_NAME"))
    blob = bucket.blob(f"uploads/{file.filename}.wav")
    blob.upload_from_string(buf.getvalue(), content_type="audio/wav")
    uri = f"gs://{bucket.name}/{blob.name}"
    # 3. Speech-to-Text
    speech_client = speech.SpeechClient()
    audio_gcs = speech.RecognitionAudio(uri=uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=audio.frame_rate,
        language_code="en-US",
        enable_automatic_punctuation=True
    )
    op = speech_client.long_running_recognize(config=config, audio=audio_gcs)
    res = op.result(timeout=120)
    text = "\n".join(r.alternatives[0].transcript for r in res.results)
    return JSONResponse({"transcription": text})
