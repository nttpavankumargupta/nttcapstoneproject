# Quick Start Guide - Job Matching Agent

Get started with the Job Matching Agent in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- OpenAI API key

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up Environment

Create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

Replace `your_api_key_here` with your actual OpenAI API key.

## Step 3: Run the Application

### Option A: Streamlit Web Interface (Recommended)

```bash
streamlit run streamlit_app.py
```

This opens an interactive web interface where you can:
- Paste or upload job descriptions (TXT, PDF, DOCX, DOC)
- Add multiple resumes (paste text or upload TXT, PDF, DOCX, DOC files)
- View beautifully formatted results with match scores and gap analysis
- Download analysis results

### Option B: Command Line with Sample Data

```bash
python main.py
```

This runs a complete demo with 3 sample resumes against a sample job description.

### Option C: Command Line with Custom Data

```bash
python example_job_matching.py
```

Edit `example_job_matching.py` to customize the job description and resumes, then run it.

## Understanding the Output

The agent will provide:

1. **Match Score** (0-100): Overall fit for the position
2. **Matched Skills**: Skills the candidate has that match job requirements
3. **Missing Skills**: Required skills the candidate lacks
4. **Strengths**: Candidate's relevant strengths
5. **Gaps**: Specific areas where the candidate falls short
6. **Summary**: Overall assessment of the candidate

### Example Output

```
#1 Rank
📋 Candidate: John Smith
   Match Score: 92.0/100

   ✅ Matched Skills: Python, TensorFlow, AWS, Docker
   ❌ Missing Skills: None

   💪 Strengths:
      • 7+ years of Python experience exceeds requirement
      • Strong ML framework expertise

   ⚠️  Gaps:
      • No vector database experience mentioned

   📝 Summary: Excellent fit with strong technical background
```

## Using in Your Code

```python
from src.config.config import Config
from src.graph_builder.job_match_graph import JobMatchGraphBuilder

# Initialize
llm = Config.get_llm()
graph_builder = JobMatchGraphBuilder(llm)
graph_builder.build()

# Prepare data
job_description = "Your job description here..."
resumes = [
    {"name": "Candidate Name", "content": "Resume content..."}
]

# Run analysis
result = graph_builder.run(job_description, resumes)

# Access results
best_candidate = result.best_candidate
print(f"Best match: {best_candidate.resume_name}")
print(f"Score: {best_candidate.match_score}")
```

## Customizing the Agent

### Change LLM Model

Edit `src/config/config.py`:

```python
LLM_MODEL = "openai:gpt-4"  # or "openai:gpt-3.5-turbo"
```

### Adjust Analysis Criteria

Modify the prompts in `src/node/job_match_nodes.py` to change how the agent analyzes candidates.

## Troubleshooting

### "OPENAI_API_KEY not found"
- Ensure `.env` file exists in project root
- Check that the API key is valid

### "Module not found" errors
- Run `pip install -r requirements.txt`
- Ensure you're using Python 3.8+

### JSON parsing errors
- The LLM occasionally returns malformed JSON
- The code includes error handling and will retry or skip problematic resumes
- Consider using GPT-4 for more reliable JSON formatting

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize `example_job_matching.py` with your own data
- Integrate the agent into your application
- Explore the codebase to understand the LangGraph workflow

## Support

For issues or questions:
1. Check the Troubleshooting section in README.md
2. Review the code comments
3. Examine the example scripts

Happy job matching! 🎯
