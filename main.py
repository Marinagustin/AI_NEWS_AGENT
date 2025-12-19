
import os
import sys
from typing import Dict, Literal, Optional, List
from datetime import datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uvicorn

load_dotenv()

# Initialize LLM
llm_model_name = os.getenv("LLM_MODEL_NAME")
llm = init_chat_model(llm_model_name)
print("✅ LLM initialized")

# Create output directory for markdown files
OUTPUT_DIR = "generated_articles"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# AGENT WORKFLOW CODE
# =============================================================================

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
def search_web(query: str) -> Dict:
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


# --- NEW: File Writer Tool ---
@tool
def file_writer_tool(content: str, topic: str) -> Dict:
    """
    Save the final article content to a markdown file.
    
    Args:
        content: The article content to save
        topic: The topic of the article (used for filename)
    
    Returns:
        Dict with status and file_path
    """
    try:
        # Create a safe filename from the topic
        safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in topic)
        safe_topic = safe_topic.replace(' ', '_')[:50]  # Limit length
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_topic}_{timestamp}.md"
        file_path = os.path.join(OUTPUT_DIR, filename)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Article saved to: {file_path}")
        
        return {
            "status": "success",
            "file_path": file_path,
            "filename": filename,
            "message": f"Article successfully saved to {filename}"
        }
    except Exception as e:
        print(f"❌ Error saving file: {str(e)}")
        return {
            "status": "error",
            "file_path": "",
            "filename": "",
            "message": f"Failed to save file: {str(e)}"
        }


# --- Supervisor Agent (LLM-powered) ---
def supervisor_agent(state: SupervisorState) -> Dict:
    print("👔 Supervisor is reviewing the workflow...")
    # Compose a prompt for the LLM to decide the next agent
    prompt = f"""
You are the supervisor of a multi-agent news workflow. Based on the current state, decide which agent should act next.

Agents:
- researcher: Gathers factual information about the topic.
- writer: Writes a creative news article using research and analysis.
- editor: Reviews and improves the article for clarity and professionalism.
- file_writer: Saves the final article to a markdown file.

Current State:
Topic: {state.get('topic','')}
Research Summary: {bool(state.get('research_summary'))}
Article: {bool(state.get('article'))}
Final Article: {bool(state.get('final_article'))}
File Path: {state.get('file_path', '')}

Instructions:
- If research_summary is missing, assign researcher.
- If article is missing, assign writer.
- If final_article is missing, assign editor.
- If file_path is missing, assign file_writer.
- If all are present including file_path, mark task_complete and assign end.
- Only one agent should be assigned at a time.

Reply with the next agent to act (one of: researcher, writer, editor, file_writer, end) and a short message for the log.
Format:
next_agent: <agent_name>
message: <short message>
task_complete: <true/false>
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    # Parse the LLM response
    next_agent = "file_writer"
    message = "✅ Supervisor: Task completed"
    task_complete = False
    for line in response.content.splitlines():
        if line.lower().startswith("next_agent:"):
            next_agent = line.split(":",1)[1].strip()
        elif line.lower().startswith("message:"):
            message = line.split(":",1)[1].strip()
        elif line.lower().startswith("task_complete:"):
            val = line.split(":",1)[1].strip().lower()
            task_complete = val == "true"
    
    # If we have final_article but no file_path, go to file_writer
    if state.get('final_article') and not state.get('file_path'):
        next_agent = "file_writer"
        task_complete = False
    
    return {
        "messages": [AIMessage(content=message)],
        "next_agent": next_agent,
        "task_complete": task_complete
    }


# --- Researcher Agent (factual persona) ---
def researcher_agent(state: SupervisorState) -> Dict:
    print("🔍 Researcher is working...")
    topic = state["topic"]
    result = search_web.invoke(topic)
    summary = result.get("summary", "").strip()
    links = result.get("links", [])
    return {
        "messages": [AIMessage(content="🔍 Researcher (factual): Web research completed.")],
        "research_summary": summary,
        "references": links,
        "next_agent": "supervisor"
    }


# --- Writer Agent (creative persona) ---
def writer_agent(state: SupervisorState) -> Dict:
    print("✍️ Writer is drafting the article...")
    prompt = f"""
