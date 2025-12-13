import os
from typing import Dict, Literal
from datetime import datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()

llm_model_name = os.getenv("LLM_MODEL_NAME")
llm = init_chat_model(llm_model_name)
print("✅ LLM initialized")


class SupervisorState(MessagesState):
    next_agent: str = ""
    topic: str = ""
    research_summary: str = ""
    references: list[str] = []
    article: str = ""
    final_article: str = ""
    task_complete: bool = False

@tool
def search_web(query: str) -> Dict:
    """Search the web using Tavily"""
    search = TavilySearchResults(max_results=5)
    results = search.invoke(query)

    summaries = []
    links = []

    for r in results:
        summaries.append(r["content"])
        links.append(r["url"])

    return {
        "summary": "\n\n".join(summaries),
        "links": links
    }

def supervisor_agent(state: SupervisorState) -> Dict:
    if not state.get("research_summary"):
        return {
            "messages": [AIMessage(content="📋 Supervisor: Assigning Researcher")],
            "next_agent": "researcher"
        }

    if not state.get("article"):
        return {
            "messages": [AIMessage(content="✍️ Supervisor: Assigning Writer")],
            "next_agent": "writer"
        }

    if not state.get("final_article"):
        return {
            "messages": [AIMessage(content="📝 Supervisor: Assigning Editor")],
            "next_agent": "editor"
        }

    return {
        "messages": [AIMessage(content="✅ Supervisor: Task completed")],
        "next_agent": "end",
        "task_complete": True
    }

def researcher_agent(state: SupervisorState) -> Dict:
    topic = state["topic"]

    result = search_web.invoke(topic)

    return {
        "messages": [AIMessage(content="🔍 Researcher: Web research completed")],
        "research_summary": result["summary"],
        "references": result["links"],
        "next_agent": "supervisor"
    }

def writer_agent(state: SupervisorState) -> Dict:
    prompt = f"""
Write a well-structured news article on:

Topic: {state['topic']}

Research:
{state['research_summary']}

Include:
- Headline
- Introduction
- Key developments
- Conclusion
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "messages": [AIMessage(content="✍️ Writer: Article drafted")],
        "article": response.content,
        "next_agent": "supervisor"
    }

def editor_agent(state: SupervisorState) -> Dict:
    prompt = f"""
You are an editor.

Review and improve the article below.
Ensure clarity, factual tone, and readability.

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

{response.content}

{'='*60}
🔗 References:
""" + "\n".join(state["references"])

    return {
        "messages": [AIMessage(content="📝 Editor: Article approved")],
        "final_article": final_output,
        "next_agent": "supervisor"
    }


def router(state: SupervisorState) -> Literal[
    "supervisor", "researcher", "writer", "editor", "__end__"
]:
    if state.get("task_complete"):
        return END
    return state.get("next_agent", "supervisor")


workflow = StateGraph(SupervisorState)

workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("writer", writer_agent)
workflow.add_node("editor", editor_agent)

workflow.set_entry_point("supervisor")

for node in ["supervisor", "researcher", "writer", "editor"]:
    workflow.add_conditional_edges(
        node,
        router,
        {
            "supervisor": "supervisor",
            "researcher": "researcher",
            "writer": "writer",
            "editor": "editor",
            END: END
        }
    )

graph = workflow.compile()

# Optional: Visualize the graph
# try:
#     png_bytes = graph.get_graph().draw_mermaid_png()
#     with open("newsgraph.png", "wb") as f:
#         f.write(png_bytes)
#     print("Graph saved as graph.png")
# except Exception as e:
#     print("Graph visualization failed:", e)


if __name__ == "__main__":
    topic = input("🗞️ Enter news topic: ")

    result = graph.invoke({
        "topic": topic,
        "messages": [HumanMessage(content=topic)]
    })

    print(result["final_article"])

