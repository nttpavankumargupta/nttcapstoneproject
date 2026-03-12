"""Graph builder for Interview Preparation LangGraph workflow"""

from langgraph.graph import StateGraph, END
from src.state.interview_prep_state import InterviewPrepState
from src.node.interview_prep_nodes import InterviewPrepNodes


class InterviewPrepGraphBuilder:
    """Builds and manages the interview preparation LangGraph workflow"""
    
    def __init__(self, llm):
        """
        Initialize interview prep graph builder
        
        Args:
            llm: Language model instance
        """
        self.nodes = InterviewPrepNodes(llm)
        self.graph = None
    
    def build(self):
        """
        Build the interview preparation workflow graph
        
        Returns:
            Compiled graph instance
        """
        # Create state graph
        builder = StateGraph(InterviewPrepState)
        
        # Add nodes
        builder.add_node("parse_job_description", self.nodes.parse_job_description)
        builder.add_node("generate_questions", self.nodes.generate_questions)
        builder.add_node("finalize_questions", self.nodes.finalize_questions)
        
        # Set entry point
        builder.set_entry_point("parse_job_description")
        
        # Add edges - sequential workflow
        builder.add_edge("parse_job_description", "generate_questions")
        builder.add_edge("generate_questions", "finalize_questions")
        builder.add_edge("finalize_questions", END)
        
        # Compile graph
        self.graph = builder.compile()
        return self.graph
    
    def run(self, job_description: str, num_questions: int, difficulty_level: str, 
            easy_count: int = 0, moderate_count: int = 0, difficult_count: int = 0) -> InterviewPrepState:
        """
        Run the interview preparation workflow
        
        Args:
            job_description: Job description text
            num_questions: Total number of questions to generate
            difficulty_level: Difficulty level ("Easy", "Moderate", "Difficult", or "Mixed")
            easy_count: Number of easy questions (for Mixed mode)
            moderate_count: Number of moderate questions (for Mixed mode)
            difficult_count: Number of difficult questions (for Mixed mode)
            
        Returns:
            Final InterviewPrepState with generated questions
        """
        if self.graph is None:
            self.build()
        
        initial_state = InterviewPrepState(
            job_description_text=job_description,
            num_questions=num_questions,
            difficulty_level=difficulty_level,
            easy_count=easy_count,
            moderate_count=moderate_count,
            difficult_count=difficult_count
        )
        
        result = self.graph.invoke(initial_state)
        
        # Convert dict result back to InterviewPrepState object
        if isinstance(result, dict):
            return InterviewPrepState(**result)
        return result
