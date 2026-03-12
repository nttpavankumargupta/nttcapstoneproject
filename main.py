"""Job Matching Agent using LangGraph"""

from src.config.config import Config
from src.graph_builder.job_match_graph import JobMatchGraphBuilder


def print_separator():
    """Print a visual separator"""
    print("\n" + "="*80 + "\n")


def print_candidate_analysis(match):
    """Print detailed analysis for a candidate"""
    print(f"📋 Candidate: {match.resume_name}")
    print(f"   Match Score: {match.match_score:.1f}/100")
    print(f"\n   ✅ Matched Skills: {', '.join(match.matched_skills) if match.matched_skills else 'None'}")
    print(f"   ❌ Missing Skills: {', '.join(match.missing_skills) if match.missing_skills else 'None'}")
    print(f"\n   💪 Strengths:")
    for strength in match.strengths:
        print(f"      • {strength}")
    print(f"\n   ⚠️  Gaps:")
    for gap in match.gaps:
        print(f"      • {gap}")
    print(f"\n   📝 Summary: {match.summary}")
    print_separator()


def main():
    """Main function to demonstrate job matching agent"""
    
    print("🤖 Job Matching Agent with LangGraph")
    print_separator()
    
    # Initialize LLM
    print("Initializing language model...")
    llm = Config.get_llm()
    
    # Create job matching graph
    print("Building job matching workflow graph...")
    graph_builder = JobMatchGraphBuilder(llm)
    graph_builder.build()
    print("✅ Graph built successfully!")
    print_separator()
    
    # Sample job description
    job_description = """
    Senior Software Engineer - AI/ML Platform
    
    We are seeking a Senior Software Engineer to join our AI/ML Platform team. 
    
    Required Skills:
    - 5+ years of Python programming experience
    - Strong experience with machine learning frameworks (TensorFlow, PyTorch)
    - Experience with cloud platforms (AWS, GCP, or Azure)
    - Proficiency in Docker and Kubernetes
    - Strong understanding of REST APIs and microservices
    
    Preferred Skills:
    - Experience with LangChain or similar LLM frameworks
    - Knowledge of vector databases (Pinecone, Weaviate, FAISS)
    - Experience with CI/CD pipelines
    - Familiarity with React or similar frontend frameworks
    
    Requirements:
    - Bachelor's degree in Computer Science or related field
    - Experience leading technical projects
    - Strong communication and collaboration skills
    - Experience with agile development methodologies
    """
    
    # Sample resumes
    resumes = [
        {
            "name": "John Smith",
            "content": """
            John Smith
            Senior Software Engineer
            
            Experience:
            - 7 years of Python development
            - Built ML pipelines using TensorFlow and PyTorch
            - Deployed applications on AWS using Docker and Kubernetes
            - Led a team of 4 engineers on an AI chatbot project
            - Developed RESTful APIs and microservices architecture
            
            Skills:
            Python, TensorFlow, PyTorch, AWS, Docker, Kubernetes, REST APIs, 
            PostgreSQL, Redis, Git, CI/CD (Jenkins), React
            
            Education:
            Master's in Computer Science, Stanford University
            """
        },
        {
            "name": "Sarah Johnson",
            "content": """
            Sarah Johnson
            Machine Learning Engineer
            
            Experience:
            - 4 years of Python and ML experience
            - Worked with PyTorch for deep learning models
            - Experience with Azure cloud services
            - Built LangChain applications for document Q&A
            - Integrated FAISS vector database for similarity search
            
            Skills:
            Python, PyTorch, Azure, LangChain, FAISS, Pinecone, Docker, 
            FastAPI, MongoDB, Streamlit
            
            Education:
            Bachelor's in Data Science, UC Berkeley
            """
        },
        {
            "name": "Michael Chen",
            "content": """
            Michael Chen
            Full Stack Developer
            
            Experience:
            - 3 years of software development
            - Strong Python and JavaScript experience
            - Built web applications using React and Node.js
            - Some experience with Docker
            - Worked with REST APIs and GraphQL
            
            Skills:
            Python, JavaScript, React, Node.js, TypeScript, Docker, 
            REST APIs, GraphQL, MongoDB, PostgreSQL, Git
            
            Education:
            Bachelor's in Software Engineering, MIT
            """
        }
    ]
    
    print("📄 Job Description:")
    print(job_description[:200] + "...")
    print_separator()
    
    print(f"📚 Number of Resumes to Analyze: {len(resumes)}")
    for resume in resumes:
        print(f"   • {resume['name']}")
    print_separator()
    
    # Run the job matching workflow
    print("🔄 Running job matching analysis...")
    print("   Step 1: Parsing job description...")
    print("   Step 2: Parsing resumes...")
    print("   Step 3: Analyzing matches and identifying gaps...")
    print("   Step 4: Finalizing results...")
    print_separator()
    
    result = graph_builder.run(job_description, resumes)
    
    # Display results
    if result.error:
        print(f"❌ Error: {result.error}")
        return
    
    print("✅ Analysis Complete!")
    print_separator()
    
    print("📊 RESULTS - All Candidates (Ranked by Match Score)")
    print_separator()
    
    for idx, match in enumerate(result.candidate_matches, 1):
        print(f"#{idx} Rank")
        print_candidate_analysis(match)
    
    # Highlight best candidate
    if result.best_candidate:
        print("🏆 BEST FIT CANDIDATE")
        print_separator()
        print_candidate_analysis(result.best_candidate)
        
    print("✅ Job matching analysis completed successfully!")


if __name__ == "__main__":
    main()
