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
        Identifies PRIMARY (must-have core) and SECONDARY (nice-to-have) skills
        
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
Carefully identify PRIMARY skills (must-have, core, critical) vs SECONDARY skills (nice-to-have, preferred, optional).

Job Description:
{state.job_description_text}

Extract and return ONLY a JSON object with this exact structure:
{{
    "title": "job title",
    "primary_skills": ["core skill1", "core skill2", ...],
    "secondary_skills": ["nice-to-have skill1", "nice-to-have skill2", ...],
    "requirements": ["requirement1", "requirement2", ...]
}}

Guidelines:
- PRIMARY SKILLS: Core technical skills explicitly required, years of experience requirements, must-have certifications
- SECONDARY SKILLS: Preferred/nice-to-have skills, optional technologies, bonus qualifications
- Be thorough and extract all mentioned skills and technologies."""

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
            
            # Map to required_skills and preferred_skills for backward compatibility
            primary = parsed.get("primary_skills", [])
            secondary = parsed.get("secondary_skills", [])
            
            job_desc = JobDescription(
                title=parsed.get("title", "Unknown Position"),
                content=state.job_description_text,
                required_skills=primary,  # Primary skills = required
                preferred_skills=secondary,  # Secondary skills = preferred
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
        Uses weighted scoring: Score = (WP * SP) + (WS * SS)
        WP = Weight for Primary Skills (0.7)
        SP = Similarity Score for Primary Skills
        WS = Weight for Secondary Skills (0.3)
        SS = Similarity Score for Secondary Skills
        
        Args:
            state: Current job match state
            
        Returns:
            Updated state with candidate matches
        """
        if not state.job_description or not state.resumes:
            state_dict = state.model_dump()
            state_dict["error"] = "Missing job description or resumes for analysis"
            return JobMatchState(**state_dict)
        
        # Scoring weights
        WP = 0.7  # Weight for Primary Skills
        WS = 0.3  # Weight for Secondary Skills
        
        candidate_matches = []
        
        for resume in state.resumes:
            # Step 1: Calculate similarity scores separately for primary and secondary skills
            primary_skills_prompt = f"""Analyze how well the candidate matches the PRIMARY (required) skills for this job.

PRIMARY SKILLS REQUIRED: {', '.join(state.job_description.required_skills)}

CANDIDATE'S SKILLS: {', '.join(resume.skills)}
CANDIDATE'S EXPERIENCE: {', '.join(resume.experience)}

Return ONLY a JSON object:
{{
    "similarity_score": 0.0-100.0,
    "matched_primary_skills": ["skill1", "skill2", ...],
    "missing_primary_skills": ["skill1", "skill2", ...]
}}

Calculate similarity_score as: (number of matched primary skills / total primary skills) * 100"""

            secondary_skills_prompt = f"""Analyze how well the candidate matches the SECONDARY (preferred/nice-to-have) skills for this job.

SECONDARY SKILLS PREFERRED: {', '.join(state.job_description.preferred_skills)}

CANDIDATE'S SKILLS: {', '.join(resume.skills)}
CANDIDATE'S EXPERIENCE: {', '.join(resume.experience)}

Return ONLY a JSON object:
{{
    "similarity_score": 0.0-100.0,
    "matched_secondary_skills": ["skill1", "skill2", ...],
    "missing_secondary_skills": ["skill1", "skill2", ...]
}}

Calculate similarity_score as: (number of matched secondary skills / total secondary skills) * 100"""

            try:
                # Get primary skills analysis
                response_primary = self.llm.invoke(primary_skills_prompt)
                content_primary = response_primary.content if hasattr(response_primary, 'content') else str(response_primary)
                
                start = content_primary.find('{')
                end = content_primary.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content_primary[start:end]
                    primary_data = json.loads(json_str)
                else:
                    primary_data = json.loads(content_primary)
                
                SP = float(primary_data.get("similarity_score", 0.0))
                matched_primary = primary_data.get("matched_primary_skills", [])
                missing_primary = primary_data.get("missing_primary_skills", [])
                
                # Get secondary skills analysis
                response_secondary = self.llm.invoke(secondary_skills_prompt)
                content_secondary = response_secondary.content if hasattr(response_secondary, 'content') else str(response_secondary)
                
                start = content_secondary.find('{')
                end = content_secondary.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content_secondary[start:end]
                    secondary_data = json.loads(json_str)
                else:
                    secondary_data = json.loads(content_secondary)
                
                SS = float(secondary_data.get("similarity_score", 0.0))
                matched_secondary = secondary_data.get("matched_secondary_skills", [])
                missing_secondary = secondary_data.get("missing_secondary_skills", [])
                
                # Calculate weighted score: Score = (WP * SP) + (WS * SS)
                weighted_score = (WP * SP) + (WS * SS)
                
                # Get overall analysis for strengths, gaps, and summary
                overall_prompt = f"""Provide an overall assessment of this candidate for the position.

Job Title: {state.job_description.title}

PRIMARY SKILLS MATCHED: {', '.join(matched_primary)}
PRIMARY SKILLS MISSING: {', '.join(missing_primary)}
SECONDARY SKILLS MATCHED: {', '.join(matched_secondary)}
SECONDARY SKILLS MISSING: {', '.join(missing_secondary)}

Candidate Experience: {', '.join(resume.experience)}
Candidate Education: {', '.join(resume.education)}

Return ONLY a JSON object:
{{
    "strengths": ["strength1", "strength2", "strength3"],
    "gaps": ["gap1", "gap2", "gap3"],
    "summary": "2-3 sentence overall assessment"
}}"""

                response_overall = self.llm.invoke(overall_prompt)
                content_overall = response_overall.content if hasattr(response_overall, 'content') else str(response_overall)
                
                start = content_overall.find('{')
                end = content_overall.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content_overall[start:end]
                    overall_data = json.loads(json_str)
                else:
                    overall_data = json.loads(content_overall)
                
                # Combine all matched and missing skills
                all_matched = matched_primary + matched_secondary
                all_missing = missing_primary + missing_secondary
                
                match = CandidateMatch(
                    resume_id=resume.id,
                    resume_name=resume.name,
                    match_score=round(weighted_score, 2),
                    matched_skills=all_matched,
                    missing_skills=all_missing,
                    gaps=overall_data.get("gaps", []),
                    strengths=overall_data.get("strengths", []),
                    summary=overall_data.get("summary", f"Weighted Score: {weighted_score:.1f} (Primary: {SP:.1f}, Secondary: {SS:.1f})")
                )
                candidate_matches.append(match)
                
            except Exception as e:
                print(f"Error analyzing resume {resume.name}: {str(e)}")
                # Fallback to basic match
                match = CandidateMatch(
                    resume_id=resume.id,
                    resume_name=resume.name,
                    match_score=0.0,
                    matched_skills=[],
                    missing_skills=[],
                    gaps=[f"Error during analysis: {str(e)}"],
                    strengths=[],
                    summary="Analysis failed"
                )
                candidate_matches.append(match)
                continue
        
        # Sort by match score (weighted score)
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
