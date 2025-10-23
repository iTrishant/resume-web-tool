from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from google import genai
from dotenv import load_dotenv
import os
import copy

load_dotenv()
router = APIRouter()

if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')):
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Get API key from environment
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY_1', '')

# Initialize Gemini client
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY_1 not found in environment variables")

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    raise ValueError(f"Failed to initialize Gemini client: {str(e)}")

# ==================== Pydantic Models for Request ====================

class Question(BaseModel):
    type: str = Field(..., description="Question type: 'open' or 'mcq'")
    text: str = Field(..., description="The question text")
    options: Optional[List[str]] = Field(None, description="Options for MCQ questions")

class Answer(BaseModel):
    answer: str = Field(..., description="The candidate's answer")

class EvaluationRequest(BaseModel):
    questions: List[Question] = Field(..., description="List of questions")
    answers: List[str] = Field(..., description="List of answers")
    difficulty: str = Field(default="intermediate", description="Difficulty level: novice/intermediate/actual/challenge")
    test_duration: int = Field(default=900, description="Allowed time in seconds")
    attempt_duration: int = Field(default=850, description="Actual time taken in seconds")

# ==================== Pydantic Models for Response Schema ====================

class Feedback(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]

class DetailedResult(BaseModel):
    question_number: int
    type: str
    question: str
    answer: str
    score: float
    topic: str
    feedback: str
    key_points_covered: List[str]
    key_points_missed: List[str]

class PerformanceByTopic(BaseModel):
    topic: str
    score: float

class PerformanceByType(BaseModel):
    type: str
    avg_score: float
    count: int
    accuracy: float

class DifficultyLevel(BaseModel):
    count: int
    avg_score: float

class DifficultyAnalysis(BaseModel):
    easy: DifficultyLevel
    medium: DifficultyLevel
    hard: DifficultyLevel

class AnswerQualityMetrics(BaseModel):
    avg_length_words: int
    completeness_score: float
    clarity_score: float
    technical_accuracy: float

class TimeSpentAnalysis(BaseModel):
    total_time_minutes: int
    avg_time_per_question_seconds: int
    questions_rushed: List[int]
    questions_overthought: List[int]

class SkillRadar(BaseModel):
    Technical_Knowledge: float = Field(..., alias="Technical Knowledge")
    Problem_Solving: float = Field(..., alias="Problem Solving")
    Clarity: float
    Depth: float
    
    class Config:
        populate_by_name = True

class ComparisonMetrics(BaseModel):
    percentile: int
    better_than_average_by: float

class ProgressOverQuestions(BaseModel):
    scores: List[float]

class Analytics(BaseModel):
    performance_by_topic: List[PerformanceByTopic]
    performance_by_type: List[PerformanceByType]
    difficulty_analysis: DifficultyAnalysis
    answer_quality_metrics: AnswerQualityMetrics
    time_spent_analysis: TimeSpentAnalysis
    skill_radar: SkillRadar
    comparison_metrics: ComparisonMetrics
    progress_over_questions: ProgressOverQuestions

class PracticeResource(BaseModel):
    topic: str
    resource: str

class Recommendations(BaseModel):
    focus_areas: List[str]
    practice_resources: List[PracticeResource]
    next_steps: str

class EvaluationResponse(BaseModel):
    progress_summary: str = Field(..., description="One-line status indicating candidate's current standing or readiness level")
    overall_score: float
    grade: str
    feedback: Feedback
    detailed_results: List[DetailedResult]
    analytics: Analytics
    recommendations: Recommendations

def remove_titles_from_schema(schema: dict) -> dict:
    """
    Recursively removes 'title' keys from a JSON schema dictionary.
    The Google AI API for structured output does not support the 'title' parameter.
    """
    if isinstance(schema, dict):
        # Remove 'title' key if it exists at the current level
        schema.pop('title', None)
        
        # Iterate over a copy of items to allow modification
        for key, value in list(schema.items()):
            if isinstance(value, dict):
                # Recurse into nested dictionaries (like 'properties', 'items', '$defs')
                remove_titles_from_schema(value)
            elif isinstance(value, list):
                # Recurse into items in a list (e.g., in 'anyOf', 'allOf', 'oneOf')
                for item in value:
                    if isinstance(item, dict):
                        remove_titles_from_schema(item)
    return schema

# ==================== API Endpoints ====================

@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Technical Assessment Evaluation Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "POST /evaluate": "Evaluate a technical assessment",
            "GET /health": "Health check endpoint",
            "GET /test-gemini": "Test Gemini client connection"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Service is running"}

@router.get("/test-gemini")
async def test_gemini():
    """Test Gemini client connection"""
    try:
        # Simple test call
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Say 'Hello, Gemini is working!'",
            config={"temperature": 0.1}
        )
        return {
            "status": "success",
            "gemini_response": response.text,
            "api_key_configured": bool(GEMINI_API_KEY)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "api_key_configured": bool(GEMINI_API_KEY)
        }

