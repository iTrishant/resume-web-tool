# Mock-Test-Generator

A unified Flask API that powers resume–JD matching and technical interview question generation using Google Gemini.

## Core Features

- Parse PDF resumes and job descriptions into structured JSON
- Compute resume ↔ JD match score with reasoning
- Generate technical interview questions (open + MCQs) based on resume and JD
- All endpoints are unified under a single service (port **8000**)

## Endpoints

### `GET /`  
**Health check**  
Returns:  
```json
{
  "status": "unified matcher + generator service running"
}
```

---

### `POST /resume`  
**Description:** Upload a resume PDF and receive structured JSON output.  
**Input:**  
- `multipart/form-data` with a file field named `"file"` (PDF resume)

**Response:**  
```json
{
  "Full Name": "...",
  "Email": "...",
  "GitHub": "...",
  "LinkedIn": "...",
  "Employment Details": [...],
  "Technical Skills": [...],
  "Soft Skills": [...],
  "Education": [...]
}
```

---

### `POST /jd`  
**Description:** Upload a job description PDF and receive structured JSON output.  
**Input:**  
- `multipart/form-data` with a file field named `"file"` (PDF JD)

**Response:**  
```json
{
  "Required Skills": [...],
  "Required Experience": "...",
  "Required Education": "..."
}
```

---

### `POST /match`  
**Description:** Compare resume and JD JSON to get a compatibility score and analysis.  
**Input:**  
```json
{
  "resume_json": { ... },
  "jd_json": { ... }
}
```

**Response:**  
```json
{
  "score": 87,
  "strengths": [...],
  "gaps": [...]
}
```

---

### `POST /generate`  
**Description:** Generate technical interview questions based on resume + JD.  
**Input:**  
```json
{
  "resume_json": { ... },
  "jd_json": { ... }
}
```

**Response:**  
```json
{
  "open_questions": [
    "Explain your experience with...",
    "How would you approach...",
    ...
  ],
  "mcq": {
    "question": "Context-based category",
    "subquestions": [
      {
        "q": "i. What is ...?",
        "options": [
          "a. ...", "b. ...", "c. ...", "d. ...", "e. ..."
        ]
      },
      ...
    ]
  }
}
```

## Folder Structure

```
unified_service/
├── app.py
├── matcher_utils.py
├── generator_utils.py
├── requirements.txt
```



# Deployed Mock Test Generator

A Streamlit-based application that automatically generates technical interview questions and computes resume-to-job-description match percentage using Google Gemini (gemini-1.5-flash).

## Live Demo

### Try it out here: https://mock-test-generator-zumgvqpifghieuoka3r299.streamlit.app/


Resume–JD Matching: Calculates match percentage between candidate's resume and job description.

Question Generation: Produces 5 tailor-made technical interview questions (q1–q5) plus a multiple-choice question with subparts (a–g).





