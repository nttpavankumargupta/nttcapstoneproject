"""LangGraph nodes for job matching workflow"""

from typing import List, Dict
import json
from src.state.job_match_state import (
    JobMatchState, 
    JobDescription, 
    Resume, 
    CandidateMatch
)


class JobMatchNodes:
    """Contains node functions for job matching workflow"""

    def __init__(self, llm):
        """
        Initialize job match nodes
        
        Args:
            llm: Language model instance
        """
        self.llm = llm

    def parse_job_description(self, state: JobMatchState) -> JobMatchState:
        """
        Parse job description to extract structured information
        
        Args:
            state: Current job match state
            
        Returns:
            Updated state with parsed job description
        """
        if not state.job_description_text:
            state_dict = state.model_dump()
            state_dict["error"] = "No job description provided"
            return JobMatchState(**state_dict)
        
        prompt = f"""Analyze this job description and extract structured information.

Job Description:
{state.job_description_text}

Extract and return ONLY a JSON object with this exact structure:
{{
    "title": "job title",
    "required_skills": ["skill1", "skill2", ...],
    "preferred_skills": ["skill1", "skill2", ...],
    "requirements": ["requirement1", "requirement2", ...]
}}

Be thorough and extract all mentioned skills, technologies, and requirements."""

        response = self.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                parsed = json.loads(json_str)
            else:
                parsed = json.loads(content)
            
            job_desc = JobDescription(
                title=parsed.get("title", "Unknown Position"),
                content=state.job_description_text,
                required_skills=parsed.get("required_skills", []),
                preferred_skills=parsed.get("preferred_skills", []),
                requirements=parsed.get("requirements", [])
            )
            
            state_dict = state.model_dump()
            state_dict["job_description"] = job_desc
            return JobMatchState(**state_dict)
        except Exception as e:
            state_dict = state.model_dump()
            state_dict["error"] = f"Error parsing job description: {str(e)}"
            return JobMatchState(**state_dict)

    def parse_resumes(self, state: JobMatchState) -> JobMatchState:
        """
        Parse all resumes to extract structured information
        
        Args:
            state: Current job match state
            
        Returns:
            Updated state with parsed resumes
        """
        if not state.resume_texts:
            state_dict = state.model_dump()
            state_dict["error"] = "No resumes provided"
            return JobMatchState(**state_dict)
        
        parsed_resumes = []
        
        for idx, resume_data in enumerate(state.resume_texts):
            resume_name = resume_data.get("name", f"Resume_{idx+1}")
            resume_content = resume_data.get("content", "")
            
            if not resume_content:
                continue
            
            prompt = f"""Analyze this resume and extract structured information.

Resume:
{resume_content}

Extract and return ONLY a JSON object with this exact structure:
{{
    "skills": ["skill1", "skill2", ...],
    "experience": ["experience1", "experience2", ...],
    "education": ["education1", "education2", ...]
}}

Be thorough and extract all technical skills, professional experiences, and educational qualifications."""

            try:
                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Extract JSON from response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    parsed = json.loads(json_str)
                else:
                    parsed = json.loads(content)
                
                resume = Resume(
                    id=f"resume_{idx+1}",
                    name=resume_name,
                    content=resume_content,
                    skills=parsed.get("skills", []),
                    experience=parsed.get("experience", []),
                    education=parsed.get("education", [])
                )
                parsed_resumes.append(resume)
            except Exception as e:
                # Continue with next resume if one fails
                print(f"Error parsing resume {resume_name}: {str(e)}")
                continue
        
        state_dict = state.model_dump()
        state_dict["resumes"] = parsed_resumes
        return JobMatchState(**state_dict)

    def analyze_matches(self, state: JobMatchState) -> JobMatchState:
        """
        Analyze each resume against job description to find matches and gaps
        
        Args:
            state: Current job match state
            
        Returns:
            Updated state with candidate matches
        """
        if not state.job_description or not state.resumes:
            state_dict = state.model_dump()
            state_dict["error"] = "Missing job description or resumes for analysis"
            return JobMatchState(**state_dict)
        
        candidate_matches = []
        
        for resume in state.resumes:
            # Create detailed analysis prompt
            prompt = f"""Analyze this candidate's resume against the job requirements.

Job Title: {state.job_description.title}

Required Skills: {', '.join(state.job_description.required_skills)}
Preferred Skills: {', '.join(state.job_description.preferred_skills)}
Requirements: {', '.join(state.job_description.requirements)}

Candidate Skills: {', '.join(resume.skills)}
Candidate Experience: {', '.join(resume.experience)}
Candidate Education: {', '.join(resume.education)}

Provide a detailed analysis and return ONLY a JSON object with this exact structure:
{{
    "match_score": 0.0-100.0,
    "matched_skills": ["skill1", "skill2", ...],
    "missing_skills": ["skill1", "skill2", ...],
    "gaps": ["gap1", "gap2", ...],
    "strengths": ["strength1", "strength2", ...],
    "summary": "Brief summary of the candidate's fit for this role"
}}

- match_score: 0-100 indicating overall fit
- matched_skills: Skills from job requirements that candidate has
- missing_skills: Required skills the candidate lacks
- gaps: Specific gaps or weaknesses relative to job requirements
- strengths: Candidate's strengths relevant to this position
- summary: 2-3 sentence overall assessment"""

            try:
                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Extract JSON from response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    parsed = json.loads(json_str)
                else:
                    parsed = json.loads(content)
                
                match = CandidateMatch(
                    resume_id=resume.id,
                    resume_name=resume.name,
                    match_score=float(parsed.get("match_score", 0.0)),
                    matched_skills=parsed.get("matched_skills", []),
                    missing_skills=parsed.get("missing_skills", []),
                    gaps=parsed.get("gaps", []),
                    strengths=parsed.get("strengths", []),
                    summary=parsed.get("summary", "")
                )
                candidate_matches.append(match)
            except Exception as e:
                print(f"Error analyzing resume {resume.name}: {str(e)}")
                continue
        
        # Sort by match score
        candidate_matches.sort(key=lambda x: x.match_score, reverse=True)
        
        state_dict = state.model_dump()
        state_dict["candidate_matches"] = candidate_matches
        state_dict["best_candidate"] = candidate_matches[0] if candidate_matches else None
        return JobMatchState(**state_dict)

    def finalize_results(self, state: JobMatchState) -> JobMatchState:
        """
        Finalize the analysis results
        
        Args:
            state: Current job match state
            
        Returns:
            Updated state with analysis complete flag
        """
        state_dict = state.model_dump()
        state_dict["analysis_complete"] = True
        return JobMatchState(**state_dict)
