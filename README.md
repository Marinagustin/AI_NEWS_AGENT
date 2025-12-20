# AI News Agent 📰

An intelligent multi-agent system that automatically researches, writes, and edits news articles on any given topic using LangGraph and LLMs.

## Overview

This application demonstrates a collaborative AI agent workflow where multiple specialized agents work together under a supervisor to create high-quality news articles:

1. **Supervisor** - Orchestrates the workflow and routes tasks between agents
2. **Researcher** - Searches the web for relevant information on the topic
3. **Writer** - Crafts a well-structured news article based on research
4. **Editor** - Reviews and refines the article for clarity and quality
5. **File Writer** - Saves the final article to a Markdown file

## Features

- 🔍 **Web Research** - Uses Tavily Search to gather current information
- ✍️ **Article Generation** - LLM-powered article writing with structure
- 📝 **Content Editing** - Editorial review and improvement of articles
- 🎯 **Multi-Agent Orchestration** - LangGraph-based workflow management
- 🔗 **Source Attribution** - Automatically includes references to sources
- 💾 **File Writing** - Saves articles as Markdown files

## Architecture

The application uses **LangGraph** to create a stateful agent graph:

```
Supervisor → Researcher → (research_summary)
    ↓
    → Writer → (article)
    ↓
    → Editor → (final_article)
    ↓
    → File Writer → (saved_article)
    ↓
    → End
```

### State Management

The `SupervisorState` maintains:

- `messages`: Conversation history
- `topic`: News topic to research
- `research_summary`: Web research findings
- `references`: Source URLs
- `article`: Raw article draft
- `final_article`: Polished final version
- `task_complete`: Workflow completion flag
- `file_path`: Path to the saved article file

## Installation

### Prerequisites

- Python 3.8+
- API keys for:
  - LLM provider (Groq, OpenAI, etc.)
  - Tavily Search API

### Setup

1. **Clone and navigate to the project:**

   ```bash
   cd ai_news_agent
   ```

2. **Install dependencies:**

   ```bash
   uv add -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```
   LLM_MODEL_NAME=groq/mixtral-8x7b-32768
   TAVILY_API_KEY=your_tavily_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

## Usage

### Running the Agent

```bash
python main.py
```

Or directly:

```bash
python app/supervisor_news_agent.py
```

### Example

```
🗞️ Enter news topic: Artificial Intelligence breakthroughs in 2025
```

The system will:

1. Research the topic using web search
2. Generate a comprehensive news article
3. Edit and polish the content
4. Save the final article to a file
5. Output the file path for download

### Sample Output

```
📰 FINAL NEWS ARTICLE
============================================================
Topic: Artificial Intelligence breakthroughs in 2025
Generated on: 2025-12-13 14:30
============================================================

[Full article content with headline, introduction, key developments, and conclusion]

============================================================
🔗 References:
https://source1.com
https://source2.com

📂 Saved to: generated_articles/Artificial_Intelligence_breakthroughs_in_2025_20251213_1430.md
```

## Dependencies

- **langgraph** - Agent workflow orchestration
- **langchain** - LLM framework and tools
- **langsmith** - Monitoring and debugging
- **langchain-groq** - Groq LLM integration
- **langchain-tavily** - Web search integration
- **python-dotenv** - Environment configuration
- **ipython** - Interactive utilities

See `requirements.txt` for full details.

## Project Structure

```
ai_news_agent/
├── main.py                          # Entry point
├── app/
│   └── supervisor_news_agent.py     # Main agent implementation
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project configuration
└── README.md                        # This file
```

## Agent Descriptions

### Supervisor Agent

Routes tasks through the workflow. Decides what step comes next based on the state:

- If no research: assign Researcher
- If no article: assign Writer
- If no final article: assign Editor
- If no file path: assign File Writer
- If all complete: end task

### Researcher Agent

Performs web searches using the Tavily Search API:

- Searches for the given topic
- Collects up to 5 relevant results
- Summarizes content for the writer
- Preserves source URLs for references

### Writer Agent

Creates structured news articles:

- Takes research summary as input
- Generates well-formatted articles with:
  - Compelling headlines
  - Clear introductions
  - Key developments
  - Conclusions
- Uses the configured LLM for generation

### Editor Agent

Reviews and improves the article:

- Ensures clarity and readability
- Maintains factual tone
- Approves final version
- Formats output with metadata and references

### File Writer Agent

The File Writer agent is responsible for saving the final article to a Markdown file. It ensures that the content is stored in a structured and accessible format for future use.

