"""Graph builder for Gap Analysis and Course Recommendation LangGraph workflow"""

from langgraph.graph import StateGraph, END
from src.state.gap_analysis_state import GapAnalysisState
from src.node.gap_analysis_nodes import GapAnalysisNodes
from src.vectorstore.course_vectorstore import CourseVectorStore


class GapAnalysisGraphBuilder:
    """Builds and manages the gap analysis and course recommendation LangGraph workflow"""
    
    def __init__(self, llm, course_vectorstore: CourseVectorStore):
        """
        Initialize gap analysis graph builder
        
        Args:
            llm: Language model instance
            course_vectorstore: Course vector store for recommendations
        """
        self.nodes = GapAnalysisNodes(llm, course_vectorstore)
        self.graph = None
    
    def build(self):
        """
        Build the gap analysis workflow graph
        
        Returns:
            Compiled graph instance
        """
        # Create state graph
        builder = StateGraph(GapAnalysisState)
        
        # Add nodes
        builder.add_node("identify_skill_gaps", self.nodes.identify_skill_gaps)
        builder.add_node("search_relevant_courses", self.nodes.search_relevant_courses)
        builder.add_node("recommend_courses", self.nodes.recommend_courses)
        builder.add_node("create_learning_path", self.nodes.create_learning_path)
        
        # Set entry point
        builder.set_entry_point("identify_skill_gaps")
        
        # Add edges - sequential workflow
        builder.add_edge("identify_skill_gaps", "search_relevant_courses")
        builder.add_edge("search_relevant_courses", "recommend_courses")
        builder.add_edge("recommend_courses", "create_learning_path")
        builder.add_edge("create_learning_path", END)
        
        # Compile graph
        self.graph = builder.compile()
        return self.graph
    
    def run(self, job_description: str, answer_evaluations: list, 
            missing_practical_skills: list) -> GapAnalysisState:
        """
        Run the gap analysis and course recommendation workflow
        
        Args:
            job_description: Original job description
            answer_evaluations: List of answer evaluations from previous agent
            missing_practical_skills: List of missing practical skills
            
        Returns:
            Final GapAnalysisState with course recommendations
        """
        if self.graph is None:
            self.build()
        
        initial_state = GapAnalysisState(
            job_description_text=job_description,
            answer_evaluations=answer_evaluations,
            missing_practical_skills=missing_practical_skills
        )
        
        result = self.graph.invoke(initial_state)
        
        # Convert dict result back to GapAnalysisState object
        if isinstance(result, dict):
            return GapAnalysisState(**result)
        return result
