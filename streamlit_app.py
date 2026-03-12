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

    #✅ NEW: persist answers + candidate selection across reruns
    if "candidate_answers" not in st.session_state:
        st.session_state.candidate_answers = {}
    if "selected_candidate_id" not in st.session_state:
        st.session_state.selected_candidate_id = ""

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
            st.session_state.candidate_answers = {}   
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
                        st.session_state.resumes,
                        target_resume_id=st.session_state.selected_candidate_id,
                        candidate_answers={}
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
                st.markdown("AGENT 1")
                st.markdown("### 📋 All Candidates (Ranked)")
                
                for idx, match in enumerate(result.candidate_matches, 1):
                    if result.best_candidate and match.resume_id == result.best_candidate.resume_id:
                       continue
                    display_candidate_match(match, idx, is_best=False)
            
            st.markdown("---")
            st.markdown("### 🤖 Agent 2 + 3 + 4: Interview, Evaluation & Learning Plan")

            # Candidate picker (persist selection)
            candidate_options = {m.resume_name: m.resume_id for m in result.candidate_matches}
            default_id = result.best_candidate.resume_id if result.best_candidate else list(candidate_options.values())[0]

            # pick default name based on stored ID
            stored_id = st.session_state.selected_candidate_id or default_id
            default_name = next((n for n, cid in candidate_options.items() if cid == stored_id), list(candidate_options.keys())[0])

            selected_name = st.selectbox(
                 "Select candidate:",
                 list(candidate_options.keys()),
                 index=list(candidate_options.keys()).index(default_name),
                 key="candidate_selectbox"
            )
            selected_id = candidate_options[selected_name]
            st.session_state.selected_candidate_id = selected_id

          # If questions exist, show them; else show info
            if getattr(result, "interview_questions", None) and len(result.interview_questions) > 0:
               st.success(f"Interview questions ready: {len(result.interview_questions)}")
            else:
               st.info("No interview questions found yet. Click Analyze Candidates (Agent 2 runs automatically after ranking).")

            # Answers (persist in session_state)
            if getattr(result, "interview_questions", None) and len(result.interview_questions) > 0:
                for q in result.interview_questions:
                    st.markdown(f"**[{q.id}] ({q.category} | {q.skill_tag} | {q.difficulty})**")
                    st.write(q.question)

                    with st.expander("Expected Answers "):
                        for r in q.rubric:
                            st.markdown(f"- {r}")

                    st.session_state.candidate_answers[q.id] = st.text_area(
                       f"Answer for {q.id}",
                       value=st.session_state.candidate_answers.get(q.id, ""),
                       key=f"ans_{q.id}",
                       height=120
                    )
                    st.markdown("---")

                if st.button("✅ Evaluate Answers", key="eval_btn"):
                    eval_state = st.session_state.graph_builder.run(
                        job_description,
                        st.session_state.resumes,
                        target_resume_id=selected_id,
                        candidate_answers=st.session_state.candidate_answers
                    )
                    st.session_state.analysis_result = eval_state
                    st.rerun()

           # Show evaluation (Agent 3)
            if getattr(result, "interview_evaluation", None):
                ev = result.interview_evaluation
                st.markdown("---")
                st.header("📌 Evaluation (Agent 3)")
            
                st.metric("Overall Score", f"{ev.overall_score:.1f}/100")
                st.write(f"**Recommendation:** {ev.recommendation}")
                st.write(ev.summary)
            
                st.subheader("Per-question breakdown")
                for pq in ev.per_question:
                    st.markdown(f"### {pq.question_id} — {pq.score}/5 ({pq.verdict})")
                    st.write(pq.feedback)
            
            # Show learning plan (Agent 4) only if generated
            plan = getattr(result, "learning_plan", None)
            if plan:
                st.markdown("---")
                st.header("📚 Learning Plan (Agent 4 - Triggered due to incorrect answers)")
                st.success(f"Estimated duration: {plan.overall_duration_weeks} weeks")
                st.write(plan.summary)
            
                for mod in plan.modules:
                    with st.expander(f"{mod.skill} — {mod.level_target} ({mod.duration_weeks} weeks @ {mod.weekly_hours} hrs/week)"):
                        if mod.prerequisites:
                            st.markdown("**Prerequisites**")
                            for p in mod.prerequisites:
                                st.markdown(f"- {p}")
            
                        st.markdown("**Learning steps**")
                        for s in mod.learning_steps:
                            st.markdown(f"- {s}")
            
                        if mod.resources:
                            st.markdown("**Resources**")
                            for r in mod.resources:
                                st.markdown(f"- {r}")
            
                        if mod.practice_tasks:
                            st.markdown("**Practice tasks**")
                            for t in mod.practice_tasks:
                                st.markdown(f"- {t}")
            
                        if mod.milestone:
                            st.markdown(f"**Milestone:** {mod.milestone}")
     
     
            if st.button("📥 Download Results as Text"):
                jd_title = result.job_description.title if result.job_description else "N/A"
            
                results_text = []
                results_text.append("JOB MATCHING ANALYSIS RESULTS")
                results_text.append("=" * 90)
                results_text.append(f"Job Title: {jd_title}")
                results_text.append(f"Total Candidates Analyzed: {len(result.candidate_matches)}")
                results_text.append("")
            
                # -------------------------
                # AGENT 1: Ranking + Gaps
                # -------------------------
                results_text.append("AGENT 1: CANDIDATE RANKING + GAPS")
                results_text.append("=" * 90)
            
                for idx, match in enumerate(result.candidate_matches, 1):
                    results_text.append("")
                    results_text.append("-" * 90)
                    results_text.append(f"RANK #{idx}: {match.resume_name} ({match.resume_id})")
                    results_text.append(f"Match Score: {match.match_score:.1f}/100")
                    results_text.append("-" * 90)
                    results_text.append(f"Summary: {match.summary}")
                    results_text.append(f"Matched Skills: {', '.join(match.matched_skills) if match.matched_skills else 'N/A'}")
                    results_text.append(f"Missing Skills: {', '.join(match.missing_skills) if match.missing_skills else 'N/A'}")
                    results_text.append(f"Strengths: {', '.join(match.strengths) if match.strengths else 'N/A'}")
                    results_text.append(f"Gaps: {', '.join(match.gaps) if match.gaps else 'N/A'}")
            
                # -------------------------
                # AGENT 2: Questions
                # -------------------------
                results_text.append("")
                results_text.append("AGENT 2: INTERVIEW QUESTIONS")
                results_text.append("=" * 90)
            
                if getattr(result, "interview_questions", None) and len(result.interview_questions) > 0:
                    for q in result.interview_questions:
                        results_text.append("")
                        results_text.append(f"[{q.id}] Category: {q.category} | Skill: {q.skill_tag} | Difficulty: {q.difficulty}")
                        results_text.append(f"Question: {q.question}")
                        if q.rubric:
                            results_text.append("Rubric:")
                            for r in q.rubric:
                                results_text.append(f"  - {r}")
                else:
                    results_text.append("No interview questions available.")
            
                # -------------------------
                # AGENT 3: Answers + Evaluation
                # -------------------------
                results_text.append("")
                results_text.append("AGENT 3: ANSWERS + EVALUATION")
                results_text.append("=" * 90)
            
                # Candidate answers (from session_state if present; else from result if you stored them)
                answers_dict = {}
                if "candidate_answers" in st.session_state and st.session_state.candidate_answers:
                    answers_dict = st.session_state.candidate_answers
                elif getattr(result, "candidate_answers", None):
                    answers_dict = result.candidate_answers
            
                if answers_dict:
                    results_text.append("Candidate Answers:")
                    for qid, ans in answers_dict.items():
                        results_text.append(f"- {qid}: {ans}")
                else:
                    results_text.append("Candidate Answers: Not provided.")
            
                if getattr(result, "interview_evaluation", None):
                    ev = result.interview_evaluation
                    results_text.append("")
                    results_text.append(f"Overall Score: {ev.overall_score:.1f}/100")
                    results_text.append(f"Recommendation: {ev.recommendation}")
                    results_text.append(f"Summary: {ev.summary}")
            
                    if ev.strengths:
                        results_text.append("Strengths:")
                        for s in ev.strengths:
                            results_text.append(f"  - {s}")
            
                    if ev.concerns:
                        results_text.append("Concerns:")
                        for c in ev.concerns:
                            results_text.append(f"  - {c}")
            
                    if ev.per_question:
                        results_text.append("")
                        results_text.append("Per-question Evaluation:")
                        for pq in ev.per_question:
                            results_text.append(f"  * {pq.question_id}: {pq.score}/5 ({pq.verdict})")
                            results_text.append(f"    Feedback: {pq.feedback}")
                            if pq.expected_points_hit:
                                results_text.append("    Expected points hit:")
                                for x in pq.expected_points_hit:
                                    results_text.append(f"      - {x}")
                            if pq.missing_points:
                                results_text.append("    Missing points:")
                                for x in pq.missing_points:
                                    results_text.append(f"      - {x}")
                else:
                    results_text.append("Evaluation: Not available (answers not evaluated yet).")
            
                # -------------------------
                # AGENT 4: Learning Plan
                # -------------------------
                results_text.append("")
                results_text.append("AGENT 4: LEARNING PLAN (Triggered on weak answers)")
                results_text.append("=" * 90)
            
                plan = getattr(result, "learning_plan", None)
                if plan:
                    results_text.append(f"Candidate: {plan.candidate_name} ({plan.candidate_id})")
                    results_text.append(f"Role: {plan.role_title}")
                    results_text.append(f"Estimated Duration: {plan.overall_duration_weeks} weeks")
                    results_text.append(f"Summary: {plan.summary}")
            
                    if plan.modules:
                        results_text.append("")
                        results_text.append("Modules:")
                        for i, mod in enumerate(plan.modules, 1):
                            results_text.append("")
                            results_text.append(f"{i}. Skill: {mod.skill}")
                            results_text.append(f"   Level Target: {mod.level_target}")
                            results_text.append(f"   Duration: {mod.duration_weeks} weeks @ {mod.weekly_hours} hrs/week")
            
                            if mod.prerequisites:
                                results_text.append("   Prerequisites:")
                                for p in mod.prerequisites:
                                    results_text.append(f"     - {p}")
            
                            if mod.learning_steps:
                                results_text.append("   Learning Steps:")
                                for s in mod.learning_steps:
                                    results_text.append(f"     - {s}")
            
                            if mod.resources:
                                results_text.append("   Resources:")
                                for r in mod.resources:
                                    results_text.append(f"     - {r}")
            
                            if mod.practice_tasks:
                                results_text.append("   Practice Tasks:")
                                for t in mod.practice_tasks:
                                    results_text.append(f"     - {t}")
            
                            if mod.milestone:
                                results_text.append(f"   Milestone: {mod.milestone}")
            
                    if plan.notes:
                        results_text.append("")
                        results_text.append("Notes:")
                        for n in plan.notes:
                            results_text.append(f"  - {n}")
                else:
                    results_text.append("No learning plan generated (Agent 4 triggers only if evaluation is weak).")
            
                final_text = "\n".join(results_text)
            
                st.download_button(
                    label="Download Full Results (Agents 1-4)",
                    data=final_text,
                    file_name="job_matching_full_results_agents_1_to_4.txt",
                    mime="text/plain"
                )# Download results option
                        



if __name__ == "__main__":
    main()
