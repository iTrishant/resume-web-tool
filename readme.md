Mock Test Generator

A Streamlit-based application that automatically generates technical interview questions and computes resume-to-job-description match percentage using Google Gemini (gemini-1.5-flash).

Live Demo

Try it out here: https://mock-test-generator-zjjvbh2pb5rek3utsfr9ub.streamlit.app/

Features

Resume–JD Matching: Calculates match percentage between candidate's resume and job description.

Question Generation: Produces 5 tailor-made technical interview questions (q1–q5) plus a multiple-choice question with subparts (a–g).

Tech Stack

Frontend: Streamlit

LLM: Google Gemini via google-generativeai

Resume Parsing: PyPDF2

Deployment: Streamlit Community Cloud

Installation & Setup

Clone the repository:

git clone https://github.com/iTrishant/mock-test-generator.git
cd mock-test-generator

Create a virtual environment and install dependencies:

python -m venv .venv
source .venv/bin/activate    # macOS/Linux
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt

Add your Gemini API key:

echo "GOOGLE_API_KEY=your_gemini_key_here" > .env

Running Locally

streamlit run app.py

Deployment to Streamlit Community Cloud

Push code to GitHub (see instructions above).

On https://share.streamlit.io, create a new app from this repo, main branch, app.py file.

Add GOOGLE_API_KEY as a Secret in the app settings.


