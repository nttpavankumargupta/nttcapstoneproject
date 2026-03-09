"""
Simple example script for job matching agent

This script demonstrates how to use the job matching agent with your own data.
Modify the job_description and resumes variables to test with your own data.
"""

from src.config.config import Config
from src.graph_builder.job_match_graph import JobMatchGraphBuilder


def main():
    # Initialize the LLM and graph builder
    print("Initializing job matching agent...")
    llm = Config.get_llm()
    graph_builder = JobMatchGraphBuilder(llm)
    graph_builder.build()
    print("✅ Ready!\n")
    
    # ============================================================================
    # CUSTOMIZE THIS SECTION WITH YOUR DATA
    # ============================================================================
    
    # Your job description
    job_description = """
    Senior Backend Developer
    
    We are looking for a Senior Backend Developer to join our team.
    
    Required Skills:
    - 5+ years of experience with Python or Java
    - Experience with SQL databases
    - RESTful API development
    - Docker and containerization
    
    Preferred Skills:
    - Experience with microservices architecture
    - Knowledge of message queues (RabbitMQ, Kafka)
    - Cloud platform experience (AWS/Azure/GCP)
    
    Requirements:
    - Bachelor's degree in Computer Science or related field
    - Strong problem-solving skills
    - Team collaboration experience
    """
    
    # Your resumes
    resumes = [
        {
            "name": "Alice Brown",
            "content": """
            Alice Brown
            Backend Engineer
            
            Experience:
            - 6 years of Python development
            - Built RESTful APIs using Flask and FastAPI
            - Worked with PostgreSQL and MongoDB
            - Deployed applications using Docker and Kubernetes
            - Experience with microservices on AWS
            
            Skills: Python, Flask, FastAPI, PostgreSQL, MongoDB, Docker, 
            Kubernetes, AWS, RabbitMQ, Git, CI/CD
            
            Education: BS Computer Science, University of Washington
            """
        },
        {
            "name": "Bob Wilson",
            "content": """
            Bob Wilson
            Software Developer
            
            Experience:
            - 3 years of Java development
            - Built backend services with Spring Boot
            - Experience with MySQL databases
            - Some Docker experience
            
            Skills: Java, Spring Boot, MySQL, Docker, REST APIs, Git, Maven
            
            Education: BS Software Engineering, Georgia Tech
            """
        }
    ]
    
    # ============================================================================
    # RUN THE ANALYSIS
    # ============================================================================
    
    print("=" * 80)
    print("Job Matching Analysis")
    print("=" * 80)
    print(f"\nAnalyzing {len(resumes)} candidates for the position...")
    print("\nThis may take a moment as the AI analyzes each resume...\n")
    
    # Run the job matching workflow
    result = graph_builder.run(job_description, resumes)
    
    # ============================================================================
    # DISPLAY RESULTS
    # ============================================================================
    
    if result.error:
        print(f"❌ Error: {result.error}")
        return
    
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    
    # Show all candidates ranked by match score
    for idx, match in enumerate(result.candidate_matches, 1):
        print(f"\n{'='*80}")
        print(f"RANK #{idx}: {match.resume_name}")
        print(f"{'='*80}")
        print(f"Match Score: {match.match_score:.1f}/100\n")
        
        print("✅ MATCHED SKILLS:")
        if match.matched_skills:
            for skill in match.matched_skills:
                print(f"   • {skill}")
        else:
            print("   None identified")
        
        print("\n❌ MISSING SKILLS:")
        if match.missing_skills:
            for skill in match.missing_skills:
                print(f"   • {skill}")
        else:
            print("   None identified")
        
        print("\n💪 STRENGTHS:")
        if match.strengths:
            for strength in match.strengths:
                print(f"   • {strength}")
        else:
            print("   None identified")
        
        print("\n⚠️  GAPS:")
        if match.gaps:
            for gap in match.gaps:
                print(f"   • {gap}")
        else:
            print("   None identified")
        
        print(f"\n📝 SUMMARY:")
        print(f"   {match.summary}")
    
    # Highlight the best candidate
    if result.best_candidate:
        print("\n" + "=" * 80)
        print("🏆 RECOMMENDED CANDIDATE")
        print("=" * 80)
        print(f"\nBest Fit: {result.best_candidate.resume_name}")
        print(f"Match Score: {result.best_candidate.match_score:.1f}/100")
        print(f"\n{result.best_candidate.summary}")
    
    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
