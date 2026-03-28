# LinkedIn Icebreaker Bot

An AI-powered assistant that generates personalized icebreakers and conversation starters based on LinkedIn profiles. Built with GitHub Models (OpenAI-compatible) and LlamaIndex, it helps make professional introductions more personal and engaging.

## Course Note

This project is my guided implementation from a course I followed to learn LLM application development and RAG workflows. The base workflow and core structure came from course instructions, and I customized/integrated parts while implementing it myself.

## 🌟 Features

- **LinkedIn Profile Analysis**: Extract professional data using Apify scraper or use mock data
- **AI-Powered Insights**: Generate interesting facts about a person's career/education
- **Personalized Q&A**: Answer specific questions about the person's background
- **Two Interfaces**: Command-line tool for quick usage and web UI for user-friendly interaction
- **Flexible**: Use mock data for practice or connect to real LinkedIn profiles with Apify

## 🚀 Quick Start

### Prerequisites

- Python 3.11+, < 3.13
- A GitHub fine-grained token with GitHub Models access (`Models: Read`), exported as `GITHUB_TOKEN`
- An Apify API token (optional - mock data available for free testing)
  - Get free token at: https://apify.com/

### Installation

1. Clone your own repository:

```bash
git clone https://github.com/Mzafeer11/LinkedIn-Analyzer.git
cd LinkedIn-Analyzer
```

If you are starting from this codebase and want to publish your own copy first:

```bash
git clone https://github.com/HaileyTQuach/icebreaker.git icebreaker-mine
cd icebreaker-mine
git remote rename origin upstream
git remote add origin https://github.com/Mzafeer11/LinkedIn-Analyzer.git
git push -u origin main
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Export required/optional environment variables:

```bash
# Required for GitHub Models
export GITHUB_TOKEN="your-fine-grained-token"

# Optional (only for real LinkedIn profile extraction with Apify)
# Get free token at: https://apify.com
export APIFY_API_TOKEN="your-apify-token-here"
```

### Using the Command Line Interface

Run the bot using the terminal:

```bash
# Use mock data (no API key needed)
python main.py --mock

# OR use a real LinkedIn profile
python main.py --url "https://www.linkedin.com/in/username/" --api-key "your-api-key"
```

### Using the Web Interface

Launch the web app:

```bash
python app.py
```

Then open your browser to the URL shown in the terminal (typically http://127.0.0.1:7860).

## 🧠 How It Works

The Icebreaker Bot uses a Retrieval-Augmented Generation (RAG) pipeline:

1. **Data Extraction**: LinkedIn profile data is retrieved via ProxyCurl API or mock data
2. **Text Processing**: Profile data is split into manageable chunks
3. **Vector Embedding**: Text chunks are converted to vector embeddings using GitHub Models
4. **Storage**: Embeddings are stored in a vector database
5. **Query & Generation**: When asked a question, relevant profile sections are retrieved and a GitHub Models LLM generates contextually accurate responses

## 🛠️ Project Structure

```
icebreaker_bot/
├── requirements.txt           # Dependencies
├── config.py                  # Configuration settings
├── modules/
│   ├── __init__.py
│   ├── data_extraction.py     # LinkedIn profile data extraction
│   ├── data_processing.py     # Data splitting and indexing
│   ├── llm_interface.py       # LLM setup and interaction
│   └── query_engine.py        # Query processing and response generation
├── app.py                     # Gradio web interface
└── main.py                    # CLI application
```

## 📝 Examples

Here are some example questions you can ask:

- "What is this person's current job title?"
- "Where did they get their education?"
- "What skills do they have related to machine learning?"
- "How long have they been working at their current company?"
- "What was their career progression?"

## 🧪 Customization

### Using Different LLM Models

You can switch between available models:

```bash
python main.py --mock --model "gpt-4.1-mini"
```

Or in the web interface, select from the dropdown menu.

### Adjusting Response Style

Edit the prompt templates in `config.py` to change how responses are generated:

```python
INITIAL_FACTS_TEMPLATE = """
You are an AI assistant that provides detailed answers based on the provided context.
...
"""
```

## 👩‍💻 Development

### For Beginners

If you're learning to build this project from scratch, check out the `1-start` branch:

```bash
git checkout 1-start
```

This branch contains starter files with TODOs and guidance for implementation.

### Running Tests

Test individual components:

```bash
# Test data extraction
python -c "from modules.data_extraction import extract_linkedin_profile; print(extract_linkedin_profile('https://www.linkedin.com/in/username/', mock=True))"

# Test the entire pipeline
python main.py --mock --test
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- GitHub Models for providing OpenAI-compatible LLM and embedding endpoints
- LlamaIndex for the data indexing and retrieval framework
- ProxyCurl for LinkedIn profile data extraction
- Eden Marco for the original tutorial inspiration
