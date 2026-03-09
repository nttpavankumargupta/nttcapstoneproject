"""Job matching state definition for LangGraph"""

from typing import List, Dict, Optional
from pydantic import BaseModel


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


class JobMatchState(BaseModel):
    """State object for job matching workflow"""
    
    # Input
    job_description_text: str = ""
    resume_texts: List[Dict[str, str]] = []  # List of {name, content}
    
    # Parsed data
    job_description: Optional[JobDescription] = None
    resumes: List[Resume] = []
    
    # Analysis results
    candidate_matches: List[CandidateMatch] = []
    best_candidate: Optional[CandidateMatch] = None
    
    # Final output
    analysis_complete: bool = False
    error: str = ""
