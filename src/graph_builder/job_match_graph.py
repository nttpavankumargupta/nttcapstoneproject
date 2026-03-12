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
        
         # NEW nodes
        builder.add_node("generate_questions", self.nodes.generate_interview_questions)
        builder.add_node("evaluate_answers", self.nodes.evaluate_candidate_answers)

         # ✅ Agent 4 node (you must implement self.nodes.generate_learning_plan)
        builder.add_node("generate_learning_plan", self.nodes.generate_learning_plan)
        
        # Set entry point
        builder.set_entry_point("parse_job_description")
        
        # Add edges - sequential workflow
        builder.add_edge("parse_job_description", "parse_resumes")
        builder.add_edge("parse_resumes", "analyze_matches")
        builder.add_edge("analyze_matches", "finalize_results")
       
        
        # After results -> generate questions
        builder.add_edge("finalize_results", "generate_questions")
        

        # Conditional:
        # If answers exist -> evaluate; else finish after questions
        def route_after_questions(state: JobMatchState):
            if getattr(state, "candidate_answers", None) and len(state.candidate_answers) > 0:
               return "evaluate_answers"
            return END

        builder.add_conditional_edges("generate_questions", route_after_questions)

        # ✅ After evaluation -> only trigger Agent 4 if score is low / recommendation is no-hire
        def route_after_evaluation(state: JobMatchState):
            ev = getattr(state, "interview_evaluation", None)
            if not ev:
               return END
            
             # Trigger rules (adjust thresholds as you like)
            if getattr(ev, "overall_score", 100) < 70:
               return "generate_learning_plan"
            if getattr(ev, "recommendation", "").lower() in ["no_hire", "strong_no_hire"]:
               return "generate_learning_plan"

            return END

        builder.add_conditional_edges("evaluate_answers", route_after_evaluation)

        # Learning plan ends the flow
        builder.add_edge("generate_learning_plan", END)

        # Compile graph
        self.graph = builder.compile()
        return self.graph
    
    def run(self, job_description: str, resumes: list, target_resume_id: str = "", candidate_answers: dict = None) -> JobMatchState:
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
            resume_texts=resumes,
            target_resume_id=target_resume_id or "",
            candidate_answers=candidate_answers or {}
        )
        result = self.graph.invoke(initial_state)
        
        # Convert dict result back to JobMatchState object
        if isinstance(result, dict):
            return JobMatchState(**result)
        return result
