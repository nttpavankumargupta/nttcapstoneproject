"""LangGraph nodes for job matching workflow"""

from typing import List, Dict
import json
from src.state.job_match_state import (
    JobMatchState, 
    JobDescription, 
    Resume, 
    CandidateMatch
)

from src.state.job_match_state import (
    JobMatchState,
    JobDescription,
    Resume,
    CandidateMatch,
    InterviewQuestion,
    InterviewEvaluation,
    AnswerEvaluation,
    LearningPlan,
    LearningModule,
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
    
    def generate_interview_questions(self, state: JobMatchState) -> JobMatchState:
        """
        Generate interview questions based on JD + best candidate gaps (or chosen candidate)
        """
        if not state.job_description:
            state_dict = state.model_dump()
            state_dict["error"] = "Missing job description for question generation"
            return JobMatchState(**state_dict)

        if not state.candidate_matches:
            state_dict = state.model_dump()
            state_dict["error"] = "Missing candidate matches for question generation"
            return JobMatchState(**state_dict)

        # Pick candidate: target_resume_id if provided else best_candidate
        target = None
        if state.target_resume_id:
            for m in state.candidate_matches:
                if m.resume_id == state.target_resume_id:
                    target = m
                    break
        if target is None:
            target = state.best_candidate or state.candidate_matches[0]

        jd = state.job_description

        prompt = f"""You are an expert technical recruiter.

Create interview questions to evaluate a candidate for the role:
Title: {jd.title}

Job required skills: {jd.required_skills}
Job preferred skills: {jd.preferred_skills}
Job requirements: {jd.requirements}

Candidate summary:
- matched_skills: {target.matched_skills}
- missing_skills: {target.missing_skills}
- gaps: {target.gaps}
- strengths: {target.strengths}

Rules:
- Create 10 questions total:
  * 6 technical (cover required skills first, then gaps)
  * 2 system design / architecture (if role suggests it; else technical deep-dive)
  * 2 behavioral (communication, leadership, collaboration)
- Each question MUST include a short rubric (3-6 bullet points) describing what a strong answer contains.
- Return ONLY JSON in the exact structure below.

JSON schema:
{{
  "questions": [
    {{
      "id": "q1",
      "category": "technical|system_design|behavioral",
      "skill_tag": "string",
      "difficulty": "easy|medium|hard",
      "question": "string",
      "rubric": ["point1","point2","point3"]
    }}
  ]
}}
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            start = content.find("{")
            end = content.rfind("}") + 1
            parsed = json.loads(content[start:end] if start != -1 else content)

            questions = []
            for q in parsed.get("questions", []):
                questions.append(
                    InterviewQuestion(
                        id=q.get("id", ""),
                        category=q.get("category", "technical"),
                        skill_tag=q.get("skill_tag", ""),
                        difficulty=q.get("difficulty", "medium"),
                        question=q.get("question", ""),
                        rubric=q.get("rubric", []),
                    )
                )

            state_dict = state.model_dump()
            state_dict["interview_questions"] = questions
            return JobMatchState(**state_dict)

        except Exception as e:
            state_dict = state.model_dump()
            state_dict["error"] = f"Error generating interview questions: {str(e)}"
            return JobMatchState(**state_dict)
        
    def evaluate_candidate_answers(self, state: JobMatchState) -> JobMatchState:
        """
        Evaluate candidate answers for correctness using rubrics + JD context
        """
        if not state.job_description:
            state_dict = state.model_dump()
            state_dict["error"] = "Missing job description for answer evaluation"
            return JobMatchState(**state_dict)

        if not state.interview_questions:
            state_dict = state.model_dump()
            state_dict["error"] = "No interview questions found for evaluation"
            return JobMatchState(**state_dict)

        if not state.candidate_answers:
            state_dict = state.model_dump()
            state_dict["error"] = "No candidate answers provided for evaluation"
            return JobMatchState(**state_dict)

        # Build Q/A bundle
        qa_bundle = []
        for q in state.interview_questions:
            ans = state.candidate_answers.get(q.id, "").strip()
            qa_bundle.append(
                {
                    "id": q.id,
                    "category": q.category,
                    "skill_tag": q.skill_tag,
                    "difficulty": q.difficulty,
                    "question": q.question,
                    "rubric": q.rubric,
                    "answer": ans,
                }
            )

        jd = state.job_description

        prompt = f"""You are a strict technical interviewer.

Evaluate the candidate answers for correctness and completeness against:
- Job role context
- The rubric for each question

Job title: {jd.title}
Required skills: {jd.required_skills}
Preferred skills: {jd.preferred_skills}
Requirements: {jd.requirements}

Here are the questions and the candidate answers (JSON):
{json.dumps(qa_bundle, ensure_ascii=False)}

Scoring:
- Score each question 0-5
- Provide:
  * verdict: strong|okay|weak
  * feedback: concise but specific
  * expected_points_hit: which rubric points were covered well
  * missing_points: which rubric points were not addressed or incorrect

Then compute:
- overall_score (0-100)
- recommendation: strong_hire|hire|no_hire|strong_no_hire
- strengths (bullets)
- concerns (bullets)
- summary (2-4 sentences)

Return ONLY JSON in this schema:
{{
  "overall_score": 0-100,
  "recommendation": "strong_hire|hire|no_hire|strong_no_hire",
  "strengths": ["..."],
  "concerns": ["..."],
  "summary": "string",
  "per_question": [
    {{
      "question_id": "q1",
      "score": 0-5,
      "verdict": "strong|okay|weak",
      "feedback": "string",
      "expected_points_hit": ["..."],
      "missing_points": ["..."]
    }}
  ]
}}
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            start = content.find("{")
            end = content.rfind("}") + 1
            parsed = json.loads(content[start:end] if start != -1 else content)

            per_q = []
            for item in parsed.get("per_question", []):
                per_q.append(
                    AnswerEvaluation(
                        question_id=item.get("question_id", ""),
                        score=float(item.get("score", 0.0)),
                        verdict=item.get("verdict", "weak"),
                        feedback=item.get("feedback", ""),
                        expected_points_hit=item.get("expected_points_hit", []),
                        missing_points=item.get("missing_points", []),
                    )
                )

            evaluation = InterviewEvaluation(
                overall_score=float(parsed.get("overall_score", 0.0)),
                recommendation=parsed.get("recommendation", "no_hire"),
                strengths=parsed.get("strengths", []),
                concerns=parsed.get("concerns", []),
                summary=parsed.get("summary", ""),
                per_question=per_q,
            )

            state_dict = state.model_dump()
            state_dict["interview_evaluation"] = evaluation
            return JobMatchState(**state_dict)

        except Exception as e:
            state_dict = state.model_dump()
            state_dict["error"] = f"Error evaluating candidate answers: {str(e)}"
            return JobMatchState(**state_dict)
        

    def generate_learning_plan(self, state: JobMatchState) -> JobMatchState:
        """
        Agent 4: Build a learning plan when interview performance is weak.
        Uses resume gaps + interview evaluation missing points.
        """
        if not state.job_description or not state.candidate_matches:
            state_dict = state.model_dump()
            state_dict["error"] = "Missing job description or candidate matches for learning plan"
            return JobMatchState(**state_dict)

        ev = getattr(state, "interview_evaluation", None)
        if not ev:
            state_dict = state.model_dump()
            state_dict["error"] = "Missing interview evaluation for learning plan"
            return JobMatchState(**state_dict)

        # Pick candidate: target_resume_id if provided else best
        target = None
        target_id = getattr(state, "target_resume_id", "") or ""
        if target_id:
            for m in state.candidate_matches:
                if m.resume_id == target_id:
                    target = m
                    break
        if target is None:
            target = state.best_candidate or state.candidate_matches[0]

        jd = state.job_description

        # Extract weak areas from evaluation
        weak_questions = []
        missing_points_flat = []
        for pq in ev.per_question:
            # treat <=2 as weak by default
            if float(pq.score) <= 2.0 or (pq.verdict or "").lower() == "weak":
                weak_questions.append({
                    "question_id": pq.question_id,
                    "score": pq.score,
                    "verdict": pq.verdict,
                    "missing_points": pq.missing_points,
                    "feedback": pq.feedback
                })
            for mp in (pq.missing_points or []):
                missing_points_flat.append(mp)

        # Keep prompt payload compact
        eval_summary = {
            "overall_score": ev.overall_score,
            "recommendation": ev.recommendation,
            "concerns": ev.concerns,
            "weak_questions": weak_questions[:6],  # cap
            "common_missing_points": missing_points_flat[:20],  # cap
        }

        prompt = f"""
You are a senior technical mentor.

A candidate interviewed for this role and performed weakly. Create a targeted learning plan to close gaps.
The plan must be practical and aligned to the job role.

ROLE:
Title: {jd.title}
Required Skills: {jd.required_skills}
Preferred Skills: {jd.preferred_skills}
Requirements: {jd.requirements}

CANDIDATE (from resume analysis):
matched_skills: {target.matched_skills}
missing_skills: {target.missing_skills}
gaps: {target.gaps}

INTERVIEW EVALUATION (focus remediation on weak topics):
{json.dumps(eval_summary, ensure_ascii=False)}

Rules:
- Prioritize: (1) weak interview topics (missing_points) then (2) missing required skills then (3) preferred skills.
- Create 4 to 8 modules total.
- Each module must include:
  * learning_steps (clear sequence)
  * practice_tasks (hands-on)
  * milestone (measurable outcome)
- Provide realistic duration and weekly hours.
- Output ONLY JSON exactly matching the schema below.

Schema:
{{
  "candidate_id": "{target.resume_id}",
  "candidate_name": "{target.resume_name}",
  "role_title": "{jd.title}",
  "overall_duration_weeks": 1-24,
  "summary": "2-4 sentences",
  "modules": [
    {{
      "skill": "string",
      "level_target": "basic|intermediate|job-ready",
      "duration_weeks": 1-12,
      "weekly_hours": 2-15,
      "prerequisites": ["..."],
      "learning_steps": ["..."],
      "resources": ["..."],
      "practice_tasks": ["..."],
      "milestone": "string"
    }}
  ],
  "notes": ["..."]
}}
"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            start = content.find("{")
            end = content.rfind("}") + 1
            parsed = json.loads(content[start:end] if start != -1 else content)

            modules = []
            for m in parsed.get("modules", []):
                modules.append(
                    LearningModule(
                        skill=m.get("skill", ""),
                        level_target=m.get("level_target", "intermediate"),
                        duration_weeks=int(m.get("duration_weeks", 2)),
                        weekly_hours=int(m.get("weekly_hours", 5)),
                        prerequisites=m.get("prerequisites", []),
                        learning_steps=m.get("learning_steps", []),
                        resources=m.get("resources", []),
                        practice_tasks=m.get("practice_tasks", []),
                        milestone=m.get("milestone", ""),
                    )
                )

            plan = LearningPlan(
                candidate_id=parsed.get("candidate_id", target.resume_id),
                candidate_name=parsed.get("candidate_name", target.resume_name),
                role_title=parsed.get("role_title", jd.title),
                overall_duration_weeks=int(parsed.get("overall_duration_weeks", 6)),
                summary=parsed.get("summary", ""),
                modules=modules,
                notes=parsed.get("notes", []),
            )

            state_dict = state.model_dump()
            state_dict["learning_plan"] = plan
            return JobMatchState(**state_dict)

        except Exception as e:
            state_dict = state.model_dump()
            state_dict["error"] = f"Error generating learning plan: {str(e)}"
            return JobMatchState(**state_dict)