def get_dereferenced_schema(model) -> dict:
    """
    Generates a JSON schema from a Pydantic model and resolves all $ref
    definitions inline. The Gemini API does not support $ref.
    """
    # Get the schema with $defs
    schema = model.model_json_schema()
    
    if "$defs" not in schema:
        # No definitions to resolve
        return schema

    # Pop the definitions out for lookup
    defs = schema.pop("$defs")

    def _resolve_refs(obj):
        """Recursively finds and replaces $ref with the actual definition."""
        if "title" in obj:
            del obj["title"]
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                # Get the definition name (e.g., "#/$defs/MyModel" -> "MyModel")
                ref_name = ref_path.split('/')[-1]
                
                if ref_name in defs:
                    # Get the actual definition
                    # Use deepcopy to handle multiple uses of the same ref
                    ref_value = copy.deepcopy(defs[ref_name])
                    # Recursively resolve refs *within* the definition itself
                    return _resolve_refs(ref_value)
                else:
                    # Can't find ref, return as is
                    return obj
            else:
                # It's a dict, but not a ref itself. Traverse its values.
                return {k: _resolve_refs(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # Traverse the list
            return [_resolve_refs(item) for item in obj]
        else:
            # Base case: string, int, etc.
            return obj

    # Start resolving from the top-level schema
    return _resolve_refs(schema)

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_assessment(request: EvaluationRequest):
    """
    Evaluate a technical assessment using Gemini AI with structured output.
    
    Args:
        request: EvaluationRequest containing questions, answers, and metadata
    
    Returns:
        EvaluationResponse: Detailed evaluation report with scores and analytics
    """
    try:
        # Validate input
        if len(request.questions) != len(request.answers):
            raise HTTPException(
                status_code=400,
                detail="Number of questions and answers must match"
            )
        
        if not GEMINI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY_1 not configured"
            )
        
        # Prepare Q&A data for prompt
        qa_pairs = []
        for i, (q, a) in enumerate(zip(request.questions, request.answers), 1):
            qa_pairs.append({
                "number": i,
                "type": q.type,
                "question": q.text,
                "options": q.options if q.options else [],
                "answer": a
            })
        
        # Construct evaluation prompt
        prompt = f"""You are an expert technical interviewer evaluating a coding assessment.

ASSESSMENT CONTEXT:
- Difficulty Level: {request.difficulty.upper()}
  * novice: Basic concepts, simple explanations expected
  * intermediate: Solid understanding, some depth required
  * actual: Professional level, thorough answers expected
  * challenge: Expert level, deep technical knowledge required
- Test Duration Allowed: {request.test_duration} seconds ({request.test_duration // 60} minutes)
- Actual Time Taken: {request.attempt_duration} seconds ({request.attempt_duration // 60} minutes)
- Total Questions: {len(request.questions)}

QUESTIONS AND ANSWERS:
{chr(10).join([f"{i}. [{q['type'].upper()}] {q['question']}{' Options: ' + ', '.join(q['options']) if q['options'] else ''}{chr(10)}   Answer: {q['answer']}" for i, q in enumerate(qa_pairs, 1)])}

YOUR TASK:
Evaluate each answer comprehensively based on the {request.difficulty} difficulty level:

1. Score each answer individually (0-10 scale)
2. Identify the topic for each question
3. List key points covered and missed for each answer
4. Provide specific, actionable feedback for each answer
5. Calculate overall performance metrics
6. Analyze answer quality (completeness, clarity, technical accuracy)
7. Identify time management patterns (rushed vs overthought questions)
8. Provide personalized recommendations with specific resources

EVALUATION CRITERIA FOR {request.difficulty.upper()} LEVEL:
{'- Expect basic understanding and simple explanations' if request.difficulty == 'novice' else ''}
{'- Expect solid conceptual grasp with some depth and examples' if request.difficulty == 'intermediate' else ''}
{'- Expect professional-level answers with comprehensive coverage' if request.difficulty == 'actual' else ''}
{'- Expect expert-level depth with advanced concepts and edge cases' if request.difficulty == 'challenge' else ''}

Be thorough, specific, and constructive in your evaluation. Focus on both strengths and areas for improvement.
"""
        print("pachu",EvaluationResponse.model_json_schema())
        # Call Gemini with structured output
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": get_dereferenced_schema(EvaluationResponse),
                    "temperature": 0.1,
                }
            )   
            
            # Parse the structured response
            evaluation_result: EvaluationResponse = response.parsed
            
        except Exception as gemini_error:
            raise HTTPException(
                status_code=500,
                detail=f"Gemini API call failed: {str(gemini_error)}"
            )
        
        return evaluation_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )

# ==================== Router Export ====================
# This module exports the router for mounting in the main FastAPI app
