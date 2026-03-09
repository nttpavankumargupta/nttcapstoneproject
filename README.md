# Job Matching Agent with LangGraph

An intelligent job matching agent built with LangGraph that analyzes resumes against job descriptions, identifies the best candidates, and highlights gaps between candidate qualifications and job requirements.

## Features

- 🔍 **Intelligent Resume Analysis**: Uses LLM to extract skills, experience, and education from resumes
- 📋 **Job Description Parsing**: Automatically identifies required skills, preferred skills, and requirements
- 🎯 **Smart Matching**: Calculates match scores and ranks candidates
- ⚠️ **Gap Analysis**: Identifies missing skills and experience gaps
- 💪 **Strength Identification**: Highlights candidate strengths relevant to the position
- 📊 **Comprehensive Reports**: Provides detailed analysis for each candidate

## Architecture

The agent uses a LangGraph workflow with the following nodes:

1. **Parse Job Description**: Extracts structured information from job posting
2. **Parse Resumes**: Analyzes each resume to extract skills, experience, and education
3. **Analyze Matches**: Compares candidates against requirements and calculates fit
4. **Finalize Results**: Ranks candidates and identifies best fit

```
┌─────────────────────────┐
│  Parse Job Description  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│    Parse Resumes        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Analyze Matches       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Finalize Results      │
└─────────────────────────┘
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Streamlit Web Interface (Recommended)

Launch the interactive web interface:

```bash
streamlit run streamlit_app.py
```

This opens a user-friendly web interface where you can:
- Paste or upload job descriptions (supports TXT, PDF, DOCX, DOC formats)
- Add multiple resumes (paste text or upload files in TXT, PDF, DOCX, DOC formats)
- View interactive analysis results
- Download results as text files

### Basic Command Line Usage

Run the main script with example data:

```bash
python main.py
```

This will run a demonstration with sample job descriptions and resumes.

### Programmatic Usage

```python
from src.config.config import Config
from src.graph_builder.job_match_graph import JobMatchGraphBuilder

# Initialize LLM
llm = Config.get_llm()

# Create graph builder
graph_builder = JobMatchGraphBuilder(llm)
graph_builder.build()

# Define job description
job_description = """
Senior Software Engineer position requiring:
- 5+ years Python experience
- Machine learning expertise
- Cloud platform experience (AWS/GCP/Azure)
"""

# Define resumes
resumes = [
    {
        "name": "Jane Doe",
        "content": "Jane Doe - 7 years Python, TensorFlow, AWS..."
    },
    {
        "name": "John Smith", 
        "content": "John Smith - 3 years Python, React..."
    }
]

# Run analysis
result = graph_builder.run(job_description, resumes)

# Access results
for match in result.candidate_matches:
    print(f"{match.resume_name}: {match.match_score}/100")
    print(f"Matched Skills: {match.matched_skills}")
    print(f"Missing Skills: {match.missing_skills}")
    print(f"Gaps: {match.gaps}")
    print(f"Strengths: {match.strengths}")
```

### Custom Integration

You can integrate the job matching agent into your own application:

```python
from src.state.job_match_state import JobMatchState
from src.graph_builder.job_match_graph import JobMatchGraphBuilder

# Your custom job description and resumes
job_desc = load_job_description_from_database()
resumes = load_resumes_from_storage()

# Run analysis
result = graph_builder.run(job_desc, resumes)

# Get best candidate
best_fit = result.best_candidate
print(f"Best candidate: {best_fit.resume_name}")
print(f"Match score: {best_fit.match_score}")
```

## Project Structure

```
.
├── main.py                          # Main entry point with examples
├── src/
│   ├── config/
│   │   └── config.py               # Configuration and LLM initialization
│   ├── state/
│   │   ├── rag_state.py            # Original RAG state (legacy)
│   │   └── job_match_state.py      # Job matching state definitions
│   ├── node/
│   │   ├── nodes.py                # Original nodes (legacy)
│   │   ├── reactnode.py            # Original ReAct nodes (legacy)
│   │   └── job_match_nodes.py      # Job matching node implementations
│   └── graph_builder/
│       ├── graph_builder.py        # Original graph builder (legacy)
│       └── job_match_graph.py      # Job matching graph builder
├── requirements.txt                 # Python dependencies
└── README.md                       # This file
```

## State Management

The agent uses Pydantic models for type-safe state management:

### JobMatchState
- `job_description_text`: Raw job description input
- `resume_texts`: List of resume dictionaries
- `job_description`: Parsed job description
- `resumes`: Parsed resume objects
- `candidate_matches`: Analysis results for all candidates
- `best_candidate`: Top-ranked candidate
- `analysis_complete`: Workflow completion flag

### CandidateMatch
- `resume_id`: Unique identifier
- `resume_name`: Candidate name
- `match_score`: 0-100 fit score
- `matched_skills`: Skills matching requirements
- `missing_skills`: Required skills candidate lacks
- `gaps`: Detailed gap analysis
- `strengths`: Candidate's relevant strengths
- `summary`: Overall assessment

## Configuration

Edit `src/config/config.py` to customize:

- **LLM Model**: Change `LLM_MODEL` to use different OpenAI models
- **API Keys**: Set environment variables for different providers

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in `requirements.txt`:
  - langchain
  - langchain-core
  - langchain-openai
  - langgraph
  - pydantic
  - python-dotenv

## Example Output

```
🤖 Job Matching Agent with LangGraph
================================================================================

📊 RESULTS - All Candidates (Ranked by Match Score)
================================================================================

#1 Rank
📋 Candidate: John Smith
   Match Score: 92.0/100

   ✅ Matched Skills: Python, TensorFlow, PyTorch, AWS, Docker, Kubernetes, REST APIs
   ❌ Missing Skills: None

   💪 Strengths:
      • 7+ years of Python experience exceeds requirement
      • Strong ML framework expertise with both TensorFlow and PyTorch
      • Leadership experience managing technical teams

   ⚠️  Gaps:
      • No explicit mention of vector database experience
      • Could benefit from more LangChain experience

   📝 Summary: Excellent fit with strong technical background and leadership experience.
```

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your `.env` file contains a valid OpenAI API key
2. **Import Errors**: Run `pip install -r requirements.txt` to install all dependencies
3. **JSON Parsing Errors**: The LLM occasionally returns malformed JSON; the code includes error handling

## Future Enhancements

- [x] Support for PDF and DOCX resume parsing ✅
- [x] Web interface for easy interaction ✅
- [ ] Batch processing for large candidate pools
- [ ] Integration with ATS systems
- [ ] Multi-language support
- [ ] Customizable scoring algorithms
- [ ] Email notification system
- [ ] Interview question generation based on gaps

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is provided as-is for educational and commercial use.
