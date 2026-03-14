"""Nodes for Gap Analysis and Course Recommendation LangGraph workflow"""

from typing import List, Dict
from src.state.gap_analysis_state import GapAnalysisState, SkillGap, CourseRecommendation
from src.vectorstore.course_vectorstore import CourseVectorStore


class GapAnalysisNodes:
    """Nodes for gap analysis and course recommendation workflow"""
    
    def __init__(self, llm, course_vectorstore: CourseVectorStore):
        """
        Initialize gap analysis nodes
        
        Args:
            llm: Language model instance
            course_vectorstore: Course vector store for recommendations
        """
        self.llm = llm
        self.course_vectorstore = course_vectorstore
    
    def identify_skill_gaps(self, state: GapAnalysisState) -> GapAnalysisState:
        """
        Identify skill gaps based on answer evaluations
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with identified gaps
        """
        try:
            job_description = state['job_description_text']
            missing_skills = state.get('missing_practical_skills', [])
            answer_evaluations = state.get('answer_evaluations', [])
            
            # Debug logging
            print(f"[DEBUG identify_skill_gaps]")
            print(f"  Job description length: {len(job_description)}")
            print(f"  Missing skills: {missing_skills}")
            print(f"  Number of answer evaluations: {len(answer_evaluations)}")
            
            # Build evaluation summary for context
            eval_summary = ""
            for eval in answer_evaluations[:10]:  # Limit to first 10
                # Check if eval is a dataclass or dict
                if hasattr(eval, 'question'):
                    # It's a dataclass (AnswerEvaluation object)
                    eval_summary += f"\nQuestion: {eval.question[:100]}...\n"
                    eval_summary += f"Score: {eval.score:.1f}/100\n"
                    eval_summary += f"Weaknesses: {', '.join(eval.weaknesses[:3])}\n"
                else:
                    # It's a dict
                    eval_summary += f"\nQuestion: {eval.get('question', 'N/A')[:100]}...\n"
                    eval_summary += f"Score: {eval.get('score', 0):.1f}/100\n"
                    eval_summary += f"Weaknesses: {', '.join(eval.get('weaknesses', [])[:3])}\n"
            
            prompt = f"""
            Based on the job requirements and candidate's answer evaluations, identify specific skill gaps.
            
            Job Description:
            {job_description[:1000]}...
            
            Missing Practical Skills Identified:
            {chr(10).join(f"- {skill}" for skill in missing_skills)}
            
            Sample Answer Evaluations:
            {eval_summary}
            
            For each significant skill gap, provide:
            
            SKILL_GAP:
            SKILL_NAME: [specific skill name]
            IMPORTANCE: [Critical/High/Medium/Low]
            CURRENT_LEVEL: [None/Basic/Intermediate]
            REQUIRED_LEVEL: [Basic/Intermediate/Advanced/Expert]
            GAP_DESCRIPTION: [Brief description of the gap and why it matters]
            ---
            
            Focus on practical skills that are most important for job success.
            Identify 5-8 key skill gaps.
            """
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse skill gaps
            skill_gaps = self._parse_skill_gaps(content, state)
            
            # Extract priority skills (Critical and High importance)
            priority_skills = [
                gap.skill_name for gap in skill_gaps 
                if gap.importance in ['Critical', 'High']
            ]
            
            return {
                **state,
                "identified_gaps": skill_gaps,
                "priority_skills": priority_skills
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to identify skill gaps: {str(e)}"
            }
    
    def _parse_skill_gaps(self, content: str, state: GapAnalysisState) -> List[SkillGap]:
        """Parse skill gaps from LLM response"""
        gaps = []
        blocks = content.split('SKILL_GAP:')
        
        for block in blocks[1:]:  # Skip first empty block
            lines = block.split('\n')
            skill_name = ""
            importance = "Medium"
            current_level = "None"
            required_level = "Intermediate"
            gap_description = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('---'):
                    break
                if line.startswith('SKILL_NAME:'):
                    skill_name = line.replace('SKILL_NAME:', '').strip()
                elif line.startswith('IMPORTANCE:'):
                    importance = line.replace('IMPORTANCE:', '').strip()
                elif line.startswith('CURRENT_LEVEL:'):
                    current_level = line.replace('CURRENT_LEVEL:', '').strip()
                elif line.startswith('REQUIRED_LEVEL:'):
                    required_level = line.replace('REQUIRED_LEVEL:', '').strip()
                elif line.startswith('GAP_DESCRIPTION:'):
                    gap_description = line.replace('GAP_DESCRIPTION:', '').strip()
                elif gap_description and not line.startswith('SKILL'):
                    gap_description += " " + line
            
            if skill_name:
                gaps.append(SkillGap(
                    skill_name=skill_name,
                    importance=importance,
                    current_level=current_level,
                    required_level=required_level,
                    gap_description=gap_description.strip()
                ))
        
        # If no gaps parsed from LLM, create gaps from missing skills list
        if not gaps:
            missing_skills = state.get('missing_practical_skills', [])
            if missing_skills:
                for skill in missing_skills[:8]:  # Limit to 8 skills
                    gaps.append(SkillGap(
                        skill_name=skill,
                        importance="High",
                        current_level="Basic",
                        required_level="Intermediate",
                        gap_description=f"Need to develop {skill} skills to meet job requirements"
                    ))
            else:
                # Absolute fallback if no missing skills provided
                gaps.append(SkillGap(
                    skill_name="General Skills",
                    importance="High",
                    current_level="Basic",
                    required_level="Intermediate",
                    gap_description="Need to develop practical skills"
                ))
        
        return gaps
    
    def search_relevant_courses(self, state: GapAnalysisState) -> GapAnalysisState:
        """
        Search for relevant courses using vector store
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with course search results
        """
        try:
            if state.get('error'):
                print(f"[DEBUG search_relevant_courses] Skipping due to error: {state.get('error')}")
                return state
            
            skill_gaps = state.get('identified_gaps', [])
            print(f"[DEBUG search_relevant_courses] Number of skill gaps: {len(skill_gaps)}")
            
            if not skill_gaps:
                return {
                    **state,
                    "error": "No skill gaps identified to search courses for"
                }
            
            # Search courses for each skill gap
            all_course_results = {}
            
            for gap in skill_gaps:
                # Create a search query combining skill name and description
                search_query = f"{gap.skill_name} {gap.gap_description}"
                print(f"[DEBUG search_relevant_courses] Searching for: '{search_query[:100]}'")
                
                # Search for relevant courses
                courses = self.course_vectorstore.search_courses(search_query, n_results=5)
                all_course_results[gap.skill_name] = courses
                
                # Debug: log search results
                print(f"[DEBUG search_relevant_courses] Found {len(courses)} courses for '{gap.skill_name}'")
                if courses:
                    print(f"  Sample course: {courses[0].get('course_name', 'N/A')[:60]}")
            
            print(f"[DEBUG search_relevant_courses] Total gaps processed: {len(all_course_results)}")
            
            # Store in state for next node
            return {
                **state,
                "_course_search_results": all_course_results
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to search courses: {str(e)}"
            }
    
    def recommend_courses(self, state: GapAnalysisState) -> GapAnalysisState:
        """
        Generate course recommendations based on gaps and search results
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with course recommendations
        """
        try:
            if state.get('error'):
                print(f"[DEBUG recommend_courses] Skipping due to error: {state.get('error')}")
                return state
            
            skill_gaps = state.get('identified_gaps', [])
            course_search_results = state.get('_course_search_results', {})
            
            print(f"[DEBUG recommend_courses] Starting recommendation process")
            print(f"  Number of skill gaps: {len(skill_gaps)}")
            print(f"  Number of course search results: {len(course_search_results)}")
            
            recommendations = []
            seen_courses = set()  # Track unique courses
            
            # Prioritize critical and high importance gaps
            sorted_gaps = sorted(
                skill_gaps,
                key=lambda g: {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}.get(g.importance, 4)
            )
            
            print(f"[DEBUG recommend_courses] Processing {len(sorted_gaps)} gaps")
            
            for gap in sorted_gaps:
                courses = course_search_results.get(gap.skill_name, [])
                print(f"[DEBUG recommend_courses] Gap: '{gap.skill_name}' - {len(courses)} courses available")
                
                for course in courses[:3]:  # Top 3 courses per gap
                    course_id = course['course_id']
                    
                    # Avoid duplicate recommendations
                    if course_id in seen_courses:
                        continue
                    
                    seen_courses.add(course_id)
                    
                    # Use LLM to generate relevance score and reason
                    prompt = f"""
                    Evaluate this course for addressing the skill gap:
                    
                    Skill Gap: {gap.skill_name}
                    Gap Description: {gap.gap_description}
                    Importance: {gap.importance}
                    Current Level: {gap.current_level}
                    Required Level: {gap.required_level}
                    
                    Course: {course['course_name']}
                    Course Summary: {course['summary']}
                    
                    Provide:
                    RELEVANCE_SCORE: [0-100, how well does this course address the gap?]
                    REASON: [One sentence explaining why this course is relevant]
                    """
                    
                    response = self.llm.invoke(prompt)
                    content = response.content if hasattr(response, 'content') else str(response)
                    
                    print(f"[DEBUG recommend_courses] LLM response preview: {content[:200]}")
                    
                    relevance_score, reason = self._parse_course_evaluation(content)
                    
                    # Debug: log evaluation
                    print(f"[DEBUG recommend_courses] Course: {course['course_name'][:50]} - Score: {relevance_score}")
                    
                    # Only recommend if relevance score is above threshold  
                    if relevance_score >= 40:
                        # Calculate priority based on importance and relevance score
                        priority = self._calculate_priority(gap.importance, relevance_score)
                        
                        # Estimate target time based on course summary length and complexity
                        target_time = self._estimate_target_time(course['summary'])
                        
                        recommendations.append(CourseRecommendation(
                            course_id=course_id,
                            course_name=course['course_name'],
                            summary=course['summary'],
                            relevance_score=relevance_score,
                            addresses_gaps=[gap.skill_name],
                            reason=reason,
                            priority=priority,
                            target_time=target_time
                        ))
                        print(f"    ✓ Added to recommendations (Priority: {priority}, Time: {target_time})")
                    else:
                        print(f"    ✗ Below threshold (40)")
            
            print(f"[DEBUG recommend_courses] Total recommendations before sorting: {len(recommendations)}")
            
            # Sort by relevance score
            recommendations.sort(key=lambda r: r.relevance_score, reverse=True)
            
            # Limit to top 10 recommendations
            recommendations = recommendations[:10]
            
            print(f"[DEBUG recommend_courses] Final recommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"  {i}. {rec.course_name[:50]} - Score: {rec.relevance_score}")
            
            return {
                **state,
                "course_recommendations": recommendations
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to recommend courses: {str(e)}"
            }
    
    def _calculate_priority(self, importance: str, relevance_score: float) -> int:
        """
        Calculate course priority (1-5) based on gap importance and relevance score
        
        5 = Must do
        4 = Highly Recommended
        3 = Recommended
        2 = Optional
        1 = Nice to have
        """
        # Base priority on importance
        importance_map = {
            'Critical': 5,
            'High': 4,
            'Medium': 3,
            'Low': 2
        }
        base_priority = importance_map.get(importance, 3)
        
        # Adjust based on relevance score
        if relevance_score >= 85:
            priority = min(5, base_priority + 1)
        elif relevance_score >= 70:
            priority = base_priority
        elif relevance_score >= 55:
            priority = max(1, base_priority - 1)
        else:
            priority = max(1, base_priority - 2)
        
        return priority
    
    def _estimate_target_time(self, course_summary: str) -> str:
        """Estimate target time based on course summary complexity"""
        summary_length = len(course_summary)
        
        # Check for complexity indicators
        complexity_indicators = ['advanced', 'comprehensive', 'in-depth', 'complete', 'mastery', 'expert']
        is_complex = any(indicator in course_summary.lower() for indicator in complexity_indicators)
        
        # Estimate based on length and complexity
        if summary_length > 500 or is_complex:
            return "4-6 Weeks"
        elif summary_length > 300:
            return "2-3 Weeks"
        elif summary_length > 150:
            return "1-2 Weeks"
        else:
            return "1 Week"
    
    def _parse_course_evaluation(self, content: str) -> tuple:
        """Parse course evaluation from LLM response"""
        relevance_score = 70.0  # Default
        reason = "This course covers relevant topics for skill development"
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('RELEVANCE_SCORE:'):
                try:
                    score_text = line.replace('RELEVANCE_SCORE:', '').strip()
                    relevance_score = float(score_text)
                except:
                    pass
            elif line.startswith('REASON:'):
                reason = line.replace('REASON:', '').strip()
        
        return relevance_score, reason
    
    def create_learning_path(self, state: GapAnalysisState) -> GapAnalysisState:
        """
        Create an ordered learning path from recommended courses
        
        Args:
            state: Current workflow state
            
        Returns:
            Final state with learning path and summary
        """
        try:
            if state.get('error'):
                return state
            
            recommendations = state.get('course_recommendations', [])
            skill_gaps = state.get('identified_gaps', [])
            priority_skills = state.get('priority_skills', [])
            
            if not recommendations:
                return {
                    **state,
                    "learning_path": [],
                    "estimated_learning_time": "N/A",
                    "summary": "No specific courses recommended at this time. Focus on practical experience and hands-on projects."
                }
            
            # Create learning path prompt
            course_list = "\n".join([
                f"{i+1}. {rec.course_name} (Score: {rec.relevance_score:.0f}, Addresses: {', '.join(rec.addresses_gaps)})"
                for i, rec in enumerate(recommendations)
            ])
            
            priority_list = ", ".join(priority_skills[:5])
            
            prompt = f"""
            Create an optimal learning path from these recommended courses:
            
            {course_list}
            
            Priority Skills to Address: {priority_list}
            
            Provide:
            LEARNING_PATH: (ordered list of course names, starting with foundational courses)
            - [course 1]
            - [course 2]
            - [course 3]
            
            ESTIMATED_TIME: [e.g., "3-6 months" or "8-12 weeks"]
            
            SUMMARY:
            [2-3 sentences explaining the learning path strategy and expected outcomes]
            """
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse learning path
            learning_path, estimated_time, summary = self._parse_learning_path(content, recommendations)
            
            return {
                **state,
                "learning_path": learning_path,
                "estimated_learning_time": estimated_time,
                "summary": summary
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to create learning path: {str(e)}"
            }
    
    def _parse_learning_path(self, content: str, recommendations: List[CourseRecommendation]) -> tuple:
        """Parse learning path from LLM response"""
        learning_path = []
        estimated_time = "3-6 months"
        summary = ""
        
        lines = content.split('\n')
        current_section = None
        
        # Create course name to ID mapping
        course_name_to_id = {rec.course_name: rec.course_id for rec in recommendations}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if 'LEARNING_PATH' in line:
                current_section = 'path'
            elif 'ESTIMATED_TIME' in line:
                current_section = 'time'
                time_text = line.replace('ESTIMATED_TIME:', '').strip()
                if time_text:
                    estimated_time = time_text
            elif 'SUMMARY' in line:
                current_section = 'summary'
            elif current_section == 'path' and (line.startswith('-') or line.startswith('•')):
                course_name = line.lstrip('-•').strip()
                # Try to match course name to ID
                for rec_name, rec_id in course_name_to_id.items():
                    if rec_name.lower() in course_name.lower() or course_name.lower() in rec_name.lower():
                        if rec_id not in learning_path:  # Avoid duplicates
                            learning_path.append(rec_id)
                        break
            elif current_section == 'summary':
                summary += line + " "
        
        # If no path was extracted, use recommendations in order
        if not learning_path:
            learning_path = [rec.course_id for rec in recommendations[:5]]
        
        if not summary:
            summary = f"Recommended learning path includes {len(learning_path)} courses focusing on priority skills."
        
        return learning_path, estimated_time, summary.strip()
