# Mock-Test-Generator

A two-service Flask micro-API for:
1. Resume–JD Matcher
2. Technical Question Generator

Together they power a mock-interview pipeline:
- parse PDF resumes and JDs into JSON
- compute resume↔JD match score
- generate tailored technical questions

Endpoints:

Matcher service (port 8001)

  GET    /           returns {"status": "matcher service is running"}

  POST   /resume     upload form-file “file” → parsed resume JSON

  POST   /jd         upload form-file “file” → parsed JD JSON

  POST   /match      JSON {resume_json, jd_json} → match result JSON

Question generator (port 8002)

  GET    /           returns {"status": "matcher service is running"}

  POST   /generate   JSON {resume_json, jd_json} → {"questions": [...]}

-end



# Deployed Mock Test Generator

A Streamlit-based application that automatically generates technical interview questions and computes resume-to-job-description match percentage using Google Gemini (gemini-1.5-flash).

## Live Demo

### Try it out here: [https://mock-test-generator-zjjvbh2pb5rek3utsfr9ub.streamlit.app/](https://mock-test-generator-jmbfkvdfz7wfc22wy9a5zc.streamlit.app/)


Resume–JD Matching: Calculates match percentage between candidate's resume and job description.

Question Generation: Produces 5 tailor-made technical interview questions (q1–q5) plus a multiple-choice question with subparts (a–g).





