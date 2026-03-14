"""Streamlit UI for Multi-Agent System"""

import streamlit as st
from pathlib import Path
import sys
import time
import truststore

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config.config import Config
from src.graph_builder.job_match_graph import JobMatchGraphBuilder
from src.graph_builder.interview_prep_graph import InterviewPrepGraphBuilder
from src.graph_builder.answer_eval_graph import AnswerEvalGraphBuilder
from src.graph_builder.gap_analysis_graph import GapAnalysisGraphBuilder
from src.utils.document_parser import extract_text_from_file
from src.vectorstore.course_vectorstore import CourseVectorStore
from src.state.answer_eval_state import QuestionAnswer

# Page configuration
st.set_page_config(
    page_title="🤖 AI Agent Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 10px;
    }
    .match-score {
        font-size: 24px;
        font-weight: bold;
        color: #2196F3;
    }
    .agent-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #e3f2fd;
        margin: 10px 0;
        border-left: 5px solid #2196F3;
    }
    </style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'job_match_graph_builder' not in st.session_state:
        st.session_state.job_match_graph_builder = None
    if 'job_match_result' not in st.session_state:
        st.session_state.job_match_result = None
    if 'resumes' not in st.session_state:
        st.session_state.resumes = []
    if 'interview_prep_graph_builder' not in st.session_state:
        st.session_state.interview_prep_graph_builder = None
    if 'interview_prep_result' not in st.session_state:
        st.session_state.interview_prep_result = None
    if 'answer_eval_graph_builder' not in st.session_state:
        st.session_state.answer_eval_graph_builder = None
    if 'answer_eval_result' not in st.session_state:
        st.session_state.answer_eval_result = None
    if 'gap_analysis_graph_builder' not in st.session_state:
        st.session_state.gap_analysis_graph_builder = None
    if 'gap_analysis_result' not in st.session_state:
        st.session_state.gap_analysis_result = None
    if 'course_vectorstore' not in st.session_state:
        st.session_state.course_vectorstore = None
    if 'courses_loaded' not in st.session_state:
        st.session_state.courses_loaded = False
    if 'question_answers' not in st.session_state:
        st.session_state.question_answers = []

@st.cache_resource
def initialize_job_match_builder():
    """Initialize the job matching graph builder (cached)"""
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        graph_builder = JobMatchGraphBuilder(llm)
        graph_builder.build()
        return graph_builder
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        return None

@st.cache_resource
def initialize_interview_prep_builder():
    """Initialize the interview prep graph builder (cached)"""
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        graph_builder = InterviewPrepGraphBuilder(llm)
        graph_builder.build()
        return graph_builder
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        return None

@st.cache_resource
def initialize_answer_eval_builder():
    """Initialize the answer evaluation graph builder (cached)"""
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        graph_builder = AnswerEvalGraphBuilder(llm)
        graph_builder.build()
        return graph_builder
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        return None

@st.cache_resource
def initialize_gap_analysis_builder():
    """Initialize the gap analysis graph builder (cached)"""
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        
        # Initialize course vector store
        course_store = CourseVectorStore()
        course_path = Path("data/Course Master List.xlsx")
        
        if course_path.exists():
            course_store.load_courses_from_excel(str(course_path))
        
        graph_builder = GapAnalysisGraphBuilder(llm, course_store)
        graph_builder.build()
        return graph_builder, course_store
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        return None, None

def display_candidate_match(match, rank, is_best=False):
    """Display a candidate match card"""
    with st.container():
        if is_best:
            st.markdown("### 🏆 BEST FIT CANDIDATE")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### #{rank} - {match.resume_name}")
        
        with col2:
            st.markdown(f'<div class="match-score">Score: {match.match_score:.1f}/100</div>', unsafe_allow_html=True)
        
        # Create tabs for different information
        tabs = st.tabs(["📊 Summary", "✅ Matched Skills", "❌ Missing Skills", "💪 Strengths", "⚠️ Gaps"])
        
        with tabs[0]:
            st.write(match.summary)
        
        with tabs[1]:
            if match.matched_skills:
                for skill in match.matched_skills:
                    st.markdown(f"• {skill}")
            else:
                st.info("No matched skills identified")
        
        with tabs[2]:
            if match.missing_skills:
                for skill in match.missing_skills:
                    st.markdown(f"• {skill}")
            else:
                st.success("No critical skills missing!")
        
        with tabs[3]:
            if match.strengths:
                for strength in match.strengths:
                    st.markdown(f"• {strength}")
            else:
                st.info("No specific strengths identified")
        
        with tabs[4]:
            if match.gaps:
                for gap in match.gaps:
                    st.markdown(f"• {gap}")
            else:
                st.success("No significant gaps identified!")
        
        st.markdown("---")