You are a creative news writer. Write a well-structured, engaging news article with a creative tone.

Topic: {state['topic']}

Research (factual, from researcher):
{state['research_summary']}

Include:
- Headline
- Introduction
- Key developments
- Conclusion

Be creative, but stay true to the facts.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return {
        "messages": [AIMessage(content="✍️ Writer (creative): Article drafted.")],
        "article": response.content.strip(),
        "next_agent": "supervisor"
    }


# --- Editor Agent ---
def editor_agent(state: SupervisorState) -> Dict:
    print("📝 Editor is reviewing the article...")
    prompt = f"""
You are an experienced news editor.

Review and improve the article below for clarity, factual tone, and readability. Ensure the article is concise and professional.

ARTICLE:
{state['article']}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    final_output = f"""
📰 FINAL NEWS ARTICLE
{'='*60}
Topic: {state['topic']}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*60}

{response.content.strip()}

{'='*60}
🔗 References:
""" + "\n".join(state["references"])
    return {
        "messages": [AIMessage(content="📝 Editor: Article approved.")],
        "final_article": final_output.strip(),
        "next_agent": "supervisor"
    }


# --- File Writer Agent (UPDATED) ---
def file_writer_agent(state: SupervisorState) -> Dict:
    print("💾 File Writer agent is working...")
    # Get the final content
    final_content = state.get("final_article") or state.get("article") or ""
    
    if not final_content:
        return {
            "messages": [AIMessage(content="⚠️ File Writer: No content to save.")],
            "markdown_content": "",
            "file_path": "",
            "next_agent": "end",
            "task_complete": True
        }
    
    # Use the file_writer_tool to save the file
    result = file_writer_tool.invoke({
        "content": final_content,
        "topic": state.get("topic", "article")
    })
    
    return {
        "messages": [AIMessage(content=f"💾 File Writer: {result.get('message', 'File saved.')}")],
        "markdown_content": final_content,
        "file_path": result.get("file_path", ""),
        "next_agent": "end",
        "task_complete": True
    }


# --- Router ---
def router(state: SupervisorState) -> Literal[
    "supervisor", "researcher", "writer", "editor", "file_writer", "__end__"
]:
    if state.get("task_complete") and state.get("file_path"):
        return END
    # Always ensure file_writer runs before ending
    next_agent = state.get("next_agent", "supervisor")
    if next_agent == "end" and not state.get("file_path"):
        return "file_writer"
    if next_agent == "end":
        return END
    return next_agent


# --- Workflow Graph ---
workflow = StateGraph(SupervisorState)
workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("writer", writer_agent)
workflow.add_node("editor", editor_agent)
workflow.add_node("file_writer", file_writer_agent)

workflow.set_entry_point("supervisor")

for node in ["supervisor", "researcher", "writer", "editor", "file_writer"]:
    workflow.add_conditional_edges(
        node,
        router,
        {
            "supervisor": "supervisor",
            "researcher": "researcher",
            "writer": "writer",
            "editor": "editor",
            "file_writer": "file_writer",
            END: END
        }
    )

graph = workflow.compile()


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="AI News Agent API",
    description="Multi-agent system for automated news article generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for async execution
executor = ThreadPoolExecutor(max_workers=3)


# --- Request/Response Models ---

class JobStatus(str, Enum):
    PENDING = "pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    EDITING = "editing"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"


class ArticleRequest(BaseModel):
    topic: str = Field(
        ..., 
        description="The news topic to research and write about",
        min_length=3,
        examples=["Latest developments in AI technology"]
    )


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    topic: str
    created_at: datetime
    message: str


class ArticleResponse(BaseModel):
    status: JobStatus
    topic: str
    article: Optional[str] = None
    research_summary: Optional[str] = None
    references: Optional[List[str]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    markdown_content: Optional[str] = None
    file_path: Optional[str] = None  # NEW: Include file path


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    llm_model: str


# --- In-memory job storage ---
jobs: Dict[str, Dict] = {}


# --- Helper Functions ---

def update_job_status(job_id: str, status: JobStatus, **kwargs):
    """Update job status and additional fields"""
    if job_id in jobs:
        jobs[job_id]["status"] = status
        jobs[job_id].update(kwargs)
        print(f"📊 Job {job_id[:8]}... status: {status}")


async def run_agent_workflow(job_id: str, topic: str):
    """Run the agent workflow asynchronously"""
    try:
        print(f"\n🚀 Starting workflow for job: {job_id[:8]}...")
        update_job_status(job_id, JobStatus.RESEARCHING)
        
        # Run the workflow in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            graph.invoke,
            {
                "topic": topic,
                "messages": [HumanMessage(content=topic)]
            }
        )
        
        # Update job with results, including file_path
        update_job_status(
            job_id,
            JobStatus.COMPLETED,
            article=result.get("final_article", ""),
            research_summary=result.get("research_summary", ""),
            references=result.get("references", []),
            markdown_content=result.get("markdown_content", result.get("final_article", "")),
            file_path=result.get("file_path", ""),
            completed_at=datetime.now()
        )
        
        print(f"✅ Workflow completed for job: {job_id[:8]}...")
        
    except Exception as e:
        print(f"❌ Workflow failed for job {job_id[:8]}...: {str(e)}")
        update_job_status(
            job_id,
            JobStatus.FAILED,
            error=str(e),
            completed_at=datetime.now()
        )


# --- API Endpoints ---

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - Health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        llm_model=llm_model_name or "unknown"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        llm_model=llm_model_name or "unknown"
    )


# --- Download Markdown Content Endpoint (UPDATED) ---
@app.get("/api/v1/articles/download-markdown")
async def download_article_markdown():
    """
    Download the latest generated markdown content as a file.
    """
    # Find the most recent completed job with file_path
    completed_jobs = [job for job in jobs.values() if job.get("status") == JobStatus.COMPLETED]
    if not completed_jobs:
        raise HTTPException(status_code=404, detail="No completed article found for download.")
    
    # Sort by created_at descending
    completed_jobs.sort(key=lambda x: x["created_at"], reverse=True)
    job = completed_jobs[0]
    
    # Get file path
    file_path = job.get("file_path")
    if file_path and os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type="text/markdown",
            filename=os.path.basename(file_path)
        )
    
    # Fallback to content
    content = job.get("markdown_content") or job.get("final_article") or job.get("article")
    if not content:
        raise HTTPException(status_code=404, detail="No article content available for download.")
    
    return StreamingResponse(
        iter([content]),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=final.md"}
    )


from fastapi import Request

# --- Direct Article Generation Endpoint (UPDATED for UI) ---
@app.post("/api/v1/articles/generate", response_model=ArticleResponse, status_code=200)
async def generate_article_direct(request: ArticleRequest):
    """
    Generate a news article based on the provided topic.
    Returns the article, markdown content, and download URL for UI.
    """
    created_at = datetime.now()
    try:
        print(f"\n📝 Direct article request")
        print(f"   Topic: {request.topic}")

        # Run the workflow synchronously
        result = await asyncio.get_event_loop().run_in_executor(
            executor,
            graph.invoke,
            {
                "topic": request.topic,
                "messages": [HumanMessage(content=request.topic)]
            }
        )

        completed_at = datetime.now()
        # Build download URL if file_path exists
        file_path = result.get("file_path", "")
        filename = os.path.basename(file_path) if file_path else None
        download_url = f"/api/v1/articles/download/{filename}" if filename else None

        # Return markdown_content and download_url for UI
        return {
            "status": JobStatus.COMPLETED,
            "topic": request.topic,
            "article": result.get("final_article", ""),
            "research_summary": result.get("research_summary", ""),
            "references": result.get("references", []),
            "created_at": created_at,
            "completed_at": completed_at,
            "error": None,
            "markdown_content": result.get("markdown_content", result.get("final_article", "")),
            "file_path": file_path,
            "download_url": download_url
        }
    except Exception as e:
        print(f"❌ Direct workflow failed: {str(e)}")
        return {
            "status": JobStatus.FAILED,
            "topic": request.topic,
            "article": None,
            "research_summary": None,
            "references": None,
            "created_at": created_at,
            "completed_at": datetime.now(),
            "error": str(e),
            "markdown_content": None,
            "file_path": None,
            "download_url": None
        }
# --- Download Specific Markdown File Endpoint ---
@app.get("/api/v1/articles/download/{filename}")
async def download_specific_markdown(filename: str):
    """
    Download a specific markdown file by filename from the generated_articles directory.
    """
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type="text/markdown",
            filename=filename
        )
    raise HTTPException(status_code=404, detail="File not found.")


@app.get("/api/v1/articles/status/{job_id}", response_model=ArticleResponse)
async def get_article_status(job_id: str):
    """
    Get the status and results of an article generation job.
    
    Returns the current status and, if completed, the full article.
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=404, 
            detail=f"Job not found: {job_id}"
        )
    
    job = jobs[job_id]
    return ArticleResponse(**job)


