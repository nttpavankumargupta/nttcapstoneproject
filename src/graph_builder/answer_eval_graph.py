"""Graph builder for Answer Evaluation LangGraph workflow"""

from langgraph.graph import StateGraph, END
from src.state.answer_eval_state import AnswerEvalState
from src.node.answer_eval_nodes import AnswerEvalNodes


class AnswerEvalGraphBuilder:
    """Builds and manages the answer evaluation LangGraph workflow"""
    
    def __init__(self, llm):
        """
        Initialize answer evaluation graph builder
        
        Args:
            llm: Language model instance
        """
        self.nodes = AnswerEvalNodes(llm)
        self.graph = None
    
    def build(self):
        """
        Build the answer evaluation workflow graph
        
        Returns:
            Compiled graph instance
        """
        # Create state graph
        builder = StateGraph(AnswerEvalState)
        
        # Add nodes
        builder.add_node("evaluate_individual_answers", self.nodes.evaluate_individual_answers)
        builder.add_node("aggregate_results", self.nodes.aggregate_results)
        builder.add_node("generate_summary", self.nodes.generate_summary)
        
        # Set entry point
        builder.set_entry_point("evaluate_individual_answers")
        
        # Add edges - sequential workflow
        builder.add_edge("evaluate_individual_answers", "aggregate_results")
        builder.add_edge("aggregate_results", "generate_summary")
        builder.add_edge("generate_summary", END)
        
        # Compile graph
        self.graph = builder.compile()
        return self.graph
    
    def run(self, job_description: str, questions_and_answers: list) -> AnswerEvalState:
        """
        Run the answer evaluation workflow
        
        Args:
            job_description: Original job description
            questions_and_answers: List of QuestionAnswer objects
            
        Returns:
            Final AnswerEvalState with evaluations
        """
        if self.graph is None:
            self.build()
        
        initial_state = AnswerEvalState(
            job_description_text=job_description,
            questions_and_answers=questions_and_answers
        )
        
        result = self.graph.invoke(initial_state)
        
        # Convert dict result back to AnswerEvalState object
        if isinstance(result, dict):
            return AnswerEvalState(**result)
        return result