#### Features

- **Safe File Naming**: Generates filenames based on the topic and timestamp to avoid conflicts.
- **Markdown Format**: Saves articles in Markdown for easy readability and formatting.
- **Error Handling**: Handles file write errors gracefully and provides detailed error messages.

#### File Path

The articles are saved in the `generated_articles` directory. The file path is included in the API response for easy access.

#### Example

If the topic is "AI in Healthcare," the file might be saved as:
```
generated_articles/AI_in_Healthcare_20251220_153045.md
```

This ensures that articles are organized and timestamped for traceability.

## Configuration

### LLM Model Selection

Edit the `LLM_MODEL_NAME` in your `.env` file:

```
# Using Groq
LLM_MODEL_NAME=groq/mixtral-8x7b-32768

# Using OpenAI
LLM_MODEL_NAME=openai/gpt-4

# Using Anthropic
LLM_MODEL_NAME=anthropic/claude-3-sonnet-20240229
```

## Extending the System

### Add Custom Tools

```python
@tool
def custom_tool(input: str) -> str:
    """Custom tool description"""
    # Implementation
    return result
```

Then add to agent prompts or state.

### Modify Agent Behavior

Edit the prompt templates in each agent function to change:

- Article style or structure
- Review criteria for the editor
- Search query formulation

### Add New Agents

1. Create a new agent function following the pattern
2. Add it to the workflow graph
3. Update router logic in the supervisor
4. Add state fields if needed

## Troubleshooting

| Issue             | Solution                                       |
| ----------------- | ---------------------------------------------- |
| API key errors    | Verify `.env` file has correct keys            |
| No search results | Check Tavily API quota and internet connection |
| LLM errors        | Ensure model name matches provider format      |
| Slow execution    | Reduce search result count in `search_web()`   |

## Monitoring and Debugging

The system prints status messages during execution:

- `✅ LLM initialized` - Model loaded successfully
- `🔍 Researcher: Web research completed` - Search finished
- `✍️ Writer: Article drafted` - Article generation done
- `📝 Editor: Article approved` - Editing complete
- `💾 File Writer: Article saved` - File writing complete

## Future Enhancements

- [ ] Support for fact-checking agents
- [ ] Multi-language article generation
- [ ] Image sourcing and inclusion
- [ ] Scheduling for automated news generation
- [ ] Custom output formats (PDF, email, etc.)
- [ ] Performance metrics and analytics

## License

MIT License - Feel free to use and modify for your projects.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or issues.

---

**Built with** LangGraph, LangChain, and AI agents for automated content creation.

## Streamlit Integration

The project includes a Streamlit-based user interface for generating and downloading articles interactively. The Streamlit app communicates with the FastAPI backend to trigger the article generation workflow.

### Running the Streamlit App

1. Ensure the FastAPI server is running:
   ```bash
   python main.py
   ```

2. Start the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```

3. Open the app in your browser at `http://localhost:8501`.

### Features

- **Interactive Input**: Enter a topic and generate articles.
- **Progress Visualization**: Real-time progress updates during article generation.
- **Download Options**: Save articles as Markdown or plain text.
- **Research Summary and References**: View research findings and source links.

---

## API Endpoints

The FastAPI backend provides the following endpoints:

### Health Check
- **GET /**
  - Description: Check the health of the API.
  - Response: Status, timestamp, version, and LLM model name.

### Generate Article
- **POST /api/v1/articles/generate**
  - Description: Generate a news article based on the provided topic.
  - Request Body:
    ```json
    {
      "topic": "Latest developments in AI technology"
    }
    ```
  - Response: Article content, research summary, references, and file path.

### Download Article
- **GET /api/v1/articles/download/{filename}**
  - Description: Download a specific article by filename.

### List Articles
- **GET /api/v1/articles/list**
  - Description: List all generated articles with optional filtering by status.

### Delete Article
- **DELETE /api/v1/articles/{job_id}**
  - Description: Delete a specific article generation job.

---

## Example Workflow

1. **Input Topic**: Provide a topic like "Advancements in Renewable Energy."
2. **Agent Workflow**:
   - Researcher gathers information.
   - Writer drafts the article.
   - Editor refines the content.
   - File Writer saves the article.
3. **Output**:
   - Final article with references.
   - Downloadable Markdown and text files.

---

## Screenshots

### Streamlit App
![Streamlit App](docs/screenshots/streamlit_app.png)

### API Documentation
![API Docs](docs/screenshots/api_docs.png)

---
