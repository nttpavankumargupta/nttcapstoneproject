"""Nodes for Answer Evaluation LangGraph workflow"""

from typing import List
from src.state.answer_eval_state import AnswerEvalState, AnswerEvaluation


class AnswerEvalNodes:
    """Nodes for answer evaluation workflow"""
    
    def __init__(self, llm):
        """
        Initialize answer evaluation nodes
        
        Args:
            llm: Language model instance
        """
        self.llm = llm
    
    def evaluate_individual_answers(self, state: AnswerEvalState) -> AnswerEvalState:
        """
        Evaluate each answer individually with focus on practical understanding
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with individual evaluations
        """
        try:
            questions_and_answers = state['questions_and_answers']
            evaluations = []
            
            for qa in questions_and_answers:
                prompt = f"""
                You are an expert interviewer evaluating a candidate's answer with a focus on PRACTICAL understanding, not theoretical knowledge.
                
                Question: {qa.question}
                Topic: {qa.question_topic}
                Difficulty: {qa.question_difficulty}
                
                Expected Key Points:
                {chr(10).join(f"- {point}" for point in qa.expected_answer_points)}
                
                Candidate's Answer:
                {qa.candidate_answer}
                
                Evaluate this answer focusing on:
                1. PRACTICAL UNDERSTANDING (70% weight): Does the candidate demonstrate real-world application, hands-on experience, problem-solving ability?
                2. THEORETICAL KNOWLEDGE (30% weight): Does the candidate understand concepts?
                
                Provide evaluation in this format:
                PRACTICALITY_SCORE: [0-100]
                THEORETICAL_SCORE: [0-100]
                OVERALL_SCORE: [0-100]
                
                STRENGTHS:
                - [strength 1]
                - [strength 2]
                
                WEAKNESSES:
                - [weakness 1]
                - [weakness 2]
                
                MISSING_PRACTICAL_ASPECTS:
                - [practical aspect 1 that's missing]
                - [practical aspect 2 that's missing]
                
                FEEDBACK:
                [Detailed feedback focusing on practical understanding and areas for improvement]
                """
                
                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                
                # Parse the evaluation
                evaluation = self._parse_evaluation(qa.question, qa.candidate_answer, content)
                evaluations.append(evaluation)
            
            return {
                **state,
                "evaluations": evaluations
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to evaluate answers: {str(e)}"
            }
    
    def _parse_evaluation(self, question: str, answer: str, content: str) -> AnswerEvaluation:
        """Parse LLM response into structured evaluation"""
        lines = content.split('\n')
        
        practicality_score = 0.0
        theoretical_score = 0.0
        overall_score = 0.0
        strengths = []
        weaknesses = []
        missing_practical = []
        feedback = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('PRACTICALITY_SCORE:'):
                try:
                    practicality_score = float(line.split(':')[1].strip())
                except:
                    practicality_score = 50.0
            elif line.startswith('THEORETICAL_SCORE:'):
                try:
                    theoretical_score = float(line.split(':')[1].strip())
                except:
                    theoretical_score = 50.0
            elif line.startswith('OVERALL_SCORE:'):
                try:
                    overall_score = float(line.split(':')[1].strip())
                except:
                    overall_score = (practicality_score * 0.7 + theoretical_score * 0.3)
            elif line.startswith('STRENGTHS:'):
                current_section = 'strengths'
            elif line.startswith('WEAKNESSES:'):
                current_section = 'weaknesses'
            elif line.startswith('MISSING_PRACTICAL_ASPECTS:'):
                current_section = 'missing'
            elif line.startswith('FEEDBACK:'):
                current_section = 'feedback'
            elif line.startswith('-') or line.startswith('•'):
                point = line.lstrip('-•').strip()
                if current_section == 'strengths':
                    strengths.append(point)
                elif current_section == 'weaknesses':
                    weaknesses.append(point)
                elif current_section == 'missing':
                    missing_practical.append(point)
            elif current_section == 'feedback':
                feedback += line + " "
        
        # If overall score wasn't parsed, calculate it
        if overall_score == 0.0 and (practicality_score > 0 or theoretical_score > 0):
            overall_score = practicality_score * 0.7 + theoretical_score * 0.3
        
        return AnswerEvaluation(
            question=question,
            candidate_answer=answer,
            score=overall_score,
            practicality_score=practicality_score,
            theoretical_score=theoretical_score,
            strengths=strengths if strengths else ["Response provided"],
            weaknesses=weaknesses if weaknesses else ["Needs more detail"],
            missing_practical_aspects=missing_practical if missing_practical else ["Practical examples"],
            feedback=feedback.strip() if feedback else "Evaluation completed"
        )
    
    def aggregate_results(self, state: AnswerEvalState) -> AnswerEvalState:
        """
        Aggregate individual evaluations into overall assessment
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with aggregated results
        """
        try:
            if state.get('error'):
                return state
            
            evaluations = state.get('evaluations', [])
            
            if not evaluations:
                return {
                    **state,
                    "error": "No evaluations to aggregate"
                }
            
            # Calculate overall scores
            total_practical = sum(e.practicality_score for e in evaluations)
            total_theoretical = sum(e.theoretical_score for e in evaluations)
            count = len(evaluations)
            
            overall_practical_score = total_practical / count
            overall_theoretical_score = total_theoretical / count
            
            # Collect all practical skills and gaps
            all_strengths = []
            all_weaknesses = []
            all_missing_practical = []
            
            for eval in evaluations:
                all_strengths.extend(eval.strengths)
                all_weaknesses.extend(eval.weaknesses)
                all_missing_practical.extend(eval.missing_practical_aspects)
            
            # Identify strong and weak areas
            prompt = f"""
            Based on these answer evaluations, identify the candidate's strong and weak areas:
            
            Average Practical Score: {overall_practical_score:.1f}/100
            Average Theoretical Score: {overall_theoretical_score:.1f}/100
            
            All Strengths Noted:
            {chr(10).join(f"- {s}" for s in all_strengths[:20])}
            
            All Weaknesses Noted:
            {chr(10).join(f"- {w}" for w in all_weaknesses[:20])}
            
            Missing Practical Aspects:
            {chr(10).join(f"- {m}" for m in all_missing_practical[:20])}
            
            Provide:
            STRONG_AREAS: (3-5 key areas where candidate excels)
            - [area 1]
            - [area 2]
            
            WEAK_AREAS: (3-5 key areas needing improvement)
            - [area 1]
            - [area 2]
            
            PRACTICAL_SKILLS_DEMONSTRATED: (specific practical skills shown)
            - [skill 1]
            - [skill 2]
            
            MISSING_PRACTICAL_SKILLS: (practical skills not demonstrated)
            - [skill 1]
            - [skill 2]
            """
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse aggregated results
            strong_areas, weak_areas, practical_skills, missing_skills = self._parse_aggregation(content)
            
            return {
                **state,
                "overall_score": overall_practical_score,
                "overall_theoretical_score": overall_theoretical_score,
                "strong_areas": strong_areas,
                "weak_areas": weak_areas,
                "practical_skills_demonstrated": practical_skills,
                "missing_practical_skills": missing_skills
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to aggregate results: {str(e)}"
            }
    
    def _parse_aggregation(self, content: str) -> tuple:
        """Parse aggregated results from LLM response"""
        lines = content.split('\n')
        
        strong_areas = []
        weak_areas = []
        practical_skills = []
        missing_skills = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if 'STRONG_AREAS' in line:
                current_section = 'strong'
            elif 'WEAK_AREAS' in line:
                current_section = 'weak'
            elif 'PRACTICAL_SKILLS_DEMONSTRATED' in line:
                current_section = 'practical'
            elif 'MISSING_PRACTICAL_SKILLS' in line:
                current_section = 'missing'
            elif line.startswith('-') or line.startswith('•'):
                item = line.lstrip('-•').strip()
                if current_section == 'strong':
                    strong_areas.append(item)
                elif current_section == 'weak':
                    weak_areas.append(item)
                elif current_section == 'practical':
                    practical_skills.append(item)
                elif current_section == 'missing':
                    missing_skills.append(item)
        
        return (
            strong_areas if strong_areas else ["General understanding"],
            weak_areas if weak_areas else ["Needs more practical experience"],
            practical_skills if practical_skills else ["Basic skills"],
            missing_skills if missing_skills else ["Advanced practical skills"]
        )
    
    def generate_summary(self, state: AnswerEvalState) -> AnswerEvalState:
        """
        Generate overall evaluation summary
        
        Args:
            state: Current workflow state
            
        Returns:
            Final state with summary
        """
        try:
            if state.get('error'):
                return state
            
            prompt = f"""
            Create a comprehensive evaluation summary for this candidate:
            
            Overall Practical Score: {state['overall_score']:.1f}/100
            Overall Theoretical Score: {state['overall_theoretical_score']:.1f}/100
            
            Strong Areas:
            {chr(10).join(f"- {area}" for area in state['strong_areas'])}
            
            Weak Areas:
            {chr(10).join(f"- {area}" for area in state['weak_areas'])}
            
            Practical Skills Demonstrated:
            {chr(10).join(f"- {skill}" for skill in state['practical_skills_demonstrated'])}
            
            Missing Practical Skills:
            {chr(10).join(f"- {skill}" for skill in state['missing_practical_skills'])}
            
            Write a 2-3 paragraph summary that:
            1. Evaluates the candidate's practical readiness for the role
            2. Highlights their key strengths and areas for development
            3. Provides specific recommendations for improvement
            4. Emphasizes practical skills over theoretical knowledge
            """
            
            response = self.llm.invoke(prompt)
            summary = response.content if hasattr(response, 'content') else str(response)
            
            return {
                **state,
                "summary": summary
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to generate summary: {str(e)}"
            }
