"""Graph builder for job matching LangGraph workflow"""

from langgraph.graph import StateGraph, END
from src.state.job_match_state import JobMatchState
from src.node.job_match_nodes import JobMatchNodes


class JobMatchGraphBuilder:
    """Builds and manages the job matching LangGraph workflow"""
    
    def __init__(self, llm):
        """
        Initialize job match graph builder
        
        Args:
            llm: Language model instance
        """
        self.nodes = JobMatchNodes(llm)
        self.graph = None
    
    def build(self):
        """
        Build the job matching workflow graph
        
        Returns:
            Compiled graph instance
        """
        # Create state graph
        builder = StateGraph(JobMatchState)
        
        # Add nodes
        builder.add_node("parse_job_description", self.nodes.parse_job_description)
        builder.add_node("parse_resumes", self.nodes.parse_resumes)
        builder.add_node("analyze_matches", self.nodes.analyze_matches)
        builder.add_node("finalize_results", self.nodes.finalize_results)
        
        # Set entry point
        builder.set_entry_point("parse_job_description")
        
        # Add edges - sequential workflow
        builder.add_edge("parse_job_description", "parse_resumes")
        builder.add_edge("parse_resumes", "analyze_matches")
        builder.add_edge("analyze_matches", "finalize_results")
        builder.add_edge("finalize_results", END)
        
        # Compile graph
        self.graph = builder.compile()
        return self.graph
    
    def run(self, job_description: str, resumes: list) -> JobMatchState:
        """
        Run the job matching workflow
        
        Args:
            job_description: Job description text
            resumes: List of resume dictionaries with 'name' and 'content' keys
            
        Returns:
            Final JobMatchState with analysis results
        """
        if self.graph is None:
            self.build()
        
        initial_state = JobMatchState(
            job_description_text=job_description,
            resume_texts=resumes
        )
        result = self.graph.invoke(initial_state)
        
        # Convert dict result back to JobMatchState object
        if isinstance(result, dict):
            return JobMatchState(**result)
        return result
