from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from datetime import datetime
import os

# Initialize LLM
llm_model_name = os.getenv("LLM_MODEL_NAME")
llm = init_chat_model(llm_model_name)

# --- State for the workflow ---
class SupervisorState(MessagesState):
    next_agent: str = ""
    topic: str = ""
    research_summary: str = ""
    references: list[str] = []
    article: str = ""
    final_article: str = ""
    markdown_content: str = ""
    task_complete: bool = False
    file_path: str = ""  # NEW: Store the file path

# --- Tool: Web Search ---
@tool
def search_web(query: str) -> dict:
    """Search the web using Tavily and return clean summary and links."""
    search = TavilySearchResults(max_results=5)
    results = search.invoke(query)
    summaries = []
    links = []
    for r in results:
        summaries.append(r.get("content", ""))
        links.append(r.get("url", ""))
    return {
        "summary": "\n\n".join(summaries).strip(),
        "links": [link for link in links if link]
    }

# --- Workflow Graph ---
workflow = StateGraph(SupervisorState)

# Add nodes to the workflow
def dummy_agent(state):
    return {}

workflow.add_node("supervisor", dummy_agent)
workflow.add_node("researcher", dummy_agent)
workflow.add_node("writer", dummy_agent)
workflow.add_node("editor", dummy_agent)
workflow.add_node("file_writer", dummy_agent)

# Set entry point
workflow.set_entry_point("supervisor")

# Compile the graph
graph = workflow.compile()