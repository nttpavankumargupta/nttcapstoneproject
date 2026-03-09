"""State management for Interview Preparation Agent"""

from typing import TypedDict, List, Optional
from dataclasses import dataclass


@dataclass
class InterviewQuestion:
    """Represents a single interview question"""
    question: str
    difficulty: str  # "Easy", "Moderate", "Difficult"
    topic: str
    expected_answer_points: List[str]
    follow_up_questions: List[str]


class InterviewPrepState(TypedDict, total=False):
    """
    State for Interview Preparation workflow
    
    Attributes:
        job_description_text: Raw job description text
        num_questions: Number of questions to generate
        difficulty_level: Selected difficulty level or "Mixed"
        easy_count: Number of easy questions (for mixed mode)
        moderate_count: Number of moderate questions (for mixed mode)
        difficult_count: Number of difficult questions (for mixed mode)
        parsed_jd: Parsed job description with key requirements
        questions: Generated interview questions
        error: Error message if any
    """
    job_description_text: str
    num_questions: int
    difficulty_level: str
    easy_count: int
    moderate_count: int
    difficult_count: int
    parsed_jd: dict
    questions: List[InterviewQuestion]
    error: Optional[str]