@app.get("/api/v1/articles/list", response_model=List[ArticleResponse])
async def list_articles(
    limit: int = 10,
    status: Optional[JobStatus] = None
):
    """
    List all article generation jobs with optional filtering.
    
    Query parameters:
    - limit: Maximum number of results (default: 10)
    - status: Filter by job status (optional)
    """
    filtered_jobs = []
    
    for job in jobs.values():
        if status is None or job["status"] == status:
            filtered_jobs.append(ArticleResponse(**job))
    
    # Sort by created_at descending
    filtered_jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    return filtered_jobs[:limit]


@app.delete("/api/v1/articles/{job_id}")
async def delete_article_job(job_id: str):
    """
    Delete an article generation job
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=404, 
            detail=f"Job not found: {job_id}"
        )
    
    del jobs[job_id]
    
    return {
        "message": "Job deleted successfully",
        "job_id": job_id,
        "timestamp": datetime.now()
    }


@app.get("/api/v1/stats")
async def get_statistics():
    """
    Get system statistics including job counts by status
    """
    total_jobs = len(jobs)
    status_counts = {}
    
    for job in jobs.values():
        status = job["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total_jobs": total_jobs,
        "status_breakdown": status_counts,
        "timestamp": datetime.now(),
        "llm_model": llm_model_name
    }


# --- Main Entry Point ---

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI News Agent System")
    parser.add_argument(
        "--mode",
        choices=["cli", "api"],
        default="api",
        help="Run mode: 'cli' for command line or 'api' for API server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API port (default: 8000)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "cli":
        # Original CLI mode
        print("\n" + "="*60)
        print("AI News Agent - CLI Mode")
        print("="*60 + "\n")
        
        topic = input("🗞️  Enter news topic: ")
        result = graph.invoke({
            "topic": topic,
            "messages": [HumanMessage(content=topic)]
        })
        print("\n" + result.get("final_article", "No article generated."))
        if result.get("file_path"):
            print(f"\n✅ Article saved to: {result.get('file_path')}")
        
    else:
        # API mode
        print("\n" + "="*60)
        print("AI News Agent - API Mode")
        print("="*60)
        print(f"🚀 Starting server on http://{args.host}:{args.port}")
        print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
        print(f"📖 ReDoc: http://{args.host}:{args.port}/redoc")
        print(f"📁 Articles saved to: {os.path.abspath(OUTPUT_DIR)}")
        print("="*60 + "\n")
        
        uvicorn.run(
            app, 
            host=args.host, 
            port=args.port,
            log_level="info"
        )