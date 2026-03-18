"""Graph builder for job matching LangGraph workflow"""

from langgraph.graph import StateGraph, END
from src.state.job_match_state import JobMatchState
from src.node.job_match_nodes import JobMatchNodes
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JobMatchGraphBuilder:
    """Builds and manages the job matching LangGraph workflow"""
    
    def __init__(self, llm):
        """
        Initialize job match graph builder
        
        Args:
            llm: Language model instance
        """
        logger.info("Initializing JobMatchGraphBuilder")
        self.nodes = JobMatchNodes(llm)
        self.graph = None
        logger.debug("JobMatchGraphBuilder initialized successfully")
    
    def build(self):
        """
        Build the job matching workflow graph
        
        Returns:
            Compiled graph instance
        """
        logger.info("Building job matching workflow graph")
        try:
            # Create state graph
            builder = StateGraph(JobMatchState)
            
            # Add nodes
            logger.debug("Adding graph nodes")
            builder.add_node("parse_job_description", self.nodes.parse_job_description)
            builder.add_node("parse_resumes", self.nodes.parse_resumes)
            builder.add_node("analyze_matches", self.nodes.analyze_matches)
            builder.add_node("finalize_results", self.nodes.finalize_results)
            
            # Set entry point
            builder.set_entry_point("parse_job_description")
            
            # Add edges - sequential workflow
            logger.debug("Configuring graph edges")
            builder.add_edge("parse_job_description", "parse_resumes")
            builder.add_edge("parse_resumes", "analyze_matches")
            builder.add_edge("analyze_matches", "finalize_results")
            builder.add_edge("finalize_results", END)
            
            # Compile graph
            logger.debug("Compiling graph")
            self.graph = builder.compile()
            logger.info("Job matching workflow graph built successfully")
            return self.graph
        except Exception as e:
            logger.error(f"Failed to build job matching graph: {str(e)}", exc_info=True)
            raise
    
    def run(self, job_description: str, resumes: list) -> JobMatchState:
        """
        Run the job matching workflow
        
        Args:
            job_description: Job description text
            resumes: List of resume dictionaries with 'name' and 'content' keys
            
        Returns:
            Final JobMatchState with analysis results
        """
        logger.info(f"Running job matching workflow with {len(resumes)} resume(s)")
        try:
            if self.graph is None:
                logger.warning("Graph not built, building now")
                self.build()
            
            initial_state = JobMatchState(
                job_description_text=job_description,
                resume_texts=resumes
            )
            
            logger.debug("Invoking graph with initial state")
            result = self.graph.invoke(initial_state)
            
            # Convert dict result back to JobMatchState object
            if isinstance(result, dict):
                result = JobMatchState(**result)
            
            logger.info("Job matching workflow completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error running job matching workflow: {str(e)}", exc_info=True)
            raise
