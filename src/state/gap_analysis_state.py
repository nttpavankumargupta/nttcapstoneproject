"""State management for Gap Analysis and Course Recommendation Agent"""

from typing import TypedDict, List, Optional
from dataclasses import dataclass


@dataclass
class SkillGap:
    """Represents a skill gap identified"""
    skill_name: str
    importance: str  # "Critical", "High", "Medium", "Low"
    current_level: str  # "None", "Basic", "Intermediate"
    required_level: str  # "Basic", "Intermediate", "Advanced", "Expert"
    gap_description: str


@dataclass
class CourseRecommendation:
    """Represents a recommended course"""
    course_id: str
    course_name: str
    summary: str
    relevance_score: float  # 0-100
    addresses_gaps: List[str]  # List of skill names this course addresses
    reason: str  # Why this course is recommended
    priority: int  # 1-5 rating (5 = Must do, 4 = Highly Recommended, 3 = Recommended, 2 = Optional, 1 = Nice to have)
    target_time: str  # e.g., "1 Week", "2 Weeks", "1 Month"


class GapAnalysisState(TypedDict, total=False):
    """
    State for Gap Analysis and Course Recommendation workflow
    
    Attributes:
        job_description_text: Original job description
        answer_evaluations: Evaluations from previous agent
        missing_practical_skills: Skills identified as missing from answer eval
        identified_gaps: Detailed list of skill gaps
        _course_search_results: Internal - course search results by skill (dict)
        course_recommendations: List of recommended courses
        learning_path: Ordered list of courses for optimal learning
        estimated_learning_time: Estimated time to close gaps
        priority_skills: Skills to focus on first
        summary: Overall gap analysis summary
        error: Error message if any
    """
    job_description_text: str
    answer_evaluations: List[dict]
    missing_practical_skills: List[str]
    identified_gaps: List[SkillGap]
    _course_search_results: dict  # Internal field for passing search results
    course_recommendations: List[CourseRecommendation]
    learning_path: List[str]  # Ordered course IDs
    estimated_learning_time: str
    priority_skills: List[str]
    summary: str
    error: Optional[str]
