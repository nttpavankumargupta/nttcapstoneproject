"""Streamlit UI for Multi-Agent System"""

import streamlit as st
from pathlib import Path
import sys
import time
import truststore

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config.config import Config
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)
from src.graph_builder.job_match_graph import JobMatchGraphBuilder
from src.graph_builder.interview_prep_graph import InterviewPrepGraphBuilder
from src.graph_builder.answer_eval_graph import AnswerEvalGraphBuilder
from src.graph_builder.gap_analysis_graph import GapAnalysisGraphBuilder
from src.utils.document_parser import extract_text_from_file
from src.vectorstore.course_vectorstore import CourseVectorStore
from src.state.answer_eval_state import QuestionAnswer

# Page configuration
st.set_page_config(
    page_title="Multi-Agent AI System",
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
    .header-container {
        display: flex;
        align-items: center;
        padding: 20px 0;
        border-bottom: 3px solid #0066CC;
        margin-bottom: 30px;
    }
    .header-logo {
        width: 80px;
        height: 80px;
        margin-right: 20px;
    }
    .header-title {
        font-size: 32px;
        font-weight: bold;
        color: #0066CC;
        margin: 0;
    }
    .header-subtitle {
        font-size: 18px;
        color: #666;
        margin: 5px 0 0 0;
    }
    </style>
""", unsafe_allow_html=True)

def display_header():
    """Display application header"""
    st.markdown("## Multi-Agent AI System")
    st.markdown("---")

def init_session_state():
    """Initialize session state variables"""
    if 'active_page' not in st.session_state:
        st.session_state.active_page = 'home'
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
    logger.info("Initializing Job Matching graph builder")
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        graph_builder = JobMatchGraphBuilder(llm)
        graph_builder.build()
        logger.info("Job Matching graph builder initialized successfully")
        return graph_builder
    except Exception as e:
        logger.error(f"Failed to initialize Job Matching builder: {str(e)}", exc_info=True)
        st.error(f"Failed to initialize: {str(e)}")
        return None

@st.cache_resource
def initialize_interview_prep_builder():
    """Initialize the interview prep graph builder (cached)"""
    logger.info("Initializing Interview Prep graph builder")
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        graph_builder = InterviewPrepGraphBuilder(llm)
        graph_builder.build()
        logger.info("Interview Prep graph builder initialized successfully")
        return graph_builder
    except Exception as e:
        logger.error(f"Failed to initialize Interview Prep builder: {str(e)}", exc_info=True)
        st.error(f"Failed to initialize: {str(e)}")
        return None

@st.cache_resource
def initialize_answer_eval_builder():
    """Initialize the answer evaluation graph builder (cached)"""
    logger.info("Initializing Answer Evaluation graph builder")
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        graph_builder = AnswerEvalGraphBuilder(llm)
        graph_builder.build()
        logger.info("Answer Evaluation graph builder initialized successfully")
        return graph_builder
    except Exception as e:
        logger.error(f"Failed to initialize Answer Evaluation builder: {str(e)}", exc_info=True)
        st.error(f"Failed to initialize: {str(e)}")
        return None

@st.cache_resource
def initialize_gap_analysis_builder():
    """Initialize the gap analysis graph builder (cached)"""
    logger.info("Initializing Gap Analysis graph builder and course vector store")
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        
        # Initialize course vector store
        course_store = CourseVectorStore()
        course_path = Path("data/Course Master List.xlsx")
        
        if course_path.exists():
            logger.info(f"Loading courses from {course_path}")
            course_store.load_courses_from_excel(str(course_path))
            logger.info("Courses loaded successfully")
        else:
            logger.warning(f"Course file not found at {course_path}")
        
        graph_builder = GapAnalysisGraphBuilder(llm, course_store)
        graph_builder.build()
        logger.info("Gap Analysis graph builder initialized successfully")
        return graph_builder, course_store
    except Exception as e:
        logger.error(f"Failed to initialize Gap Analysis builder: {str(e)}", exc_info=True)
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
        st.info("Upload candidate resume files (multiple files supported)")
        
        uploaded_resumes = st.file_uploader(
            "Select resume files",
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
                        "content": content,
                        "filename": resume_file.name
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
            logger.warning("Job matching analysis attempted without job description")
        elif not st.session_state.resumes:
            st.error("❌ Please add at least one resume")
            logger.warning("Job matching analysis attempted without resumes")
        elif st.session_state.job_match_graph_builder:
            logger.info(f"Starting job matching analysis with {len(st.session_state.resumes)} resumes")
            with st.spinner("🔄 Analyzing candidates..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("Step 1/4: Parsing job description...")
                    progress_bar.progress(25)
                    logger.debug("Parsing job description")
                    time.sleep(0.5)
                    
                    status_text.text("Step 2/4: Processing resumes...")
                    progress_bar.progress(50)
                    logger.debug("Processing resumes")
                    time.sleep(0.5)
                    
                    status_text.text("Step 3/4: Analyzing matches and gaps...")
                    progress_bar.progress(75)
                    logger.debug("Analyzing matches and gaps")
                    
                    result = st.session_state.job_match_graph_builder.run(
                        job_description,
                        st.session_state.resumes
                    )
                    
                    status_text.text("Step 4/4: Finalizing results...")
                    progress_bar.progress(100)
                    logger.debug("Finalizing results")
                    
                    st.session_state.job_match_result = result
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    logger.info("Job matching analysis completed successfully")
                    st.success("✅ Analysis complete!")
                    
                except Exception as e:
                    logger.error(f"Error during job matching analysis: {str(e)}", exc_info=True)
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
            
            # Display results in tabular format
            st.subheader("📋 Candidate Rankings")
            
            # Create table data
            import pandas as pd
            
            table_data = []
            for idx, match in enumerate(result.candidate_matches, 1):
                # Find the filename from uploaded resumes
                filename = "N/A"
                for resume in st.session_state.resumes:
                    if resume['name'] == match.resume_name:
                        filename = resume.get('filename', match.resume_name)
                        break
                
                table_data.append({
                    'Rank': idx,
                    "Candidate's Name": match.resume_name,
                    "Resume File": filename,
                    'Match Score': f"{match.match_score:.1f}/100",
                    'Score Value': match.match_score,  # For styling
                    'Key Strengths': ', '.join(match.strengths[:3]) if match.strengths else 'N/A',
                    'Missing Skills/Gaps': ', '.join(match.missing_skills[:3]) if match.missing_skills else 'None'
                })
            
            df = pd.DataFrame(table_data)
            
            # Apply color styling based on score
            def highlight_score(row):
                score = row['Score Value']
                if score > 75:
                    return ['background-color: #d4edda'] * len(row)  # Green
                elif score >= 50:
                    return ['background-color: #fff3cd'] * len(row)  # Amber/Yellow
                else:
                    return [''] * len(row)  # Default
            
            # Apply styling first, then hide Score Value column
            styled_df = df.style.apply(highlight_score, axis=1).hide(axis='columns', subset=['Score Value'])
            
            # Display the table with styling
            st.dataframe(
                styled_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small", help="Candidate ranking"),
                    "Candidate's Name": st.column_config.TextColumn("Candidate Name", width="medium"),
                    "Resume File": st.column_config.TextColumn("Resume File", width="medium"),
                    "Match Score": st.column_config.TextColumn("Score", width="small"),
                    "Key Strengths": st.column_config.TextColumn("Key Strengths", width="large"),
                    "Missing Skills/Gaps": st.column_config.TextColumn("Missing Skills/Gaps", width="large")
                }
            )
            
            # Add legend
            col_legend1, col_legend2, col_legend3 = st.columns(3)
            with col_legend1:
                st.markdown("🟢 **Excellent Match** (>75%)")
            with col_legend2:
                st.markdown("🟡 **Good Match** (50-75%)")
            with col_legend3:
                st.markdown("⚪ **Needs Review** (<50%)")
            
            st.markdown("---")
            
            # Detailed view with expandable sections
            st.subheader("🔍 Detailed Candidate Analysis")
            
            for idx, match in enumerate(result.candidate_matches, 1):
                is_best = (idx == 1)
                if is_best:
                    display_candidate_match(match, idx, is_best=True)
                else:
                    with st.expander(f"#{idx} - {match.resume_name} (Score: {match.match_score:.1f}/100)"):
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
    
    # Check if we have job description from Agent 1
    has_job_description = False
    detected_job_description = ""
    
    # Try to get job description from job matching (Agent 1)
    if st.session_state.job_match_result:
        job_desc_obj = st.session_state.job_match_result.job_description
        if job_desc_obj and hasattr(job_desc_obj, 'original_text'):
            detected_job_description = job_desc_obj.original_text
            if detected_job_description:
                has_job_description = True
    
    # Display detection status
    if has_job_description:
        st.success("✅ Job description detected from Agent 1 (Job Matching)! You can use it directly.")
    
    # Job Description Input with auto-detection
    st.subheader("📋 Job Description")
    
    if has_job_description:
        input_method = st.radio(
            "Input method:", 
            ["Use detected job description", "Paste Text", "Upload File"], 
            key="interview_jd_method", 
            horizontal=True
        )
    else:
        st.info("💡 Run Job Matching (Agent 1) first, or enter job description manually")
        input_method = st.radio(
            "Input method:", 
            ["Paste Text", "Upload File"], 
            key="interview_jd_method", 
            horizontal=True
        )
    
    if input_method == "Use detected job description" and has_job_description:
        st.text_area("Detected Job Description:", detected_job_description[:300] + "..." if len(detected_job_description) > 300 else detected_job_description, height=150, disabled=True, key="detected_jd_display_int")
        job_description = detected_job_description
    elif input_method == "Paste Text":
        job_description = st.text_area(
            "Paste the job description:",
            height=300,
            placeholder="Enter the job description for which you want to generate interview questions...",
            key="manual_jd_input_int"
        )
    elif input_method == "Upload File":
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
            logger.warning("Interview prep attempted without job description")
        elif difficulty_level == "Mixed" and (easy_count + moderate_count + difficult_count) != num_questions:
            st.error("❌ Question distribution must equal total number of questions")
            logger.warning(f"Invalid question distribution: {easy_count}+{moderate_count}+{difficult_count} != {num_questions}")
        elif st.session_state.interview_prep_graph_builder:
            logger.info(f"Generating {num_questions} interview questions with difficulty: {difficulty_level}")
            with st.spinner("🔄 Generating interview questions..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("Step 1/3: Analyzing job description...")
                    progress_bar.progress(33)
                    logger.debug("Analyzing job description for questions")
                    time.sleep(0.5)
                    
                    status_text.text("Step 2/3: Generating questions...")
                    progress_bar.progress(66)
                    logger.debug("Generating interview questions")
                    
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
                    logger.debug("Finalizing questions")
                    
                    st.session_state.interview_prep_result = result
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    logger.info(f"Successfully generated {len(result.get('questions', []))} interview questions")
                    st.success("✅ Questions generated successfully!")
                    
                except Exception as e:
                    logger.error(f"Error generating interview questions: {str(e)}", exc_info=True)
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
            
            # Group questions by difficulty
            easy_questions = [q for q in questions if q.difficulty == "Easy"]
            moderate_questions = [q for q in questions if q.difficulty == "Moderate"]
            difficult_questions = [q for q in questions if q.difficulty == "Difficult"]
            
            # Display questions grouped by difficulty
            if easy_questions:
                st.markdown("### 🟢 Easy Questions")
                for idx, question in enumerate(easy_questions, 1):
                    st.markdown(f"**{idx}.** {question.question}")
                    st.markdown("")
                st.markdown("---")
            
            if moderate_questions:
                st.markdown("### 🟡 Moderate Questions")
                for idx, question in enumerate(moderate_questions, 1):
                    st.markdown(f"**{idx}.** {question.question}")
                    st.markdown("")
                st.markdown("---")
            
            if difficult_questions:
                st.markdown("### 🔴 Difficult Questions")
                for idx, question in enumerate(difficult_questions, 1):
                    st.markdown(f"**{idx}.** {question.question}")
                    st.markdown("")
            
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

def render_mermaid(mermaid_code):
    """Render Mermaid diagram using HTML and JavaScript"""
    html_code = f"""
    <div class="mermaid">
    {mermaid_code}
    </div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """
    st.components.v1.html(html_code, height=600, scrolling=True)

def implementation_docs():
    """Implementation Documentation Page"""
    st.title("📖 Implementation Documentation")
    st.markdown("**System Architecture & Implementation Details**")
    
    # Read the architecture documentation
    arch_doc_path = Path("ARCHITECTURE.md")
    
    if arch_doc_path.exists():
        with open(arch_doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process the markdown content to extract and render Mermaid diagrams
        import re
        
        # Split content by mermaid code blocks
        parts = re.split(r'```mermaid\n(.*?)```', content, flags=re.DOTALL)
        
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Regular markdown content
                if part.strip():
                    st.markdown(part, unsafe_allow_html=True)
            else:
                # Mermaid diagram
                st.markdown("---")
                render_mermaid(part)
                st.markdown("---")
    else:
        st.error("❌ Architecture documentation not found. Please ensure ARCHITECTURE.md exists in the project root.")
        
        # Provide fallback basic info
        st.markdown("""
        ## System Overview
        
        The NTT DATA Capstone Project is a Multi-Agent AI System with four specialized agents:
        
        1. **🎯 Job Matching Agent**: Matches candidates to job descriptions
        2. **� Interview Prep Agent**: Generates tailored interview questions  
        3. **✅ Answer Evaluation Agent**: Evaluates candidate responses
        4. **🎓 Gap Analysis Agent**: Recommends courses for skill gaps
        
        ### Technology Stack
        - **Frontend**: Streamlit
        - **AI/ML**: Azure OpenAI (GPT-4), LangGraph, LangChain
        - **Vector Database**: ChromaDB
        - **Data Processing**: pandas, openpyxl, PyPDF2, python-docx
        """)

def home_page():
    """Home page with agent selection"""
    
    st.title("🤖 AI Agent Hub")
    st.markdown("### Welcome to the Multi-Agent System")
    
    st.markdown("---")
    
    # Initialize agents in background if not ready
    if st.session_state.job_match_graph_builder is None:
        with st.spinner("Initializing Job Matching Agent..."):
            st.session_state.job_match_graph_builder = initialize_job_match_builder()
    
    if st.session_state.interview_prep_graph_builder is None:
        with st.spinner("Initializing Interview Prep Agent..."):
            st.session_state.interview_prep_graph_builder = initialize_interview_prep_builder()
    
    if st.session_state.answer_eval_graph_builder is None:
        with st.spinner("Initializing Answer Evaluation Agent..."):
            st.session_state.answer_eval_graph_builder = initialize_answer_eval_builder()
    
    if st.session_state.gap_analysis_graph_builder is None or st.session_state.course_vectorstore is None:
        with st.spinner("Initializing Gap Analysis Agent and loading courses..."):
            builder, course_store = initialize_gap_analysis_builder()
            if builder and course_store:
                st.session_state.gap_analysis_graph_builder = builder
                st.session_state.course_vectorstore = course_store
                st.session_state.courses_loaded = True
    
    # Check agent status after initialization attempts
    job_match_ready = st.session_state.job_match_graph_builder is not None
    interview_prep_ready = st.session_state.interview_prep_graph_builder is not None
    answer_eval_ready = st.session_state.answer_eval_graph_builder is not None
    gap_analysis_ready = (st.session_state.gap_analysis_graph_builder is not None and 
                          st.session_state.course_vectorstore is not None)
    
    # Overall system status
    all_ready = job_match_ready and interview_prep_ready and answer_eval_ready and gap_analysis_ready
    
    # Display overall status
    col_status1, col_status2 = st.columns([3, 1])
    with col_status1:
        st.subheader("📊 System Status")
    with col_status2:
        if all_ready:
            st.success("✅ All Systems Ready")
        else:
            st.warning("� Initializing...")
    
    st.markdown("---")
    
    # Agent Cards with Status
    st.markdown("### 🚀 Available Agents")
    
    # Row 1: Job Matching and Interview Prep
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        st.markdown("#### 🎯 Job Matching Agent")
        if job_match_ready:
            st.success("✅ Ready")
        else:
            st.warning("⚠️ Not Initialized")
        st.markdown("Find the best candidates for job openings with AI-powered analysis")
        st.markdown("**Features:**")
        st.markdown("- Resume parsing and analysis")
        st.markdown("- Skill gap identification")
        st.markdown("- Candidate ranking")
        if st.button("Launch Job Matching →", key="nav_job_match", use_container_width=True, disabled=not job_match_ready):
            st.info("👆 Click the '🎯 Job Matching' tab above to start")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        st.markdown("#### 📝 Interview Prep Agent")
        if interview_prep_ready:
            st.success("✅ Ready")
        else:
            st.warning("⚠️ Not Initialized")
        st.markdown("Generate tailored interview questions from job descriptions")
        st.markdown("**Features:**")
        st.markdown("- AI-generated questions")
        st.markdown("- Multiple difficulty levels")
        st.markdown("- Expected answer points")
        if st.button("Launch Interview Prep →", key="nav_interview", use_container_width=True, disabled=not interview_prep_ready):
            st.info("👆 Click the '📝 Interview Prep' tab above to start")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 2: Answer Evaluation and Gap Analysis
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        st.markdown("#### ✅ Answer Evaluation Agent")
        if answer_eval_ready:
            st.success("✅ Ready")
        else:
            st.warning("⚠️ Not Initialized")
        st.markdown("Evaluate candidate answers with practical-focused scoring")
        st.markdown("**Features:**")
        st.markdown("- Practicality scoring")
        st.markdown("- Strength & weakness analysis")
        st.markdown("- Missing skills identification")
        if st.button("Launch Answer Eval →", key="nav_answer_eval", use_container_width=True, disabled=not answer_eval_ready):
            st.info("👆 Click the '✅ Answer Evaluation' tab above to start")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        st.markdown("#### 🎓 Gap Analysis Agent")
        if gap_analysis_ready:
            st.success("✅ Ready")
        else:
            st.warning("⚠️ Not Initialized")
        st.markdown("Get personalized course recommendations for skill gaps")
        st.markdown("**Features:**")
        st.markdown("- Skill gap identification")
        st.markdown("- Course recommendations")
        st.markdown("- Learning path generation")
        if st.button("Launch Gap Analysis →", key="nav_gap_analysis", use_container_width=True, disabled=not gap_analysis_ready):
            st.info("👆 Click the '🎓 Gap Analysis' tab above to start")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Success message when all ready
    if all_ready:
        st.success("🎉 All agents are ready! Select an agent tab above to get started.")

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
    
    # Check if we have interview prep results to use
    has_interview_questions = (st.session_state.interview_prep_result is not None and 
                               st.session_state.interview_prep_result.get('questions'))
    
    # Check if we have job description from previous agents
    has_job_description = False
    detected_job_description = ""
    
    # Try to get job description from interview prep (Agent 2)
    if st.session_state.interview_prep_result:
        detected_job_description = st.session_state.interview_prep_result.get('job_description_text', '')
        if detected_job_description:
            has_job_description = True
    
    # Display detection status
    if has_interview_questions:
        st.success("✅ Interview questions detected from Agent 2! You can use them directly.")
    
    if has_job_description:
        st.success("✅ Job description detected from previous agent! You can use it directly.")
    
    # Job Description Input with auto-detection
    st.subheader("📋 Job Description")
    
    if has_job_description:
        use_detected = st.radio(
            "Data source:",
            ["Use detected job description", "Enter manually"],
            horizontal=True,
            key="jd_source"
        )
    else:
        st.info("💡 Run Interview Prep (Agent 2) first, or enter job description manually")
        use_detected = "Enter manually"
    
    if use_detected == "Use detected job description" and has_job_description:
        st.text_area("Detected Job Description:", detected_job_description[:300] + "..." if len(detected_job_description) > 300 else detected_job_description, height=100, disabled=True, key="detected_jd_display")
        job_description = detected_job_description
    else:
        job_description = st.text_area(
            "Paste the job description:",
            height=200,
            placeholder="Enter the job description that was used for interview questions...",
            key="manual_jd_input"
        )
    
    st.markdown("---")
    
    # Question and Answer Input
    st.subheader("❓ Questions and Answers")
    
    # Input method selection
    input_method = st.radio(
        "Input method:",
        ["Manual Entry", "Upload File", "Use Agent 2 Questions"],
        horizontal=True,
        disabled=not has_interview_questions if "Use Agent 2 Questions" in ["Manual Entry", "Upload File", "Use Agent 2 Questions"] else False
    )
    
    # Handle different input methods
    if input_method == "Manual Entry":
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
    
    elif input_method == "Upload File":
        st.info("📁 Upload a text file containing questions and answers. Format: Q: followed by A: on new lines")
        
        uploaded_qa_file = st.file_uploader(
            "Upload Q&A file",
            type=['txt'],
            key="qa_upload",
            help="Expected format:\nQ: Question text here?\nA: Answer text here.\n\nQ: Next question?\nA: Next answer."
        )
        
        if uploaded_qa_file:
            try:
                file_content = uploaded_qa_file.read().decode('utf-8')
                
                # Parse Q&A from file
                parsed_qa = []
                lines = file_content.split('\n')
                current_question = None
                current_answer = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Q:'):
                        # Save previous Q&A if exists
                        if current_question and current_answer:
                            parsed_qa.append({
                                "question": current_question,
                                "answer": ' '.join(current_answer)
                            })
                        current_question = line[2:].strip()
                        current_answer = []
                    elif line.startswith('A:'):
                        current_answer = [line[2:].strip()]
                    elif line and current_answer is not None:
                        current_answer.append(line)
                
                # Save last Q&A
                if current_question and current_answer:
                    parsed_qa.append({
                        "question": current_question,
                        "answer": ' '.join(current_answer)
                    })
                
                if parsed_qa:
                    st.session_state.question_answers = parsed_qa
                    st.success(f"✅ Successfully parsed {len(parsed_qa)} question(s) and answer(s)!")
                    
                    with st.expander("Preview Parsed Q&A"):
                        for idx, qa in enumerate(parsed_qa, 1):
                            st.markdown(f"**Q{idx}:** {qa['question'][:100]}...")
                            st.markdown(f"**A{idx}:** {qa['answer'][:100]}...")
                            st.markdown("---")
                else:
                    st.warning("⚠️ No Q&A pairs found. Please check the file format.")
                    
            except Exception as e:
                st.error(f"❌ Error parsing file: {str(e)}")
        
        if st.session_state.question_answers:
            if st.button("🗑️ Clear Uploaded Q&A"):
                st.session_state.question_answers = []
                st.rerun()
    
    elif input_method == "Use Agent 2 Questions":
        if has_interview_questions:
            questions = st.session_state.interview_prep_result.get('questions', [])
            
            st.info(f"📝 {len(questions)} questions available from Agent 2. Add candidate answers below.")
            
            # Select which questions to answer
            selected_questions = st.multiselect(
                "Select questions to answer:",
                options=range(len(questions)),
                format_func=lambda i: f"Q{i+1}: {questions[i].question[:80]}...",
                default=list(range(min(5, len(questions))))
            )
            
            if selected_questions:
                st.markdown(f"**Adding answers for {len(selected_questions)} selected question(s)**")
                
                # Form to add answers
                with st.form("agent2_qa_form"):
                    answers_dict = {}
                    for idx in selected_questions:
                        q = questions[idx]
                        st.markdown(f"**Question {idx+1}:**")
                        st.write(q.question)
                        answers_dict[idx] = st.text_area(
                            f"Candidate's Answer for Q{idx+1}:",
                            height=100,
                            key=f"answer_{idx}",
                            placeholder="Enter the candidate's answer..."
                        )
                        st.markdown("---")
                    
                    submit_answers = st.form_submit_button("✅ Add Answers to Evaluation")
                    
                    if submit_answers:
                        qa_list = []
                        for idx in selected_questions:
                            if answers_dict[idx].strip():
                                qa_list.append({
                                    "question": questions[idx].question,
                                    "answer": answers_dict[idx]
                                })
                        
                        if qa_list:
                            st.session_state.question_answers = qa_list
                            st.success(f"✅ Added {len(qa_list)} Q&A pairs for evaluation!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Please provide at least one answer")
            
            if st.session_state.question_answers:
                with st.expander("View Q&A to be Evaluated"):
                    for idx, qa in enumerate(st.session_state.question_answers, 1):
                        st.markdown(f"**Q{idx}:** {qa['question']}")
                        st.markdown(f"**A{idx}:** {qa['answer'][:100]}...")
                        st.markdown("---")
                
                if st.button("🗑️ Clear Q&A"):
                    st.session_state.question_answers = []
                    st.rerun()
        else:
            st.warning("⚠️ No questions available from Agent 2. Please generate questions first in the Interview Prep tab.")
    
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
    
    # Display header with logo
    display_header()

    # Initialize session state
    init_session_state()

    
    # Create tabs for different agents
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Home", 
        "🎯 Job Matching", 
        "📝 Interview Prep", 
        "✅ Answer Evaluation",
        "🎓 Gap Analysis",
        "� Implementation Docs"
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
        implementation_docs()

if __name__ == "__main__":
    main()
