from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.cloud import storage
from google.cloud import speech_v1p1beta1 as speech
from pydub import AudioSegment
import io
import os
import asyncio
import traceback

app = FastAPI()

# Allow all origins for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    text: str

@app.post("/generate")
async def generate_endpoint(req: GenerateRequest):
    """
    Evaluate candidate's answer transcript.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project="179385229806", location="europe-southwest1",
        )

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

        model = "projects/179385229806/locations/europe-southwest1/endpoints/3649608946076876800"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=req.text)
                ]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=1,
            seed=0,
            max_output_tokens=65535,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
            system_instruction=[types.Part.from_text(text=sys_prompt)],
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
        )

        output = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text is not None:
                output += chunk.text

        return PlainTextResponse(output)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/generate-transcript")
async def generate_transcript(file: UploadFile = File(...)):
    """
    Convert uploaded audio file (mp3/ogg/webm) to transcript text using Google STT.
    """
    try:
        # 1. Read file content
        file_bytes = await file.read()
        # 2. Detect file format from filename
        filename = file.filename.lower()
        if filename.endswith('.mp3'):
            audio_format = 'mp3'
        elif filename.endswith('.ogg'):
            audio_format = 'ogg'
        elif filename.endswith('.webm'):
            audio_format = 'webm'
        else:
            return JSONResponse(content={"error": "Unsupported file type. Please upload mp3, ogg, or webm."}, status_code=400)

        # 3. Convert to WAV/LINEAR16 in memory
        audio = AudioSegment.from_file(io.BytesIO(file_bytes), format=audio_format)
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav", parameters=["-acodec", "pcm_s16le"])
        wav_bytes = wav_io.getvalue()

        # 4. Upload WAV to Google Cloud Storage
        bucket_name = "my-audio-transcripts-bucket-deltav"
        destination_blob_name = f"uploads/{file.filename}.wav"
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(wav_bytes, content_type="audio/wav")
        gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"

        # 5. Call Google Speech-to-Text with GCS URI
        client = speech.SpeechClient()
        audio_gcs = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=audio.frame_rate,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        operation = client.long_running_recognize(config=config, audio=audio_gcs)
        response = operation.result(timeout=600)

        # 6. Collect transcription
        transcription = '\n'.join(
            result.alternatives[0].transcript for result in response.results
        )
        return JSONResponse(content={"transcription": transcription})

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500) 
    
