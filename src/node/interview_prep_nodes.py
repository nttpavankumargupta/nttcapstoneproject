"""Nodes for Interview Preparation LangGraph workflow"""

from typing import List
from src.state.interview_prep_state import InterviewPrepState, InterviewQuestion


class InterviewPrepNodes:
    """Nodes for interview question generation workflow"""
    
    def __init__(self, llm):
        """
        Initialize interview prep nodes
        
        Args:
            llm: Language model instance
        """
        self.llm = llm
    
    def parse_job_description(self, state: InterviewPrepState) -> InterviewPrepState:
        """
        Parse job description to extract key requirements
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with parsed job description
        """
        try:
            prompt = f"""
            Analyze this job description and extract key information:
            
            Job Description:
            {state['job_description_text']}
            
            Extract and structure the following:
            1. Job Title
            2. Required Technical Skills (list)
            3. Required Soft Skills (list)
            4. Years of Experience Required
            5. Key Responsibilities (list)
            6. Required Qualifications (list)
            7. Main Technologies/Tools mentioned
            
            Provide the output in a structured format.
            """
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            return {
                **state,
                "parsed_jd": {
                    "raw_content": content,
                    "extracted": True
                }
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to parse job description: {str(e)}"
            }
    
    def generate_questions(self, state: InterviewPrepState) -> InterviewPrepState:
        """
        Generate interview questions based on requirements
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with generated questions
        """
        try:
            if state.get('error'):
                return state
            
            num_questions = state['num_questions']
            difficulty_level = state['difficulty_level']
            
            # Build difficulty instructions
            if difficulty_level == "Mixed":
                easy_count = state.get('easy_count', 0)
                moderate_count = state.get('moderate_count', 0)
                difficult_count = state.get('difficult_count', 0)
                
                difficulty_instruction = f"""
                Generate exactly {num_questions} questions with this distribution:
                - {easy_count} Easy questions (basic concepts, definitions, simple scenarios)
                - {moderate_count} Moderate questions (practical applications, problem-solving)
                - {difficult_count} Difficult questions (complex scenarios, system design, advanced concepts)
                """
            else:
                difficulty_instruction = f"""
                Generate exactly {num_questions} questions at {difficulty_level} difficulty level.
                
                {difficulty_level} level characteristics:
                - Easy: Basic concepts, definitions, simple scenarios
                - Moderate: Practical applications, problem-solving, real-world examples
                - Difficult: Complex scenarios, system design, advanced concepts, trade-offs
                """
            
            prompt = f"""
            Based on this job description analysis:
            {state['parsed_jd']['raw_content']}
            
            {difficulty_instruction}
            
            For EACH question, provide:
            1. The question text
            2. Difficulty level (Easy/Moderate/Difficult)
            3. Topic/Category (e.g., "Technical Skills - Python", "Problem Solving", "System Design")
            4. 3-5 key points that should be in a good answer
            5. 2-3 potential follow-up questions
            
            Format each question as:
            ---
            QUESTION: [question text]
            DIFFICULTY: [Easy/Moderate/Difficult]
            TOPIC: [topic]
            EXPECTED POINTS:
            - [point 1]
            - [point 2]
            - [point 3]
            FOLLOW-UP QUESTIONS:
            - [follow-up 1]
            - [follow-up 2]
            ---
            
            Make questions relevant to the job requirements and assess candidate suitability effectively.
            """
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse the response into structured questions
            questions = self._parse_questions(content)
            
            return {
                **state,
                "questions": questions
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Failed to generate questions: {str(e)}"
            }
    
    def _parse_questions(self, content: str) -> List[InterviewQuestion]:
        """Parse LLM response into structured questions"""
        questions = []
        
        # Split by question separator
        question_blocks = content.split('---')
        
        for block in question_blocks:
            if not block.strip():
                continue
                
            try:
                lines = block.strip().split('\n')
                question_text = ""
                difficulty = ""
                topic = ""
                expected_points = []
                follow_ups = []
                
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith('QUESTION:'):
                        question_text = line.replace('QUESTION:', '').strip()
                        current_section = 'question'
                    elif line.startswith('DIFFICULTY:'):
                        difficulty = line.replace('DIFFICULTY:', '').strip()
                        current_section = 'difficulty'
                    elif line.startswith('TOPIC:'):
                        topic = line.replace('TOPIC:', '').strip()
                        current_section = 'topic'
                    elif line.startswith('EXPECTED POINTS:'):
                        current_section = 'expected'
                    elif line.startswith('FOLLOW-UP QUESTIONS:'):
                        current_section = 'followup'
                    elif line.startswith('-') or line.startswith('•'):
                        point = line.lstrip('-•').strip()
                        if current_section == 'expected':
                            expected_points.append(point)
                        elif current_section == 'followup':
                            follow_ups.append(point)
                
                if question_text:
                    questions.append(InterviewQuestion(
                        question=question_text,
                        difficulty=difficulty if difficulty else "Moderate",
                        topic=topic if topic else "General",
                        expected_answer_points=expected_points if expected_points else ["Relevant answer demonstrating understanding"],
                        follow_up_questions=follow_ups if follow_ups else []
                    ))
            
            except Exception as e:
                # Skip malformed questions
                continue
        
        return questions
    
    def finalize_questions(self, state: InterviewPrepState) -> InterviewPrepState:
        """
        Finalize and validate questions
        
        Args:
            state: Current workflow state
            
        Returns:
            Final state with validated questions
        """
        if state.get('error'):
            return state
        
        questions = state.get('questions', [])
        
        # Ensure we have the requested number of questions
        if len(questions) < state['num_questions']:
            return {
                **state,
                "error": f"Generated {len(questions)} questions but {state['num_questions']} were requested"
            }
        
        # Trim to exact number if we have more
        if len(questions) > state['num_questions']:
            questions = questions[:state['num_questions']]
        
        return {
            **state,
            "questions": questions
        }
