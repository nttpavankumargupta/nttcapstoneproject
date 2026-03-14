"""State management for Answer Evaluation Agent"""

from typing import TypedDict, List, Optional
from dataclasses import dataclass


@dataclass
class QuestionAnswer:
    """Represents a question and its answer"""
    question: str
    question_topic: str
    question_difficulty: str
    candidate_answer: str
    expected_answer_points: List[str]


@dataclass
class AnswerEvaluation:
    """Represents evaluation of a single answer"""
    question: str
    candidate_answer: str
    score: float  # 0-100
    practicality_score: float  # 0-100 (focus on practical understanding)
    theoretical_score: float  # 0-100 (theoretical knowledge)
    strengths: List[str]
    weaknesses: List[str]
    missing_practical_aspects: List[str]
    feedback: str


class AnswerEvalState(TypedDict, total=False):
    """
    State for Answer Evaluation workflow
    
    Attributes:
        job_description_text: Original job description
        questions_and_answers: List of questions with candidate answers
        evaluations: List of answer evaluations
        overall_score: Overall practical score (0-100)
        overall_theoretical_score: Overall theoretical score (0-100)
        strong_areas: Areas where candidate performed well
        weak_areas: Areas needing improvement
        practical_skills_demonstrated: List of practical skills shown
        missing_practical_skills: List of practical skills missing
        summary: Overall evaluation summary
        error: Error message if any
    """
    job_description_text: str
    questions_and_answers: List[QuestionAnswer]
    evaluations: List[AnswerEvaluation]
    overall_score: float
    overall_theoretical_score: float
    strong_areas: List[str]
    weak_areas: List[str]
    practical_skills_demonstrated: List[str]
    missing_practical_skills: List[str]
    summary: str
    error: Optional[str]
