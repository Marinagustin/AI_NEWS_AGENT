from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage
from app.workflow import graph

# --- Supervisor Agent ---
def supervisor_agent(state):
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
    response = graph.llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

# --- Researcher Agent ---
def researcher_agent(state):
    print("🔍 Researcher is working...")
    topic = state["topic"]
    result = graph.search_web.invoke(topic)
    return {
        "research_summary": result.get("summary", ""),
        "references": result.get("links", [])
    }

# --- Writer Agent ---
def writer_agent(state):
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
    response = graph.llm.invoke([HumanMessage(content=prompt)])
    return {"article": response.content.strip()}

# --- Editor Agent ---
def editor_agent(state):
    print("📝 Editor is reviewing the article...")
    prompt = f"""
You are an experienced news editor.

Review and improve the article below for clarity, factual tone, and readability. Ensure the article is concise and professional.

ARTICLE:
{state['article']}
"""
    response = graph.llm.invoke([HumanMessage(content=prompt)])
    return {"final_article": response.content.strip()}

# --- File Writer Agent ---
def file_writer_agent(state):
    print("💾 File Writer agent is working...")
    final_content = state.get("final_article") or state.get("article") or ""
    if not final_content:
        return {"error": "No content to save."}
    # Save to file logic here
    return {"file_path": "path/to/file.md"}