def job_matching_agent():
    """Job Matching Agent Interface"""
    st.title("🎯 Job Matching Agent")
    st.markdown("**Find the best candidates for your job opening with AI-powered analysis**")
    
    # Initialize system
    if st.session_state.job_match_graph_builder is None:
        with st.spinner("Initializing Job Matching AI system..."):
            graph_builder = initialize_job_match_builder()
            if graph_builder:
                st.session_state.job_match_graph_builder = graph_builder
                st.success("✅ System ready!")
    
    st.markdown("---")
    
    # Create two columns for input
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Job Description")
        
        # Option to upload or paste
        input_method = st.radio("Input method:", ["Paste Text", "Upload File"], key="jd_method", horizontal=True)
        
        if input_method == "Paste Text":
            job_description = st.text_area(
                "Paste the job description:",
                height=400,
                placeholder="Enter the complete job description including required skills, qualifications, and responsibilities..."
            )
        else:
            uploaded_jd = st.file_uploader(
                "Upload job description", 
                type=['txt', 'pdf', 'docx', 'doc'], 
                key="jd_upload",
                help="Supported formats: TXT, PDF, DOCX, DOC"
            )
            if uploaded_jd:
                try:
                    file_content = uploaded_jd.read()
                    job_description = extract_text_from_file(file_content, uploaded_jd.name)
                    st.text_area("Job Description Preview:", job_description[:500] + "..." if len(job_description) > 500 else job_description, height=300, disabled=True)
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    job_description = ""
            else:
                job_description = ""
    
    with col2:
        st.subheader("📚 Resumes")
        
        # Resume input method
        resume_method = st.radio("Input method:", ["Paste Text", "Upload Files"], key="resume_method", horizontal=True)
        
        if resume_method == "Paste Text":
            st.info("Add resumes one at a time")
            
            with st.form("add_resume_form"):
                candidate_name = st.text_input("Candidate Name:")
                resume_text = st.text_area("Resume Content:", height=250, placeholder="Paste resume content here...")
                add_button = st.form_submit_button("➕ Add Resume")
                
                if add_button and candidate_name and resume_text:
                    st.session_state.resumes.append({
                        "name": candidate_name,
                        "content": resume_text
                    })
                    st.success(f"Added resume for {candidate_name}")
                    st.rerun()
        else:
            uploaded_resumes = st.file_uploader(
                "Upload resume files",
                type=['txt', 'pdf', 'docx', 'doc'],
                accept_multiple_files=True,
                key="resume_upload",
                help="Supported formats: TXT, PDF, DOCX, DOC"
            )
            
            if uploaded_resumes:
                temp_resumes = []
                errors = []
                for resume_file in uploaded_resumes:
                    try:
                        file_content = resume_file.read()
                        content = extract_text_from_file(file_content, resume_file.name)
                        name = Path(resume_file.name).stem
                        temp_resumes.append({
                            "name": name,
                            "content": content
                        })
                    except Exception as e:
                        errors.append(f"{resume_file.name}: {str(e)}")
                
                st.session_state.resumes = temp_resumes
                
                if errors:
                    st.warning("⚠️ Some files could not be processed:")
                    for error in errors:
                        st.text(f"• {error}")
        
        # Display added resumes
        if st.session_state.resumes:
            st.success(f"**{len(st.session_state.resumes)} resume(s) ready for analysis**")
            
            with st.expander("View Resume List"):
                for idx, resume in enumerate(st.session_state.resumes, 1):
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.write(f"{idx}. {resume['name']}")
                    with col_b:
                        if st.button("🗑️", key=f"remove_{idx}"):
                            st.session_state.resumes.pop(idx-1)
                            st.rerun()
            
            if st.button("🗑️ Clear All Resumes", type="secondary"):
                st.session_state.resumes = []
                st.rerun()
    
    st.markdown("---")
    
    # Analyze button
    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    with col_center2:
        analyze_button = st.button("🚀 Analyze Candidates", type="primary", use_container_width=True)
    
    # Run analysis
    if analyze_button:
        if not job_description:
            st.error("❌ Please provide a job description")
        elif not st.session_state.resumes:
            st.error("❌ Please add at least one resume")
        elif st.session_state.job_match_graph_builder:
            with st.spinner("🔄 Analyzing candidates..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("Step 1/4: Parsing job description...")
                    progress_bar.progress(25)
                    time.sleep(0.5)
                    
                    status_text.text("Step 2/4: Processing resumes...")
                    progress_bar.progress(50)
                    time.sleep(0.5)
                    
                    status_text.text("Step 3/4: Analyzing matches and gaps...")
                    progress_bar.progress(75)
                    
                    result = st.session_state.job_match_graph_builder.run(
                        job_description,
                        st.session_state.resumes
                    )
                    
                    status_text.text("Step 4/4: Finalizing results...")
                    progress_bar.progress(100)
                    
                    st.session_state.job_match_result = result
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success("✅ Analysis complete!")
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    st.exception(e)
    
    # Display results
    if st.session_state.job_match_result:
        result = st.session_state.job_match_result
        
        if result.error:
            st.error(f"❌ Analysis Error: {result.error}")
        elif result.candidate_matches:
            st.markdown("---")
            st.header("📊 Analysis Results")
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Candidates", len(result.candidate_matches))
            with col2:
                if result.best_candidate:
                    st.metric("Best Match Score", f"{result.best_candidate.match_score:.1f}/100")
            with col3:
                avg_score = sum(m.match_score for m in result.candidate_matches) / len(result.candidate_matches)
                st.metric("Average Score", f"{avg_score:.1f}/100")
            
            st.markdown("---")
            
            # Display best candidate first
            if result.best_candidate:
                display_candidate_match(result.best_candidate, 1, is_best=True)
            
            # Display other candidates
            if len(result.candidate_matches) > 1:
                st.markdown("### 📋 All Candidates (Ranked)")
                
                for idx, match in enumerate(result.candidate_matches, 1):
                    display_candidate_match(match, idx, is_best=False)
            
            # Download results option
            st.markdown("---")
            if st.button("📥 Download Results as Text"):
                results_text = f"JOB MATCHING ANALYSIS RESULTS\n{'='*80}\n\n"
                results_text += f"Job Title: {result.job_description.title if result.job_description else 'N/A'}\n"
                results_text += f"Total Candidates Analyzed: {len(result.candidate_matches)}\n\n"
                
                for idx, match in enumerate(result.candidate_matches, 1):
                    results_text += f"\n{'='*80}\n"
                    results_text += f"RANK #{idx}: {match.resume_name}\n"
                    results_text += f"{'='*80}\n"
                    results_text += f"Match Score: {match.match_score:.1f}/100\n\n"
                    results_text += f"Matched Skills: {', '.join(match.matched_skills)}\n"
                    results_text += f"Missing Skills: {', '.join(match.missing_skills)}\n"
                    results_text += f"Strengths: {', '.join(match.strengths)}\n"
                    results_text += f"Gaps: {', '.join(match.gaps)}\n"
                    results_text += f"Summary: {match.summary}\n"
                
                st.download_button(
                    label="Download Results",
                    data=results_text,
                    file_name="job_matching_results.txt",
                    mime="text/plain"
                )

def interview_prep_agent():
    """Interview Preparation Agent Interface"""
    st.title("📝 Interview Question Generator")
    st.markdown("**Generate tailored interview questions based on job descriptions**")
    
    # Initialize system
    if st.session_state.interview_prep_graph_builder is None:
        with st.spinner("Initializing Interview Prep AI system..."):
            graph_builder = initialize_interview_prep_builder()
            if graph_builder:
                st.session_state.interview_prep_graph_builder = graph_builder
                st.success("✅ System ready!")
    
    st.markdown("---")
    
    # Job Description Input
    st.subheader("📋 Job Description")
    
    input_method = st.radio("Input method:", ["Paste Text", "Upload File"], key="interview_jd_method", horizontal=True)
    
    if input_method == "Paste Text":
        job_description = st.text_area(
            "Paste the job description:",
            height=300,
            placeholder="Enter the job description for which you want to generate interview questions..."
        )
    else:
        uploaded_jd = st.file_uploader(
            "Upload job description", 
            type=['txt', 'pdf', 'docx', 'doc'], 
            key="interview_jd_upload",
            help="Supported formats: TXT, PDF, DOCX, DOC"
        )
        if uploaded_jd:
            try:
                file_content = uploaded_jd.read()
                job_description = extract_text_from_file(file_content, uploaded_jd.name)
                st.text_area("Preview:", job_description[:300] + "...", height=200, disabled=True)
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                job_description = ""
        else:
            job_description = ""
    
    st.markdown("---")
    
    # Question Configuration
    st.subheader("⚙️ Question Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_questions = st.number_input(
            "Number of Questions",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
            help="Total number of questions to generate"
        )
    
    with col2:
        difficulty_level = st.selectbox(
            "Difficulty Level",
            options=["Mixed", "Easy", "Moderate", "Difficult"],
            index=0,
            help="Select question difficulty level"
        )
    
    # Show distribution controls for Mixed mode
    easy_count = 0
    moderate_count = 0
    difficult_count = 0
    
    if difficulty_level == "Mixed":
        st.info("📊 Customize the distribution of question difficulty levels")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            easy_count = st.number_input(
                "Easy Questions",
                min_value=0,
                max_value=num_questions,
                value=max(1, num_questions // 3),
                step=1
            )
        
        with col_b:
            moderate_count = st.number_input(
                "Moderate Questions",
                min_value=0,
                max_value=num_questions,
                value=max(1, num_questions // 3),
                step=1
            )
        
        with col_c:
            difficult_count = st.number_input(
                "Difficult Questions",
                min_value=0,
                max_value=num_questions,
                value=max(1, num_questions - (num_questions // 3) * 2),
                step=1
            )
        
        total_selected = easy_count + moderate_count + difficult_count
        if total_selected != num_questions:
            st.warning(f"⚠️ Selected distribution ({total_selected}) doesn't match total questions ({num_questions})")
    
    st.markdown("---")
    
    # Generate button
    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    with col_center2:
        generate_button = st.button("🚀 Generate Questions", type="primary", use_container_width=True)
    
    # Run generation
    if generate_button:
        if not job_description:
            st.error("❌ Please provide a job description")
        elif difficulty_level == "Mixed" and (easy_count + moderate_count + difficult_count) != num_questions:
            st.error("❌ Question distribution must equal total number of questions")
        elif st.session_state.interview_prep_graph_builder:
            with st.spinner("🔄 Generating interview questions..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("Step 1/3: Analyzing job description...")
                    progress_bar.progress(33)
                    time.sleep(0.5)
                    
                    status_text.text("Step 2/3: Generating questions...")
                    progress_bar.progress(66)
                    
                    result = st.session_state.interview_prep_graph_builder.run(
                        job_description,
                        num_questions,
                        difficulty_level,
                        easy_count,
                        moderate_count,
                        difficult_count
                    )
                    
                    status_text.text("Step 3/3: Finalizing questions...")
                    progress_bar.progress(100)
                    
                    st.session_state.interview_prep_result = result
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success("✅ Questions generated successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating questions: {str(e)}")
                    st.exception(e)
    
    # Display results
    if st.session_state.interview_prep_result:
        result = st.session_state.interview_prep_result
        
        if result.get('error'):
            st.error(f"❌ Error: {result['error']}")
        elif result.get('questions'):
            questions = result['questions']
            
            st.markdown("---")
            st.header("📊 Generated Interview Questions")
            
            # Summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Questions", len(questions))
            with col2:
                easy_q = sum(1 for q in questions if q.difficulty == "Easy")
                st.metric("Easy", easy_q)
            with col3:
                moderate_q = sum(1 for q in questions if q.difficulty == "Moderate")
                st.metric("Moderate", moderate_q)
            with col4:
                difficult_q = sum(1 for q in questions if q.difficulty == "Difficult")
                st.metric("Difficult", difficult_q)
            
            st.markdown("---")
            
            # Display questions
            for idx, question in enumerate(questions, 1):
                with st.expander(f"❓ Question {idx}: {question.question[:80]}...", expanded=(idx == 1)):
                    # Difficulty badge
                    if question.difficulty == "Easy":
                        st.markdown("🟢 **Difficulty:** Easy")
                    elif question.difficulty == "Moderate":
                        st.markdown("🟡 **Difficulty:** Moderate")
                    else:
                        st.markdown("🔴 **Difficulty:** Difficult")
                    
                    st.markdown(f"**📌 Topic:** {question.topic}")
                    st.markdown("---")
                    
                    # Question
                    st.markdown("### Question")
                    st.write(question.question)
                    
                    # Expected answer points
                    if question.expected_answer_points:
                        st.markdown("### ✅ Key Points in a Good Answer")
                        for point in question.expected_answer_points:
                            st.markdown(f"• {point}")
                    
                    # Follow-up questions
                    if question.follow_up_questions:
                        st.markdown("### 🔄 Follow-up Questions")
                        for follow_up in question.follow_up_questions:
                            st.markdown(f"• {follow_up}")
            
            # Download option
            st.markdown("---")
            if st.button("📥 Download Questions"):
                questions_text = "INTERVIEW QUESTIONS\n"
                questions_text += "="*80 + "\n\n"
                
                for idx, question in enumerate(questions, 1):
                    questions_text += f"\nQUESTION {idx}\n"
                    questions_text += "-"*80 + "\n"
                    questions_text += f"Difficulty: {question.difficulty}\n"
                    questions_text += f"Topic: {question.topic}\n\n"
                    questions_text += f"Q: {question.question}\n\n"
                    
                    if question.expected_answer_points:
                        questions_text += "Key Points in a Good Answer:\n"
                        for point in question.expected_answer_points:
                            questions_text += f"  • {point}\n"
                        questions_text += "\n"
                    
                    if question.follow_up_questions:
                        questions_text += "Follow-up Questions:\n"
                        for follow_up in question.follow_up_questions:
                            questions_text += f"  • {follow_up}\n"
                        questions_text += "\n"
                
                st.download_button(
                    label="Download Interview Questions",
                    data=questions_text,
                    file_name="interview_questions.txt",
                    mime="text/plain"
                )

def rag_agent():
    """RAG (Retrieval Augmented Generation) Agent Interface"""
    st.title("📚 RAG Agent")
    st.markdown("**Ask questions about your documents with AI-powered search and generation**")
    
    st.info("🚧 RAG Agent - Coming Soon!")
    
    st.markdown("""
    ### Features (Planned):
    - 📄 Upload and process multiple documents
    - 🔍 Semantic search across your document collection
    - 💬 Ask questions and get AI-generated answers
    - 📊 View source documents and relevant excerpts
    """)

def home_page():
    """Home page with agent selection"""
    st.title("🤖 AI Agent Hub")
    st.markdown("### Welcome to the Multi-Agent System")
    st.markdown("Select an agent from the tabs above to get started!")
    
    st.markdown("---")
    
    st.info("💡 Click on any tab above to explore the available AI agents")

def answer_evaluation_agent():
    """Answer Evaluation Agent Interface - Agent 3"""
    st.title("✅ Answer Evaluation Agent")
    st.markdown("**Evaluate candidate answers with practical-focused scoring**")
    
    # Initialize system
    if st.session_state.answer_eval_graph_builder is None:
        with st.spinner("Initializing Answer Evaluation AI system..."):
            graph_builder = initialize_answer_eval_builder()
            if graph_builder:
                st.session_state.answer_eval_graph_builder = graph_builder
                st.success("✅ System ready!")
    
    st.markdown("---")
    
    # Job Description Input
    st.subheader("📋 Job Description")
    job_description = st.text_area(
        "Paste the job description:",
        height=200,
        placeholder="Enter the job description that was used for interview questions..."
    )
    
    st.markdown("---")
    
    # Question and Answer Input
    st.subheader("❓ Questions and Answers")
    st.markdown("Add interview questions and candidate's answers for evaluation")
    
    # Display existing Q&A
    if st.session_state.question_answers:
        st.success(f"**{len(st.session_state.question_answers)} question(s) added**")
        
        with st.expander("View Questions & Answers"):
            for idx, qa in enumerate(st.session_state.question_answers, 1):
                st.markdown(f"**Q{idx}:** {qa['question']}")
                st.markdown(f"**A{idx}:** {qa['answer'][:100]}...")
                st.markdown("---")
        
        if st.button("🗑️ Clear All Q&A"):
            st.session_state.question_answers = []
            st.rerun()
    
    # Add new Q&A
    with st.form("add_qa_form"):
        question = st.text_area("Question:", height=100, placeholder="Enter the interview question...")
        answer = st.text_area("Candidate's Answer:", height=150, placeholder="Enter the candidate's answer...")
        add_qa_button = st.form_submit_button("➕ Add Question & Answer")
        
        if add_qa_button and question and answer:
            st.session_state.question_answers.append({
                "question": question,
                "answer": answer
            })
            st.success("Q&A added successfully!")
            st.rerun()
    
    st.markdown("---")
    
    # Evaluate button
    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    with col_center2:
        evaluate_button = st.button("🚀 Evaluate Answers", type="primary", use_container_width=True)
    
    # Run evaluation
    if evaluate_button:
        if not job_description:
            st.error("❌ Please provide a job description")
        elif not st.session_state.question_answers:
            st.error("❌ Please add at least one question and answer")
        elif st.session_state.answer_eval_graph_builder:
            with st.spinner("🔄 Evaluating answers..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("Step 1/3: Analyzing answers...")
                    progress_bar.progress(33)
                    
                    # Convert to QuestionAnswer objects
                    qa_objects = [
                        QuestionAnswer(
                            question=qa["question"],
                            question_topic="General",  # Default topic
                            question_difficulty="Medium",  # Default difficulty
                            candidate_answer=qa["answer"],
                            expected_answer_points=[]  # No expected points for manual entry
                        )
                        for qa in st.session_state.question_answers
                    ]
                    
                    status_text.text("Step 2/3: Scoring practical skills...")
                    progress_bar.progress(66)
                    
                    result = st.session_state.answer_eval_graph_builder.run(
                        job_description,
                        qa_objects
                    )
                    
                    status_text.text("Step 3/3: Generating summary...")
                    progress_bar.progress(100)
                    
                    st.session_state.answer_eval_result = result
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success("✅ Evaluation complete!")
                    
                except Exception as e:
                    st.error(f"❌ Error during evaluation: {str(e)}")
                    st.exception(e)
    
    # Display results
    if st.session_state.answer_eval_result:
        result = st.session_state.answer_eval_result
        
        # Debug logging
        st.write("**[DEBUG] Result keys:**", list(result.keys()) if isinstance(result, dict) else "Not a dict")
        
        st.markdown("---")
        st.header("📊 Evaluation Results")
        
        # Check for error first
        if result.get('error'):
            st.error(f"❌ Error: {result.get('error')}")
            return
        
        # Overall metrics
        evaluations = result.get('evaluations', [])
        st.write(f"**[DEBUG] Number of evaluations:** {len(evaluations)}")
        
        if evaluations:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_score = sum(e.score for e in evaluations)
                max_score = len(evaluations) * 100
                overall_pct = (total_score / max_score * 100) if max_score > 0 else 0
                st.metric("Overall Score", f"{overall_pct:.1f}%")
            
            with col2:
                avg_score = total_score / len(evaluations) if evaluations else 0
                st.metric("Average Score", f"{avg_score:.1f}/100")
            
            with col3:
                st.metric("Questions Evaluated", len(evaluations))
            
            st.markdown("---")
            
            # Display evaluation summary
            summary = result.get('summary', '')
            if summary:
                st.subheader("📝 Overall Summary")
                st.write(summary)
                st.markdown("---")
            
            # Individual answer evaluations
            st.subheader("📋 Individual Answer Evaluations")
            
            for idx, evaluation in enumerate(evaluations, 1):
                with st.expander(f"Question {idx} - Score: {evaluation.score:.1f}/100", expanded=(idx == 1)):
                    st.markdown("#### Question")
                    st.write(evaluation.question)
                    
                    st.markdown("#### Candidate's Answer")
                    st.write(evaluation.candidate_answer)
                    
                    st.markdown("---")
                    
                    # Scores
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Overall Score", f"{evaluation.score:.1f}/100")
                    with col_b:
                        st.metric("Practicality", f"{evaluation.practicality_score:.1f}/100")
                    
                    # Strengths
                    if evaluation.strengths:
                        st.markdown("#### 💪 Strengths")
                        for strength in evaluation.strengths:
                            st.markdown(f"• {strength}")
                    
                    # Weaknesses
                    if evaluation.weaknesses:
                        st.markdown("#### ⚠️ Weaknesses")
                        for weakness in evaluation.weaknesses:
                            st.markdown(f"• {weakness}")
                    
                    # Missing practical aspects
                    if evaluation.missing_practical_aspects:
                        st.markdown("#### 🎯 Missing Practical Aspects")
                        for aspect in evaluation.missing_practical_aspects:
                            st.markdown(f"• {aspect}")
                    
                    # Feedback
                    if evaluation.feedback:
                        st.markdown("#### 💬 Feedback")
                        st.write(evaluation.feedback)
            
            # Missing skills
            missing_skills = result.get('missing_practical_skills', [])
            if missing_skills:
                st.markdown("---")
                st.subheader("🎯 Missing Practical Skills (Overall)")
                for skill in missing_skills:
                    st.markdown(f"• {skill}")
            
            # Download results
            st.markdown("---")
            if st.button("📥 Download Evaluation Report"):
                report_text = "ANSWER EVALUATION REPORT\n"
                report_text += "="*80 + "\n\n"
                report_text += f"Total Questions: {len(evaluations)}\n"
                report_text += f"Overall Score: {overall_pct:.1f}%\n\n"
                
                if summary:
                    report_text += f"Summary:\n{summary}\n\n"
                
                for idx, evaluation in enumerate(evaluations, 1):
                    report_text += f"\n{'='*80}\n"
                    report_text += f"QUESTION {idx}\n"
                    report_text += f"{'='*80}\n"
                    report_text += f"Q: {evaluation.question}\n\n"
                    report_text += f"A: {evaluation.candidate_answer}\n\n"
                    report_text += f"Score: {evaluation.score:.1f}/100\n"
                    report_text += f"Practicality Score: {evaluation.practicality_score:.1f}/100\n\n"
                    if evaluation.strengths:
                        report_text += f"Strengths: {', '.join(evaluation.strengths)}\n"
                    if evaluation.weaknesses:
                        report_text += f"Weaknesses: {', '.join(evaluation.weaknesses)}\n"
                    report_text += f"\nFeedback: {evaluation.feedback}\n"
                
                if missing_skills:
                    report_text += f"\n{'='*80}\n"
                    report_text += "MISSING PRACTICAL SKILLS:\n"
                    for skill in missing_skills:
                        report_text += f"• {skill}\n"
                
                st.download_button(
                    label="Download Report",
                    data=report_text,
                    file_name="answer_evaluation_report.txt",
                    mime="text/plain"
                )
        else:
            st.info("No evaluations available. Please check the debug information above.")

def gap_analysis_agent():
    """Gap Analysis and Course Recommendation Agent - Agent 4"""
    st.title("🎓 Gap Analysis & Course Recommendation")
    st.markdown("**Identify skill gaps and get personalized course recommendations**")
    
    # Initialize system
    if st.session_state.gap_analysis_graph_builder is None or st.session_state.course_vectorstore is None:
        with st.spinner("Initializing Gap Analysis AI system and loading courses..."):
            builder, course_store = initialize_gap_analysis_builder()
            if builder and course_store:
                st.session_state.gap_analysis_graph_builder = builder
                st.session_state.course_vectorstore = course_store
                st.session_state.courses_loaded = True
                st.success("✅ System ready! Courses loaded successfully.")
            else:
                st.error("❌ Failed to initialize system. Please check if Course Master List.xlsx exists in data folder.")
    
    st.markdown("---")
    
    # Check if we have evaluation results to use
    has_eval_results = st.session_state.answer_eval_result is not None
    
    if has_eval_results:
        st.success("✅ Answer evaluation results detected! You can use them directly.")
        use_existing = st.radio(
            "Data source:",
            ["Use existing evaluation results", "Enter manually"],
            horizontal=True
        )
    else:
        st.info("💡 Run Answer Evaluation first, or enter data manually")
        use_existing = "Enter manually"
    
    job_description = ""
    missing_skills = []
    
    if use_existing == "Use existing evaluation results" and has_eval_results:
        result = st.session_state.answer_eval_result
        job_description = result.get('job_description_text', '')
        missing_skills = result.get('missing_practical_skills', [])
        
        st.subheader("📋 Detected Job Description")
        st.text_area("Job Description (from evaluation):", job_description[:300] + "...", height=100, disabled=True)
        
        st.subheader("🎯 Detected Missing Skills")
        if missing_skills:
            for skill in missing_skills:
                st.markdown(f"• {skill}")
        else:
            st.info("No missing skills detected")
    
    else:
        st.subheader("📋 Job Description")
        job_description = st.text_area(
            "Paste the job description:",
            height=200,
            placeholder="Enter the job description..."
        )
        
        st.subheader("🎯 Missing Skills")
        st.markdown("Enter the skills that need improvement (one per line)")
        
        skills_input = st.text_area(
            "Missing Skills:",
            height=150,
            placeholder="Python\nMachine Learning\nDocker\n..."
        )
        
        if skills_input:
            missing_skills = [skill.strip() for skill in skills_input.split('\n') if skill.strip()]
    
    st.markdown("---")
    
    # Analyze button
    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    with col_center2:
        analyze_button = st.button("🚀 Analyze Gaps & Recommend Courses", type="primary", use_container_width=True)
    
    # Run analysis
    if analyze_button:
        if not job_description:
            st.error("❌ Please provide a job description")
        elif not missing_skills:
            st.error("❌ Please provide at least one missing skill")
        elif st.session_state.gap_analysis_graph_builder:
            with st.spinner("🔄 Analyzing skill gaps and finding courses..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("Step 1/4: Identifying skill gaps...")
                    progress_bar.progress(25)
                    
                    # Prepare answer evaluations if available
                    answer_evals = []
                    if use_existing == "Use existing evaluation results" and st.session_state.answer_eval_result:
                        answer_evals = st.session_state.answer_eval_result.get('evaluations', [])
                    
                    status_text.text("Step 2/4: Searching relevant courses...")
                    progress_bar.progress(50)
                    
                    result = st.session_state.gap_analysis_graph_builder.run(
                        job_description,
                        answer_evals,
                        missing_skills
                    )
                    
                    status_text.text("Step 3/4: Ranking recommendations...")
                    progress_bar.progress(75)
                    
                    status_text.text("Step 4/4: Creating learning path...")
                    progress_bar.progress(100)
                    
                    st.session_state.gap_analysis_result = result
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success("✅ Analysis complete!")
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    st.exception(e)
    
    # Display results
    if st.session_state.gap_analysis_result:
        result = st.session_state.gap_analysis_result
        
        st.markdown("---")
        st.header("📊 Gap Analysis Results")
        
        # Display course recommendations
        if result.get('course_recommendations'):
            st.subheader("📚 Recommended Courses")
            
            # Create DataFrame for tabular display
            import pandas as pd
            
            course_data = []
            priority_map = {
                5: "⭐⭐⭐⭐⭐ Must Do",
                4: "⭐⭐⭐⭐ Highly Recommended",
                3: "⭐⭐⭐ Recommended",
                2: "⭐⭐ Optional",
                1: "⭐ Nice to Have"
            }
            
            for course in result['course_recommendations']:
                course_data.append({
                    'Course ID': course.course_id,
                    'Course Name': course.course_name,
                    'Priority': priority_map.get(course.priority, "⭐⭐⭐ Recommended"),
                    'Rating': f"{course.priority}/5",
                    'Target Time': course.target_time,
                    'Relevance': f"{course.relevance_score:.0f}%",
                    'Skills Covered': ', '.join(course.addresses_gaps)
                })
            
            df = pd.DataFrame(course_data)
            
            # Display table with custom styling
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Course ID": st.column_config.TextColumn("Course ID", width="small"),
                    "Course Name": st.column_config.TextColumn("Course Name", width="large"),
                    "Priority": st.column_config.TextColumn("Priority", width="medium"),
                    "Rating": st.column_config.TextColumn("Value", width="small"),
                    "Target Time": st.column_config.TextColumn("Target Time", width="small"),
                    "Relevance": st.column_config.TextColumn("Match", width="small"),
                    "Skills Covered": st.column_config.TextColumn("Skills to Cover", width="large")
                }
            )
            
            st.markdown("---")
            
            # Show detailed view as expandable sections
            st.subheader("📖 Course Details")
            for idx, course in enumerate(result['course_recommendations'], 1):
                priority_text = priority_map.get(course.priority, "Recommended")
                with st.expander(f"{idx}. {course.course_name} - {priority_text}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Priority Rating", f"{course.priority}/5")
                    with col2:
                        st.metric("Relevance Score", f"{course.relevance_score:.0f}%")
                    with col3:
                        st.metric("Estimated Time", course.target_time)
                    
                    st.markdown("**Course ID:**")
                    st.code(course.course_id)
                    
                    st.markdown("**Addresses Skills:**")
                    for skill in course.addresses_gaps:
                        st.markdown(f"• {skill}")
                    
                    st.markdown("**Why Recommended:**")
                    st.info(course.reason)
                    
                    st.markdown("**Course Summary:**")
                    st.write(course.summary)

            st.markdown("---")
        
        # Display learning path
        if result.get('learning_path'):
            st.subheader("🗺️ Suggested Learning Path")
            st.write(result['learning_path'])
            st.markdown("---")
        
        # Download results
        if st.button("📥 Download Learning Plan"):
            plan_text = "SKILL GAP ANALYSIS & LEARNING PLAN\n"
            plan_text += "="*80 + "\n\n"
            
            if result.get('identified_gaps'):
                plan_text += "SKILL GAPS:\n"
                plan_text += "-"*80 + "\n"
                for gap in result['identified_gaps']:
                    plan_text += f"\n{gap.skill_name} (Importance: {gap.importance})\n"
                    plan_text += f"Description: {gap.gap_description}\n"
                    plan_text += f"Current Level: {gap.current_level}\n"
                    plan_text += f"Required Level: {gap.required_level}\n"
                plan_text += "\n"
            
            if result.get('course_recommendations'):
                plan_text += "RECOMMENDED COURSES:\n"
                plan_text += "-"*80 + "\n"
                for idx, course in enumerate(result['course_recommendations'], 1):
                    plan_text += f"\n{idx}. {course.course_name} (ID: {course.course_id})\n"
                    plan_text += f"Relevance: {course.relevance_score:.1f}%\n"
                    if course.addresses_gaps:
                        plan_text += f"Addresses: {', '.join(course.addresses_gaps)}\n"
                    if course.summary:
                        plan_text += f"Summary: {course.summary}\n"
                    plan_text += "\n"
            
            if result.get('learning_path'):
                plan_text += "LEARNING PATH:\n"
                plan_text += "-"*80 + "\n"
                plan_text += result['learning_path'] + "\n"
            
            st.download_button(
                label="Download Learning Plan",
                data=plan_text,
                file_name="learning_plan.txt",
                mime="text/plain"
            )

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()
    
    # Create tabs for different agents
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Home", 
        "🎯 Job Matching", 
        "📝 Interview Prep", 
        "✅ Answer Evaluation",
        "🎓 Gap Analysis",
        "📚 RAG Agent"
    ])
    
    with tab1:
        home_page()
    
    with tab2:
        job_matching_agent()
    
    with tab3:
        interview_prep_agent()
    
    with tab4:
        answer_evaluation_agent()
    
    with tab5:
        gap_analysis_agent()
    
    with tab6:
        rag_agent()

if __name__ == "__main__":
    main()
