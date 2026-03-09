"""Streamlit UI for Job Matching Agent"""

import streamlit as st
from pathlib import Path
import sys
import time
import truststore

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config.config import Config
from src.graph_builder.job_match_graph import JobMatchGraphBuilder
from src.utils.document_parser import extract_text_from_file

# Page configuration
st.set_page_config(
    page_title="🎯 Job Matching Agent",
    page_icon="🎯",
    layout="wide"
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
    .candidate-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .best-match {
        border: 3px solid gold;
        background-color: #fffde7;
    }
    </style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'graph_builder' not in st.session_state:
        st.session_state.graph_builder = None
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'resumes' not in st.session_state:
        st.session_state.resumes = []

@st.cache_resource
def initialize_graph_builder():
    """Initialize the graph builder (cached)"""
    try:
        truststore.inject_into_ssl()
        llm = Config.get_llm()
        graph_builder = JobMatchGraphBuilder(llm)
        graph_builder.build()
        return graph_builder
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        return None

def display_candidate_match(match, rank, is_best=False):
    """Display a candidate match card"""
    container_class = "candidate-card best-match" if is_best else "candidate-card"
    
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

def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.title("🎯 Job Matching Agent with LangGraph")
    st.markdown("**Find the best candidates for your job opening with AI-powered analysis**")
    
    # Initialize system
    if st.session_state.graph_builder is None:
        with st.spinner("Initializing AI system..."):
            graph_builder = initialize_graph_builder()
            if graph_builder:
                st.session_state.graph_builder = graph_builder
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
                        # Remove file extension from name
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
        elif st.session_state.graph_builder:
            with st.spinner("🔄 Analyzing candidates... This may take a moment..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Update progress
                    status_text.text("Step 1/4: Parsing job description...")
                    progress_bar.progress(25)
                    time.sleep(0.5)
                    
                    status_text.text("Step 2/4: Processing resumes...")
                    progress_bar.progress(50)
                    time.sleep(0.5)
                    
                    status_text.text("Step 3/4: Analyzing matches and gaps...")
                    progress_bar.progress(75)
                    
                    # Run analysis
                    result = st.session_state.graph_builder.run(
                        job_description,
                        st.session_state.resumes
                    )
                    
                    status_text.text("Step 4/4: Finalizing results...")
                    progress_bar.progress(100)
                    
                    st.session_state.analysis_result = result
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success("✅ Analysis complete!")
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    st.exception(e)
    
    # Display results
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        
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

if __name__ == "__main__":
    main()
