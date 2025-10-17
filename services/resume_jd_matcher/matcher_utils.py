import requests
import re
import json
import google.generativeai as genai
import os
from urllib.parse import urlparse

resume_cache = {}
jd_cache = {}

def get_gemini_model():
    """Get Gemini model with configured API key"""
    api_key = os.getenv("GEMINI_API_KEY_3")
    if not api_key:
        raise ValueError("GEMINI_API_KEY_3 not configured")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash-exp")

def fetch_content_from_url(url: str) -> str:
    """Fetch content from URL (supports various formats)"""
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
        
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/pdf' in content_type:
            # Handle PDF URLs
            return extract_text_from_pdf_url(response.content)
        elif 'text/html' in content_type:
            # Handle HTML pages (like LinkedIn profiles, GitHub profiles, etc.)
            return extract_text_from_html(response.text)
        elif 'text/plain' in content_type:
            # Handle plain text URLs
            return response.text
        else:
            # Try to decode as text for other content types
            return response.text
            
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch content from URL: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing URL content: {str(e)}")

def extract_text_from_pdf_url(pdf_content: bytes) -> str:
    """Extract text from PDF content downloaded from URL"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        return "".join(page.get_text() for page in doc)
    except ImportError:
        raise ValueError("PyMuPDF not available for PDF processing")
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_html(html_content: str) -> str:
    """Extract text from HTML content"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except ImportError:
        # Fallback: simple regex-based HTML tag removal
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from HTML: {str(e)}")

def parse_and_match_resume_jd(resume_text: str, jd_text: str) -> dict:
    """
    Single API call to parse resume, parse JD, and calculate match percentage
    """
    prompt = f"""
You are an AI specialized in resume and job description analysis. Perform the following tasks in a single response:

1. Parse the resume and extract:
   - Full Name
   - Email
   - GitHub
   - LinkedIn
   - Employment Details
   - Technical Skills
   - Soft Skills
   - Education (Degree, Institution, Year, CGPA)

2. Parse the job description and extract:
   - Required Skills
   - Required Experience
   - Required Education

3. Compare the resume and job description to calculate:
   - Match score (0-100)
   - Strengths (areas where candidate matches well)
   - Gaps (areas where candidate lacks required skills/experience)

Return your response as STRICT JSON in this exact format:
{{
    "resume_data": {{
        "Full Name": "...",
        "Email": "...",
        "GitHub": "...",
        "LinkedIn": "...",
        "Employment Details": [...],
        "Technical Skills": [...],
        "Soft Skills": [...],
        "Education": [...]
    }},
    "jd_data": {{
        "Required Skills": [...],
        "Required Experience": "...",
        "Required Education": "..."
    }},
    "match_result": {{
        "score": 85,
        "strengths": ["Strong Python experience", "Relevant project work"],
        "gaps": ["Missing AWS experience", "No team leadership"]
    }}
}}

RESUME TEXT:
{resume_text}

JOB DESCRIPTION TEXT:
{jd_text}
"""
    
    model = get_gemini_model()
    resp = model.generate_content(prompt)
    
    # Extract JSON from response
    obj = re.search(r"\{.*\}", resp.text, re.S)
    if obj:
        return json.loads(obj.group(0))
    else:
        raise ValueError("Failed to parse JSON response from Gemini")

# Legacy functions for backward compatibility (if needed)
def extract_resume_json(text: str) -> dict:
    """Legacy function - use parse_and_match_resume_jd instead"""
    result = parse_and_match_resume_jd(text, "")
    return result.get("resume_data", {})

def extract_jd_json(text: str) -> dict:
    """Legacy function - use parse_and_match_resume_jd instead"""
    result = parse_and_match_resume_jd("", text)
    return result.get("jd_data", {})

def compare(resume_json: dict, jd_json: dict) -> dict:
    """Legacy function - use parse_and_match_resume_jd instead"""
    # Convert dicts back to text for the combined function
    resume_text = json.dumps(resume_json, indent=2)
    jd_text = json.dumps(jd_json, indent=2)
    result = parse_and_match_resume_jd(resume_text, jd_text)
    return result.get("match_result", {})
