"""Job matching state definition for LangGraph"""

from typing import List, Dict, Optional
from pydantic import BaseModel
from typing import Any


class Resume(BaseModel):
    """Resume data model"""
    id: str
    name: str
    content: str
    skills: List[str] = []
    experience: List[str] = []
    education: List[str] = []


class JobDescription(BaseModel):
    """Job description data model"""
    title: str
    content: str
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    requirements: List[str] = []


class CandidateMatch(BaseModel):
    """Match result for a candidate"""
    resume_id: str
    resume_name: str
    match_score: float
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    gaps: List[str] = []
    strengths: List[str] = []
    summary: str = ""

class InterviewQuestion(BaseModel):
    """Interview question data model"""
    id: str
    category: str  # e.g., "technical", "behavioral", "system_design"
    skill_tag: str  # e.g., "Python", "Kubernetes"
    difficulty: str  # "easy" | "medium" | "hard"
    question: str
    rubric: List[str] = []  # bullet points for ideal answer / scoring


class AnswerEvaluation(BaseModel):
    """Per-question evaluation"""
    question_id: str
    score: float  # 0-5 or 0-10 (your choice; consistent with prompt)
    verdict: str  # "strong" | "okay" | "weak"
    feedback: str
    expected_points_hit: List[str] = []
    missing_points: List[str] = []


class InterviewEvaluation(BaseModel):
    """Overall interview evaluation"""
    overall_score: float  # 0-100
    recommendation: str  # "strong_hire" | "hire" | "no_hire" | "strong_no_hire"
    strengths: List[str] = []
    concerns: List[str] = []
    per_question: List[AnswerEvaluation] = []
    summary: str = ""

# -----------------------------
# Agent 4: Learning plan
# -----------------------------
class LearningModule(BaseModel):
    skill: str
    level_target: str  # basic | intermediate | job-ready
    duration_weeks: int
    weekly_hours: int
    prerequisites: List[str] = []
    learning_steps: List[str] = []
    resources: List[str] = []
    practice_tasks: List[str] = []
    milestone: str = ""


class LearningPlan(BaseModel):
    candidate_id: str
    candidate_name: str
    role_title: str
    overall_duration_weeks: int
    summary: str = ""
    modules: List[LearningModule] = []
    notes: List[str] = []


class JobMatchState(BaseModel):
    """State object for job matching workflow"""
    
    target_resume_id: str = ""
    # Input
   # Inputs
    job_description_text: str = ""
    resume_texts: List[Dict[str, str]] = []

    # Interview controls
    target_resume_id: str = ""
    candidate_answers: Dict[str, str] = {}

    # Parsed data
    job_description: Optional[JobDescription] = None
    resumes: List[Resume] = []

    # Analysis results
    candidate_matches: List[CandidateMatch] = []
    best_candidate: Optional[CandidateMatch] = None

    # Interview outputs
    interview_questions: List[InterviewQuestion] = []
    interview_evaluation: Optional[InterviewEvaluation] = None
    

    # Agent 4 outputs
    learning_plan: Optional[LearningPlan] = None
    
    # Final
    analysis_complete: bool = False
    error: str = ""
